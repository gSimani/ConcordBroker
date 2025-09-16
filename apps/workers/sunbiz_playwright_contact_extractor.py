"""
Sunbiz Contact Extractor using Playwright MCP
Downloads officer contact information via web interface
"""

import asyncio
import os
import sys
import io
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import json
from playwright.async_api import async_playwright, Page, Browser
from supabase import create_client

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class SunbizPlaywrightContactExtractor:
    """Extract Sunbiz officer contacts using Playwright MCP"""
    
    def __init__(self):
        # Web credentials
        self.base_url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
        # Local storage
        self.download_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\SUNBIZ_PLAYWRIGHT")
        self.download_path.mkdir(parents=True, exist_ok=True)
        
        # Supabase connection
        self.supabase_url = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
        self.supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        # Progress tracking
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.files_downloaded = 0
        self.contacts_extracted = 0
        self.contacts_saved = 0
        
        # Contact patterns
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(r'[\(]?[0-9]{3}[\)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4}')
        
    async def initialize_browser(self):
        """Initialize Playwright browser with download settings"""
        print("🚀 Initializing Playwright browser...")
        
        playwright = await async_playwright().start()
        
        # Launch browser with download handling
        self.browser = await playwright.chromium.launch(
            headless=False,  # Keep visible for debugging
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        # Create context with download path
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = await context.new_page()
        self.page.set_default_timeout(60000)
        
        print("✅ Browser initialized successfully")
        
    async def navigate_and_login(self):
        """Navigate to SFTP site and login"""
        print(f"🌐 Navigating to {self.base_url}...")
        
        await self.page.goto(self.base_url, wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Take screenshot of initial page
        screenshot_path = self.download_path / "01_initial_page.png"
        await self.page.screenshot(path=screenshot_path)
        print(f"📸 Screenshot saved: {screenshot_path}")
        
        # Look for login form
        print("🔍 Looking for login form...")
        
        # Try multiple login selectors
        login_selectors = [
            'input[name="username"]',
            'input[name="user"]', 
            'input[name="login"]',
            'input[type="text"]:first-of-type',
            '#username',
            '#user'
        ]
        
        username_field = None
        for selector in login_selectors:
            try:
                username_field = await self.page.wait_for_selector(selector, timeout=5000)
                if username_field:
                    print(f"✅ Found username field: {selector}")
                    break
            except:
                continue
        
        if not username_field:
            print("❌ No username field found, checking page content...")
            
            # Get page content to understand structure
            content = await self.page.content()
            page_text = await self.page.inner_text('body')
            
            # Save page content for debugging
            content_file = self.download_path / "page_content.html"
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"📄 Page content saved: {content_file}")
            print(f"📝 Page text preview: {page_text[:500]}...")
            
            # Check if this is a file browser interface
            if any(keyword in page_text.lower() for keyword in ['files', 'directory', 'folder', 'download']):
                print("✅ Detected file browser interface, no login needed")
                return True
            else:
                print("❌ Login form not found and no file browser detected")
                return False
        
        # Fill login form
        print("📝 Filling login credentials...")
        
        await username_field.fill(self.username)
        print(f"✅ Username filled: {self.username}")
        
        # Find password field
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            '#password'
        ]
        
        password_field = None
        for selector in password_selectors:
            try:
                password_field = await self.page.wait_for_selector(selector, timeout=3000)
                if password_field:
                    print(f"✅ Found password field: {selector}")
                    break
            except:
                continue
        
        if password_field:
            await password_field.fill(self.password)
            print("✅ Password filled")
            
            # Click login button
            login_button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                '.login-button'
            ]
            
            for selector in login_button_selectors:
                try:
                    await self.page.click(selector)
                    print(f"✅ Login button clicked: {selector}")
                    break
                except:
                    continue
            
            # Wait for navigation
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # Take screenshot after login
            login_screenshot = self.download_path / "02_after_login.png"
            await self.page.screenshot(path=login_screenshot)
            print(f"📸 Post-login screenshot: {login_screenshot}")
            
        return True
        
    async def explore_directory_structure(self):
        """Explore the directory structure for officer data"""
        print("🗂️ Exploring directory structure...")
        
        # Take screenshot of current page
        explore_screenshot = self.download_path / "03_directory_structure.png"
        await self.page.screenshot(path=explore_screenshot)
        
        # Get page content to analyze structure
        page_text = await self.page.inner_text('body')
        
        # Look for directory/file links
        links = await self.page.query_selector_all('a')
        link_texts = []
        
        for link in links:
            try:
                text = await link.inner_text()
                href = await link.get_attribute('href')
                if text and href:
                    link_texts.append({'text': text.strip(), 'href': href})
            except:
                continue
        
        # Save directory structure
        structure_file = self.download_path / "directory_structure.json"
        with open(structure_file, 'w', encoding='utf-8') as f:
            json.dump({
                'page_text': page_text[:2000],  # First 2000 chars
                'links': link_texts,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"📄 Directory structure saved: {structure_file}")
        print(f"📊 Found {len(link_texts)} links")
        
        # Look for officer/contact related directories
        target_keywords = ['off', 'officer', 'director', 'contact', 'AG', 'agent', 'annual', 'doc']
        
        relevant_links = []
        for link in link_texts:
            text_lower = link['text'].lower()
            if any(keyword in text_lower for keyword in target_keywords):
                relevant_links.append(link)
        
        print(f"🎯 Found {len(relevant_links)} relevant links:")
        for link in relevant_links[:10]:  # Show first 10
            print(f"  - {link['text']} -> {link['href']}")
        
        return relevant_links
        
    async def navigate_to_officer_data(self, relevant_links: List[Dict]):
        """Navigate to directories containing officer data"""
        print("📁 Navigating to officer data directories...")
        
        # Priority order for directories
        priority_keywords = ['off', 'officer', 'AG', 'agent', 'director', 'annual']
        
        for keyword in priority_keywords:
            matching_links = [link for link in relevant_links 
                            if keyword in link['text'].lower()]
            
            if matching_links:
                target_link = matching_links[0]
                print(f"🎯 Navigating to: {target_link['text']}")
                
                try:
                    # Click the link
                    link_selector = f'a[href="{target_link["href"]}"]'
                    await self.page.click(link_selector)
                    
                    # Wait for navigation
                    await self.page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)
                    
                    # Take screenshot
                    nav_screenshot = self.download_path / f"04_navigated_to_{keyword}.png"
                    await self.page.screenshot(path=nav_screenshot)
                    
                    # Check if we found files
                    page_content = await self.page.inner_text('body')
                    if '.txt' in page_content.lower() or 'file' in page_content.lower():
                        print(f"✅ Found files in {keyword} directory")
                        return True
                    else:
                        print(f"⚠️ No files found in {keyword} directory, trying next...")
                        # Go back and try next
                        await self.page.go_back()
                        await self.page.wait_for_load_state('networkidle')
                        
                except Exception as e:
                    print(f"❌ Error navigating to {keyword}: {e}")
                    continue
        
        print("❌ Could not find officer data directories")
        return False
        
    async def download_officer_files(self):
        """Download officer contact files"""
        print("📥 Downloading officer contact files...")
        
        # Get all download links on current page
        download_links = await self.page.query_selector_all('a')
        
        txt_files = []
        for link in download_links:
            try:
                href = await link.get_attribute('href')
                text = await link.inner_text()
                
                if href and '.txt' in href.lower():
                    txt_files.append({'text': text, 'href': href, 'element': link})
                    
            except:
                continue
        
        print(f"📋 Found {len(txt_files)} text files to download")
        
        # Download first few files (limit to avoid overwhelming)
        download_limit = min(3, len(txt_files))
        
        for i, file_info in enumerate(txt_files[:download_limit]):
            try:
                print(f"📥 Downloading file {i+1}/{download_limit}: {file_info['text']}")
                
                # Start download
                async with self.page.expect_download() as download_info:
                    await file_info['element'].click()
                
                download = await download_info.value
                
                # Save with meaningful name
                safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', file_info['text'])
                save_path = self.download_path / f"officer_data_{i+1}_{safe_name}.txt"
                
                await download.save_as(save_path)
                print(f"✅ Downloaded: {save_path}")
                
                self.files_downloaded += 1
                
                # Small delay between downloads
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Error downloading {file_info['text']}: {e}")
        
        return self.files_downloaded > 0
        
    async def extract_contacts_from_files(self):
        """Extract contact information from downloaded files"""
        print("🔍 Extracting contacts from downloaded files...")
        
        # Find all downloaded text files
        txt_files = list(self.download_path.glob("officer_data_*.txt"))
        
        all_contacts = []
        
        for file_path in txt_files:
            print(f"📄 Processing: {file_path.name}")
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                file_contacts = []
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Find emails and phones
                    emails = self.email_pattern.findall(line)
                    phones = self.phone_pattern.findall(line)
                    
                    if emails or phones:
                        # Get context lines
                        context_start = max(0, i-2)
                        context_end = min(len(lines), i+3)
                        context = ' '.join(lines[context_start:context_end])
                        
                        # Extract entity/officer info from context
                        entity_name = ""
                        officer_name = ""
                        
                        # Simple name extraction
                        for ctx_line in lines[context_start:context_end]:
                            if any(entity_type in ctx_line.upper() for entity_type in ['LLC', 'INC', 'CORP']):
                                entity_name = ctx_line.strip()[:100]
                            if any(title in ctx_line.upper() for title in ['PRESIDENT', 'CEO', 'DIRECTOR']):
                                officer_name = ctx_line.strip()[:100]
                        
                        contact = {
                            'entity_name': entity_name or 'EXTRACTED_ENTITY',
                            'officer_name': officer_name or 'EXTRACTED_OFFICER',
                            'officer_email': emails[0] if emails else None,
                            'officer_phone': phones[0] if phones else None,
                            'source_file': file_path.name,
                            'line_number': i + 1,
                            'context': context[:200],
                            'all_emails': emails,
                            'all_phones': phones
                        }
                        
                        file_contacts.append(contact)
                        self.contacts_extracted += 1
                
                all_contacts.extend(file_contacts)
                print(f"  ✅ Extracted {len(file_contacts)} contacts")
                
            except Exception as e:
                print(f"  ❌ Error processing {file_path.name}: {e}")
        
        print(f"📊 Total contacts extracted: {len(all_contacts)}")
        return all_contacts
        
    async def save_contacts_to_database(self, contacts: List[Dict]):
        """Save extracted contacts to Supabase"""
        print(f"💾 Saving {len(contacts)} contacts to database...")
        
        for contact in contacts:
            try:
                # Prepare record for existing sunbiz_officers table
                officer_record = {
                    'doc_number': f"PLAYWRIGHT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.contacts_saved}",
                    'officer_name': contact['officer_name'],
                    'officer_title': 'CONTACT_EXTRACTED',
                    'officer_address': 'PLAYWRIGHT_EXTRACTED',
                    'officer_city': 'EXTRACTED',
                    'officer_state': 'FL',
                    'officer_zip': '00000',
                    'officer_email': contact['officer_email'],
                    'officer_phone': contact['officer_phone'],
                    'source_file': contact['source_file'],
                    'import_date': datetime.now().isoformat()
                }
                
                # Insert into database
                result = self.supabase.table('sunbiz_officers').insert(officer_record).execute()
                
                if result.data:
                    self.contacts_saved += 1
                    
                    if self.contacts_saved % 10 == 0:
                        print(f"  📊 Saved {self.contacts_saved} contacts...")
                        
            except Exception as e:
                print(f"  ❌ Error saving contact: {e}")
        
        print(f"✅ Successfully saved {self.contacts_saved} contacts")
        
    async def create_extraction_report(self):
        """Create comprehensive extraction report"""
        report_path = self.download_path / f"extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'extraction_date': datetime.now().isoformat(),
            'base_url': self.base_url,
            'files_downloaded': self.files_downloaded,
            'contacts_extracted': self.contacts_extracted,
            'contacts_saved': self.contacts_saved,
            'download_path': str(self.download_path),
            'browser_used': 'Playwright Chromium',
            'success_rate': f"{(self.contacts_saved / max(1, self.contacts_extracted)) * 100:.1f}%"
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Report saved: {report_path}")
        
    async def run_extraction(self):
        """Main extraction workflow"""
        print("=" * 60)
        print("SUNBIZ PLAYWRIGHT CONTACT EXTRACTION")
        print("=" * 60)
        
        try:
            # Initialize browser
            await self.initialize_browser()
            
            # Navigate and login
            login_success = await self.navigate_and_login()
            if not login_success:
                raise Exception("Login/navigation failed")
            
            # Explore directory structure
            relevant_links = await self.explore_directory_structure()
            
            # Navigate to officer data
            officer_found = await self.navigate_to_officer_data(relevant_links)
            if not officer_found:
                print("⚠️ No officer directories found, proceeding with current location")
            
            # Download files
            download_success = await self.download_officer_files()
            if not download_success:
                print("⚠️ No files downloaded, checking for existing data")
            
            # Extract contacts
            contacts = await self.extract_contacts_from_files()
            
            # Save to database
            if contacts:
                await self.save_contacts_to_database(contacts)
            
            # Create report
            await self.create_extraction_report()
            
            print("\n✅ Extraction completed successfully!")
            
        except Exception as e:
            print(f"❌ Critical error: {e}")
            
        finally:
            if self.browser:
                await self.browser.close()
                print("🔒 Browser closed")


async def main():
    """Main entry point"""
    extractor = SunbizPlaywrightContactExtractor()
    await extractor.run_extraction()
    
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Files Downloaded: {extractor.files_downloaded}")
    print(f"Contacts Extracted: {extractor.contacts_extracted}")
    print(f"Contacts Saved: {extractor.contacts_saved}")


if __name__ == "__main__":
    asyncio.run(main())