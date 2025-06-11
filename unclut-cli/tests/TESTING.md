# Testing Documentation

## Test Coverage

### Unit Tests

1. **unsub_process.py**
   - `process_unsubscribe_links()`
     - Handles matching number of links and senders
     - Handles empty/invalid links
     - Handles duplicate links
     - Processes unsubscribe requests in dry-run mode
     - Processes actual unsubscribe requests
   - `unsubscribe_from_link()`
     - Handles valid unsubscribe URLs
     - Handles invalid URLs
     - Handles network errors
     - Verifies unsubscribe confirmation

2. **email_fetcher.py**
   - `fetch_promotional_emails()`
   - `delete_emails_from_sender()`
   - `preview_emails_with_sequence()`

3. **unsubscribe_list.py**
   - `extract_unsubscribe_links()`
   - `_process_email()`

### Integration Tests

1. **test_unsubscribe_integration.py**
   - Test successful processing of unsubscribe links
   - Test handling of mismatched links and senders
   - Test handling of empty/invalid links
   - Test interaction between components

## Running Tests

### Prerequisites
- Python 3.7+
- pytest
- pytest-cov (for coverage reporting)
- Required packages from requirements.txt

### Running All Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests with coverage
pytest --cov=. --cov-report=html

# Run a specific test file
pytest tests/test_unsubscribe_integration.py -v
```

### Viewing Coverage Report

After running tests with coverage, open `htmlcov/index.html` in a web browser to view the coverage report.

## Test Data

Test data is provided through fixtures in `conftest.py`:

- `sample_senders`: List of test email senders
- `sample_links`: List of test unsubscribe links
- `mock_gmail_service`: Mock Gmail service for testing

## Adding New Tests

1. Create a new test file in the `tests` directory with the prefix `test_`
2. Use the existing fixtures or create new ones in `conftest.py`
3. Follow the existing test patterns and naming conventions
4. Add any new test dependencies to `requirements-test.txt`

## Test Maintenance

- Keep test data up to date with the application
- Update tests when making changes to the codebase
- Run tests locally before pushing changes
- Ensure all tests pass before merging to main
