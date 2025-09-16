"""
Sunbiz SFTP Debug Agent - Enhanced login detection
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SunbizDebugAgent:
    def __init__(self):
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
    async def run(self):
        """Run the debug agent"""
        logger.info("Starting Sunbiz Debug Agent...")
        
        async with async_playwright() as p:
            # Launch browser in visible mode for debugging
            browser = await p.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to the URL
                logger.info(f"Navigating to {self.url}")
                response = await page.goto(self.url, wait_until='networkidle', timeout=60000)
                logger.info(f"Response status: {response.status if response else 'No response'}")
                
                # Wait a bit for page to fully load
                await asyncio.sleep(3)
                
                # Take screenshot
                screenshot_path = self.base_path / f"page_loaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Screenshot saved: {screenshot_path}")
                
                # Get page content for analysis
                page_content = await page.content()
                content_file = self.base_path / f"page_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(content_file, 'w', encoding='utf-8') as f:
                    f.write(page_content)
                logger.info(f"Page content saved: {content_file}")
                
                # Try to find all input fields
                logger.info("Searching for input fields...")
                
                # Get all inputs
                inputs = await page.query_selector_all('input')
                logger.info(f"Found {len(inputs)} input fields")
                
                for i, input_elem in enumerate(inputs):
                    input_type = await input_elem.get_attribute('type')
                    input_name = await input_elem.get_attribute('name')
                    input_id = await input_elem.get_attribute('id')
                    input_placeholder = await input_elem.get_attribute('placeholder')
                    is_visible = await input_elem.is_visible()
                    
                    logger.info(f"Input {i+1}: type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}, visible={is_visible}")
                
                # Look for username field with various strategies
                username_filled = False
                username_selectors = [
                    'input[type="text"]:visible',
                    'input[name*="user" i]:visible',
                    'input[id*="user" i]:visible',
                    'input[placeholder*="user" i]:visible',
                    'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):first-of-type'
                ]
                
                for selector in username_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for elem in elements:
                            if await elem.is_visible():
                                await elem.fill(self.username)
                                logger.info(f"Username filled using selector: {selector}")
                                username_filled = True
                                break
                        if username_filled:
                            break
                    except Exception as e:
                        logger.debug(f"Failed with selector {selector}: {e}")
                
                if not username_filled:
                    # Try clicking first then filling
                    logger.info("Trying click-then-fill approach...")
                    first_input = await page.query_selector('input[type="text"]')
                    if first_input:
                        await first_input.click()
                        await page.keyboard.type(self.username)
                        username_filled = True
                        logger.info("Username typed using keyboard")
                
                # Look for password field
                password_filled = False
                password_selectors = [
                    'input[type="password"]:visible',
                    'input[name*="pass" i]:visible',
                    'input[id*="pass" i]:visible',
                    'input[placeholder*="pass" i]:visible'
                ]
                
                for selector in password_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for elem in elements:
                            if await elem.is_visible():
                                await elem.fill(self.password)
                                logger.info(f"Password filled using selector: {selector}")
                                password_filled = True
                                break
                        if password_filled:
                            break
                    except Exception as e:
                        logger.debug(f"Failed with selector {selector}: {e}")
                
                if not password_filled:
                    # Try using tab to navigate to password field
                    logger.info("Trying tab navigation to password field...")
                    await page.keyboard.press('Tab')
                    await page.keyboard.type(self.password)
                    password_filled = True
                    logger.info("Password typed using keyboard after tab")
                
                # Take screenshot after filling
                screenshot_path = self.base_path / f"after_fill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"Screenshot after fill saved: {screenshot_path}")
                
                # Find and click submit button
                submit_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Login")',
                    'button:has-text("Sign in")',
                    'button:has-text("Submit")',
                    'input[value*="login" i]',
                    'input[value*="submit" i]',
                    'button',
                    'input[type="button"]'
                ]
                
                submit_clicked = False
                for selector in submit_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for elem in elements:
                            if await elem.is_visible():
                                elem_text = await elem.inner_text() if await elem.get_attribute('type') != 'input' else await elem.get_attribute('value')
                                logger.info(f"Found potential submit button: {elem_text}")
                                await elem.click()
                                logger.info(f"Clicked submit using selector: {selector}")
                                submit_clicked = True
                                break
                        if submit_clicked:
                            break
                    except Exception as e:
                        logger.debug(f"Failed with selector {selector}: {e}")
                
                if not submit_clicked:
                    # Try pressing Enter
                    logger.info("Trying Enter key to submit...")
                    await page.keyboard.press('Enter')
                
                # Wait for navigation
                logger.info("Waiting for navigation after login...")
                await page.wait_for_load_state('networkidle', timeout=30000)
                await asyncio.sleep(3)
                
                # Take screenshot after login
                screenshot_path = self.base_path / f"after_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Screenshot after login saved: {screenshot_path}")
                
                # Check if login was successful
                page_text = await page.inner_text('body')
                if 'doc' in page_text.lower() or 'folder' in page_text.lower() or 'directory' in page_text.lower():
                    logger.info("Login appears successful - found directory listing")
                    
                    # Try to find and click doc folder
                    doc_selectors = [
                        'a:has-text("doc")',
                        'text=doc',
                        '[href*="doc"]',
                        'td:has-text("doc")'
                    ]
                    
                    for selector in doc_selectors:
                        try:
                            elem = await page.query_selector(selector)
                            if elem and await elem.is_visible():
                                await elem.click()
                                logger.info(f"Clicked doc folder using: {selector}")
                                break
                        except Exception as e:
                            logger.debug(f"Failed to click doc with {selector}: {e}")
                    
                    # Wait and take final screenshot
                    await page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)
                    
                    screenshot_path = self.base_path / f"in_doc_folder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    await page.screenshot(path=str(screenshot_path), full_page=True)
                    logger.info(f"Screenshot in doc folder saved: {screenshot_path}")
                    
                    # Get the file listing
                    page_content = await page.content()
                    content_file = self.base_path / f"doc_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    with open(content_file, 'w', encoding='utf-8') as f:
                        f.write(page_content)
                    logger.info(f"Doc folder content saved: {content_file}")
                    
                else:
                    logger.warning("Login may have failed - no directory listing found")
                    logger.info(f"Page text snippet: {page_text[:500]}")
                
                # Keep browser open for manual inspection
                logger.info("Keeping browser open for 30 seconds for manual inspection...")
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error during execution: {e}")
                # Take error screenshot
                screenshot_path = self.base_path / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"Error screenshot saved: {screenshot_path}")
                raise
                
            finally:
                await browser.close()
                logger.info("Browser closed")

async def main():
    agent = SunbizDebugAgent()
    await agent.run()

if __name__ == "__main__":
    print("Starting Sunbiz Debug Agent...")
    print("This will open a browser window and attempt to login.")
    print("Screenshots and logs will be saved to TEMP\\DATABASE folder.")
    print("-" * 50)
    asyncio.run(main())