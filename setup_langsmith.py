#!/usr/bin/env python3
"""
LangSmith Configuration Setup
Ensures LangSmith API key is permanently configured
"""

import os
import sys
from pathlib import Path

# PERMANENT LangSmith API Key
LANGSMITH_API_KEY = "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"

def setup_langsmith():
    """Set up LangSmith configuration permanently"""
    
    print("Setting up LangSmith configuration...")
    
    # Set environment variables
    os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "concordbroker-property-analysis"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    
    # Create or update .env.langchain file
    env_file = Path(".env.langchain")
    env_content = f"""# LangSmith Configuration (PERMANENT)
LANGSMITH_API_KEY={LANGSMITH_API_KEY}
LANGCHAIN_API_KEY={LANGSMITH_API_KEY}
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=concordbroker-property-analysis
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
"""
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print(f"[OK] LangSmith API key configured: {LANGSMITH_API_KEY[:20]}...")
    print(f"[OK] Configuration saved to {env_file}")
    
    # Verify configuration
    try:
        from langsmith import Client
        client = Client(api_key=LANGSMITH_API_KEY)
        print("[OK] LangSmith client initialized successfully")
        
        # Test connection
        try:
            # Create a test run
            client.create_run(
                name="test_connection",
                run_type="chain",
                inputs={"test": "connection"},
                outputs={"status": "success"}
            )
            print("[OK] LangSmith connection verified")
        except Exception as e:
            print(f"[WARNING] LangSmith connection test failed: {e}")
            print("   This might be normal if you're offline or the API key hasn't been activated yet")
    
    except ImportError:
        print("[WARNING] LangSmith not installed. Run: pip install langsmith")
    
    return LANGSMITH_API_KEY

def add_to_system_env():
    """Add LangSmith key to system environment (Windows)"""
    
    if sys.platform == "win32":
        import subprocess
        
        try:
            # Set user environment variable
            subprocess.run([
                "setx", 
                "LANGSMITH_API_KEY", 
                LANGSMITH_API_KEY
            ], check=True)
            
            subprocess.run([
                "setx", 
                "LANGCHAIN_API_KEY", 
                LANGSMITH_API_KEY
            ], check=True)
            
            print("[OK] LangSmith API key added to Windows user environment")
            print("   You may need to restart your terminal for changes to take effect")
            
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] Could not set system environment variable: {e}")
    else:
        print("[INFO] To make the API key permanent on Unix systems, add to your shell profile:")
        print(f"   export LANGSMITH_API_KEY={LANGSMITH_API_KEY}")
        print(f"   export LANGCHAIN_API_KEY={LANGSMITH_API_KEY}")

def verify_all_files():
    """Verify API key is in all necessary files"""
    
    files_to_check = [
        "apps/langchain_system/core.py",
        "apps/api/langchain_api.py",
        "mcp-server/langchain-integration.js",
        ".env.langchain"
    ]
    
    print("\n[VERIFY] Verifying API key in project files:")
    
    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            content = path.read_text()
            if LANGSMITH_API_KEY in content:
                print(f"  [OK] {file_path}")
            else:
                print(f"  [WARNING] {file_path} - API key not found")
        else:
            print(f"  [ERROR] {file_path} - File not found")

if __name__ == "__main__":
    print("=" * 60)
    print("[START] ConcordBroker LangSmith Configuration")
    print("=" * 60)
    
    # Setup LangSmith
    api_key = setup_langsmith()
    
    # Add to system environment
    add_to_system_env()
    
    # Verify files
    verify_all_files()
    
    print("\n" + "=" * 60)
    print("[COMPLETE] LangSmith configuration complete!")
    print(f"[NOTE] Your API key: {api_key}")
    print("[LINK] LangSmith Dashboard: https://smith.langchain.com")
    print("=" * 60)