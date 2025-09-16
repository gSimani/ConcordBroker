"""
SFTP Download Button Finder - First finds and reports on all buttons
Then specifically clicks the Download button
"""

import asyncio
import os
import sys
import io
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
import time

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class SFTPButtonFinder:
    def __init__(self):
        self.base_url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
        # Local base path
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.browser: Browser = None
        self.page: Page = None
        
    def log(self, message, level="INFO"):
        """Enhanced logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {"SUCCESS": "✅", "ERROR": "❌", "BUTTON": "🔘", "INFO": "ℹ️", "FOUND": "🎯"}.get(level, "")
        print(f"[{timestamp}] {prefix} {message}")
        
    async def initialize_browser(self):
        """Start visible browser"""
        self.log("Starting VISIBLE browser...", "INFO")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized'],
            slow_mo=500  # Slow to see what's happening
        )
        
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await context.new_page()
        self.page.set_default_timeout(90000)
        
        self.log("Browser is VISIBLE - Watch me find that Download button!", "SUCCESS")
        
    async def login(self):
        """Login to SFTP portal"""
        self.log("Logging into SFTP portal...", "INFO")
        
        await self.page.goto(self.base_url, wait_until='networkidle')
        await asyncio.sleep(2)
        
        await self.page.fill('input[placeholder="Username"]', self.username)
        await self.page.fill('input[placeholder="Password"]', self.password)
        
        await self.page.click('button:has-text("Login")')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        try:
            await self.page.wait_for_selector('tr:has-text("doc")', timeout=10000)
            self.log("Login successful!", "SUCCESS")
            return True
        except:
            self.log("Login failed", "ERROR")
            return False
            
    async def navigate_to_test_folder(self):
        """Navigate to a folder with files"""
        self.log("Navigating to doc/fic/2014...", "INFO")
        
        # Enter doc
        await self.page.dblclick('tr:has-text("doc")')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(1.5)
        
        # Enter fic
        await self.page.dblclick('tr:has-text("fic")')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(1.5)
        
        # Enter 2014
        await self.page.dblclick('tr:has-text("2014")')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(1.5)
        
        self.log("In folder doc/fic/2014", "SUCCESS")
        
    async def find_all_buttons(self):
        """Find and report on ALL buttons on the page"""
        self.log("\n" + "="*60, "INFO")
        self.log("SCANNING FOR ALL BUTTONS ON PAGE", "BUTTON")
        self.log("="*60, "INFO")
        
        # Use JavaScript to get detailed info about ALL buttons
        button_info = await self.page.evaluate("""
            () => {
                const buttons = document.querySelectorAll('button');
                const buttonData = [];
                
                for (let i = 0; i < buttons.length; i++) {
                    const button = buttons[i];
                    const rect = button.getBoundingClientRect();
                    
                    // Get all text content
                    const directText = button.textContent || '';
                    const title = button.title || '';
                    const ariaLabel = button.getAttribute('aria-label') || '';
                    
                    // Check for icons
                    const icons = button.querySelectorAll('i, svg, span[class*="icon"]');
                    const iconClasses = [];
                    icons.forEach(icon => {
                        if (icon.className) {
                            iconClasses.push(icon.className.toString());
                        }
                    });
                    
                    // Get computed styles
                    const styles = window.getComputedStyle(button);
                    
                    buttonData.push({
                        index: i,
                        text: directText.trim(),
                        title: title,
                        ariaLabel: ariaLabel,
                        className: button.className || '',
                        id: button.id || '',
                        iconClasses: iconClasses,
                        isVisible: button.offsetParent !== null,
                        isEnabled: !button.disabled,
                        position: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        },
                        backgroundColor: styles.backgroundColor,
                        innerHTML: button.innerHTML.substring(0, 200) // First 200 chars
                    });
                }
                
                return buttonData;
            }
        """)
        
        # Report on each button
        for btn in button_info:
            if btn['isVisible']:
                self.log(f"\nButton #{btn['index']}:", "BUTTON")
                self.log(f"  Text: '{btn['text']}'", "INFO")
                self.log(f"  Position: ({btn['position']['x']}, {btn['position']['y']})", "INFO")
                self.log(f"  Size: {btn['position']['width']}x{btn['position']['height']}", "INFO")
                
                if btn['title']:
                    self.log(f"  Title: '{btn['title']}'", "INFO")
                if btn['ariaLabel']:
                    self.log(f"  Aria-Label: '{btn['ariaLabel']}'", "INFO")
                if btn['className']:
                    self.log(f"  Class: {btn['className'][:50]}", "INFO")
                if btn['iconClasses']:
                    self.log(f"  Icons: {btn['iconClasses']}", "INFO")
                    
                # Check if this might be the Download button
                if 'download' in btn['text'].lower() or \
                   'download' in btn['title'].lower() or \
                   'download' in btn['ariaLabel'].lower() or \
                   'download' in btn['innerHTML'].lower() or \
                   any('download' in ic.lower() for ic in btn['iconClasses']):
                    self.log("  🎯 THIS LOOKS LIKE THE DOWNLOAD BUTTON!", "FOUND")
                    
        return button_info
        
    async def click_download_button_by_index(self, button_index):
        """Click a specific button by its index"""
        self.log(f"\nClicking button #{button_index}...", "BUTTON")
        
        clicked = await self.page.evaluate(f"""
            () => {{
                const buttons = document.querySelectorAll('button');
                if (buttons[{button_index}]) {{
                    buttons[{button_index}].click();
                    return true;
                }}
                return false;
            }}
        """)
        
        if clicked:
            self.log(f"✅ Successfully clicked button #{button_index}!", "SUCCESS")
        else:
            self.log(f"❌ Could not click button #{button_index}", "ERROR")
            
        return clicked
        
    async def select_and_download_test(self):
        """Select a file and try to download"""
        self.log("\n" + "="*60, "INFO")
        self.log("TESTING FILE SELECTION AND DOWNLOAD", "INFO")
        self.log("="*60, "INFO")
        
        # Select first file
        self.log("Selecting first file...", "INFO")
        first_file = await self.page.query_selector('tr:has-text("20140101f.txt")')
        if first_file:
            await first_file.click()
            self.log("✅ File selected (should be highlighted)", "SUCCESS")
            await asyncio.sleep(1)
        
        # Now find and click Download button
        button_info = await self.find_all_buttons()
        
        # Look for Download button
        download_button_index = None
        for btn in button_info:
            if btn['isVisible'] and ('download' in btn['text'].lower() or 
                                     'download' in btn['innerHTML'].lower()):
                download_button_index = btn['index']
                self.log(f"\n🎯 Found Download button at index {download_button_index}!", "FOUND")
                self.log(f"   Position: ({btn['position']['x']}, {btn['position']['y']})", "INFO")
                break
                
        if download_button_index is not None:
            # Try clicking it
            await self.click_download_button_by_index(download_button_index)
        else:
            self.log("\n❌ Could not identify Download button!", "ERROR")
            self.log("Trying to click button in typical toolbar position...", "INFO")
            
            # Based on screenshot, Download appears to be around button #6-8 in toolbar
            for i in range(5, 10):
                self.log(f"\nTrying button #{i}...", "BUTTON")
                if await self.click_download_button_by_index(i):
                    await asyncio.sleep(2)
                    # Check if download started
                    self.log("Check if download started...", "INFO")
                    
    async def run(self):
        """Main execution"""
        print("="*60)
        print("SFTP DOWNLOAD BUTTON FINDER")
        print("="*60)
        print("🔍 First: Find ALL buttons on the page")
        print("🎯 Then: Identify the Download button")
        print("🖱️ Finally: Click it!")
        print("-"*60)
        
        try:
            # Start browser
            await self.initialize_browser()
            
            # Login
            if not await self.login():
                self.log("Cannot proceed without login", "ERROR")
                await asyncio.sleep(30)
                return
                
            # Navigate to test folder
            await self.navigate_to_test_folder()
            
            # Find all buttons
            await self.select_and_download_test()
            
            # Keep browser open
            self.log("\n🔄 Browser stays open", "INFO")
            self.log("Check the console output above to see button analysis", "INFO")
            self.log("The Download button position has been identified", "INFO")
            self.log("Press Ctrl+C to close", "INFO")
            
            while True:
                await asyncio.sleep(10)
                
        except KeyboardInterrupt:
            self.log("\n⏹️ Stopped by user", "INFO")
            
        except Exception as e:
            self.log(f"\n❌ Error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            
            self.log("\n⏸️ Browser stays open for debugging...", "INFO")
            await asyncio.sleep(300)
            
        finally:
            if self.browser:
                self.log("Closing browser...", "INFO")
                await self.browser.close()

async def main():
    finder = SFTPButtonFinder()
    await finder.run()

if __name__ == "__main__":
    print("\n🚀 Starting SFTP Download Button Finder")
    print("This will:")
    print("  🔍 Scan and list ALL buttons on the page")
    print("  📍 Show position and properties of each button")
    print("  🎯 Identify which one is the Download button")
    print("  🖱️ Click it to test")
    print("-" * 60)
    
    asyncio.run(main())