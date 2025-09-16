#!/usr/bin/env python3
"""
Check what's actually on the NAV page
"""

import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_nav_page():
    """Check the NAV page structure"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Visible browser for debugging
        page = await browser.new_page()
        
        try:
            url = "https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV/2024"
            
            logger.info(f"Navigating to: {url}")
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Try multiple selectors
            selectors = [
                'a',  # All links
                'a[href*=".txt"]',  # Text files
                'a[href*=".TXT"]',  # Text files uppercase
                'a[href*="NAV"]',  # Links containing NAV
                'td',  # Table cells
                '.ms-vb2',  # SharePoint table cells
                '.ms-unselectedtitle'  # SharePoint titles
            ]
            
            for selector in selectors:
                elements = await page.locator(selector).all()
                if elements:
                    logger.info(f"\nFound {len(elements)} elements with selector '{selector}':")
                    for i, elem in enumerate(elements[:5]):  # Show first 5
                        try:
                            text = await elem.inner_text()
                            if 'NAV' in text.upper():
                                href = await elem.get_attribute('href') if await elem.get_attribute('href') else 'N/A'
                                logger.info(f"  {i+1}. Text: {text}")
                                if href != 'N/A':
                                    logger.info(f"     URL: {href}")
                        except:
                            pass
            
            # Get all text content
            logger.info("\n\nSearching page for NAV files...")
            page_text = await page.content()
            
            # Look for NAV patterns
            import re
            nav_patterns = [
                r'NAV[ND]\d+',  # NAVN or NAVD followed by numbers
                r'NAV\s*[ND]',  # NAV N or NAV D with space
                r'\.TXT',  # TXT files
                r'NAVN\d+.*?\.TXT',  # Full NAVN filename pattern
                r'NAVD\d+.*?\.TXT'  # Full NAVD filename pattern
            ]
            
            for pattern in nav_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    logger.info(f"\nPattern '{pattern}' found {len(matches)} matches:")
                    for match in matches[:5]:
                        logger.info(f"  - {match}")
            
            # Try to extract all file links
            file_links = await page.evaluate('''
                () => {
                    const links = [];
                    const anchors = document.querySelectorAll('a');
                    anchors.forEach(anchor => {
                        const href = anchor.href;
                        const text = anchor.textContent.trim();
                        if (text && (text.includes('NAV') || text.includes('.TXT') || text.includes('.txt'))) {
                            links.push({
                                text: text,
                                href: href
                            });
                        }
                    });
                    return links;
                }
            ''')
            
            if file_links:
                logger.info(f"\n\nFound {len(file_links)} NAV-related links:")
                for link in file_links[:10]:
                    logger.info(f"  File: {link['text']}")
                    logger.info(f"  URL: {link['href']}")
                    logger.info("")
            
            # Wait to see the page
            logger.info("\nBrowser will close in 10 seconds...")
            await page.wait_for_timeout(10000)
            
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(check_nav_page())