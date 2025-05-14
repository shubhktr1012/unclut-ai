from base64 import urlsafe_b64decode
import re

def extract_unsubscribe_links(service_or_email_data, user_id='me', max_results=20):
    """
    Extract unsubscribe links from Gmail messages.

    Args:
        service_or_email_data: Either an authorized Gmail API service instance or a single email message data dict
        user_id: Gmail user ID, usually "me" (only used if service is provided)
        max_results: How many messages to scan (only used if service is provided)

    Returns:
        List of unsubscribe links.
    """
    unsubscribe_links = []
    
    # If a service object is provided, fetch messages
    if hasattr(service_or_email_data, 'users'):
        messages = []
        results = service_or_email_data.users().messages().list(
            userId=user_id, 
            labelIds=['INBOX'], 
            maxResults=max_results
        ).execute()
        
        for msg in results.get('messages', []):
            msg_data = service_or_email_data.users().messages().get(
                userId=user_id, 
                id=msg['id'], 
                format='full'
            ).execute()
            _process_email(msg_data, unsubscribe_links)
    else:
        # If a single email data dict is provided
        _process_email(service_or_email_data, unsubscribe_links)
    
    return list(set(unsubscribe_links))  # Remove duplicates

def _process_email(email_data, links_list):
    """Helper function to process a single email's data and extract unsubscribe links."""
    payload = email_data.get('payload', {})
    headers = payload.get('headers', [])
    
    # Try to find "List-Unsubscribe" header
    for header in headers:
        if header.get('name', '').lower() == 'list-unsubscribe':
            value = header.get('value', '')
            found_links = re.findall(r'<(http[s]?://[^>]+)>', value)
            links_list.extend(found_links)
            if found_links:
                return  # Found links in header, no need to check body
    
    # Check body for visible unsubscribe links if not in headers
    parts = payload.get('parts', [])
    for part in parts:
        if part.get('mimeType') == 'text/html':
            body_data = part.get('body', {}).get('data')
            if body_data:
                try:
                    html = urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                    found_links = re.findall(r'href=[\'\"](http[s]?://[^\'\"]+?unsubscribe[^\'\"]*)[\'\"]', html, re.IGNORECASE)
                    links_list.extend(found_links)
                except Exception as e:
                    print(f"Error processing email body: {str(e)}")
