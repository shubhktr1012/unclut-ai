import re
import base64
import logging
from typing import List, Dict, Any, Union
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_unsubscribe_links(service_or_email_data, user_id='me', max_results=20):
    """
    Extract unsubscribe links from Gmail messages with improved HTML parsing.

    Args:
        service_or_email_data: Either an authorized Gmail API service instance or a single email message data dict
        user_id: Gmail user ID, usually "me" (only used if service is provided)
        max_results: How many messages to scan (only used if service is provided)

    Returns:
        List of unsubscribe links.
    """
    unsubscribe_links = []
    
    try:
        # If a service object is provided, fetch messages
        if hasattr(service_or_email_data, 'users'):
            logger.info(f"Fetching up to {max_results} messages...")
            results = service_or_email_data.users().messages().list(
                userId=user_id, 
                labelIds=['INBOX'], 
                maxResults=max_results
            ).execute()
            
            for msg in results.get('messages', [])[:max_results]:  # Limit to max_results
                try:
                    msg_data = service_or_email_data.users().messages().get(
                        userId=user_id, 
                        id=msg['id'], 
                        format='full'
                    ).execute()
                    _process_email(msg_data, unsubscribe_links)
                except Exception as e:
                    logger.error(f"Error processing message {msg.get('id')}: {str(e)}")
        else:
            # If a single email data dict is provided
            if not isinstance(service_or_email_data, dict):
                logger.error("Invalid email data format. Expected a dictionary.")
                return []
                
            # Extract the message data if it's a Gmail message
            if 'payload' in service_or_email_data and 'headers' in service_or_email_data['payload']:
                _process_email(service_or_email_data, unsubscribe_links)
            else:
                logger.error("Invalid email message format. Missing 'payload' or 'headers'.")
    except Exception as e:
        logger.error(f"Error in extract_unsubscribe_links: {str(e)}")
    
    # Remove duplicates while preserving order and filter out None/empty values
    seen = set()
    return [x for x in unsubscribe_links if x and not (x in seen or seen.add(x))]

def _extract_links_from_html(html_content: str) -> List[str]:
    """Extract unsubscribe links from HTML content using BeautifulSoup."""
    if not html_content:
        return []
    
    links = set()
    
    try:
        # Clean up common HTML issues
        html_content = html_content.replace('=\r\n', '').replace('=\n', '')
        
        # Try to parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Common patterns in unsubscribe links
        patterns = [
            r'unsubscribe',
            r'email_preferences',
            r'preferences',
            r'optout',
            r'opt-out',
            r'manage_preferences',
            r'emailpreferences',
            r'email-preferences',
            r'email_optout',
            r'email-optout'
        ]
        
        # Find all links that match our patterns
        for pattern in patterns:
            for a in soup.find_all('a', href=re.compile(pattern, re.IGNORECASE)):
                href = a.get('href', '').strip()
                if href:
                    links.add(href)
        
        # Also look for mailto: links with unsubscribe in the email
        for a in soup.find_all('a', href=re.compile(r'mailto:.*unsubscribe', re.IGNORECASE)):
            href = a.get('href', '').strip()
            if href:
                links.add(href)
                
    except Exception as e:
        logger.warning(f"Error parsing HTML: {str(e)}")
        # Fallback to simple regex if BeautifulSoup fails
        links.update(re.findall(r'https?://[^\s">]+unsubscribe[^\s">]*', html_content, re.IGNORECASE))
    
    return list(links)

def _process_email(email_data: Dict[str, Any], links_list: List[str]) -> None:
    """Process a single email's data and extract unsubscribe links."""
    try:
        payload = email_data.get('payload', {})
        headers = {}
        
        # Extract headers into a dictionary for easier access
        for header in payload.get('headers', []):
            name = header.get('name', '').lower()
            value = header.get('value', '')
            headers[name] = value
        
        # Check List-Unsubscribe header first
        if 'list-unsubscribe' in headers:
            value = headers['list-unsubscribe']
            found_links = re.findall(r'<([^>]*)>', value)  # Get everything between <>
            found_links = [link for link in found_links if link.startswith(('http://', 'https://', 'mailto:'))]
            if found_links:
                logger.debug(f"Found {len(found_links)} unsubscribe links in headers")
                links_list.extend(found_links)
                return  # Found links in header, no need to check body
        
        # Check email body for unsubscribe links
        parts = payload.get('parts', [])
        if not parts and payload.get('body', {}).get('data'):
            parts = [payload]  # Handle non-multipart emails
            
        for part in parts:
            mime_type = part.get('mimeType', '').lower()
            body_data = part.get('body', {}).get('data')
            
            if not body_data:
                continue
                
            try:
                # Decode the body data
                if mime_type == 'text/html' or 'html' in mime_type:
                    html = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                    found_links = _extract_links_from_html(html)
                    if found_links:
                        logger.debug(f"Found {len(found_links)} unsubscribe links in HTML body")
                        links_list.extend(found_links)
                        
                elif mime_type == 'text/plain' or 'text' in mime_type:
                    text = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                    found_links = re.findall(r'https?://[^\s"]+unsubscribe[^\s">]*', text, re.IGNORECASE)
                    if found_links:
                        logger.debug(f"Found {len(found_links)} unsubscribe links in plain text")
                        links_list.extend(found_links)
                        
            except Exception as e:
                logger.warning(f"Error processing email part: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in _process_email: {str(e)}")
