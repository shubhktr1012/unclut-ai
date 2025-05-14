import re
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple, Set, Optional
import logging
from datetime import datetime
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
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
            
        # Make the request
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
                return False, f"Unsubscription confirmation not detected{redirect_info}"
        else:
            return False, f"Request failed with status code: {response.status_code}{redirect_info}"
            
    except requests.exceptions.RequestException as e:
        return False, f"Request error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

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
    if len(unsub_links) != len(selected_senders):
        logging.error("Mismatch between number of links and senders")
        return {}
    
    for link, sender in zip(unsub_links, selected_senders):
        # Skip if link is None, empty, or whitespace
        if not link or not str(link).strip():
            logging.warning(f"Skipping empty/invalid link for sender: {sender}")
            results[sender] = {
                'status': 'skipped',
                'link': '',
                'message': 'Empty or invalid unsubscribe link',
                'timestamp': datetime.now().isoformat()
            }
            continue
            
        # Clean and normalize the link
        link = str(link).strip()
        
        # Skip duplicate links for the same sender
        if (sender, link) in processed_links:
            logging.info(f"Skipping duplicate link for {sender}: {link}")
            results[f"{sender} (duplicate)"] = {
                'status': 'skipped',
                'link': link,
                'message': 'Duplicate link for this sender',
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
            success, message = unsubscribe_from_link(link)
            status = 'success' if success else 'failed'
            logging.info(f"Unsubscribe for {sender}: {status} - {message}")
            results[sender] = {
                'status': status,
                'link': link,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
    
    return results

# Alias for backward compatibility
test_unsubscribe_actions = process_unsubscribe_links

# Make the function available when imported
__all__ = ['process_unsubscribe_links', 'test_unsubscribe_actions']