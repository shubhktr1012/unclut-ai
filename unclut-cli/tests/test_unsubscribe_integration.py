"""
Integration tests for the unsubscribe functionality.
"""
import unittest
import logging
import os
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any

# Add parent directory to path so we can import our modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unsub_process import process_unsubscribe_links, unsubscribe_from_link
from email_fetcher import fetch_promotional_emails, delete_emails_from_sender
from unsubscribe_list import extract_unsubscribe_links

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_integration.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class TestUnsubscribeIntegration(unittest.TestCase):
    """Integration tests for unsubscribe functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_senders = [
            "test1@example.com",
            "test2@example.com",
            "test3@example.com",
            "test4@example.com"
        ]
        
        self.test_links = [
            "https://example.com/unsub/1",
            "https://example.com/unsub/2",
            "https://example.com/unsub/3",
            "https://example.com/unsub/4"
        ]
    
    def test_process_unsubscribe_links_success(self):
        """Test successful processing of unsubscribe links."""
        with patch('unsub_process.unsubscribe_from_link') as mock_unsubscribe:
            # Configure the mock to return success for all links
            mock_unsubscribe.return_value = (True, "Successfully unsubscribed")
            
            # Call the function with dry_run=True
            results = process_unsubscribe_links(
                unsub_links=self.test_links,
                selected_senders=self.test_senders,
                dry_run=True
            )
            
            # Verify results
            self.assertEqual(len(results), len(self.test_senders))
            for sender, result in results.items():
                self.assertIn(sender, self.test_senders)
                self.assertEqual(result['status'], 'dry_run')
    
    def test_process_unsubscribe_links_mismatch(self):
        """Test handling of mismatched links and senders."""
        # Should log an error and return an empty dictionary
        results = process_unsubscribe_links(
            unsub_links=self.test_links[:2],  # Only 2 links
            selected_senders=self.test_senders,  # But 4 senders
            dry_run=True
        )
        self.assertEqual(results, {})  # Should return empty dict on mismatch
    
    def test_process_unsubscribe_links_empty_links(self):
        """Test handling of empty or invalid links."""
        test_links = ["", "   ", "https://valid.com"]
        senders = ["sender1@example.com", "sender2@example.com", "sender3@example.com"]
        
        # Debug output
        print(f"\nTest links: {test_links}")
        print(f"Senders: {senders}")
        print(f"Number of links: {len(test_links)}")
        print(f"Number of senders: {len(senders)}")
        
        # Ensure the number of links matches the number of senders
        self.assertEqual(len(test_links), len(senders))
        
        results = process_unsubscribe_links(
            unsub_links=test_links,
            selected_senders=senders,
            dry_run=True
        )
        
        # Debug output
        print(f"Results: {results}")
        
        # Should process all senders, but mark empty/invalid ones as skipped
        self.assertEqual(len(results), len(senders))
        self.assertEqual(results[senders[0]]['status'], 'skipped')
        self.assertEqual(results[senders[1]]['status'], 'skipped')
        self.assertEqual(results[senders[2]]['status'], 'dry_run')

if __name__ == '__main__':
    unittest.main()
