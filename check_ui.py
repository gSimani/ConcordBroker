from playwright.sync_api import sync_playwright
import os
from datetime import datetime

def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        # Create screenshots directory
        screenshots_dir = "ui_screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Check homepage
        print("Capturing homepage...")
        page.goto("http://localhost:5174/")
        page.wait_for_timeout(2000)
        page.screenshot(path=f"{screenshots_dir}/homepage_{timestamp}.png", full_page=True)
        
        # Check dashboard
        print("Capturing dashboard...")
        page.goto("http://localhost:5174/dashboard")
        page.wait_for_timeout(3000)
        page.screenshot(path=f"{screenshots_dir}/dashboard_{timestamp}.png", full_page=True)
        
        # Check search page
        print("Capturing search page...")
        page.goto("http://localhost:5174/search")
        page.wait_for_timeout(2000)
        page.screenshot(path=f"{screenshots_dir}/search_{timestamp}.png", full_page=True)
        
        browser.close()
        print(f"Screenshots saved in {os.path.abspath(screenshots_dir)}")

if __name__ == "__main__":
    take_screenshots()