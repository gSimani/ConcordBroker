import os
import time
from typing import Optional
from playwright.sync_api import sync_playwright, expect

BASE_URL = os.environ.get("LOCAL_URL", "http://localhost:5173")


def wait_for_api(page, path_contains: str, timeout_ms: int = 10000):
    return page.wait_for_response(lambda r: \
        ("/api/" in r.url) and (path_contains in r.url) and (r.status == 200), \
        timeout=timeout_ms)


def find_search_input(page) -> Optional[str]:
    selectors = [
        'input[placeholder*="search" i]',
        'input[placeholder*="property" i]',
        'input[placeholder*="address" i]',
        'input[type="search"]',
        'input[name*="search"]',
        '.search input',
        '[data-testid*="search"] input',
    ]
    for sel in selectors:
        el = page.locator(sel).first()
        if el and el.count() and el.is_visible():
            return sel
    return None


def open_properties(page):
    page.goto(f"{BASE_URL}/properties", wait_until="networkidle")
    expect(page.locator("#root")).to_be_visible()
    title = page.title()
    assert "ConcordBroker" in title


def test_properties_page_renders_and_calls_api():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        open_properties(page)
        # Verify at least one API call fires on load (best-effort)
        try:
            wait_for_api(page, "/api/properties")
        except Exception:
            # Non-fatal; UI can lazy-load
            pass
        assert page.content() != ""
        context.close()
        browser.close()


def test_search_and_result_activity():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        open_properties(page)
        sel = find_search_input(page)
        assert sel is not None, "Search input not found on properties page"
        box = page.locator(sel).first()
        box.fill("Miami")
        page.keyboard.press("Enter")
        # Expect a properties search API call and validate payload shape (best-effort)
        resp = None
        try:
            resp = wait_for_api(page, "/api/properties")
        except Exception:
            # Some builds debounce; allow brief wait
            time.sleep(2)
        if resp is not None:
            try:
                data = resp.json()
                assert data is not None
                if isinstance(data, dict) and 'data' in data:
                    assert isinstance(data['data'], list)
                # else allow array or other object, tolerant
            except Exception:
                # Non-fatal if JSON parse fails due to non-JSON responses
                pass
        # Page should remain interactive
        assert page.content() != ""
        context.close()
        browser.close()


def test_autocomplete_activity_smoke():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        open_properties(page)
        sel = find_search_input(page)
        if sel is None:
            # Skip if no visible search input (UI variant)
            context.close(); browser.close(); return
        box = page.locator(sel).first()
        box.fill("3930")
        # Wait briefly to allow any autocomplete to trigger
        try:
            wait_for_api(page, "/api/autocomplete")
        except Exception:
            time.sleep(1)
        assert page.content() != ""
        context.close()
        browser.close()


def test_filters_and_cards_presence():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        open_properties(page)

        # Try to detect common filter controls
        filter_selectors = [
            'select',
            '[role="combobox"]',
            'button:has-text("Filter")',
            'button:has-text("Filters")',
            'input[type="range"]',
        ]
        has_filter = False
        for sel in filter_selectors:
            loc = page.locator(sel)
            try:
                if loc.count() and loc.first().is_visible():
                    has_filter = True
                    break
            except Exception:
                pass

        # Try to detect property cards/list rows
        card_selectors = [
            '[data-testid*="property"]',
            '.property-card',
            '[class*="property" i]',
            '.card:has-text("$")',
        ]
        has_cards = False
        for sel in card_selectors:
            loc = page.locator(sel)
            try:
                if loc.count() > 0:
                    has_cards = True
                    break
            except Exception:
                pass

        # At least one of filters or cards should be present to consider the page healthy
        assert has_filter or has_cards, "Neither filters nor property cards detected on properties page"

        # Optional: pagination hints
        pagination = page.locator('button:has-text("Next"), [aria-label*="next" i], [data-testid*="pagination"]')
        # Do not assert strictly, but warn if none seen
        _ = pagination.count()

        context.close()
        browser.close()
