"""
Playwright Automated Data Verification System
Verifies data placement across all tabs and subtabs using browser automation
"""

from playwright.async_api import async_playwright, Page, Browser, ElementHandle
import asyncio
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import json
import logging
from datetime import datetime
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image
import pytesseract
from dataclasses import dataclass, field
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TabVerificationResult:
    """Result of tab data verification"""
    tab_name: str
    fields_checked: int
    fields_correct: int
    fields_missing: int
    fields_incorrect: int
    errors: List[str] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class FieldVerification:
    """Individual field verification result"""
    field_name: str
    expected_value: Any
    actual_value: Any
    location: str
    is_correct: bool
    confidence: float
    screenshot_path: Optional[str] = None
    error: Optional[str] = None

class PlaywrightDataVerifier:
    """Automated verification of data placement using Playwright"""

    def __init__(self, base_url: str = "http://localhost:5173"):
        self.base_url = base_url
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.verification_results = []
        self.screenshots_dir = Path("verification_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)

        # Tab selectors mapping
        self.tab_selectors = {
            'overview': 'button:has-text("Overview")',
            'core-property': 'button:has-text("Core Property Info")',
            'valuation': 'button:has-text("Valuation")',
            'permit': 'button:has-text("Permit")',
            'sunbiz': 'button:has-text("Sunbiz Info")',
            'taxes': 'button:has-text("Property Tax Info")',
            'sales-tax-deed': 'button:has-text("Sales Tax Deed")',
            'tax-deed-sales': 'button:has-text("Tax Deed Sales")',
            'owner': 'button:has-text("Owner")',
            'sales': 'button:has-text("Sales History")',
            'building': 'button:has-text("Building")',
            'land': 'button:has-text("Land & Legal")',
            'exemptions': 'button:has-text("Exemptions")',
            'notes': 'button:has-text("Notes")'
        }

        # Field selectors by tab
        self.field_selectors = self._initialize_field_selectors()

    def _initialize_field_selectors(self) -> Dict[str, Dict[str, str]]:
        """Initialize field selectors for each tab"""
        return {
            'overview': {
                'address': '.property-address, [data-field="address"]',
                'city': '.property-city, [data-field="city"]',
                'parcel_id': '.property-parcel, [data-field="parcel_id"]',
                'just_value': '[data-field="just_value"], .just-value',
                'taxable_value': '[data-field="taxable_value"], .taxable-value',
                'land_value': '[data-field="land_value"], .land-value',
                'sale_price': '[data-field="sale_price"], .sale-price',
                'sale_date': '[data-field="sale_date"], .sale-date'
            },
            'core-property': {
                'owner_name': '[data-field="owner_name"], .owner-name',
                'owner_address': '[data-field="owner_address"], .owner-address',
                'living_area': '[data-field="living_area"], .living-area',
                'land_sqft': '[data-field="land_sqft"], .land-sqft',
                'bedrooms': '[data-field="bedrooms"], .bedrooms',
                'bathrooms': '[data-field="bathrooms"], .bathrooms',
                'year_built': '[data-field="year_built"], .year-built',
                'units': '[data-field="units"], .units'
            },
            'valuation': {
                'market_value': '[data-field="market_value"], .market-value',
                'assessed_value': '[data-field="assessed_value"], .assessed-value',
                'building_value': '[data-field="building_value"], .building-value',
                'land_value': '[data-field="land_value"], .land-value',
                'total_value': '[data-field="total_value"], .total-value'
            },
            'taxes': {
                'tax_amount': '[data-field="tax_amount"], .tax-amount',
                'millage_rate': '[data-field="millage_rate"], .millage-rate',
                'exemptions': '[data-field="exemptions"], .exemptions',
                'homestead': '[data-field="homestead"], .homestead'
            },
            'sunbiz': {
                'entity_name': '[data-field="entity_name"], .entity-name',
                'doc_number': '[data-field="doc_number"], .doc-number',
                'status': '[data-field="entity_status"], .entity-status',
                'filing_date': '[data-field="filing_date"], .filing-date',
                'registered_agent': '[data-field="registered_agent"], .registered-agent'
            },
            'permit': {
                'permit_number': '[data-field="permit_number"], .permit-number',
                'permit_type': '[data-field="permit_type"], .permit-type',
                'issue_date': '[data-field="issue_date"], .issue-date',
                'contractor': '[data-field="contractor"], .contractor',
                'permit_value': '[data-field="permit_value"], .permit-value'
            },
            'sales': {
                'sale_date': '[data-field="sale_date"], .sale-date',
                'sale_price': '[data-field="sale_price"], .sale-price',
                'seller': '[data-field="seller"], .seller',
                'buyer': '[data-field="buyer"], .buyer',
                'deed_type': '[data-field="deed_type"], .deed-type'
            },
            'tax-deed-sales': {
                'td_number': '[data-field="td_number"], .td-number',
                'auction_date': '[data-field="auction_date"], .auction-date',
                'opening_bid': '[data-field="opening_bid"], .opening-bid',
                'winning_bid': '[data-field="winning_bid"], .winning-bid',
                'auction_status': '[data-field="auction_status"], .auction-status'
            }
        }

    async def initialize(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Set to True for production
            args=['--disable-blink-features=AutomationControlled']
        )
        self.page = await self.browser.new_page()

        # Set viewport for consistent screenshots
        await self.page.set_viewport_size({'width': 1920, 'height': 1080})

        logger.info("Playwright browser initialized for data verification")

    async def close(self):
        """Close browser and cleanup"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        logger.info("Browser closed")

    async def navigate_to_property(self, property_id: str):
        """Navigate to a specific property page"""
        url = f"{self.base_url}/property/{property_id}"
        await self.page.goto(url, wait_until='networkidle')
        await self.page.wait_for_timeout(2000)  # Allow page to fully render
        logger.info(f"Navigated to property: {property_id}")

    async def verify_tab_data(self, tab_name: str, expected_data: Dict[str, Any]) -> TabVerificationResult:
        """Verify data in a specific tab"""
        result = TabVerificationResult(tab_name=tab_name, fields_checked=0, fields_correct=0,
                                        fields_missing=0, fields_incorrect=0)

        try:
            # Click on the tab
            if tab_name in self.tab_selectors:
                await self.page.click(self.tab_selectors[tab_name])
                await self.page.wait_for_timeout(1000)  # Wait for tab content to load

            # Take screenshot of tab
            screenshot_path = await self.take_screenshot(f"{tab_name}_tab")
            result.screenshots.append(screenshot_path)

            # Get field selectors for this tab
            field_selectors = self.field_selectors.get(tab_name, {})

            # Verify each field
            for field_name, selector in field_selectors.items():
                result.fields_checked += 1

                # Get expected value
                expected_value = expected_data.get(field_name)

                # Verify field
                field_result = await self.verify_field(field_name, selector, expected_value)

                if field_result.is_correct:
                    result.fields_correct += 1
                elif field_result.actual_value is None:
                    result.fields_missing += 1
                    result.errors.append(f"Field '{field_name}' is missing")
                else:
                    result.fields_incorrect += 1
                    result.errors.append(
                        f"Field '{field_name}' incorrect: expected '{expected_value}', got '{field_result.actual_value}'"
                    )

            # Calculate confidence
            if result.fields_checked > 0:
                result.confidence = result.fields_correct / result.fields_checked

        except Exception as e:
            logger.error(f"Error verifying tab {tab_name}: {e}")
            result.errors.append(str(e))

        return result

    async def verify_field(self, field_name: str, selector: str, expected_value: Any) -> FieldVerification:
        """Verify a single field value"""
        verification = FieldVerification(
            field_name=field_name,
            expected_value=expected_value,
            actual_value=None,
            location=selector,
            is_correct=False,
            confidence=0.0
        )

        try:
            # Try multiple selector strategies
            element = None
            selectors_to_try = [
                selector,
                f"text={field_name}",
                f"[aria-label*='{field_name}']",
                f"*:has-text('{field_name}')"
            ]

            for sel in selectors_to_try:
                try:
                    element = await self.page.wait_for_selector(sel, timeout=3000)
                    if element:
                        break
                except:
                    continue

            if element:
                # Get actual value
                actual_value = await self.extract_field_value(element)
                verification.actual_value = actual_value

                # Compare values
                verification.is_correct, verification.confidence = self.compare_values(
                    expected_value, actual_value
                )

                # Take screenshot if incorrect
                if not verification.is_correct:
                    screenshot_path = await self.take_element_screenshot(element, field_name)
                    verification.screenshot_path = screenshot_path

        except Exception as e:
            verification.error = str(e)
            logger.warning(f"Could not verify field {field_name}: {e}")

        return verification

    async def extract_field_value(self, element: ElementHandle) -> Any:
        """Extract value from an element"""
        try:
            # Try different methods to get value
            value = await element.inner_text()

            if not value:
                value = await element.get_attribute('value')

            if not value:
                value = await element.get_attribute('data-value')

            # Clean the value
            if value:
                value = value.strip()
                # Remove currency symbols and format
                if '$' in value:
                    value = value.replace('$', '').replace(',', '')
                    try:
                        value = float(value)
                    except:
                        pass

            return value

        except Exception as e:
            logger.error(f"Error extracting field value: {e}")
            return None

    def compare_values(self, expected: Any, actual: Any) -> Tuple[bool, float]:
        """Compare expected and actual values"""
        if expected is None and actual is None:
            return True, 1.0

        if expected is None or actual is None:
            return False, 0.0

        # Convert to strings for comparison
        expected_str = str(expected).lower().strip()
        actual_str = str(actual).lower().strip()

        # Exact match
        if expected_str == actual_str:
            return True, 1.0

        # Numeric comparison with tolerance
        try:
            expected_num = float(expected_str.replace(',', '').replace('$', ''))
            actual_num = float(actual_str.replace(',', '').replace('$', ''))
            if abs(expected_num - actual_num) < 0.01:
                return True, 0.99
        except:
            pass

        # Fuzzy string matching
        from fuzzywuzzy import fuzz
        similarity = fuzz.ratio(expected_str, actual_str) / 100.0

        return similarity > 0.85, similarity

    async def take_screenshot(self, name: str) -> str:
        """Take a screenshot of the current page"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = self.screenshots_dir / filename

        await self.page.screenshot(path=str(filepath), full_page=False)

        return str(filepath)

    async def take_element_screenshot(self, element: ElementHandle, name: str) -> str:
        """Take a screenshot of a specific element"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"element_{name}_{timestamp}.png"
        filepath = self.screenshots_dir / filename

        await element.screenshot(path=str(filepath))

        return str(filepath)

    async def verify_all_tabs(self, property_id: str, expected_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Verify data across all tabs for a property"""
        results = {
            'property_id': property_id,
            'timestamp': datetime.now().isoformat(),
            'tabs': {},
            'summary': {
                'total_tabs': 0,
                'tabs_verified': 0,
                'total_fields': 0,
                'fields_correct': 0,
                'fields_missing': 0,
                'fields_incorrect': 0,
                'overall_confidence': 0.0
            }
        }

        # Navigate to property
        await self.navigate_to_property(property_id)

        # Verify each tab
        for tab_name in self.tab_selectors.keys():
            if tab_name in expected_data:
                logger.info(f"Verifying tab: {tab_name}")

                # Verify tab data
                tab_result = await self.verify_tab_data(tab_name, expected_data[tab_name])
                results['tabs'][tab_name] = {
                    'fields_checked': tab_result.fields_checked,
                    'fields_correct': tab_result.fields_correct,
                    'fields_missing': tab_result.fields_missing,
                    'fields_incorrect': tab_result.fields_incorrect,
                    'confidence': tab_result.confidence,
                    'errors': tab_result.errors,
                    'screenshots': tab_result.screenshots
                }

                # Update summary
                results['summary']['total_tabs'] += 1
                if tab_result.confidence > 0.8:
                    results['summary']['tabs_verified'] += 1
                results['summary']['total_fields'] += tab_result.fields_checked
                results['summary']['fields_correct'] += tab_result.fields_correct
                results['summary']['fields_missing'] += tab_result.fields_missing
                results['summary']['fields_incorrect'] += tab_result.fields_incorrect

        # Calculate overall confidence
        if results['summary']['total_fields'] > 0:
            results['summary']['overall_confidence'] = (
                results['summary']['fields_correct'] / results['summary']['total_fields']
            )

        # Generate verification status
        confidence = results['summary']['overall_confidence']
        if confidence >= 0.95:
            results['status'] = 'VERIFIED'
        elif confidence >= 0.80:
            results['status'] = 'MOSTLY_VERIFIED'
        elif confidence >= 0.60:
            results['status'] = 'PARTIALLY_VERIFIED'
        else:
            results['status'] = 'NEEDS_REVIEW'

        return results

    async def visual_verification_with_ocr(self, screenshot_path: str) -> Dict[str, Any]:
        """Perform OCR on screenshot to verify data visibility"""
        try:
            # Load image
            image = cv2.imread(screenshot_path)

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply thresholding
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

            # Perform OCR
            text = pytesseract.image_to_string(thresh)

            # Extract key-value pairs
            lines = text.split('\n')
            data_found = {}

            for line in lines:
                # Look for patterns like "Field: Value"
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        data_found[key] = value

            return {
                'screenshot': screenshot_path,
                'text_found': text,
                'data_extracted': data_found,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"OCR verification failed: {e}")
            return {'error': str(e)}

    async def generate_verification_report(self, results: Dict[str, Any]) -> str:
        """Generate HTML verification report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Data Verification Report - {results['property_id']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .summary {{ background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .tab-result {{ margin: 20px 0; padding: 15px; border: 1px solid #bdc3c7; border-radius: 5px; }}
                .success {{ color: #27ae60; font-weight: bold; }}
                .error {{ color: #e74c3c; font-weight: bold; }}
                .warning {{ color: #f39c12; font-weight: bold; }}
                .confidence-bar {{ background: #ecf0f1; height: 20px; border-radius: 10px; overflow: hidden; }}
                .confidence-fill {{ background: #3498db; height: 100%; transition: width 0.3s; }}
                .screenshot {{ max-width: 300px; margin: 10px; border: 1px solid #bdc3c7; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ecf0f1; }}
                th {{ background: #34495e; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Data Verification Report</h1>
                <p>Property ID: {results['property_id']}</p>
                <p>Generated: {results['timestamp']}</p>
                <p>Status: <span class="{self.get_status_class(results['status'])}">{results['status']}</span></p>
            </div>

            <div class="summary">
                <h2>Summary</h2>
                <p>Total Tabs Checked: {results['summary']['total_tabs']}</p>
                <p>Tabs Verified: {results['summary']['tabs_verified']}</p>
                <p>Total Fields: {results['summary']['total_fields']}</p>
                <p>Fields Correct: <span class="success">{results['summary']['fields_correct']}</span></p>
                <p>Fields Missing: <span class="warning">{results['summary']['fields_missing']}</span></p>
                <p>Fields Incorrect: <span class="error">{results['summary']['fields_incorrect']}</span></p>
                <h3>Overall Confidence: {results['summary']['overall_confidence']:.1%}</h3>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: {results['summary']['overall_confidence']*100}%"></div>
                </div>
            </div>

            <h2>Tab Results</h2>
        """

        for tab_name, tab_data in results['tabs'].items():
            html += f"""
            <div class="tab-result">
                <h3>{tab_name.replace('-', ' ').title()}</h3>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Fields Checked</td>
                        <td>{tab_data['fields_checked']}</td>
                    </tr>
                    <tr>
                        <td>Fields Correct</td>
                        <td class="success">{tab_data['fields_correct']}</td>
                    </tr>
                    <tr>
                        <td>Fields Missing</td>
                        <td class="warning">{tab_data['fields_missing']}</td>
                    </tr>
                    <tr>
                        <td>Fields Incorrect</td>
                        <td class="error">{tab_data['fields_incorrect']}</td>
                    </tr>
                    <tr>
                        <td>Confidence</td>
                        <td>{tab_data['confidence']:.1%}</td>
                    </tr>
                </table>
            """

            if tab_data['errors']:
                html += "<h4>Errors:</h4><ul>"
                for error in tab_data['errors']:
                    html += f"<li class='error'>{error}</li>"
                html += "</ul>"

            html += "</div>"

        html += """
        </body>
        </html>
        """

        # Save report
        report_path = self.screenshots_dir / f"verification_report_{results['property_id']}.html"
        with open(report_path, 'w') as f:
            f.write(html)

        return str(report_path)

    def get_status_class(self, status: str) -> str:
        """Get CSS class for status"""
        if status == 'VERIFIED':
            return 'success'
        elif status == 'MOSTLY_VERIFIED':
            return 'warning'
        else:
            return 'error'

# Integration with MCP
class MCPVerificationIntegration:
    """Integration with MCP Server for verification results"""

    def __init__(self, mcp_url: str = "http://localhost:3001"):
        self.mcp_url = mcp_url
        self.verifier = PlaywrightDataVerifier()

    async def verify_and_report(self, property_id: str, expected_data: Dict[str, Dict[str, Any]]):
        """Verify property data and report to MCP"""

        # Initialize verifier
        await self.verifier.initialize()

        try:
            # Run verification
            results = await self.verifier.verify_all_tabs(property_id, expected_data)

            # Generate report
            report_path = await self.verifier.generate_verification_report(results)

            # Send results to MCP
            async with aiohttp.ClientSession() as session:
                headers = {
                    'x-api-key': 'concordbroker-mcp-key-claude',
                    'Content-Type': 'application/json'
                }

                payload = {
                    'property_id': property_id,
                    'verification_results': results,
                    'report_path': report_path
                }

                async with session.post(
                    f"{self.mcp_url}/api/verification/playwright",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        logger.info(f"Verification results sent to MCP for {property_id}")
                    else:
                        logger.error(f"Failed to send verification results: {response.status}")

        finally:
            await self.verifier.close()

        return results

# Example usage
async def main():
    """Example usage of Playwright verification"""

    verifier = PlaywrightDataVerifier()
    await verifier.initialize()

    try:
        # Sample expected data
        expected_data = {
            'overview': {
                'address': '123 Main St',
                'city': 'Miami',
                'parcel_id': '064210010010',
                'just_value': 500000,
                'taxable_value': 450000
            },
            'core-property': {
                'owner_name': 'John Doe',
                'living_area': 2500,
                'bedrooms': 3,
                'bathrooms': 2.5,
                'year_built': 2005
            }
        }

        # Run verification
        results = await verifier.verify_all_tabs('064210010010', expected_data)

        print(f"Verification Status: {results['status']}")
        print(f"Overall Confidence: {results['summary']['overall_confidence']:.1%}")

        # Generate report
        report_path = await verifier.generate_verification_report(results)
        print(f"Report saved to: {report_path}")

    finally:
        await verifier.close()

if __name__ == "__main__":
    asyncio.run(main())