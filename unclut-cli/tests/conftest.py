"""
Pytest configuration and fixtures for tests.
"""
import pytest
from typing import List, Dict, Any

@pytest.fixture
def sample_senders() -> List[str]:
    """Return a list of sample sender email addresses."""
    return [
        "test1@example.com",
        "test2@example.com",
        "test3@example.com",
        "test4@example.com"
    ]

@pytest.fixture
def sample_links() -> List[str]:
    """Return a list of sample unsubscribe links."""
    return [
        "https://example.com/unsub/1",
        "https://example.com/unsub/2",
        "https://example.com/unsub/3",
        "https://example.com/unsub/4"
    ]

@pytest.fixture
def mock_gmail_service():
    """Create a mock Gmail service for testing."""
    class MockMessage:
        def __init__(self, msg_id, sender, subject):
            self.id = msg_id
            self.sender = sender
            self.subject = subject
    
    class MockService:
        def users(self):
            return self
        
        def messages(self):
            return self
        
        def list(self, userId, labelIds, maxResults):
            return self
        
        def execute(self):
            return {
                'messages': [
                    {'id': 'msg1', 'threadId': 't1'},
                    {'id': 'msg2', 'threadId': 't2'}
                ]
            }
        
        def get(self, userId, id, format):
            return self
        
        def batchDelete(self, userId, body):
            return self
    
    return MockService()
