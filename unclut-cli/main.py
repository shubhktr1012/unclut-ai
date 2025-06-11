#!/usr/bin/env python3
"""
Gmail Smart Unsubscriber - Main Entry Point

This script provides a command-line interface for unsubscribing from emails
and cleaning up your Gmail inbox.
"""

def main():
    """
    Main entry point for the Gmail Smart Unsubscriber.
    This is now just a wrapper that imports and runs the CLI menu.
    """
    try:
        from cli_menu import cli_main
        cli_main()
    except ImportError as e:
        print(f"Error: Failed to import required modules. {e}")
        print("Please make sure you have installed all the required dependencies.")
        print("You can install them using: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 1
    return 0

if __name__ == '__main__':
    main()
