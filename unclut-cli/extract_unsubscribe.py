"""
Script to extract unsubscribe links from emails more reliably.
"""
import base64
import re
import json
from typing import List, Dict, Any
from bs4 import BeautifulSoup

def extract_links_from_html(html_content: str) -> List[str]:
    """Extract unsubscribe links from HTML content."""
    if not html_content:
        return []
    
    # Try to decode if it's base64 encoded
    try:
        html_content = base64.b64decode(html_content).decode('utf-8', errors='ignore')
    except:
        pass
    
    # Clean up HTML entities and other common issues
    html_content = html_content.replace('=\r\n', '').replace('=\n', '')
    
    # Try to parse with BeautifulSoup
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for common unsubscribe link patterns
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
        links = []
        for pattern in patterns:
            for a in soup.find_all('a', href=re.compile(pattern, re.IGNORECASE)):
                href = a.get('href', '').strip()
                if href and href not in links:
                    links.append(href)
        
        # Also look for mailto: links with unsubscribe in the email
        for a in soup.find_all('a', href=re.compile(r'mailto:.*unsubscribe', re.IGNORECASE)):
            href = a.get('href', '').strip()
            if href and href not in links:
                links.append(href)
        
        return links
    
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        # Fallback to regex if BeautifulSoup fails
        return re.findall(r'https?://[^\s">]+unsubscribe[^\s">]*', html_content, re.IGNORECASE)

def process_email_data(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process email data and extract unsubscribe links."""
    result = {
        'id': email_data.get('id'),
        'snippet': email_data.get('snippet', ''),
        'from': '',
        'subject': '',
        'unsubscribe_links': [],
        'headers': {}
    }
    
    # Extract headers
    payload = email_data.get('payload', {})
    headers = {}
    for header in payload.get('headers', []):
        name = header.get('name', '').lower()
        value = header.get('value', '')
        headers[name] = value
        
        if name == 'from':
            result['from'] = value
        elif name == 'subject':
            result['subject'] = value
    
    result['headers'] = headers
    
    # Check List-Unsubscribe header
    if 'list-unsubscribe' in headers:
        links = re.findall(r'<(https?://[^>]+)>', headers['list-unsubscribe'])
        result['unsubscribe_links'].extend(links)
    
    # Check email body for unsubscribe links
    parts = payload.get('parts', [])
    for part in parts:
        if part.get('mimeType') == 'text/html':
            body_data = part.get('body', {}).get('data', '')
            if body_data:
                html_links = extract_links_from_html(body_data)
                result['unsubscribe_links'].extend(html_links)
    
    # Remove duplicates
    result['unsubscribe_links'] = list(set(result['unsubscribe_links']))
    
    return result

def main():
    """Main function to test the extraction."""
    try:
        # Load the email data from the debug file
        with open('email_debug.json', 'r', encoding='utf-8') as f:
            email_data = json.load(f)
        
        # Process the email
        result = process_email_data(email_data)
        
        # Print the results
        print("\n=== Email Information ===")
        print(f"From: {result['from']}")
        print(f"Subject: {result['subject']}")
        print(f"Snippet: {result['snippet']}")
        
        print("\n=== Unsubscribe Links Found ===")
        if result['unsubscribe_links']:
            for i, link in enumerate(result['unsubscribe_links'], 1):
                print(f"{i}. {link}")
        else:
            print("No unsubscribe links found in this email.")
        
        # Save the results
        with open('unsubscribe_results.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print("\nResults saved to 'unsubscribe_results.json'")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
