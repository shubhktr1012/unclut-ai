import sys
import time
from typing import Callable, Optional, List, Dict, Any
from unsub_process import process_unsubscribe_links
from email_fetcher import delete_emails_from_sender, fetch_promotional_emails, preview_emails_with_sequence
from unsubscribe_list import extract_unsubscribe_links
from setup_gmail_service import create_service
from config import config as app_config

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

def run_with_loading(message: str, func: Callable, *args, **kwargs) -> Optional[bool]:
    """Run a function with a loading indicator."""
    safe_print(f"\n    {BLUE}{message}...{RESET}", end="\r")
    try:
        result = func(*args, **kwargs)
        safe_print(" " * 50, end="\r")  # Clear the line
        safe_print(f"    {GREEN}✓ {message} completed successfully!{RESET}")
        return result
    except Exception as e:
        safe_print(" " * 50, end="\r")  # Clear the line
        safe_print(f"    {RED}✗ Error during {message.lower()}: {str(e)}{RESET}")
        return False

def get_senders_to_process(service) -> List[Dict[str, Any]]:
    """Helper function to get senders from promotional emails."""
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

def main():
    """Main function to run the CLI menu."""
    # Initialize Gmail service
    try:
        service = create_service()
    except Exception as e:
        safe_print(f"\n    {RED}Failed to initialize Gmail service: {str(e)}{RESET}")
        safe_print("    Please check your credentials and try again.")
        sys.exit(1)
    
    while True:
        clear_screen()
        display_banner()
        display_menu()
        
        choice = get_user_choice()
        
        if choice == "1":  # Only Unsubscribe
            clear_screen()
            safe_print("\n    {BLUE}=== UNSUBSCRIBE ONLY ==={RESET}\n")
            selected_emails = get_senders_to_process(service)
            if selected_emails:
                senders = [email['sender_email'] for email in selected_emails]
                # For each sender, we need to fetch emails to get unsubscribe links
                for sender in senders:
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
                        run_with_loading("Processing unsubscribe requests",
                                       lambda l=links, s=[sender]: process_unsubscribe_links(l, s, dry_run=app_config['DRY_RUN']))
                        
                    except Exception as e:
                        safe_print(f"    {RED}Error processing {sender}: {str(e)}{RESET}")
            
        elif choice == "2":  # Only Delete
            clear_screen()
            safe_print("\n    {BLUE}=== DELETE EMAILS ONLY ==={RESET}\n")
            selected_emails = get_senders_to_process(service)
            if selected_emails:
                for email in selected_emails:
                    sender = email['sender_email']
                    run_with_loading(f"Deleting emails from {sender}", 
                                   lambda s=sender: delete_emails_from_sender(service, s, dry_run=app_config['DRY_RUN']))
            
        elif choice == "3":  # Both Unsubscribe and Delete
            clear_screen()
            safe_print("\n    {BLUE}=== UNSUBSCRIBE AND DELETE ==={RESET}\n")
            selected_emails = get_senders_to_process(service)
            if selected_emails:
                senders = [email['sender_email'] for email in selected_emails]
                if run_with_loading("Processing unsubscribe requests", 
                                  lambda: process_unsubscribe_links([], senders, dry_run=app_config['DRY_RUN'])):
                    for email in selected_emails:
                        sender = email['sender_email']
                        run_with_loading(f"Deleting emails from {sender}", 
                                       lambda s=sender: delete_emails_from_sender(service, sender, dry_run=app_config['DRY_RUN']))
            
        elif choice == "4":  # Help
            clear_screen()
            show_help()
            continue
            
        elif choice == "5":  # Quit
            safe_print("\n    {BLUE}Thank you for using Gmail Unsubscriber & Cleaner. Goodbye! \ud83d\udc4b{RESET}\n")
            sys.exit(0)
        
        # Pause before returning to menu
        safe_print("\n    {GRAY}Press Enter to return to the main menu...{RESET}", end="")
        input()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        safe_print("\n\n    {BLUE}Operation cancelled by user. Exiting...{RESET}\n")
        sys.exit(0)
