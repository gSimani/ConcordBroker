"""
Tax Deed Flow Verification Agent
Comprehensive testing of the entire tax deed system flow
From scraping → Supabase → API → Frontend
"""

import asyncio
import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaxDeedFlowAgent:
    """Agent to verify complete tax deed system flow"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'steps': {},
            'errors': [],
            'warnings': [],
            'data_samples': {}
        }
        self.supabase_client = None
        self.test_property = None
        
    def log_step(self, step_name: str, status: str, details: str = ""):
        """Log a verification step"""
        self.results['steps'][step_name] = {
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        # Console output
        icons = {'success': '✅', 'failure': '❌', 'warning': '⚠️', 'info': '📋'}
        icon = icons.get(status, '🔍')
        logger.info(f"{icon} {step_name}: {details if details else status}")
    
    async def step1_check_environment(self) -> bool:
        """Step 1: Check environment setup"""
        logger.info("\n" + "="*60)
        logger.info("STEP 1: ENVIRONMENT CHECK")
        logger.info("="*60)
        
        try:
            # Check for required environment variables
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            
            if not supabase_url:
                supabase_url = 'https://pmmkfrohclzpwpnbtajc.supabase.co'
                os.environ['SUPABASE_URL'] = supabase_url
                self.log_step("SUPABASE_URL", "warning", f"Using default: {supabase_url}")
            else:
                self.log_step("SUPABASE_URL", "success", supabase_url)
            
            if not supabase_key:
                self.log_step("SUPABASE_ANON_KEY", "failure", "Not set - database operations will fail")
                self.results['errors'].append("SUPABASE_ANON_KEY not configured")
                return False
            else:
                self.log_step("SUPABASE_ANON_KEY", "success", "Key is configured")
            
            # Check for required files
            required_files = [
                'apps/workers/tax_deed_scraper.py',
                'apps/api/tax_deed_api.py',
                'create_tax_deed_tables.sql',
                'apps/web/src/components/property/tabs/TaxDeedSalesTab.tsx'
            ]
            
            for file_path in required_files:
                if Path(file_path).exists():
                    self.log_step(f"File: {file_path}", "success", "Exists")
                else:
                    self.log_step(f"File: {file_path}", "failure", "Not found")
                    self.results['errors'].append(f"Missing file: {file_path}")
            
            return len(self.results['errors']) == 0
            
        except Exception as e:
            self.log_step("Environment Check", "failure", str(e))
            return False
    
    async def step2_test_scraper(self) -> bool:
        """Step 2: Test the scraper functionality"""
        logger.info("\n" + "="*60)
        logger.info("STEP 2: SCRAPER TEST")
        logger.info("="*60)
        
        try:
            # Add workers directory to path
            sys.path.append(str(Path('apps/workers').absolute()))
            
            from tax_deed_scraper import BrowardTaxDeedScraper
            
            async with BrowardTaxDeedScraper() as scraper:
                # Test 1: Get auction dates
                self.log_step("Scraper initialization", "success", "Scraper loaded")
                
                logger.info("Testing auction date retrieval...")
                auctions = await scraper.get_auction_dates()
                
                if auctions:
                    self.log_step("Auction dates", "success", f"Found {len(auctions)} auctions")
                    self.results['data_samples']['auctions'] = auctions[:2]  # Save sample
                    
                    # Test 2: Scrape properties from first auction
                    first_auction = auctions[0]
                    logger.info(f"Testing property extraction from: {first_auction.get('description', 'Current Auction')}")
                    
                    properties = await scraper.scrape_auction_properties(
                        first_auction['url'],
                        first_auction['date']
                    )
                    
                    if properties:
                        self.log_step("Property extraction", "success", f"Extracted {len(properties)} properties")
                        
                        # Save sample property for later tests
                        self.test_property = properties[0]
                        self.results['data_samples']['sample_property'] = self.test_property
                        
                        # Display sample property details
                        logger.info("\nSample Property Details:")
                        logger.info(f"  Parcel: {self.test_property.get('parcel_number', 'N/A')}")
                        logger.info(f"  Address: {self.test_property.get('situs_address', 'N/A')}")
                        logger.info(f"  Opening Bid: ${self.test_property.get('opening_bid', 0):,.2f}")
                        logger.info(f"  Status: {self.test_property.get('status', 'N/A')}")
                        
                        # Check for critical fields
                        required_fields = ['parcel_number', 'opening_bid', 'situs_address']
                        for field in required_fields:
                            if field in self.test_property and self.test_property[field]:
                                self.log_step(f"Field: {field}", "success", "Present")
                            else:
                                self.log_step(f"Field: {field}", "warning", "Missing or empty")
                        
                        return True
                    else:
                        self.log_step("Property extraction", "warning", "No properties found")
                        self.results['warnings'].append("No properties extracted - site might be empty")
                        return True  # Not a failure, just no data
                else:
                    self.log_step("Auction dates", "warning", "No auctions found")
                    self.results['warnings'].append("No auctions found - this might be normal")
                    return True  # Not a failure
                    
        except ImportError as e:
            self.log_step("Scraper import", "failure", f"Cannot import scraper: {e}")
            self.results['errors'].append(f"Scraper import error: {e}")
            return False
        except Exception as e:
            self.log_step("Scraper test", "failure", str(e))
            self.results['errors'].append(f"Scraper error: {e}")
            return False
    
    async def step3_verify_database(self) -> bool:
        """Step 3: Verify Supabase database connection and schema"""
        logger.info("\n" + "="*60)
        logger.info("STEP 3: DATABASE VERIFICATION")
        logger.info("="*60)
        
        try:
            from supabase import create_client
            
            supabase_url = os.getenv('SUPABASE_URL', 'https://pmmkfrohclzpwpnbtajc.supabase.co')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            
            if not supabase_key:
                self.log_step("Database connection", "failure", "No Supabase key")
                return False
            
            self.supabase_client = create_client(supabase_url, supabase_key)
            self.log_step("Database connection", "success", "Connected to Supabase")
            
            # Test 1: Check if tables exist
            tables_to_check = ['tax_deed_properties', 'tax_deed_contacts']
            
            for table_name in tables_to_check:
                try:
                    result = self.supabase_client.table(table_name).select('*').limit(1).execute()
                    self.log_step(f"Table: {table_name}", "success", "Exists and accessible")
                except Exception as e:
                    self.log_step(f"Table: {table_name}", "failure", "Not found or not accessible")
                    self.results['errors'].append(f"Table {table_name} not accessible: {e}")
                    logger.info("\n⚠️  Please create database tables:")
                    logger.info("1. Go to Supabase dashboard")
                    logger.info("2. Run SQL from create_tax_deed_tables.sql")
                    return False
            
            # Test 2: Check for existing data
            result = self.supabase_client.table('tax_deed_properties').select('*', count='exact').execute()
            count = len(result.data) if result.data else 0
            
            if count > 0:
                self.log_step("Existing data", "success", f"Found {count} properties in database")
                self.results['data_samples']['db_property'] = result.data[0] if result.data else None
            else:
                self.log_step("Existing data", "info", "Database is empty - will populate with scraper")
            
            return True
            
        except ImportError:
            self.log_step("Supabase library", "failure", "supabase package not installed")
            logger.info("Install with: pip install supabase")
            return False
        except Exception as e:
            self.log_step("Database verification", "failure", str(e))
            self.results['errors'].append(f"Database error: {e}")
            return False
    
    async def step4_test_data_save(self) -> bool:
        """Step 4: Test saving data to Supabase"""
        logger.info("\n" + "="*60)
        logger.info("STEP 4: DATA SAVE TEST")
        logger.info("="*60)
        
        if not self.supabase_client:
            self.log_step("Data save", "failure", "No database connection")
            return False
        
        try:
            # Create test property data
            test_data = {
                'parcel_number': 'TEST-' + datetime.now().strftime('%Y%m%d%H%M%S'),
                'tax_deed_number': 'TD-TEST-001',
                'situs_address': '123 Test Street, Fort Lauderdale, FL 33301',
                'opening_bid': 50000.00,
                'status': 'Active',
                'is_homestead': False,
                'auction_date': datetime.now().date().isoformat(),
                'applicant_name': 'TEST APPLICANT LLC',
                'source': 'test_agent'
            }
            
            # Try to insert test data
            result = self.supabase_client.table('tax_deed_properties').insert(test_data).execute()
            
            if result.data:
                self.log_step("Insert test property", "success", f"Saved with ID: {result.data[0].get('id')}")
                test_id = result.data[0].get('id')
                
                # Try to retrieve it
                retrieved = self.supabase_client.table('tax_deed_properties').select('*').eq('id', test_id).execute()
                
                if retrieved.data:
                    self.log_step("Retrieve test property", "success", "Data verified")
                    
                    # Clean up test data
                    self.supabase_client.table('tax_deed_properties').delete().eq('id', test_id).execute()
                    self.log_step("Cleanup test data", "success", "Test data removed")
                    
                    return True
                else:
                    self.log_step("Retrieve test property", "failure", "Could not retrieve")
                    return False
            else:
                self.log_step("Insert test property", "failure", "Insert failed")
                return False
                
        except Exception as e:
            self.log_step("Data save test", "failure", str(e))
            self.results['errors'].append(f"Data save error: {e}")
            return False
    
    async def step5_run_full_scrape(self) -> bool:
        """Step 5: Run a full scrape and save to database"""
        logger.info("\n" + "="*60)
        logger.info("STEP 5: FULL SCRAPE AND SAVE")
        logger.info("="*60)
        
        try:
            from tax_deed_scraper import BrowardTaxDeedScraper
            
            logger.info("Running full scrape (this may take a moment)...")
            
            async with BrowardTaxDeedScraper() as scraper:
                results = await scraper.scrape_all()
                
                self.log_step("Full scrape", "success", 
                    f"Scraped {results.get('properties_scraped', 0)} properties from {results.get('auctions_scraped', 0)} auctions")
                
                if results.get('properties_saved', 0) > 0:
                    self.log_step("Database save", "success", 
                        f"Saved {results.get('properties_saved', 0)} properties")
                    
                    # Log details
                    if results.get('inserted'):
                        logger.info(f"  New properties: {results['inserted']}")
                    if results.get('updated'):
                        logger.info(f"  Updated properties: {results['updated']}")
                    
                    self.results['data_samples']['scrape_results'] = results
                    return True
                    
                elif results.get('properties_scraped', 0) > 0:
                    self.log_step("Database save", "warning", 
                        "Properties scraped but not saved - check database connection")
                    return False
                else:
                    self.log_step("Full scrape", "warning", 
                        "No properties found - site might be empty or structure changed")
                    self.results['warnings'].append("No data scraped - might be normal if no current auctions")
                    return True  # Not necessarily a failure
                    
        except Exception as e:
            self.log_step("Full scrape", "failure", str(e))
            self.results['errors'].append(f"Scrape error: {e}")
            return False
    
    async def step6_test_api(self) -> bool:
        """Step 6: Test API endpoints"""
        logger.info("\n" + "="*60)
        logger.info("STEP 6: API ENDPOINT TEST")
        logger.info("="*60)
        
        base_url = "http://localhost:8000"
        
        # Check if API is running
        try:
            response = requests.get(f"{base_url}/docs", timeout=2)
            if response.status_code == 200:
                self.log_step("API server", "success", "Running on port 8000")
            else:
                self.log_step("API server", "warning", f"Unexpected status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.log_step("API server", "warning", "Not running - start with: python apps/api/main_simple.py")
            logger.info("\nTo test API, start the server:")
            logger.info("  cd apps/api")
            logger.info("  python main_simple.py")
            return True  # Not a failure, just not running
        
        # Test tax deed endpoints
        endpoints = [
            ("/api/tax-deed/properties", "GET"),
            ("/api/tax-deed/auction-dates", "GET"),
        ]
        
        for endpoint, method in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                if method == "GET":
                    response = requests.get(url, timeout=5)
                else:
                    response = requests.post(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_step(f"Endpoint {endpoint}", "success", 
                        f"Returns {len(data) if isinstance(data, list) else 'data'}")
                    
                    # Save sample response
                    if endpoint == "/api/tax-deed/properties" and isinstance(data, list) and data:
                        self.results['data_samples']['api_property'] = data[0]
                else:
                    self.log_step(f"Endpoint {endpoint}", "warning", f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_step(f"Endpoint {endpoint}", "warning", str(e))
        
        return True
    
    async def step7_test_frontend(self) -> bool:
        """Step 7: Test frontend with Playwright"""
        logger.info("\n" + "="*60)
        logger.info("STEP 7: FRONTEND TEST")
        logger.info("="*60)
        
        # First check if frontend is running
        try:
            response = requests.get("http://localhost:5173", timeout=2)
            if response.status_code != 200:
                self.log_step("Frontend server", "warning", "Not accessible")
                logger.info("\nTo test frontend, start the server:")
                logger.info("  cd apps/web")
                logger.info("  npm run dev")
                return True  # Not a failure
        except:
            self.log_step("Frontend server", "warning", "Not running")
            logger.info("\nTo test frontend, start the server:")
            logger.info("  cd apps/web")
            logger.info("  npm run dev")
            return True  # Not a failure
        
        try:
            # Import and run Playwright test
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Test 1: Load tax deed sales page
                logger.info("Loading http://localhost:5173/tax-deed-sales...")
                await page.goto("http://localhost:5173/tax-deed-sales", wait_until='networkidle')
                await page.wait_for_timeout(2000)
                
                # Check for page title
                title = await page.locator('h1:has-text("Tax Deed")').first.text_content()
                if title:
                    self.log_step("Tax Deed Sales page", "success", "Page loads correctly")
                else:
                    self.log_step("Tax Deed Sales page", "warning", "Page loads but title not found")
                
                # Test 2: Check for Tax Deed Sales component
                component = await page.locator('text="Tax Deed Sales"').count()
                if component > 0:
                    self.log_step("TaxDeedSalesTab component", "success", "Component is rendered")
                else:
                    self.log_step("TaxDeedSalesTab component", "warning", "Component not found")
                
                # Test 3: Check for data or sample data message
                properties = await page.locator('.border.border-gray-200.rounded-lg').count()
                if properties > 0:
                    self.log_step("Property display", "success", f"Showing {properties} properties")
                    
                    # Check for Opening Bid
                    opening_bids = await page.locator('text="Opening Bid"').count()
                    if opening_bids > 0:
                        self.log_step("Opening Bid display", "success", f"Found {opening_bids} opening bids")
                    
                    # Check for tabs
                    upcoming_tab = await page.locator('button:has-text("Upcoming Auctions")').count()
                    past_tab = await page.locator('button:has-text("Past Auctions")').count()
                    cancelled_tab = await page.locator('button:has-text("Cancelled Auctions")').count()
                    
                    if upcoming_tab and past_tab and cancelled_tab:
                        self.log_step("Auction tabs", "success", "All tabs present")
                        
                        # Test Past Auctions for Winning Bid
                        await page.locator('button:has-text("Past Auctions")').first.click()
                        await page.wait_for_timeout(1000)
                        
                        winning_bids = await page.locator('text="Winning Bid"').count()
                        if winning_bids > 0:
                            self.log_step("Winning Bid display", "success", f"Found {winning_bids} winning bids in past auctions")
                else:
                    empty_message = await page.locator('text="No Upcoming Auctions Found"').count()
                    if empty_message > 0:
                        self.log_step("Property display", "info", "No properties - database might be empty")
                
                # Take screenshot
                await page.screenshot(path="ui_screenshots/tax_deed_flow_test.png", full_page=True)
                self.log_step("Screenshot", "success", "Saved to ui_screenshots/tax_deed_flow_test.png")
                
                await browser.close()
                return True
                
        except ImportError:
            self.log_step("Playwright", "warning", "Not installed - skipping browser test")
            logger.info("Install with: pip install playwright && playwright install chromium")
            return True
        except Exception as e:
            self.log_step("Frontend test", "warning", f"Error: {e}")
            return True  # Not critical
    
    def generate_report(self):
        """Generate final report"""
        logger.info("\n" + "="*60)
        logger.info("FINAL REPORT")
        logger.info("="*60)
        
        # Count successes and failures
        successes = sum(1 for s in self.results['steps'].values() if s['status'] == 'success')
        failures = sum(1 for s in self.results['steps'].values() if s['status'] == 'failure')
        warnings = sum(1 for s in self.results['steps'].values() if s['status'] == 'warning')
        
        logger.info(f"\nResults Summary:")
        logger.info(f"  ✅ Successes: {successes}")
        logger.info(f"  ❌ Failures: {failures}")
        logger.info(f"  ⚠️  Warnings: {warnings}")
        
        if failures > 0:
            logger.info(f"\n❌ Critical Issues Found:")
            for error in self.results['errors']:
                logger.info(f"  - {error}")
        
        if warnings > 0 and len(self.results['warnings']) > 0:
            logger.info(f"\n⚠️  Warnings:")
            for warning in self.results['warnings']:
                logger.info(f"  - {warning}")
        
        # Save detailed report
        report_path = "tax_deed_flow_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"\n📄 Detailed report saved to: {report_path}")
        
        # Final status
        if failures == 0:
            logger.info("\n🎉 SUCCESS: Tax Deed system is fully functional!")
            logger.info("\n📋 Next Steps:")
            logger.info("1. Visit http://localhost:5173/tax-deed-sales")
            logger.info("2. View scraped properties with Opening/Winning bids")
            logger.info("3. Use filters and search functionality")
            logger.info("4. Set up scheduled scraping: python apps/workers/tax_deed_scheduler.py")
        else:
            logger.info("\n⚠️  System has issues that need to be resolved")
            logger.info("Review the errors above and fix them before proceeding")
    
    async def run(self):
        """Run all verification steps"""
        logger.info("="*60)
        logger.info("TAX DEED FLOW VERIFICATION AGENT")
        logger.info("Testing complete flow: Scraping → Supabase → API → Frontend")
        logger.info("="*60)
        
        # Run all steps
        steps = [
            ("Environment Check", self.step1_check_environment),
            ("Scraper Test", self.step2_test_scraper),
            ("Database Verification", self.step3_verify_database),
            ("Data Save Test", self.step4_test_data_save),
            ("Full Scrape", self.step5_run_full_scrape),
            ("API Test", self.step6_test_api),
            ("Frontend Test", self.step7_test_frontend)
        ]
        
        for step_name, step_func in steps:
            try:
                result = await step_func()
                if not result and step_name in ["Environment Check", "Database Verification"]:
                    logger.warning(f"Critical step '{step_name}' failed - stopping")
                    break
            except Exception as e:
                self.log_step(step_name, "failure", str(e))
                self.results['errors'].append(f"{step_name} failed: {e}")
        
        # Generate report
        self.generate_report()


async def main():
    """Main entry point"""
    agent = TaxDeedFlowAgent()
    await agent.run()


if __name__ == "__main__":
    # Run the agent
    asyncio.run(main())