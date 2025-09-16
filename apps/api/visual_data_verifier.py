"""
Visual Data Verification System using Playwright and OpenCV
Ensures data appears correctly in the UI using computer vision
"""

import asyncio
import json
import os
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import cv2
import pytesseract
from PIL import Image
from playwright.async_api import async_playwright, Page, Browser
from sklearn.metrics import accuracy_score
import base64
from io import BytesIO

@dataclass
class VerificationResult:
    """Result of visual verification for a data field"""
    field_name: str
    expected_value: Any
    displayed_value: Any
    match_confidence: float
    screenshot_path: str
    coordinates: Tuple[int, int, int, int]  # x, y, width, height
    verification_status: str  # 'passed', 'failed', 'partial'
    timestamp: datetime

class VisualDataVerifier:
    """Visual verification system for data accuracy"""

    def __init__(self, base_url: str = "http://localhost:5173"):
        self.base_url = base_url
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.verification_results: List[VerificationResult] = []

        # Configure Tesseract for OCR
        # Update this path based on your Tesseract installation
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

        # OpenCV templates for UI elements
        self.ui_templates = {}

    async def initialize(self):
        """Initialize Playwright browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Set to True for production
            args=['--start-maximized']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await self.context.new_page()

    async def close(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate_to_property(self, parcel_id: str):
        """Navigate to a property profile page"""
        url = f"{self.base_url}/property/{parcel_id}"
        await self.page.goto(url, wait_until='networkidle')
        await self.page.wait_for_timeout(2000)  # Wait for dynamic content

    async def navigate_to_tab(self, tab_name: str):
        """Navigate to a specific tab in the property view"""
        # Click on the tab
        tab_selector = f'[data-tab="{tab_name}"], button:has-text("{tab_name}"), [value="{tab_name}"]'
        try:
            await self.page.click(tab_selector, timeout=5000)
            await self.page.wait_for_timeout(1000)  # Wait for tab content to load
        except:
            # Try alternative selectors
            await self.page.click(f'text="{tab_name}"')
            await self.page.wait_for_timeout(1000)

    async def capture_screenshot(self, element_selector: str = None) -> bytes:
        """Capture screenshot of page or specific element"""
        if element_selector:
            element = await self.page.query_selector(element_selector)
            if element:
                return await element.screenshot()
        return await self.page.screenshot(full_page=True)

    def extract_text_from_image(self, image_bytes: bytes, region: Tuple[int, int, int, int] = None) -> str:
        """Extract text from image using OCR"""
        # Convert bytes to OpenCV image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Crop to region if specified
        if region:
            x, y, w, h = region
            img = img[y:y+h, x:x+w]

        # Preprocess image for better OCR
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        # Denoise
        denoised = cv2.medianBlur(thresh, 3)

        # Extract text using Tesseract
        text = pytesseract.image_to_string(denoised, config='--psm 6')
        return text.strip()

    def find_element_coordinates(self, image_bytes: bytes, template_path: str) -> Optional[Tuple[int, int, int, int]]:
        """Find UI element coordinates using template matching"""
        # Convert bytes to OpenCV image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Load template
        if os.path.exists(template_path):
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            h, w = template.shape

            # Perform template matching
            result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val > 0.8:  # Confidence threshold
                return (max_loc[0], max_loc[1], w, h)
        return None

    async def verify_field_value(self, field_selector: str, expected_value: Any, field_name: str) -> VerificationResult:
        """Verify that a field displays the expected value"""
        try:
            # Get element text using Playwright
            element = await self.page.query_selector(field_selector)
            if not element:
                # Try alternative selectors
                element = await self.page.query_selector(f'[data-field="{field_name}"]')
                if not element:
                    element = await self.page.query_selector(f'text=/{field_name}/i')

            if element:
                # Get displayed text
                displayed_text = await element.text_content()
                displayed_text = displayed_text.strip() if displayed_text else ""

                # Get element bounding box
                bbox = await element.bounding_box()

                # Take screenshot for OCR verification
                screenshot_bytes = await element.screenshot()

                # Extract text using OCR for double verification
                ocr_text = self.extract_text_from_image(screenshot_bytes)

                # Calculate match confidence
                confidence = self._calculate_match_confidence(
                    expected_value, displayed_text, ocr_text
                )

                # Save screenshot
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"verification/{field_name}_{timestamp}.png"
                os.makedirs("verification", exist_ok=True)

                with open(screenshot_path, "wb") as f:
                    f.write(screenshot_bytes)

                # Determine verification status
                if confidence >= 0.95:
                    status = "passed"
                elif confidence >= 0.7:
                    status = "partial"
                else:
                    status = "failed"

                return VerificationResult(
                    field_name=field_name,
                    expected_value=expected_value,
                    displayed_value=displayed_text,
                    match_confidence=confidence,
                    screenshot_path=screenshot_path,
                    coordinates=(bbox['x'], bbox['y'], bbox['width'], bbox['height']) if bbox else (0, 0, 0, 0),
                    verification_status=status,
                    timestamp=datetime.now()
                )

            else:
                # Element not found
                return VerificationResult(
                    field_name=field_name,
                    expected_value=expected_value,
                    displayed_value=None,
                    match_confidence=0.0,
                    screenshot_path="",
                    coordinates=(0, 0, 0, 0),
                    verification_status="failed",
                    timestamp=datetime.now()
                )

        except Exception as e:
            print(f"Error verifying field {field_name}: {e}")
            return VerificationResult(
                field_name=field_name,
                expected_value=expected_value,
                displayed_value=None,
                match_confidence=0.0,
                screenshot_path="",
                coordinates=(0, 0, 0, 0),
                verification_status="error",
                timestamp=datetime.now()
            )

    def _calculate_match_confidence(self, expected: Any, displayed: str, ocr_text: str) -> float:
        """Calculate confidence score for field match"""
        # Convert expected value to string
        expected_str = str(expected)

        # Clean and normalize strings
        expected_clean = self._normalize_text(expected_str)
        displayed_clean = self._normalize_text(displayed)
        ocr_clean = self._normalize_text(ocr_text)

        # Calculate similarity scores
        display_score = self._string_similarity(expected_clean, displayed_clean)
        ocr_score = self._string_similarity(expected_clean, ocr_clean)

        # Weight displayed text more than OCR (as it's more reliable)
        confidence = (display_score * 0.7) + (ocr_score * 0.3)

        # Special handling for currency values
        if "$" in expected_str or "$" in displayed:
            expected_num = self._extract_number(expected_str)
            displayed_num = self._extract_number(displayed)
            if expected_num and displayed_num:
                if abs(expected_num - displayed_num) < 0.01:
                    confidence = 1.0

        return confidence

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        # Remove special characters and normalize spaces
        text = re.sub(r'[^\w\s.-]', '', str(text))
        text = ' '.join(text.split())
        return text.lower()

    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using Levenshtein distance"""
        if not str1 or not str2:
            return 0.0 if (str1 or str2) else 1.0

        # Simple character-based similarity
        longer = str1 if len(str1) > len(str2) else str2
        shorter = str2 if longer == str1 else str1

        if len(longer) == 0:
            return 1.0

        edit_distance = self._levenshtein_distance(shorter, longer)
        return (len(longer) - edit_distance) / len(longer)

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _extract_number(self, text: str) -> Optional[float]:
        """Extract numeric value from text"""
        # Remove currency symbols and commas
        text = re.sub(r'[$,]', '', text)
        # Find first number
        match = re.search(r'[\d.]+', text)
        if match:
            try:
                return float(match.group())
            except:
                pass
        return None

    async def verify_property_data(self, parcel_id: str, expected_data: Dict[str, Dict]) -> List[VerificationResult]:
        """Verify all data for a property across all tabs"""
        results = []

        # Navigate to property
        await self.navigate_to_property(parcel_id)
        await self.page.wait_for_timeout(3000)

        # Verify each tab's data
        for tab_name, tab_data in expected_data.items():
            print(f"Verifying tab: {tab_name}")

            # Navigate to tab
            await self.navigate_to_tab(tab_name)

            # Verify each field in the tab
            for field_name, expected_value in tab_data.items():
                # Build selector for field
                selector = f'[data-field="{field_name}"], .{field_name}-value, #{field_name}'

                # Verify field
                result = await self.verify_field_value(selector, expected_value, field_name)
                results.append(result)

                print(f"  {field_name}: {result.verification_status} (confidence: {result.match_confidence:.2%})")

        return results

    def generate_verification_report(self, results: List[VerificationResult]) -> str:
        """Generate detailed verification report"""
        report = []
        report.append("# Visual Data Verification Report")
        report.append(f"Generated: {datetime.now().isoformat()}\n")

        # Summary statistics
        total = len(results)
        passed = sum(1 for r in results if r.verification_status == "passed")
        failed = sum(1 for r in results if r.verification_status == "failed")
        partial = sum(1 for r in results if r.verification_status == "partial")

        report.append("## Summary")
        report.append(f"- Total fields verified: {total}")
        report.append(f"- Passed: {passed} ({(passed/total)*100:.1f}%)")
        report.append(f"- Failed: {failed} ({(failed/total)*100:.1f}%)")
        report.append(f"- Partial match: {partial} ({(partial/total)*100:.1f}%)\n")

        # Detailed results
        report.append("## Detailed Results\n")

        # Group by status
        for status in ["failed", "partial", "passed"]:
            status_results = [r for r in results if r.verification_status == status]
            if status_results:
                report.append(f"### {status.capitalize()} Verifications\n")
                report.append("| Field | Expected | Displayed | Confidence | Screenshot |")
                report.append("|-------|----------|-----------|------------|------------|")

                for result in status_results:
                    report.append(
                        f"| {result.field_name} | {result.expected_value} | "
                        f"{result.displayed_value} | {result.match_confidence:.2%} | "
                        f"[View]({result.screenshot_path}) |"
                    )
                report.append("")

        return "\n".join(report)

    def create_visual_diff_report(self, results: List[VerificationResult]):
        """Create visual diff report with annotated screenshots"""
        for result in results:
            if result.screenshot_path and os.path.exists(result.screenshot_path):
                # Load screenshot
                img = cv2.imread(result.screenshot_path)

                # Add annotation based on status
                color = (0, 255, 0) if result.verification_status == "passed" else (0, 0, 255)
                label = f"{result.field_name}: {result.verification_status}"

                # Add text overlay
                cv2.putText(img, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

                # Save annotated image
                annotated_path = result.screenshot_path.replace(".png", "_annotated.png")
                cv2.imwrite(annotated_path, img)


async def run_comprehensive_verification():
    """Run comprehensive verification test"""
    verifier = VisualDataVerifier()

    try:
        await verifier.initialize()

        # Example test data
        test_property = "064210010010"  # Example parcel ID
        expected_data = {
            "overview": {
                "property_address": "123 Main St",
                "owner_name": "John Doe",
                "just_value": "$250,000",
                "year_built": "1995"
            },
            "core-property": {
                "parcel_id": "064210010010",
                "property_use_desc": "Single Family",
                "land_sqft": "7,500",
                "zoning": "RS-1"
            },
            "valuation": {
                "just_value": "$250,000",
                "assessed_value": "$225,000",
                "taxable_value": "$200,000",
                "land_value": "$50,000",
                "building_value": "$200,000"
            }
        }

        # Run verification
        results = await verifier.verify_property_data(test_property, expected_data)

        # Generate report
        report = verifier.generate_verification_report(results)
        print("\n" + report)

        # Save report
        with open("visual_verification_report.md", "w") as f:
            f.write(report)

        # Create visual diff report
        verifier.create_visual_diff_report(results)

        print("\n✓ Visual verification complete!")
        print("✓ Report saved to: visual_verification_report.md")

    finally:
        await verifier.close()


if __name__ == "__main__":
    asyncio.run(run_comprehensive_verification())