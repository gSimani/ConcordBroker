#!/usr/bin/env python3
"""
Debug script to analyze the actual structure of the tax deed auction page
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def debug_page_structure():
    """Debug the page structure to understand how to extract data"""
    
    # Setup Chrome driver
    chrome_options = Options()
    # Remove headless mode to see what's happening
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)
    
    try:
        print("Loading page...")
        driver.get("https://broward.deedauction.net/auction/110")
        time.sleep(10)  # Wait for page to fully load
        
        print("Page title:", driver.title)
        print("Current URL:", driver.current_url)
        
        # Check for tables
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"Found {len(tables)} tables on the page")
        
        for i, table in enumerate(tables):
            print(f"\nTable {i+1}:")
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"  Rows: {len(rows)}")
            
            for j, row in enumerate(rows[:5]):  # Show first 5 rows
                cells = row.find_elements(By.TAG_NAME, "td")
                if cells:
                    cell_texts = [cell.text.strip() for cell in cells]
                    print(f"    Row {j+1} ({len(cells)} cells): {cell_texts}")
                else:
                    # Check for headers
                    headers = row.find_elements(By.TAG_NAME, "th")
                    if headers:
                        header_texts = [header.text.strip() for header in headers]
                        print(f"    Header Row {j+1} ({len(headers)} headers): {header_texts}")
        
        # Look for specific text that indicates properties
        page_source = driver.page_source
        if "51640" in page_source:
            print("\nFound tax deed number 51640 in page source")
        
        # Check for any elements containing property numbers
        all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '51640')]")
        print(f"Found {len(all_elements)} elements containing '51640'")
        
        # Check for expandable elements
        expand_buttons = driver.find_elements(By.CSS_SELECTOR, "img[src*='expand.gif']")
        print(f"Found {len(expand_buttons)} expand buttons")
        
        # Wait for user input to manually inspect
        input("Press Enter to continue (check the browser window)...")
        
        # Try to find any element with tax deed numbers
        potential_property_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Tax Deed') or contains(text(), '51640') or contains(text(), '51641') or contains(text(), '51642')]")
        print(f"Found {len(potential_property_elements)} elements with tax deed related text")
        
        for element in potential_property_elements[:5]:
            print(f"  Element text: '{element.text}' - Tag: {element.tag_name}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        input("Press Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    debug_page_structure()