import re
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple, Set, Optional
import logging
from datetime import datetime
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urljoin

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unsubscribe.log'),
        logging.StreamHandler()
    ]
)

# Common headers to mimic a browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',
}

def is_unsubscribe_confirmed(html_content: str) -> bool:
    """
    Check if the HTML content confirms successful unsubscription.
    Uses a combination of regex patterns and HTML parsing for better accuracy.
    
    Args:
        html_content: The HTML content to analyze
        
    Returns:
        bool: True if unsubscription is confirmed, False otherwise
    """
    if not html_content:
        return False
    
    # Convert to lowercase for case-insensitive matching
    content = html_content.lower()
    soup = BeautifulSoup(content, 'html.parser')
    
    # Common confirmation patterns (positive matches)
    positive_patterns = [
        r'\b(?:you\s+have\s+been|successfully|success!?)\s+unsubscribed\b',
        r'\bunsubscrib(?:ed|tion)\s+(?:was\s+)?successful(?:ly)?\b',
        r'\b(?:preferences|subscription)\s+updated\b',
        r'\b(?:you\s+are\s+now\s+unsubscribed)\b',
        r'\bunsubscribe\s+confirmed\b',
    ]
    
    # Negative patterns (if these are present, it's not a confirmation)
    negative_patterns = [
        r'\balready\s+(?:un)?subscribed\b',
        r'\b(?:please\s+)?confirm\s+your\s+unsubscription\b',
        r'\bverify\s+unsubscription\b',
        r'\bclick\s+to\s+confirm\b',
    ]
    
    # Check for negative patterns first
    for pattern in negative_patterns:
        if re.search(pattern, content):
            return False
    
    # Check for positive patterns
    for pattern in positive_patterns:
        if re.search(pattern, content):
            return True
    
    # Additional checks using BeautifulSoup
    # Look for common confirmation elements
    confirmation_selectors = [
        '.confirmation',
        '.success',
        '.alert-success',
        '.status-msg',
        '#unsubscribe-confirmation',
        '[class*="success"]',
        '[class*="confirm"]',
    ]
    
    for selector in confirmation_selectors:
        if soup.select(selector):
            # Check if the element contains confirmation text
            for element in soup.select(selector):
                element_text = element.get_text().lower()
                if any(keyword in element_text for keyword in ['unsub', 'success', 'confirm']):
                    return True
    
    return False

