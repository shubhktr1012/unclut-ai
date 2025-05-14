import os
from dotenv import load_dotenv
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """Load configuration from .env file and environment variables."""
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Default configuration values
    config = {
        'MAX_SENDERS': 50,
        'MAX_EMAILS_TO_SCAN': 100,
        'DRY_RUN': False,
        'USER_ID': 'me',
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
                    pass  # Keep default if conversion fails
    
    return config

# Load config when module is imported
config = load_config()
