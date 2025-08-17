import sys
import logging
import webbrowser
from typing import Callable, List, Dict, Any, Tuple, Optional
from unsub_process import process_unsubscribe_links
from email_fetcher import delete_emails_from_sender, fetch_promotional_emails, preview_emails_with_sequence
from unsubscribe_list import extract_unsubscribe_links
from setup_gmail_service import create_service
from config import config as app_config
from db import record_activity

USER_ID = app_config['USER_ID']

# ANSI color codes
BLUE = "\u001b[36m"
YELLOW = "\u001b[33m"
RED = "\u001b[31m"
GREEN = "\u001b[32m"
GRAY = "\u001b[90m"
RESET = "\u001b[0m"

def safe_print(*args, **kwargs):
    """Safely print text that may contain problematic Unicode characters."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # If we can't encode the output, replace problematic characters
        text = ' '.join(str(arg) for arg in args)
        cleaned = text.encode('utf-8', errors='replace').decode('utf-8')
        print(cleaned, **kwargs)

def clear_screen():
    """Clear the console screen."""
    safe_print("\033[H\033[J", end="")  # ANSI escape code to clear screen

def display_banner():
    """Display the application banner."""
    banner = """
    {BLUE}╔══════════════════════════════════════════╗
    ║      GMAIL UNSUBSCRIBER & CLEANER      ║
    ╚══════════════════════════════════════════╝{RESET}
    """
    safe_print(banner.format(BLUE=BLUE, RESET=RESET))

def display_menu():
    """Display the main menu options."""
    menu = """
    {YELLOW}1.{RESET} Only Unsubscribe from senders
    {YELLOW}2.{RESET} Only Delete emails
    {YELLOW}3.{RESET} Unsubscribe and Delete (Both)
    {YELLOW}4.{RESET} Help
    {YELLOW}5.{RESET} Quit
    """.format(YELLOW=YELLOW, RESET=RESET)
    safe_print(menu)

def get_user_choice() -> str:
    """Get and validate user's menu choice."""
    while True:
        choice = input("\n    Enter your choice (1-5): ").strip()
        if choice in ["1", "2", "3", "4", "5"]:
            return choice   
        safe_print(f"\n    {RED}Invalid choice. Please enter a number between 1 and 5.{RESET}")

def show_help():
    """Display help information."""
    help_text = """
    {BLUE}HELP MENU{RESET}
    
    {YELLOW}1.{RESET} Only Unsubscribe
       - Unsubscribes from senders listed in unsubscribe_list.py
       - No emails will be deleted
    
    {YELLOW}2.{RESET} Only Delete Emails
       - Deletes all emails from senders in unsubscribe_list.py
       - Does not unsubscribe from these senders
    
    {YELLOW}3.{RESET} Unsubscribe and Delete
       - Performs both unsubscribing and email deletion
       - This is the most comprehensive cleanup option
    
    {YELLOW}4.{RESET} Help
       - Shows this help information
    
    {YELLOW}5.{RESET} Quit
       - Exits the application
    """.format(BLUE=BLUE, YELLOW=YELLOW, RESET=RESET)
    safe_print(help_text)
    input("\n    Press Enter to return to the main menu...")

def run_with_loading(message: str, func: Callable, *args, **kwargs) -> bool | None:
    """
    Run a function with a loading indicator.
    
    Args:
        message: The message to display
        func: The function to run
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        The result of the function, or False if an exception occurred
        Returns None if the function returns None or an empty result
    """
    safe_print(f"\n    {BLUE}{message}...{RESET}", end="\r")
    try:
        result = func(*args, **kwargs)
        safe_print(" " * 50, end="\r")  # Clear the line
        
        # Only show success if we have a non-empty result
        if result is not None and result is not False and (not isinstance(result, (list, dict)) or result):
            safe_print(f"    {GREEN}✓ {message} completed successfully!{RESET}")
        else:
            safe_print(f"    {YELLOW}⚠ {message} completed with no results.{RESET}")
            
        return result
    except Exception as e:
        safe_print(" " * 50, end="\r")  # Clear the line
        error_msg = str(e)
        if not error_msg:
            error_msg = "Unknown error occurred"
        safe_print(f"    {RED}✗ Error during {message.lower()}: {error_msg}{RESET}")
        logging.error(f"Error in run_with_loading: {error_msg}", exc_info=True)
        return False