def unsubscribe_from_link(link: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    Attempt to unsubscribe from a given link.
    
    Args:
        link: The unsubscribe URL
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Skip if the link is not http(s)
        if not link.startswith(('http://', 'https://')):
            return False, f"Invalid URL: {link}"
            
        # Handle SendGrid unsubscribe links specifically
        if 'sendgrid.net' in link or 'sendgrid.com' in link:
            return handle_sendgrid_unsubscribe(link, timeout)
            
        # Make the initial GET request
        response = requests.get(
            link,
            headers=HEADERS,
            timeout=timeout,
            allow_redirects=True,
            verify=True  # Verify SSL certificates
        )
        
        # Log the final URL (after redirects)
        final_url = response.url
        redirect_info = f" (redirected from {link})" if final_url != link else ""
        
        # Check if the page looks like a confirmation page
        if response.status_code == 200:
            is_confirmed = is_unsubscribe_confirmed(response.text)
            if is_confirmed:
                return True, f"Successfully unsubscribed{redirect_info}"
            else:
                # If not confirmed, try to find and submit a form
                form_submitted = submit_unsubscribe_form(response.text, final_url, timeout)
                if form_submitted:
                    return True, f"Form submitted successfully{redirect_info}"
                return False, f"Unsubscription confirmation not detected{redirect_info}\nYou may need to unsubscribe manually: {final_url}"
        else:
            return False, f"Request failed with status code: {response.status_code}{redirect_info}"
            
    except requests.exceptions.RequestException as e:
        return False, f"Request error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def handle_sendgrid_unsubscribe(link: str, timeout: int) -> Tuple[bool, str]:
    """
    Handle SendGrid unsubscribe links which require a POST request with specific parameters.
    """
    try:
        # Extract the base URL and parameters
        parsed = urlparse(link)
        params = parse_qs(parsed.query)
        
        # Prepare the form data that SendGrid expects
        form_data = {}
        for key, value in params.items():
            if value:  # Only take the first value if multiple exist
                form_data[key] = value[0]
        
        # Add any additional required fields
        form_data.update({
            'unsub_confirm': '1',  # Confirm unsubscription
            'submit': 'Unsubscribe',
        })
        
        # Make a POST request to the same URL
        response = requests.post(
            f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
            data=form_data,
            headers={
                **HEADERS,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': f"{parsed.scheme}://{parsed.netloc}",
                'Referer': link,
            },
            timeout=timeout,
            allow_redirects=True,
            verify=True
        )
        
        if response.status_code == 200:
            # Check if the response indicates success
            if any(term in response.text.lower() for term in ['unsubscribed', 'success', 'thank you']):
                return True, "Successfully unsubscribed from SendGrid"
            else:
                return False, "SendGrid unsubscription response not confirmed"
        else:
            return False, f"SendGrid unsubscribe failed with status {response.status_code}"
            
    except Exception as e:
        return False, f"Error processing SendGrid unsubscribe: {str(e)}"

def submit_unsubscribe_form(html_content: str, base_url: str, timeout: int) -> bool:
    """
    Attempt to find and submit an unsubscribe form on the page.
    
    Returns:
        bool: True if a form was found and submitted, False otherwise
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for common unsubscribe form patterns
        forms = soup.find_all('form')
        for form in forms:
            form_action = form.get('action', '')
            form_method = form.get('method', 'get').lower()
            
            # Skip if this doesn't look like an unsubscribe form
            if not any(term in form_action.lower() or 
                      any(term in str(form).lower() for term in ['unsub', 'optout', 'preferences'])
                      for term in ['unsub', 'optout', 'preferences']):
                continue
                
            # Prepare form data
            form_data = {}
            for input_tag in form.find_all(['input', 'button']):
                if input_tag.get('type') == 'submit' and not form_data:
                    # Skip if we haven't found any other inputs yet
                    continue
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if name:
                    form_data[name] = value
            
            # Add common unsubscribe confirmation fields if they don't exist
            if not any('confirm' in k.lower() for k in form_data.keys()):
                form_data.update({
                    'unsub_confirm': '1',
                    'confirm': '1',
                    'submit': 'Unsubscribe'
                })
            
            # Determine the URL to submit to
            if form_action.startswith(('http://', 'https://')):
                submit_url = form_action
            else:
                submit_url = urljoin(base_url, form_action)
            
            # Submit the form
            if form_method == 'post':
                response = requests.post(
                    submit_url,
                    data=form_data,
                    headers={
                        **HEADERS,
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Origin': base_url.split('://')[0] + '://' + base_url.split('://')[1].split('/')[0],
                        'Referer': base_url,
                    },
                    timeout=timeout,
                    allow_redirects=True,
                    verify=True
                )
            else:
                response = requests.get(
                    submit_url,
                    params=form_data,
                    headers=HEADERS,
                    timeout=timeout,
                    allow_redirects=True,
                    verify=True
                )
            
            if response.status_code == 200:
                return True
                
    except Exception as e:
        logging.error(f"Error submitting unsubscribe form: {str(e)}")
        
    return False

def process_unsubscribe_links(unsub_links: List[str], selected_senders: List[str], dry_run: bool = True) -> Dict[str, Dict]:
    """
    Process unsubscribe links for selected senders.
    
    Args:
        unsub_links: List of unsubscribe links
        selected_senders: List of corresponding sender emails
        dry_run: If True, only log what would be done
        
    Returns:
        Dictionary with results for each sender and their unsubscribe attempts
    """
    results = {}
    processed_links = set()  # Track processed links to avoid duplicates
    
    # Validate inputs
    if not unsub_links or not selected_senders:
        error_msg = "No unsubscribe links or senders provided"
        logging.error(error_msg)
        return {'error': error_msg}
        
    if len(unsub_links) != len(selected_senders):
        error_msg = f"Mismatch between number of links ({len(unsub_links)}) and senders ({len(selected_senders)})"
        logging.error(error_msg)
        return {'error': error_msg}
    
    try:
        for link, sender in zip(unsub_links, selected_senders):
            # Skip if link is None, empty, or whitespace
            if not link or not str(link).strip():
                msg = f"Skipping empty/invalid link for sender: {sender}"
                logging.warning(msg)
                results[sender] = {
                    'status': 'skipped',
                    'link': '',
                    'message': msg,
                    'timestamp': datetime.now().isoformat()
                }
                continue
                
            # Clean and normalize the link
            link = str(link).strip()
            
            # Skip duplicate links for the same sender
            if (sender, link) in processed_links:
                info_msg = f"Skipping duplicate link for {sender}"
                logging.info(info_msg)
                results[f"{sender} (duplicate)"] = {
                    'status': 'skipped',
                    'link': link,
                    'message': info_msg,
                    'timestamp': datetime.now().isoformat()
                }
                continue
                
            # Mark this link as processed
            processed_links.add((sender, link))
            
            if dry_run:
                logging.info(f"[DRY-RUN] Would attempt to unsubscribe from {sender} using: {link}")
                results[sender] = {
                    'status': 'dry_run',
                    'link': link,
                    'message': 'Dry run - no action taken',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logging.info(f"Processing unsubscribe for {sender}...")
                try:
                    success, message = unsubscribe_from_link(link)
                    status = 'success' if success else 'failed'
                    logging.info(f"Unsubscribe for {sender}: {status} - {message}")
                    results[sender] = {
                        'status': status,
                        'link': link,
                        'message': message,
                        'timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    error_msg = f"Error processing unsubscribe for {sender}: {str(e)}"
                    logging.error(error_msg)
                    results[sender] = {
                        'status': 'error',
                        'link': link,
                        'message': error_msg,
                        'timestamp': datetime.now().isoformat()
                    }
    except Exception as e:
        error_msg = f"Unexpected error in process_unsubscribe_links: {str(e)}"
        logging.error(error_msg)
        return {'error': error_msg}
    
    # Log completion summary
    processed_count = len(results)
    skipped_count = sum(1 for r in results.values() if r.get('status') == 'skipped')
    success_count = sum(1 for r in results.values() if r.get('status') == 'success')
    failed_count = sum(1 for r in results.values() if r.get('status') in ['failed', 'error'])
    
    logging.info("\n" + "="*50)
    logging.info("UNSUBSCRIBE PROCESSING SUMMARY")
    logging.info("="*50)
    logging.info(f"Total processed: {processed_count}")
    logging.info(f"Successfully unsubscribed: {success_count}")
    logging.info(f"Skipped: {skipped_count}")
    logging.info(f"Failed/Errors: {failed_count}")
    
    if dry_run:
        logging.info("\nNOTE: This was a dry run. No actual unsubscribes were processed.")
    
    # Log detailed results at debug level
    logging.debug("\nDetailed results:" + "\n" + "\n".join(
        f"{sender}: {result['status']} - {result.get('message', 'No message')}" 
        for sender, result in results.items()
    ))
    
    return results  # Make sure to return the results

# Alias for backward compatibility
test_unsubscribe_actions = process_unsubscribe_links

# Make the function available when imported
__all__ = ['process_unsubscribe_links', 'test_unsubscribe_actions']