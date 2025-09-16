#!/usr/bin/env python3
"""
Integration script for finding and clicking the Download button in SFTP portal
Add this to your existing Playwright script
"""

import asyncio
import json
from playwright.async_api import async_playwright

class SFTPDownloadHandler:
    def __init__(self, page):
        self.page = page
    
    async def find_and_click_download(self):
        """
        Try multiple strategies to find and click the Download button
        """
        print("🔍 Searching for Download button...")
        
        # Strategy 1: Direct selectors
        download_selectors = [
            'button:has-text("Download")',
            'button:has-text("download")', 
            'a:has-text("Download")',
            'a:has-text("download")',
            'input[type="button"][value*="Download" i]',
            'input[type="submit"][value*="Download" i]',
            '[role="button"]:has-text("Download")',
            '.button:has-text("Download")',
            '.btn:has-text("Download")',
            '[title*="Download" i]',
            '[aria-label*="Download" i]',
            '[data-action*="download" i]'
        ]
        
        for selector in download_selectors:
            try:
                element = self.page.locator(selector).first
                if await element.is_visible():
                    print(f"✅ Found download button with selector: {selector}")
                    await element.click()
                    return True
            except Exception as e:
                continue
        
        # Strategy 2: Position-based (between Upload and Delete)
        print("🎯 Trying position-based detection...")
        try:
            # Find all toolbar buttons
            toolbar_buttons = await self.page.evaluate("""
                () => {
                    const buttons = [];
                    const selectors = ['button', 'a', '[role="button"]', '.button', '.btn'];
                    
                    selectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach((btn, index) => {
                            if (btn.offsetWidth > 0 && btn.offsetHeight > 0) {
                                buttons.push({
                                    index: buttons.length,
                                    text: btn.textContent?.trim() || '',
                                    tagName: btn.tagName,
                                    className: btn.className,
                                    title: btn.getAttribute('title') || '',
                                    element: btn
                                });
                            }
                        });
                    });
                    
                    return buttons;
                }
            """)
            
            # Find Upload and Delete button positions
            upload_index = -1
            delete_index = -1
            
            for i, btn in enumerate(toolbar_buttons):
                text = btn['text'].lower()
                title = btn['title'].lower()
                
                if 'upload' in text or 'upload' in title:
                    upload_index = i
                elif 'delete' in text or 'delete' in title:
                    delete_index = i
            
            if upload_index >= 0 and delete_index >= 0 and delete_index > upload_index:
                # Try buttons between Upload and Delete
                for i in range(upload_index + 1, delete_index):
                    try:
                        # Use nth-child to click the button at position i
                        await self.page.evaluate(f"""
                            () => {{
                                const buttons = Array.from(document.querySelectorAll('button, a, [role="button"], .button, .btn'))
                                    .filter(btn => btn.offsetWidth > 0 && btn.offsetHeight > 0);
                                if (buttons[{i}]) {{
                                    buttons[{i}].click();
                                    return true;
                                }}
                                return false;
                            }}
                        """)
                        print(f"✅ Clicked button at position {i} (between Upload and Delete)")
                        return True
                    except Exception as e:
                        print(f"❌ Failed to click button at position {i}: {e}")
                        continue
        
        except Exception as e:
            print(f"❌ Position-based detection failed: {e}")
        
        # Strategy 3: JavaScript-based comprehensive search
        print("🔬 Using JavaScript comprehensive search...")
        try:
            download_button = await self.page.evaluate("""
                () => {
                    // Find all potentially clickable elements
                    const allElements = document.querySelectorAll('*');
                    const candidates = [];
                    
                    for (let el of allElements) {
                        if (el.offsetWidth === 0 || el.offsetHeight === 0) continue;
                        
                        const text = el.textContent?.toLowerCase() || '';
                        const title = el.getAttribute('title')?.toLowerCase() || '';
                        const ariaLabel = el.getAttribute('aria-label')?.toLowerCase() || '';
                        const className = el.className?.toLowerCase() || '';
                        const id = el.id?.toLowerCase() || '';
                        
                        const hasDownloadText = text.includes('download') || 
                                               title.includes('download') || 
                                               ariaLabel.includes('download') ||
                                               className.includes('download') ||
                                               id.includes('download');
                        
                        const isClickable = el.tagName === 'BUTTON' ||
                                           el.tagName === 'A' ||
                                           el.onclick ||
                                           el.getAttribute('role') === 'button' ||
                                           className.includes('button') ||
                                           className.includes('btn') ||
                                           getComputedStyle(el).cursor === 'pointer';
                        
                        if (hasDownloadText && isClickable) {
                            candidates.push({
                                element: el,
                                text: el.textContent?.trim(),
                                tagName: el.tagName,
                                className: el.className,
                                title: el.getAttribute('title')
                            });
                        }
                    }
                    
                    // Try to click the first candidate
                    if (candidates.length > 0) {
                        candidates[0].element.click();
                        return candidates[0];
                    }
                    
                    return null;
                }
            """)
            
            if download_button:
                print(f"✅ Found and clicked download button: {download_button}")
                return True
        
        except Exception as e:
            print(f"❌ JavaScript search failed: {e}")
        
        # Strategy 4: Icon-based detection
        print("🎨 Trying icon-based detection...")
        icon_selectors = [
            '[src*="download" i]',
            '[class*="download" i]', 
            '[class*="arrow-down" i]',
            '[class*="fa-download" i]',
            'svg[class*="download" i]',
            'i[class*="download" i]'
        ]
        
        for selector in icon_selectors:
            try:
                # Try clicking the icon
                icon = self.page.locator(selector).first
                if await icon.is_visible():
                    await icon.click()
                    print(f"✅ Clicked download icon: {selector}")
                    return True
            except:
                try:
                    # Try clicking the parent
                    parent = self.page.locator(selector).first.locator('..')
                    if await parent.is_visible():
                        await parent.click()
                        print(f"✅ Clicked download icon parent: {selector}")
                        return True
                except:
                    continue
        
        print("❌ All strategies failed to find Download button")
        return False
    
    async def debug_all_elements(self):
        """
        Debug function to list all visible clickable elements
        """
        print("🐛 DEBUG: Analyzing all clickable elements...")
        
        elements_info = await self.page.evaluate("""
            () => {
                const elements = [];
                const allTags = document.querySelectorAll('*');
                
                allTags.forEach((el, index) => {
                    if (el.offsetWidth > 0 && el.offsetHeight > 0) {
                        const isClickable = el.tagName === 'BUTTON' ||
                                           el.tagName === 'A' ||
                                           el.onclick ||
                                           el.getAttribute('role') === 'button' ||
                                           el.className.toLowerCase().includes('button') ||
                                           el.className.toLowerCase().includes('btn') ||
                                           getComputedStyle(el).cursor === 'pointer';
                        
                        if (isClickable) {
                            elements.push({
                                index: elements.length + 1,
                                tagName: el.tagName,
                                text: el.textContent?.trim().substring(0, 50) || '',
                                className: el.className,
                                id: el.id,
                                title: el.getAttribute('title') || '',
                                ariaLabel: el.getAttribute('aria-label') || '',
                                onclick: el.onclick ? 'Has onclick' : 'No onclick',
                                role: el.getAttribute('role') || '',
                                type: el.getAttribute('type') || '',
                                value: el.getAttribute('value') || '',
                                href: el.getAttribute('href') || ''
                            });
                        }
                    }
                });
                
                return elements;
            }
        """)
        
        print(f"Found {len(elements_info)} clickable elements:")
        for i, element in enumerate(elements_info, 1):
            print(f"{i:2d}. {element['tagName']:<10} | {element['text']:<30} | {element['className']:<20} | {element['title']:<20}")
        
        return elements_info

# Example usage in your existing script:
async def example_usage():
    """
    Example of how to integrate this into your existing SFTP script
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Your existing login and navigation code here...
        await page.goto('https://sftp.floridados.gov')
        
        # After login and file selection, use the download handler
        download_handler = SFTPDownloadHandler(page)
        
        # Debug: See what elements are available
        await download_handler.debug_all_elements()
        
        # Try to click the download button
        success = await download_handler.find_and_click_download()
        
        if success:
            print("✅ Download initiated successfully!")
        else:
            print("❌ Could not find or click Download button")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(example_usage())