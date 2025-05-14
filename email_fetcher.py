from typing import List, Dict, Any, Tuple
import re
from googleapiclient.discovery import Resource
from termcolor import colored
import datetime
import logging
from config import config as app_config

def fetch_promotional_emails(service: Resource, max_senders: int = 20, max_emails_to_scan: int = 1000, fetch_full_content: bool = False) -> List[Dict[str, Any]]:
    """
    Fetches up to `max_senders` promotional emails from unique senders,
    older than 14 days. By default fetches only metadata for preview.

    Args:
        service: Gmail API service object
        max_senders: Maximum number of unique senders to fetch emails from
        max_emails_to_scan: Maximum number of emails to scan before stopping
        fetch_full_content: If True, fetches the full email content (needed for unsubscribe link extraction)

    Returns:
        List of email message data containing sender information and optionally full content
    """
    unique_senders = {}
    messages = []
    query = "category:promotions older_than:14d"
    next_page_token = None
    emails_scanned = 0
    
    while len(unique_senders) < max_senders:
        # Check if we've reached our scan limit
        if emails_scanned >= max_emails_to_scan:
            print(f"Reached maximum scan limit of {max_emails_to_scan} emails")
            break

        results = service.users().messages().list(
            userId=app_config['USER_ID'],
            q=query,
            maxResults=100,
            pageToken=next_page_token
        ).execute()
        
        new_messages = results.get('messages', [])
        if not new_messages:
            break

        # Update the number of emails scanned
        emails_scanned += len(new_messages)
            
        for msg in new_messages:
            msg_format = 'full' if fetch_full_content else 'metadata'
            msg_data = service.users().messages().get(
                userId=app_config['USER_ID'],
                id=msg['id'],
                format=msg_format,
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            # Extract sender email from "From" header
            headers = msg_data.get('payload', {}).get('headers', [])
            sender = next((h['value'] for h in headers if h['name'] == 'From'), None)

            if sender:
                match = re.search(r'<(.*?)>', sender)
                sender_email = match.group(1) if match else sender.strip()

                if sender_email and sender_email not in unique_senders:
                    msg_data['sender_email'] = sender_email
                    msg_data['sender_display'] = sender  # also keeping full "From" for nicer preview
                    unique_senders[sender_email] = msg_data
                    messages.append(msg_data)

                    if len(unique_senders) >= max_senders:
                        break
                    
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break
            
    print(f"Found {len(messages)} emails from {len(unique_senders)} unique senders")
    return messages

def get_valid_sequence_numbers(input_str: str, max_index: int) -> List[int]:
    """
    Parses user input and returns valid sequence numbers.
    
    Args:
        input_str: User input string
        max_index: Maximum valid index
        
    Returns:
        List of valid sequence numbers
    """
    valid_numbers = []
    invalid_numbers = []
    
    # Handle special cases
    if not input_str.strip():
        print(colored("Error: No input provided.", 'red'))
        return []
    
    # Convert to lowercase for case-insensitive comparison
    input_str = input_str.lower()
    
    if input_str == 'all':
        return list(range(1, max_index + 1))
    if input_str == 'quit':
        return []
    
    # Split input and process each number, stripping whitespace
    numbers = [num.strip() for num in input_str.split()]
    for num in numbers:
        if not num:  # Skip empty strings
            continue
            
        try:
            num = int(num)
            if 1 <= num <= max_index:
                valid_numbers.append(num)
            else:
                invalid_numbers.append(num)
                print(colored(f"Error: Number {num} is out of range (1-{max_index})", 'red'))
        except ValueError:
            invalid_numbers.append(num)
            print(colored(f"Error: '{num}' is not a valid number", 'red'))
    
    if invalid_numbers:
        print("Valid numbers will be processed, invalid ones ignored.")
    
    return valid_numbers

def preview_emails_with_sequence(messages: List[Dict[str, Any]]) -> Dict[int, str]:
    """
    Prints email previews with sequence numbers and returns mapping of index → sender_email.
    
    Args:
        messages: List of email message data
        
    Returns:
        Dictionary mapping sequence numbers to sender email addresses
    """
    print("\n=== Preview of Promotional Emails ===\n")
    index_to_sender = {}

    for i, msg in enumerate(messages, start=1):
        try:
            # Get headers
            headers = msg.get('payload', {}).get('headers', [])
            if not headers:
                raise ValueError("No headers found in email message")
                
            # Extract subject and date with fallbacks
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Date not available')
            
            # Get sender information
            display_name = msg.get('sender_display', 'Unknown')
            sender_email = msg.get('sender_email', 'unknown@example.com')

            # Format date more nicely
            try:
                date_obj = datetime.datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
                formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
            except (ValueError, TypeError) as e:
                try:
                    # Try alternative date format
                    date_obj = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                    formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
                except ValueError as ve:
                    # If all parsing fails, use the raw date string (truncated)
                    print(colored(f"Warning: Could not parse date for email {i} (using raw date): {date}", 'yellow'))
                    formatted_date = date[:24]  # Take first 24 characters if parsing fails
            
            # Store sender information and print preview
            index_to_sender[i] = sender_email
            print(f"[{i}] {colored(display_name, 'cyan')} | {subject}")
            print(f"    {colored(formatted_date, 'yellow')} | {sender_email}")
            print("-" * 60)
            
        except Exception as e:
            print(colored(f"Error processing email {i} from {msg.get('sender_email', 'unknown')}: {str(e)}", 'red'))
            print("-" * 60)
            continue

    print("\nUse the sequence numbers above to select senders to unsubscribe.")
    print("Enter numbers separated by spaces (e.g., '1 3 5') or type 'all' to select all.")
    print("Type 'quit' to exit without unsubscribing.")
    print("Invalid numbers will be ignored and shown in red.")
    
    # Get user input
    while True:
        try:
            user_input = input("\nEnter sequence numbers: ").strip()
            
            # Get valid sequence numbers
            valid_numbers = get_valid_sequence_numbers(user_input, len(messages))
            
            # If user wants to quit
            if not valid_numbers:
                print("Operation cancelled.")
                return {}
            
            # Process valid numbers and ignore invalid ones
            selected_senders = {num: index_to_sender[num] for num in valid_numbers}
            
            # Show summary of selections
            if selected_senders:
                print(f"\nSelected {len(selected_senders)} sender(s) to unsubscribe from:")
                for num, email in selected_senders.items():
                    print(f"[{num}] {email}")
            else:
                print("No valid selections made.")
                continue

            # Confirm with user
            confirm = input("\nProceed with unsubscribing from these senders? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("Operation cancelled by user.")
                return {}

            # Return selected senders for processing
            return selected_senders
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return {}
        except Exception as e:
            print(colored(f"An unexpected error occurred: {str(e)}", 'red'))
            continue

def get_message_ids_for_sender(service, sender_email: str, max_results: int = 1000) -> List[str]:
    """
    Fetch all message IDs from a specific sender.
    
    Args:
        service: Gmail API service instance
        sender_email: Email address of the sender
        max_results: Maximum number of messages to fetch (max 500)
        
    Returns:
        List of message IDs
    """
    try:
        # Search for messages from the sender
        query = f'from:{sender_email}'
        response = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=min(max_results, 500)  # Gmail API max is 500 per page
        ).execute()
        
        message_ids = []
        while 'messages' in response and len(message_ids) < max_results:
            message_ids.extend([msg['id'] for msg in response['messages']])
            
            # If there are more messages and we haven't reached max_results
            if 'nextPageToken' in response and len(message_ids) < max_results:
                page_token = response['nextPageToken']
                response = service.users().messages().list(
                    userId='me',
                    q=query,
                    pageToken=page_token,
                    maxResults=min(max_results - len(message_ids), 500)
                ).execute()
            else:
                break
                
        return message_ids
        
    except Exception as e:
        logging.error(f"Error fetching message IDs for {sender_email}: {str(e)}")
        return []

def delete_messages_batch(service, message_ids: List[str], batch_size: int = 1000) -> Tuple[int, List[str]]:
    """
    Delete messages in batches using Gmail's batchDelete.
    
    Args:
        service: Gmail API service instance
        message_ids: List of message IDs to delete
        batch_size: Number of messages to delete in each batch (Gmail max is 1000)
        
    Returns:
        Tuple of (number of messages deleted, list of errors)
    """
    if not message_ids:
        return 0, []
    
    total_deleted = 0
    errors = []
    
    # Process in chunks of batch_size
    for i in range(0, len(message_ids), batch_size):
        batch = message_ids[i:i + batch_size]
        try:
            service.users().messages().batchDelete(
                userId='me',
                body={'ids': batch}
            ).execute()
            total_deleted += len(batch)
            logging.info(f"Deleted {len(batch)} messages (total: {total_deleted})")
        except Exception as e:
            error_msg = f"Error deleting batch {i//batch_size + 1}: {str(e)}"
            logging.error(error_msg)
            errors.append(error_msg)
    
    return total_deleted, errors

def delete_emails_from_sender(service, sender_email: str, max_messages: int = 10000) -> Dict[str, any]:
    """
    Delete all emails from a specific sender.
    
    Args:
        service: Gmail API service instance
        sender_email: Email address of the sender
        max_messages: Maximum number of messages to delete
        
    Returns:
        Dictionary with results including count of deleted messages and any errors
    """
    logging.info(f"Starting bulk delete for sender: {sender_email}")
    
    # First, get all message IDs
    logging.info("Fetching message IDs...")
    message_ids = get_message_ids_for_sender(service, sender_email, max_messages)
    
    if not message_ids:
        return {
            'sender': sender_email,
            'total_messages': 0,
            'deleted': 0,
            'errors': ['No messages found from this sender']
        }
    
    logging.info(f"Found {len(message_ids)} messages to delete from {sender_email}")
    
    # Delete messages in batches
    deleted_count, errors = delete_messages_batch(service, message_ids)
    
    return {
        'sender': sender_email,
        'total_messages': len(message_ids),
        'deleted': deleted_count,
        'errors': errors
    }
