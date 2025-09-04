from playwright.sync_api import sync_playwright
import os
from datetime import datetime

def capture_all_pages():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        # Create screenshots directory
        screenshots_dir = "ui_screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        pages = [
            ("Homepage", "http://localhost:5174/"),
            ("Dashboard", "http://localhost:5174/dashboard"),
            ("Search Properties", "http://localhost:5174/search"),
            ("Analytics", "http://localhost:5174/analytics"),
            ("Portfolio", "http://localhost:5174/portfolio"),
            ("Market Insights", "http://localhost:5174/insights"),
            ("Clients", "http://localhost:5174/clients"),
            ("Profile", "http://localhost:5174/profile"),
            ("Settings", "http://localhost:5174/settings"),
            ("Notifications", "http://localhost:5174/notifications")
        ]
        
        for page_name, url in pages:
            try:
                print(f"Capturing {page_name}...")
                page.goto(url)
                page.wait_for_timeout(3000)
                filename = f"{screenshots_dir}/{page_name.lower().replace(' ', '_')}_{timestamp}.png"
                page.screenshot(path=filename, full_page=True)
                print(f"  [OK] Saved: {filename}")
            except Exception as e:
                print(f"  [ERROR] Error capturing {page_name}: {str(e)}")
        
        browser.close()
        print(f"\nAll screenshots saved in {os.path.abspath(screenshots_dir)}")

if __name__ == "__main__":
    capture_all_pages()