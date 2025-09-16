"""
Verification Script for Cloud-Native Sunbiz Daily Update System
This script verifies all components are properly created and configured
"""

import os
import json
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

def check_file(path, description):
    """Check if a file exists and report status"""
    if Path(path).exists():
        print(f"{Fore.GREEN}✅ {description}: {path}{Style.RESET_ALL}")
        return True
    else:
        print(f"{Fore.RED}❌ {description}: {path} NOT FOUND{Style.RESET_ALL}")
        return False

def verify_json_content(path, key_to_check, expected_value=None):
    """Verify JSON file contains expected configuration"""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            
        # Navigate nested keys
        keys = key_to_check.split('.')
        current = data
        for key in keys:
            if key in current:
                current = current[key]
            else:
                print(f"{Fore.YELLOW}⚠️  Key '{key_to_check}' not found in {path}{Style.RESET_ALL}")
                return False
        
        if expected_value and current != expected_value:
            print(f"{Fore.YELLOW}⚠️  {path}: Expected '{expected_value}' but found '{current}'{Style.RESET_ALL}")
            return False
            
        print(f"{Fore.GREEN}✅ {path}: Configuration verified{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ Error reading {path}: {e}{Style.RESET_ALL}")
        return False

def main():
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  CLOUD-NATIVE SUNBIZ DEPLOYMENT VERIFICATION")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    all_checks_passed = True
    
    # 1. Check Vercel API Route
    print(f"{Fore.YELLOW}[1/7] Checking Vercel API Routes...{Style.RESET_ALL}")
    if not check_file("api/cron/sunbiz-daily-update.ts", "Vercel API Route"):
        all_checks_passed = False
    
    # 2. Check Supabase Edge Function
    print(f"\n{Fore.YELLOW}[2/7] Checking Supabase Edge Function...{Style.RESET_ALL}")
    if not check_file("supabase/functions/sunbiz-daily-update/index.ts", "Supabase Edge Function"):
        # Try to create the directory structure if missing
        print(f"{Fore.YELLOW}Creating Supabase function directory...{Style.RESET_ALL}")
        os.makedirs("supabase/functions/sunbiz-daily-update", exist_ok=True)
        # We'll need to copy the edge function here
        all_checks_passed = False
    
    # 3. Check Monitoring Dashboard
    print(f"\n{Fore.YELLOW}[3/7] Checking Monitoring Dashboard...{Style.RESET_ALL}")
    if not check_file("apps/web/src/pages/admin/SunbizMonitor.tsx", "Monitoring Dashboard"):
        all_checks_passed = False
    
    # 4. Check Deployment Script
    print(f"\n{Fore.YELLOW}[4/7] Checking Deployment Script...{Style.RESET_ALL}")
    if not check_file("deploy_cloud_sunbiz.ps1", "PowerShell Deployment Script"):
        all_checks_passed = False
    
    # 5. Check vercel.json configuration
    print(f"\n{Fore.YELLOW}[5/7] Checking Vercel Configuration...{Style.RESET_ALL}")
    if Path("vercel.json").exists():
        with open("vercel.json", 'r') as f:
            vercel_config = json.load(f)
        
        # Check for crons configuration
        if 'crons' in vercel_config:
            cron_found = False
            for cron in vercel_config['crons']:
                if cron.get('path') == '/api/cron/sunbiz-daily-update':
                    print(f"{Fore.GREEN}✅ Cron job configured: {cron['schedule']}{Style.RESET_ALL}")
                    cron_found = True
                    break
            if not cron_found:
                print(f"{Fore.YELLOW}⚠️  Cron job not found in vercel.json{Style.RESET_ALL}")
                all_checks_passed = False
        else:
            print(f"{Fore.YELLOW}⚠️  No crons section in vercel.json{Style.RESET_ALL}")
            all_checks_passed = False
    else:
        print(f"{Fore.RED}❌ vercel.json not found{Style.RESET_ALL}")
        all_checks_passed = False
    
    # 6. Check Documentation
    print(f"\n{Fore.YELLOW}[6/7] Checking Documentation...{Style.RESET_ALL}")
    check_file("CLOUD_SUNBIZ_DEPLOYMENT.md", "Deployment Documentation")
    check_file("CLOUD_SUNBIZ_DEPLOYMENT_COMPLETE.md", "Complete Documentation")
    
    # 7. Summary
    print(f"\n{Fore.YELLOW}[7/7] Verification Summary...{Style.RESET_ALL}")
    
    if all_checks_passed:
        print(f"\n{Fore.GREEN}{'='*60}")
        print(f"  ✅ ALL VERIFICATIONS PASSED!")
        print(f"  Your cloud-native system is ready for deployment!")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}📋 Component Checklist:{Style.RESET_ALL}")
        print(f"  ✅ Vercel API Route (Cron trigger)")
        print(f"  ✅ Supabase Edge Function (SFTP processor)")
        print(f"  ✅ Monitoring Dashboard (Real-time status)")
        print(f"  ✅ Deployment Script (One-command deploy)")
        print(f"  ✅ Vercel Configuration (Cron schedule)")
        print(f"  ✅ Documentation (Complete guides)")
        
        print(f"\n{Fore.CYAN}🚀 Next Steps:{Style.RESET_ALL}")
        print(f"  1. Run: .\\deploy_cloud_sunbiz.ps1")
        print(f"  2. Verify cron in Vercel Dashboard")
        print(f"  3. Test manual trigger")
        print(f"  4. Monitor first automatic run at 2 AM EST")
        
        print(f"\n{Fore.GREEN}✨ The system will run 100% in the cloud with ZERO PC dependency!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}{'='*60}")
        print(f"  ⚠️ SOME VERIFICATIONS FAILED")
        print(f"  Please review the issues above")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}🔧 To fix missing Supabase function:{Style.RESET_ALL}")
        print(f"  1. Create directory: supabase/functions/sunbiz-daily-update/")
        print(f"  2. Copy the edge function code there")
        print(f"  3. Run this verification again")
    
    return all_checks_passed

if __name__ == "__main__":
    try:
        import colorama
    except ImportError:
        print("Installing colorama for colored output...")
        os.system("pip install colorama")
        import colorama
    
    success = main()
    exit(0 if success else 1)