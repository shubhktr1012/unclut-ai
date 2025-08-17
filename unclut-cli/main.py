#!/usr/bin/env python3
"""
Gmail Smart Unsubscriber - Main Entry Point

This script provides a command-line interface for unsubscribing from emails
and cleaning up your Gmail inbox.
"""
from __future__ import annotations

import logging
import os
import sys
import platform

# Type hints
from typing import Dict, Any, Union, List, Tuple, Callable
from typing import Optional as Opt

# Add parent directory to path to allow importing unclut_cli
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging before importing other modules to ensure proper logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Get logger for this module
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the Gmail Smart Unsubscriber CLI.
    """
    try:
        # Import and run the CLI menu
        from cli_menu import cli_main
        cli_main()
        
    except ImportError as e:
        print(f"Error: Failed to import required modules. {e}")
        print("Please make sure you have installed all the required dependencies.")
        print("You can install them using: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
