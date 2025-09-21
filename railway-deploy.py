#!/usr/bin/env python
"""
Railway Deployment Script for ConcordBroker
This script helps deploy the backend API to Railway
"""

import os
import sys
import subprocess
import json

def check_requirements():
    """Check if all required files exist for deployment"""
    required_files = [
        "railway.json",
        "nixpacks.toml",
        "apps/api/requirements.txt",
        "apps/api/ultimate_autocomplete_api.py"
    ]

    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)

    if missing:
        print("❌ Missing required files:")
        for file in missing:
            print(f"  - {file}")
        return False

    print("✅ All required files present")
    return True

def check_env_vars():
    """Check if Railway environment variables are set"""
    required_vars = [
        "RAILWAY_PROJECT_ID",
        "RAILWAY_API_TOKEN"
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print("❌ Missing environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease set these in your .env file or environment")
        return False

    print("✅ Environment variables configured")
    return True

def verify_railway_cli():
    """Check if Railway CLI is installed"""
    try:
        subprocess.run(["railway", "--version"], capture_output=True, check=True)
        print("✅ Railway CLI installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Railway CLI not found")
        print("\nInstall Railway CLI:")
        print("  Windows: powershell -Command \"iwr https://railway.app/install.ps1 | iex\"")
        print("  Mac/Linux: curl -fsSL https://railway.app/install.sh | sh")
        return False

def deploy_to_railway():
    """Deploy the application to Railway"""
    print("\n🚀 Starting Railway deployment...")

    # Login to Railway
    token = os.getenv("RAILWAY_API_TOKEN")
    if token:
        print("🔑 Authenticating with Railway...")
        subprocess.run(["railway", "login", "--token", token], check=True)

    # Deploy the application
    print("📦 Deploying to Railway...")
    project_id = os.getenv("RAILWAY_PROJECT_ID")

    if project_id:
        result = subprocess.run(
            ["railway", "up", "--project", project_id],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✅ Deployment initiated successfully!")
            print("\n📊 Check deployment status:")
            print(f"  https://railway.app/project/{project_id}")
        else:
            print("❌ Deployment failed:")
            print(result.stderr)
            return False
    else:
        print("❌ No project ID found")
        return False

    return True

def main():
    print("=" * 60)
    print("ConcordBroker Railway Deployment Script")
    print("=" * 60)

    # Check all prerequisites
    if not check_requirements():
        sys.exit(1)

    if not check_env_vars():
        sys.exit(1)

    if not verify_railway_cli():
        sys.exit(1)

    # Deploy to Railway
    if deploy_to_railway():
        print("\n✅ Railway deployment complete!")
        print("\nNext steps:")
        print("1. Check the Railway dashboard for build logs")
        print("2. Verify the health check endpoint")
        print("3. Test the API endpoints")
    else:
        print("\n❌ Railway deployment failed")
        print("\nTroubleshooting:")
        print("1. Check Railway dashboard for error logs")
        print("2. Verify environment variables in Railway")
        print("3. Ensure GitHub repository is connected")
        sys.exit(1)

if __name__ == "__main__":
    main()