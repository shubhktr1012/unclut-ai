# Gmail Unsubscriber & Cleaner

A powerful command-line tool to help you reclaim your Gmail inbox. This script automates the tedious process of unsubscribing from promotional emails and bulk-deleting old messages from those senders.

## Features

-   **Smart Scan:** Automatically finds promotional emails and identifies unique senders.
-   **Interactive Menu:** A simple, easy-to-use command-line interface to guide you through the process.
-   **Selective Actions:** Choose to:
    -   Unsubscribe only
    -   Delete all emails from a sender
    -   Do both at the same time
-   **Automated Unsubscribe:** Intelligently finds and "clicks" unsubscribe links for you.
-   **Bulk Deletion:** Quickly deletes thousands of emails in batches.
-   **Safe & Secure:** Uses the official Gmail API with OAuth 2.0, so your credentials are never stored or exposed by the application.
-   **Dry Run Mode:** Test the script's actions without making any permanent changes to your inbox.

## How It Works

1.  **Authentication:** Securely connects to your Gmail account using the official Google API.
2.  **Fetch & Identify:** Scans your inbox for promotional emails and presents you with a clean, numbered list of senders.
3.  **Select Senders:** You choose which senders you want to deal with from the list.
4.  **Choose Action:** You decide whether to unsubscribe, delete, or do both.
5.  **Execute:**
    -   For **unsubscribing**, the tool finds the unsubscribe link in the most recent email and sends a request to it.
    -   For **deleting**, the tool finds all emails from that sender and deletes them in bulk.
6.  **Report:** The tool provides real-time feedback on the actions being performed.

## Getting Started

Follow these instructions to get the project up and running on your local machine.

### Prerequisites

-   Python 3.8+
-   `pip` package manager

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/unclut-ai.git
    cd unclut-ai/unclut-cli
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Google API Credentials:**
    -   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    -   Create a new project or select an existing one.
    -   Enable the **Gmail API** for your project.
    -   Go to "Credentials", click "Create Credentials", and choose "OAuth client ID".
    -   Select "Desktop app" as the application type.
    -   Click "Download JSON" to download your credentials file.
    -   **Rename the downloaded file to `credentials.json`** and place it in the `unclut-cli` directory.

## Usage

Once the setup is complete, you can run the application with a single command:

```bash
python main.py
```

This will launch the interactive command-line menu. Just follow the on-screen prompts! The first time you run it, you will be asked to authenticate with your Google account in your web browser.

## Configuration

You can modify the application's behavior by editing the `config.py` file:

-   `DRY_RUN`: Set to `True` to simulate unsubscribing and deleting without making any actual changes. This is great for testing. Set to `False` for normal operation.
-   `MAX_SENDERS`: The maximum number of unique senders to fetch and display in the list.
-   `MAX_EMAILS_TO_SCAN`: The total number of emails to scan to find unique senders.

## Project Structure

```
unclut-cli/
├── main.py              # Main entry point of the application
├── cli_menu.py          # Handles all user interaction and the main menu
├── setup_gmail_service.py # Manages Google OAuth and Gmail API connection
├── email_fetcher.py     # Fetches, previews, and deletes emails
├── extract_unsubscribe.py # Extracts unsubscribe links from email content
├── unsub_process.py     # Processes (visits) the unsubscribe links
├── db.py                # Handles database logging of activities
├── config.py            # Application configuration
└── requirements.txt     # Project dependencies
```

## Contributing

Contributions are welcome! If you have suggestions for improvements, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
