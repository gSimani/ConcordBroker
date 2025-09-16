"""
Playwright Visual Verification System for ConcordBroker
Uses Playwright MCP and OpenCV for visual validation of data display
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import pytesseract
from playwright.async_api import async_playwright, Page, Browser
import requests
from dotenv import load_dotenv
import base64
from io import BytesIO
import re

load_dotenv('.env.mcp')

class PlaywrightVisualVerifier:
    """Visual verification system using Playwright and OpenCV"""

    def __init__(self):
        self.mcp_url = "http://localhost:3005"
        self.api_key = os.getenv('MCP_API_KEY', 'concordbroker-mcp-key-claude')
        self.frontend_url = "http://localhost:5173"
        self.screenshots_dir = Path("visual_verification_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)

        # Expected data mappings for verification
        self.verification_rules = {
            'overview': {
                'selectors': {
                    'property_address': '[data-testid="property-address"]',
                    'owner_name': '[data-testid="owner-name"]',
                    'parcel_id': '[data-testid="parcel-id"]',
                    'just_value': '[data-testid="just-value"]',
                    'land_sqft': '[data-testid="land-sqft"]',
                    'building_sqft': '[data-testid="building-sqft"]',
                    'year_built': '[data-testid="year-built"]',
                    'bedrooms': '[data-testid="bedrooms"]',
                    'bathrooms': '[data-testid="bathrooms"]'
                },
                'patterns': {
                    'property_address': r'\d+\s+[\w\s]+\,\s+\w+\,\s+FL\s+\d{5}',
                    'parcel_id': r'\d{12,}',
                    'just_value': r'\$[\d,]+',
                    'land_sqft': r'[\d,]+\s*sq\s*ft',
                    'year_built': r'(19|20)\d{2}'
                }
            },
            'ownership': {
                'selectors': {
                    'owner_name': '[data-testid="owner-name"]',
                    'owner_address': '[data-testid="owner-address"]',
                    'entity_name': '[data-testid="entity-name"]',
                    'entity_status': '[data-testid="entity-status"]',
                    'incorporation_date': '[data-testid="incorporation-date"]'
                },
                'patterns': {
                    'entity_status': r'(ACTIVE|INACTIVE|DISSOLVED)',
                    'incorporation_date': r'\d{2}/\d{2}/\d{4}'
                }
            },
            'sales_history': {
                'selectors': {
                    'sale_date': '.sale-date',
                    'sale_price': '.sale-price',
                    'seller_name': '.seller-name',
                    'buyer_name': '.buyer-name'
                },
                'patterns': {
                    'sale_price': r'\$[\d,]+',
                    'sale_date': r'\d{2}/\d{2}/\d{4}'
                }
            },
            'tax_deed': {
                'selectors': {
                    'td_number': '[data-testid="td-number"]',
                    'auction_date': '[data-testid="auction-date"]',
                    'auction_status': '[data-testid="auction-status"]',
                    'winning_bid': '[data-testid="winning-bid"]',
                    'opening_bid': '[data-testid="opening-bid"]'
                },
                'patterns': {
                    'td_number': r'TD-\d{4}-\d+',
                    'auction_status': r'(UPCOMING|CANCELLED|COMPLETED|REDEEMED)',
                    'winning_bid': r'\$[\d,]+'
                }
            }
        }

    async def capture_tab_screenshots(self, parcel_id: str) -> Dict[str, str]:
        """Capture screenshots of all tabs for a property"""
        screenshots = {}

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Set to True in production
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            try:
                # Navigate to property page
                property_url = f"{self.frontend_url}/property/{parcel_id}"
                await page.goto(property_url, wait_until='networkidle')

                # Wait for main content to load
                await page.wait_for_selector('[data-testid="property-content"]', timeout=10000)

                # Capture screenshots for each tab
                tabs = ['overview', 'ownership', 'sales-history', 'tax-deed', 'taxes', 'permits', 'sunbiz', 'analysis']

                for tab_name in tabs:
                    print(f"Capturing {tab_name} tab...")

                    # Click on tab
                    tab_selector = f'[data-testid="tab-{tab_name}"]'
                    try:
                        await page.click(tab_selector)
                        await page.wait_for_timeout(1000)  # Wait for content to load

                        # Capture screenshot
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        screenshot_path = self.screenshots_dir / f"{parcel_id}_{tab_name}_{timestamp}.png"
                        await page.screenshot(path=str(screenshot_path), full_page=True)
                        screenshots[tab_name] = str(screenshot_path)

                    except Exception as e:
                        print(f"Error capturing {tab_name}: {str(e)}")
                        screenshots[tab_name] = None

            finally:
                await browser.close()

        return screenshots

    async def verify_data_display(self, page: Page, tab_name: str, expected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that expected data is correctly displayed on the page"""
        verification_results = {
            'tab': tab_name,
            'timestamp': datetime.now().isoformat(),
            'field_verifications': {},
            'overall_accuracy': 0
        }

        if tab_name not in self.verification_rules:
            verification_results['error'] = f"No verification rules for tab: {tab_name}"
            return verification_results

        rules = self.verification_rules[tab_name]
        successful_verifications = 0
        total_verifications = 0

        # Verify each field
        for field_name, selector in rules['selectors'].items():
            total_verifications += 1
            field_result = {
                'selector': selector,
                'expected': expected_data.get(field_name),
                'found': None,
                'match': False
            }

            try:
                # Get element text
                element = await page.query_selector(selector)
                if element:
                    actual_text = await element.inner_text()
                    field_result['found'] = actual_text

                    # Check if expected data matches
                    if field_name in expected_data:
                        expected = str(expected_data[field_name])

                        # Direct match
                        if expected.lower() in actual_text.lower():
                            field_result['match'] = True
                            successful_verifications += 1

                        # Pattern match
                        elif field_name in rules.get('patterns', {}):
                            pattern = rules['patterns'][field_name]
                            if re.search(pattern, actual_text):
                                field_result['match'] = True
                                successful_verifications += 1
                else:
                    field_result['error'] = "Element not found"

            except Exception as e:
                field_result['error'] = str(e)

            verification_results['field_verifications'][field_name] = field_result

        # Calculate overall accuracy
        if total_verifications > 0:
            verification_results['overall_accuracy'] = successful_verifications / total_verifications

        return verification_results

    def extract_text_with_ocr(self, image_path: str, region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """Extract text from image using OCR"""
        try:
            image = cv2.imread(image_path)

            if region:
                x, y, w, h = region
                image = image[y:y+h, x:x+w]

            # Preprocess image for better OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

            # Extract text
            text = pytesseract.image_to_string(thresh)
            return text.strip()

        except Exception as e:
            print(f"OCR error: {str(e)}")
            return ""

    def compare_images(self, image1_path: str, image2_path: str) -> float:
        """Compare two images using OpenCV and return similarity score"""
        try:
            img1 = cv2.imread(image1_path)
            img2 = cv2.imread(image2_path)

            # Resize images to same dimensions if needed
            if img1.shape != img2.shape:
                height = min(img1.shape[0], img2.shape[0])
                width = min(img1.shape[1], img2.shape[1])
                img1 = cv2.resize(img1, (width, height))
                img2 = cv2.resize(img2, (width, height))

            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

            # Calculate structural similarity
            score = cv2.matchTemplate(gray1, gray2, cv2.TM_CCOEFF_NORMED)[0][0]

            return float(score)

        except Exception as e:
            print(f"Image comparison error: {str(e)}")
            return 0.0

    def detect_data_regions(self, image_path: str) -> List[Dict[str, Any]]:
        """Detect regions in image that likely contain data"""
        try:
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detect text regions
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # Filter out small regions
                if w > 50 and h > 20:
                    regions.append({
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'area': w * h
                    })

            # Sort by y-coordinate (top to bottom)
            regions.sort(key=lambda r: r['y'])

            return regions

        except Exception as e:
            print(f"Region detection error: {str(e)}")
            return []

    def create_visual_diff(self, expected_image: str, actual_image: str, output_path: str):
        """Create a visual diff between expected and actual images"""
        try:
            img1 = cv2.imread(expected_image)
            img2 = cv2.imread(actual_image)

            # Ensure same dimensions
            if img1.shape != img2.shape:
                height = max(img1.shape[0], img2.shape[0])
                width = max(img1.shape[1], img2.shape[1])
                img1 = cv2.resize(img1, (width, height))
                img2 = cv2.resize(img2, (width, height))

            # Calculate difference
            diff = cv2.absdiff(img1, img2)

            # Highlight differences in red
            mask = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(mask, 30, 255, cv2.THRESH_BINARY)

            # Create output image
            output = img2.copy()
            output[thresh > 0] = [0, 0, 255]  # Red color for differences

            # Save comparison
            comparison = np.hstack([img1, img2, output])
            cv2.imwrite(output_path, comparison)

            return output_path

        except Exception as e:
            print(f"Visual diff error: {str(e)}")
            return None

    async def run_visual_verification(self, parcel_id: str, expected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete visual verification for a property"""
        print(f"Starting visual verification for parcel: {parcel_id}")

        verification_report = {
            'parcel_id': parcel_id,
            'timestamp': datetime.now().isoformat(),
            'screenshots': {},
            'tab_verifications': {},
            'ocr_results': {},
            'overall_score': 0
        }

        # Capture screenshots
        print("Capturing screenshots...")
        screenshots = await self.capture_tab_screenshots(parcel_id)
        verification_report['screenshots'] = screenshots

        # Perform OCR on screenshots
        print("Performing OCR analysis...")
        for tab_name, screenshot_path in screenshots.items():
            if screenshot_path and os.path.exists(screenshot_path):
                # Extract text from entire image
                extracted_text = self.extract_text_with_ocr(screenshot_path)
                verification_report['ocr_results'][tab_name] = {
                    'text': extracted_text[:500],  # Limit for report
                    'length': len(extracted_text)
                }

                # Detect data regions
                regions = self.detect_data_regions(screenshot_path)
                verification_report['ocr_results'][tab_name]['regions_detected'] = len(regions)

        # Verify data display using Playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                property_url = f"{self.frontend_url}/property/{parcel_id}"
                await page.goto(property_url, wait_until='networkidle')

                # Verify each tab
                for tab_name in ['overview', 'ownership', 'sales-history', 'tax-deed']:
                    if tab_name in expected_data:
                        print(f"Verifying {tab_name} tab...")
                        tab_verification = await self.verify_data_display(
                            page, tab_name, expected_data[tab_name]
                        )
                        verification_report['tab_verifications'][tab_name] = tab_verification

            finally:
                await browser.close()

        # Calculate overall verification score
        scores = [v.get('overall_accuracy', 0) for v in verification_report['tab_verifications'].values()]
        if scores:
            verification_report['overall_score'] = np.mean(scores)

        # Save verification report
        report_path = self.screenshots_dir / f"verification_report_{parcel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(verification_report, f, indent=2)

        print(f"Verification complete! Report saved to: {report_path}")

        return verification_report

    async def batch_verify_properties(self, property_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify multiple properties in batch"""
        batch_report = {
            'timestamp': datetime.now().isoformat(),
            'total_properties': len(property_list),
            'property_verifications': {},
            'summary': {
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }

        for property_data in property_list:
            parcel_id = property_data.get('parcel_id')
            if parcel_id:
                print(f"\nVerifying property: {parcel_id}")
                verification = await self.run_visual_verification(parcel_id, property_data)

                batch_report['property_verifications'][parcel_id] = verification

                # Update summary
                if verification['overall_score'] >= 0.9:
                    batch_report['summary']['passed'] += 1
                elif verification['overall_score'] >= 0.7:
                    batch_report['summary']['warnings'] += 1
                else:
                    batch_report['summary']['failed'] += 1

        # Calculate overall batch score
        batch_report['overall_batch_score'] = np.mean([
            v['overall_score'] for v in batch_report['property_verifications'].values()
        ])

        return batch_report


async def main():
    """Main execution function"""
    verifier = PlaywrightVisualVerifier()

    # Example property with expected data
    test_property = {
        'parcel_id': '064210010010',
        'overview': {
            'property_address': '123 Main St, Miami, FL 33101',
            'owner_name': 'John Doe',
            'just_value': '$500,000',
            'land_sqft': '10,000',
            'year_built': '2005'
        },
        'ownership': {
            'entity_name': 'ABC Properties LLC',
            'entity_status': 'ACTIVE',
            'incorporation_date': '01/15/2020'
        },
        'sales_history': {
            'sale_date': '06/15/2023',
            'sale_price': '$450,000',
            'buyer_name': 'John Doe'
        },
        'tax_deed': {
            'td_number': 'TD-2024-001',
            'auction_status': 'UPCOMING',
            'opening_bid': '$25,000'
        }
    }

    # Run visual verification
    verification_report = await verifier.run_visual_verification(
        test_property['parcel_id'],
        test_property
    )

    print("\n" + "=" * 60)
    print("VISUAL VERIFICATION COMPLETE")
    print("=" * 60)
    print(f"Overall Score: {verification_report['overall_score']:.1%}")

    # Print tab verification results
    for tab_name, tab_result in verification_report['tab_verifications'].items():
        print(f"\n{tab_name.upper()} Tab:")
        print(f"  Accuracy: {tab_result.get('overall_accuracy', 0):.1%}")

        for field, result in tab_result.get('field_verifications', {}).items():
            status = "✅" if result.get('match') else "❌"
            print(f"    {status} {field}: {result.get('found', 'Not found')}")


if __name__ == "__main__":
    asyncio.run(main())