def get_senders_to_process(service) -> Dict[int, str]:
    """
    Helper function to get senders from promotional emails.
    
    Returns:
        Dictionary mapping sequence numbers to sender email addresses
    """
    safe_print(f"\n    {BLUE}Fetching promotional emails...{RESET}")
    promo_emails = fetch_promotional_emails(
        service, 
        max_senders=app_config['MAX_SENDERS'], 
        max_emails_to_scan=app_config['MAX_EMAILS_TO_SCAN']
    )
    
    if not promo_emails:
        safe_print(f"\n    {YELLOW}No promotional emails found.{RESET}")
        return [] 
    
    safe_print(f"\n    {BLUE}Select senders to process:{RESET}")
    selected_senders = preview_emails_with_sequence(promo_emails)
    
    if not selected_senders:
        safe_print(f"\n    {YELLOW}No senders selected.{RESET}")
        return []
    
    return selected_senders

def cli_main():
    """Main function to run the CLI menu."""
    clear_screen()
    display_banner()
    
    # Initialize Gmail service
    try:
        service = create_service()
        if not service:
            safe_print(f"{RED}Failed to create Gmail service. Please check your credentials.{RESET}")
            return
    except Exception as e:
        safe_print(f"{RED}Error initializing Gmail service: {str(e)}{RESET}")
        sys.exit(1)

    safe_print(f"\n    {GRAY}Attempting to fetch user profile...{RESET}")
    try:
        profile = service.users().getProfile(userId=USER_ID).execute()
        current_user_email = profile.get('emailAddress')
        if current_user_email:
            safe_print(f"\n    {GREEN}Logged in as: {current_user_email}{RESET}")
        else:
            safe_print(f"\n    {RED}Could not retrieve user email. Database logging will be disabled.{RESET}")
            current_user_email = None
    except Exception as e:
        safe_print(f"\n    {RED}Error fetching user profile: {e}{RESET}")
        safe_print(f"    {YELLOW}Database logging will be disabled for this session.{RESET}")
        current_user_email = None
    
    while True:
        clear_screen()
        display_banner()
        display_menu()
        
        choice = get_user_choice()
        
        if choice == "1":  # Only Unsubscribe
            clear_screen()
            safe_print("\n    {BLUE}=== UNSUBSCRIBE ONLY ==={RESET}\n")
            selected_senders = get_senders_to_process(service)
            if selected_senders:
                # For each sender, we need to fetch emails to get unsubscribe links
                for sequence, sender in selected_senders.items():
                    safe_print(f"\n    {BLUE}Processing sender: {sender}{RESET}")
                    # Fetch recent emails from this sender to find unsubscribe links
                    query = f"from:{sender} category:promotions"
                    try:
                        response = service.users().messages().list(
                            userId=USER_ID,
                            q=query,
                            maxResults=5  # Only check the most recent 5 emails
                        ).execute()
                        
                        messages = response.get('messages', [])
                        if not messages:
                            safe_print(f"    {YELLOW}No emails found from {sender} to extract unsubscribe links{RESET}")
                            continue
                            
                        # Get the first email to extract unsubscribe links
                        msg = service.users().messages().get(
                            userId=USER_ID,
                            id=messages[0]['id'],
                            format='full'
                        ).execute()
                        
                        # Extract unsubscribe links from the email
                        links = extract_unsubscribe_links(msg)
                        
                        if not links:
                            safe_print(f"    {YELLOW}No unsubscribe links found in emails from {sender}{RESET}")
                            continue
                            
                        safe_print(f"    Found {len(links)} unsubscribe link(s) for {sender}")
                        
                        # Process the unsubscribe links
                        for link in links:
                            if link.startswith('mailto:'):
                                safe_print(f"    {YELLOW}Mailto unsubscribe link found. Please unsubscribe manually: {link}{RESET}")
                                continue
                                
                            safe_print(f"    Processing unsubscribe link: {link[:100]}...")
                            try:
                                result = process_unsubscribe_links(
                                    unsub_links=[link],
                                    selected_senders=[sender],
                                    dry_run=app_config['DRY_RUN'],

                                )
                                
                                # Check if there was an error in processing
                                if 'error' in result:
                                    safe_print(f"    {RED}Error: {result['error']}{RESET}")
                                    continue
                                    
                                # Get the result for this sender
                                sender_result = result.get(sender, {})
                                status = sender_result.get('status', 'unknown')
                                message = sender_result.get('message', 'No message')
                                
                                if status == 'success':
                                    safe_print(f"    {GREEN}✓ Successfully processed unsubscribe request: {message}{RESET}")
                                    if current_user_email:
                                        record_activity(current_user_email, unsub_delta=1)
                                elif status == 'dry_run':
                                    safe_print(f"    {YELLOW}⚠ Dry run: {message}{RESET}")
                                else:
                                    safe_print(f"    {YELLOW}⚠ {message}{RESET}")
                                    
                            except Exception as e:
                                safe_print(f"    {RED}Error processing unsubscribe: {str(e)}{RESET}")
                    
                    except Exception as e:
                        safe_print(f"    {RED}Error processing {sender}: {str(e)}{RESET}")
            
        elif choice == "2":  # Only Delete
            clear_screen()
            safe_print("\n    {BLUE}=== DELETE EMAILS ONLY ==={RESET}\n")
            selected_senders = get_senders_to_process(service)
            if selected_senders:
                for sequence, sender in selected_senders.items():
                    res = run_with_loading(
                        f"Deleting emails from {sender}", 
                        lambda s=sender: delete_emails_from_sender(
                        service, 
                        s, 
                        dry_run=app_config['DRY_RUN'],
   
                        )
                    )
                    if isinstance(res, dict) and current_user_email:
                        record_activity(current_user_email, deleted_delta=res.get('deleted_count', 0))
             
        elif choice == "3":  # Both Unsubscribe and Delete
            clear_screen()
            safe_print("\n    {BLUE}=== UNSUBSCRIBE AND DELETE ==={RESET}\n")
            selected_senders = get_senders_to_process(service)
            if selected_senders:
                senders = []
                all_links = []
                
                # First collect all unsubscribe links for each sender
                for sequence, sender in selected_senders.items():
                    try:
                        # Get emails from this sender to find unsubscribe links
                        messages = service.users().messages().list(
                            userId='me',
                            q=f'from:{sender}',
                            maxResults=5  # Check up to 5 most recent emails
                        ).execute().get('messages', [])
                        
                        if messages:
                            # Get the most recent message
                            msg = service.users().messages().get(
                                userId='me',
                                id=messages[0]['id'],
                                format='full'
                            ).execute()
                            
                            # Extract unsubscribe links from the email
                            links = extract_unsubscribe_links(msg)
                            
                            if links:
                                # Handle mailto: links specially
                                if links[0].startswith('mailto:'):
                                    safe_print(f"    {YELLOW}Found mailto unsubscribe link for {sender}{RESET}")
                                    safe_print(f"    {YELLOW}Please manually unsubscribe by sending an email to: {links[0]}{RESET}")
                                    # Open default email client with pre-filled email
                                    try:
                                        webbrowser.open(links[0])
                                    except Exception as e:
                                        safe_print(f"    {RED}Could not open email client: {str(e)}{RESET}")
                                    continue  # Skip to next sender
                                else:
                                    senders.append(sender)
                                    all_links.append(links[0])
                                    safe_print(f"    Found HTTP unsubscribe link for {sender}")
                            else:
                                safe_print(f"    {YELLOW}No unsubscribe link found for {sender}{RESET}")
                        
                    except Exception as e:
                        safe_print(f"    {RED}Error processing {sender}: {str(e)}{RESET}")
                
                # Process unsubscribe links if we found any
                if senders and all_links and len(senders) == len(all_links):
                    res = run_with_loading("Processing unsubscribe requests", 
                                      lambda: process_unsubscribe_links(all_links, senders, dry_run=app_config['DRY_RUN']))
                    if isinstance(res, dict) and 'results' in res and current_user_email:
                        success_count = sum(1 for r in res['results'].values() if r.get('status') == 'success')
                        if success_count:
                            record_activity(current_user_email, unsub_delta=success_count)
                    
                    # After successful unsubscribe, delete the emails
                    if res:
                        for sender in senders:
                            del_res = run_with_loading(f"Deleting emails from {sender}", 
                                         lambda s=sender: delete_emails_from_sender(service, s, dry_run=app_config['DRY_RUN']))
                            if isinstance(del_res, dict) and current_user_email:
                                record_activity(current_user_email, deleted_delta=int(del_res.get('deleted_count', 0)))
                else:
                    safe_print(f"\n    {YELLOW}No unsubscribe links found for selected senders.{RESET}")
                    if senders:
                        safe_print(f"    {YELLOW}Deleting emails without unsubscribing...{RESET}")
                        for sender in senders:
                            run_with_loading(f"Deleting emails from {sender}", 
                                         lambda s=sender: delete_emails_from_sender(service, s, dry_run=app_config['DRY_RUN']))
            
        elif choice == "4":  # Help
            clear_screen()
            show_help()
            continue
            
        elif choice == "5":  # Quit
            safe_print(f"\n\n    {BLUE}Thank you for using Gmail Unsubscriber & Cleaner. Goodbye! \ud83d\udc4b{RESET}\n")
            sys.exit(0)
        
        # Pause before returning to menu
        safe_print(f"\n    {GRAY}Press Enter to return to the main menu...{RESET}", end="")
        input()

if __name__ == "__main__":
    try:
        cli_main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
