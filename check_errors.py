from playwright.sync_api import sync_playwright
import time

def check_console_errors():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Show browser to debug
        page = browser.new_page()
        
        # Collect console messages
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
        
        # Collect page errors
        page_errors = []
        page.on("pageerror", lambda err: page_errors.append(str(err)))
        
        # Navigate to homepage
        print("Checking homepage...")
        page.goto("http://localhost:5173/")
        page.wait_for_timeout(3000)
        
        print("\n=== Console Logs ===")
        for log in console_logs:
            print(log)
            
        print("\n=== Page Errors ===")
        for err in page_errors:
            print(err)
            
        # Check what's actually rendered
        print("\n=== Page Title ===")
        print(page.title())
        
        print("\n=== Body Content (first 500 chars) ===")
        body_text = page.text_content("body")
        print(body_text[:500] if body_text else "No body content")
        
        # Check for React root
        root_html = page.locator("#root").inner_html()
        print("\n=== Root element content (first 500 chars) ===")
        print(root_html[:500] if root_html else "No root content")
        
        time.sleep(5)  # Keep browser open to inspect
        browser.close()

if __name__ == "__main__":
    check_console_errors()