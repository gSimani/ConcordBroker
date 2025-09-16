#!/usr/bin/env python3
"""
Test LangSmith API Connection
Verifies that the LangSmith API key is working correctly
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from datetime import datetime

# Load environment variables
load_dotenv()

def test_langsmith_connection():
    """Test the LangSmith API connection"""
    
    print("=" * 60)
    print("TESTING LANGSMITH CONNECTION")
    print("=" * 60)
    
    # Get API key from environment
    api_key = os.getenv("LANGSMITH_API_KEY")
    endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    project = os.getenv("LANGSMITH_PROJECT", "concordbroker")
    
    if not api_key:
        print("ERROR: LANGSMITH_API_KEY not found in environment")
        return False
    
    print(f"[OK] API Key found: {api_key[:20]}...")
    print(f"[OK] Endpoint: {endpoint}")
    print(f"[OK] Project: {project}")
    print()
    
    try:
        # Initialize LangSmith client
        print("Connecting to LangSmith...")
        client = Client(
            api_key=api_key,
            api_url=endpoint
        )
        
        # Test the connection by listing datasets
        print("Testing API access...")
        datasets = list(client.list_datasets(limit=1))
        print(f"[OK] Successfully connected to LangSmith!")
        print(f"[OK] Found {len(datasets)} dataset(s)")
        
        # Try to create a test dataset
        print("\nCreating test dataset...")
        test_dataset_name = f"ConcordBroker_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        dataset = client.create_dataset(
            dataset_name=test_dataset_name,
            description="Test dataset to verify LangSmith connection"
        )
        print(f"[OK] Created test dataset: {test_dataset_name}")
        
        # Add a test example
        print("Adding test example...")
        client.create_examples(
            dataset_id=dataset.id,
            examples=[{
                "inputs": {"query": "test property search"},
                "outputs": {"success": True}
            }]
        )
        print("[OK] Added test example to dataset")
        
        # Clean up - delete test dataset
        print("\nCleaning up...")
        client.delete_dataset(dataset_id=dataset.id)
        print("[OK] Deleted test dataset")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] LANGSMITH CONNECTION TEST SUCCESSFUL!")
        print("=" * 60)
        print("\nYour LangSmith integration is working correctly.")
        print("You can now:")
        print("1. View traces at: https://smith.langchain.com")
        print("2. Run evaluations with the LangGraph workflows")
        print("3. Monitor workflow performance")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] ERROR: Failed to connect to LangSmith")
        print(f"Error details: {str(e)}")
        print("\nPossible issues:")
        print("1. Invalid API key")
        print("2. Network connectivity issues")
        print("3. LangSmith service issues")
        print("\nPlease verify your API key at: https://smith.langchain.com/settings")
        return False

def test_workflow_integration():
    """Test that LangGraph workflows can use LangSmith"""
    print("\n" + "=" * 60)
    print("TESTING LANGGRAPH INTEGRATION")
    print("=" * 60)
    
    try:
        # Import LangGraph components
        sys.path.append(os.path.join(os.path.dirname(__file__), 'apps'))
        from langgraph.config import config
        
        print("[OK] LangGraph configuration loaded")
        print(f"[OK] LangSmith enabled: {config.langsmith_enabled}")
        print(f"[OK] Project: {config.langsmith_project}")
        
        if config.langsmith_client:
            print("[OK] LangSmith client initialized in LangGraph")
        else:
            print("[WARNING] LangSmith client not initialized (tracing may be disabled)")
            
        return True
        
    except ImportError as e:
        print(f"[WARNING] Could not import LangGraph: {e}")
        print("This is normal if you haven't restarted the API server yet")
        return False
    except Exception as e:
        print(f"[ERROR] Error testing LangGraph integration: {e}")
        return False

if __name__ == "__main__":
    # Test LangSmith connection
    langsmith_ok = test_langsmith_connection()
    
    # Test LangGraph integration
    langgraph_ok = test_workflow_integration()
    
    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print("=" * 60)
    
    if langsmith_ok and langgraph_ok:
        print("[SUCCESS] All tests passed! Your LangSmith integration is fully operational.")
    elif langsmith_ok:
        print("[SUCCESS] LangSmith connection is working.")
        print("[WARNING] Restart your API server to enable LangGraph integration.")
    else:
        print("[ERROR] Please fix the issues above and try again.")
    
    sys.exit(0 if langsmith_ok else 1)