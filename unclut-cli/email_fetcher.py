from typing import List, Dict, Any, Tuple, Optional
import re
from googleapiclient.discovery import Resource
from termcolor import colored
import datetime
import logging
from config import config as app_config

def fetch_promotional_emails(service: Resource, max_senders: int = 20, max_emails_to_scan: int = 200, fetch_full_content: bool = False) -> List[Dict[str, Any]]:
    """
    Fetches up to `max_senders` promotional emails from unique senders,
    older than 14 days. Optimized for faster performance.

    Args:
        service: Gmail API service object
        max_senders: Maximum number of unique senders to fetch emails from
        max_emails_to_scan: Maximum number of emails to scan before stopping
        fetch_full_content: If True, fetches the full email content (slower)

    Returns:
        List of email message data containing sender information
    """
    unique_senders = {}
    messages = []
    
    # More specific query to reduce results
    query = "category:promotions older_than:14d -category:updates -category:social -category:forums"
    
    try:
        # First, get just the message IDs and basic metadata
        results = service.users().messages().list(
            userId=app_config['USER_ID'],
            q=query,
            maxResults=min(100, max_emails_to_scan),
            fields="messages(id,threadId),nextPageToken"
        ).execute()
        
        message_ids = [msg['id'] for msg in results.get('messages', [])]
        
        # Process messages in batches for better performance
        batch_size = 25
        for i in range(0, len(message_ids), batch_size):
            batch = message_ids[i:i + batch_size]
            
            for msg_id in batch:
                try:
                    # Get message with minimal metadata first
                    msg = service.users().messages().get(
                        userId=app_config['USER_ID'],
                        id=msg_id,
                        format='metadata',
                        metadataHeaders=['From', 'Subject', 'Date']
                    ).execute()
                    
                    # Extract headers
                    headers = {h['name'].lower(): h['value'] 
                             for h in msg.get('payload', {}).get('headers', [])}
                    
                    # Extract sender information
                    from_header = headers.get('from', '')
                    sender_match = re.search(r'([^<]+)<([^>]+)>', from_header)
                    
                    if sender_match:
                        sender_name = sender_match.group(1).strip()
                        sender_email = sender_match.group(2).strip()
                    else:
                        sender_name = from_header.strip()
                        sender_email = from_header.strip()
                    
                    # Only process if we haven't seen this sender yet
                    if sender_email and sender_email not in unique_senders:
                        unique_senders[sender_email] = True
                        
                        # Add sender info to message
                        msg['sender_display'] = sender_name
                        msg['sender_email'] = sender_email
                        
                        # Only fetch full content if explicitly needed
                        if fetch_full_content:
                            full_msg = service.users().messages().get(
                                userId=app_config['USER_ID'],
                                id=msg_id,
                                format='full'
                            ).execute()
                            msg.update(full_msg)
                        
                        messages.append(msg)
                        
                        # Stop if we have enough senders
                        if len(unique_senders) >= max_senders:
                            return messages
                            
                except Exception as e:
                    logging.error(f"Error processing message {msg_id}: {str(e)}")
                    continue
    
    except Exception as e:
        logging.error(f"Error fetching messages: {str(e)}")
    
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
    """
    print("\n=== Preview of Promotional Emails ===\n")
    index_to_sender = {}

    for i, msg in enumerate(messages, start=1):
        try:
            # Get headers
            headers = {h['name'].lower(): h['value'] 
                     for h in msg.get('payload', {}).get('headers', [])}
            
            # Extract subject and date with fallbacks
            subject = headers.get('subject', '(No Subject)')
            date = headers.get('date', 'Date not available')
            
            # Get sender information with fallbacks
            sender_name = msg.get('sender_display', 'Unknown')
            sender_email = msg.get('sender_email', 'unknown@example.com')

            # Format date
            formatted_date = date
            try:
                # Try parsing with timezone
                try:
                    date_obj = datetime.datetime.strptime(
                        date, '%a, %d %b %Y %H:%M:%S %z')
                except ValueError:
                    # Try without timezone
                    date_obj = datetime.datetime.strptime(
                        date.split('(')[0].strip(),  # Remove timezone info if present
                        '%a, %d %b %Y %H:%M:%S'
                    )
                formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
            except (ValueError, AttributeError) as e:
                # If parsing fails, use the first 16 chars of the date
                formatted_date = str(date)[:16]
            
            # Store sender information and print preview
            index_to_sender[i] = sender_email
            print(f"[{i}] {colored(sender_name, 'cyan')} | {subject}")
            print(f"    {colored(formatted_date, 'yellow')} | {sender_email}")
            print("-" * 60)
            
        except Exception as e:
            print(colored(f"Error processing email {i}: {str(e)}", 'red'))
            print("-" * 60)
    
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

def delete_emails_from_sender(service, sender_email: str, max_messages: int = 10000, dry_run: bool = False):
    """
    Delete all emails from a specific sender.
    
    Args:
        service: Gmail API service instance
        sender_email: Email address of the sender
        max_messages: Maximum number of messages to delete
        dry_run: If True, only simulate the deletion
        
    Returns:
        Dictionary with results including count of messages to be deleted and any errors
    """
    try:
        message_ids = get_message_ids_for_sender(service, sender_email, max_messages)
        total_messages = len(message_ids)
        
        if dry_run:
            return {
                'success': True,
                'deleted_count': total_messages,
                'errors': [],
                'sender': sender_email,
                'message': f'Would delete {total_messages} messages from {sender_email} (dry run)'
            }
        
        if not message_ids:
            return {
                'success': True,
                'deleted_count': 0,
                'errors': [],
                'sender': sender_email,
                'message': f'No messages found from {sender_email}'
            }
        
        # Delete messages in batches
        deleted_count, errors = delete_messages_batch(service, message_ids)
        
        return {
            'success': len(errors) == 0,
            'deleted_count': deleted_count,
            'errors': errors,
            'sender': sender_email,
            'message': f'Deleted {deleted_count} messages from {sender_email}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'deleted_count': 0,
            'error': str(e),
            'sender': sender_email,
            'message': f'Error deleting messages from {sender_email}: {str(e)}'
        }
