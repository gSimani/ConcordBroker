#!/usr/bin/env python3
"""
Test script for Nano Banana Design Agent connection.
Verifies the Google AI Studio (Gemini) API is properly configured.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_connection():
    """Test the Gemini API connection"""
    print("=" * 60)
    print("Nano Banana Design Agent - Connection Test")
    print("=" * 60)

    try:
        from design_agent import NanoBananaDesignAgent, GOOGLE_AI_CONFIG

        print(f"\nConfiguration:")
        print(f"  Project: {GOOGLE_AI_CONFIG['project_name']}")
        print(f"  Model: {GOOGLE_AI_CONFIG['model']}")
        print(f"  Endpoint: {GOOGLE_AI_CONFIG['api_endpoint']}")
        print(f"  API Key: {GOOGLE_AI_CONFIG['api_key'][:10]}...{GOOGLE_AI_CONFIG['api_key'][-4:]}")

        print("\nInitializing agent...")
        agent = NanoBananaDesignAgent()

        print("Connecting to Google AI Studio...")
        if agent.initialize():
            print("\n[SUCCESS] Connected to Google AI Studio!")

            # Quick test - generate a simple design concept
            print("\nRunning quick design test...")
            result = agent.generate_design_concept(
                description="Simple property value badge showing price with trend indicator",
                component_type="badge"
            )

            print(f"\n[SUCCESS] Design generation working!")
            print(f"Response preview (first 500 chars):")
            print("-" * 40)
            print(result.content[:500] + "..." if len(result.content) > 500 else result.content)
            print("-" * 40)

            return True
        else:
            print("\n[ERROR] Failed to initialize agent")
            return False

    except ImportError as e:
        print(f"\n[ERROR] Missing dependency: {e}")
        print("\nInstall with: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
