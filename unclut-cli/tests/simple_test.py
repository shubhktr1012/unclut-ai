"""
Simple test script for unsubscribe functionality.
"""
import logging
import sys
from unsub_process import process_unsubscribe_links

# Configure logging to show debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def run_test():
    # Test data
    test_senders = ["sender1@example.com", "sender2@example.com"]
    test_links = ["https://example.com/unsub/1", "https://example.com/unsub/2"]

    print("\n" + "="*50)
    print("TESTING UNSUBSCRIBE FUNCTIONALITY")
    print("="*50)
    
    print("\nTest Data:")
    print("-"*20)
    print(f"Senders: {test_senders}")
    print(f"Links:   {test_links}")
    print(f"Number of senders: {len(test_senders)}")
    print(f"Number of links:   {len(test_links)}")

    try:
        print("\nCalling process_unsubscribe_links...")
        results = process_unsubscribe_links(
            unsub_links=test_links,
            selected_senders=test_senders,
            dry_run=True
        )

        print("\nTest Results:")
        print("-"*20)
        if not results:
            print("No results returned - check the logs for errors")
        else:
            print(f"Processed {len(results)} results:")
            for sender, result in results.items():
                print(f"\nSender: {sender}")
                for key, value in result.items():
                    print(f"  {key}: {value}")
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(run_test())
