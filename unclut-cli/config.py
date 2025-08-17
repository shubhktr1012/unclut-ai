import json
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Define config path
CONFIG_DIR = os.path.expanduser('~/.unclut')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.json')

def load_config() -> Dict[str, Any]:
    """Load configuration from .env file and environment variables."""
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Default configuration values
    config = {
        'MAX_SENDERS': 50,
        'MAX_EMAILS_TO_SCAN': 100,
        'DRY_RUN': False,
        'USER_ID': 'me',  # 'me' is a special value for the authenticated user in Gmail API
    }
    
    # Update with environment variables if they exist
    for key in config.keys():
        value = os.getenv(key)
        if value is not None:
            # Convert string values to appropriate types
            if isinstance(config[key], bool):
                config[key] = value.lower() in ('true', '1', 't', 'y', 'yes')
            elif isinstance(config[key], int):
                try:
                    config[key] = int(value)
                except (ValueError, TypeError):
                    # Keep default if conversion fails
                    pass  
    
    return config

# Initialize config
config = load_config()
