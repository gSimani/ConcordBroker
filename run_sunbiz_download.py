"""
Simple runner script for Sunbiz SFTP downloads
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    """Main runner function"""
    print("="*60)
    print("SUNBIZ SFTP DOWNLOADER")
    print("="*60)
    print("\nSelect which agent to run:")
    print("1. Basic Downloader (sunbiz_sftp_downloader.py)")
    print("2. Advanced MCP Agent (sunbiz_mcp_agent.py)")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\nStarting Basic Downloader...")
        from sunbiz_sftp_downloader import SunbizSFTPDownloader
        downloader = SunbizSFTPDownloader()
        await downloader.run()
        
    elif choice == "2":
        print("\nStarting Advanced MCP Agent...")
        from sunbiz_mcp_agent import SunbizMCPAgent
        agent = SunbizMCPAgent()
        await agent.run()
        
    elif choice == "3":
        print("Exiting...")
        return
        
    else:
        print("Invalid choice. Please run again.")
        return

if __name__ == "__main__":
    # Check if playwright is installed
    try:
        import playwright
    except ImportError:
        print("\nPlaywright not installed. Installing required packages...")
        os.system("pip install -r requirements-sunbiz.txt")
        os.system("playwright install chromium")
        print("\nPackages installed. Please run the script again.")
        sys.exit(0)
    
    # Run the main function
    asyncio.run(main())