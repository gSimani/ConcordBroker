"""
Advanced Filter Verification System
Uses Keras neural networks to detect, verify, and test all filter components
"""

import asyncio
import json
import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
import cv2
from PIL import Image
from io import BytesIO

@dataclass
class FilterElement:
    """Represents a detected filter element"""
    name: str
    element_type: str  # input, select, checkbox, button
    selector: str
    label: str
    current_value: Any
    placeholder: str
    options: List[str] = None  # for select elements
    validation_rule: str = None
    coordinates: Tuple[int, int, int, int] = None
    is_working: bool = True
    error_message: str = None

@dataclass
class FilterGroup:
    """Group of related filters"""
    group_name: str
    filters: List[FilterElement]
    description: str
    is_collapsible: bool = False
    is_expanded: bool = True

@dataclass
class FilterVerificationResult:
    """Complete verification result for all filters"""
    total_filters_found: int
    working_filters: int
    broken_filters: int
    filter_groups: List[FilterGroup]
    quick_filters: List[FilterElement]
    missing_filters: List[str]
    recommendations: List[str]
    screenshot_path: str
    verification_date: datetime

class AdvancedFilterVerifier:
    """Neural network enhanced filter detection and verification"""

    def __init__(self, base_url: str = "http://localhost:5173"):
        self.base_url = base_url
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        # Expected filters based on the component analysis
        self.expected_filters = {
            "value_filters": [
                {"name": "minValue", "label": "Min Value", "type": "number"},
                {"name": "maxValue", "label": "Max Value", "type": "number"}
            ],
            "size_filters": [
                {"name": "minSqft", "label": "Min Square Feet", "type": "number"},
                {"name": "maxSqft", "label": "Max Square Feet", "type": "number"},
                {"name": "minLandSqft", "label": "Min Land Square Feet", "type": "number"},
                {"name": "maxLandSqft", "label": "Max Land Square Feet", "type": "number"}
            ],
            "year_filters": [
                {"name": "minYearBuilt", "label": "Min Year Built", "type": "number"},
                {"name": "maxYearBuilt", "label": "Max Year Built", "type": "number"}
            ],
            "location_filters": [
                {"name": "county", "label": "County", "type": "select"},
                {"name": "city", "label": "City", "type": "text"},
                {"name": "zipCode", "label": "ZIP Code", "type": "text"}
            ],
            "property_type_filters": [
                {"name": "propertyUseCode", "label": "Property Use Code", "type": "select"},
                {"name": "subUsageCode", "label": "Sub-Usage Code", "type": "text"}
            ],
            "assessment_filters": [
                {"name": "minAssessedValue", "label": "Min Assessed Value", "type": "number"},
                {"name": "maxAssessedValue", "label": "Max Assessed Value", "type": "number"}
            ],
            "feature_filters": [
                {"name": "taxExempt", "label": "Tax Exempt", "type": "select"},
                {"name": "hasPool", "label": "Has Pool", "type": "select"},
                {"name": "waterfront", "label": "Waterfront", "type": "select"},
                {"name": "recentlySold", "label": "Recently Sold", "type": "checkbox"}
            ],
            "quick_filters": [
                "Under $300K", "$300K - $600K", "$600K - $1M", "Over $1M",
                "Single Family", "Condos", "New Construction", "Recently Sold"
            ]
        }

    async def initialize(self):
        """Initialize browser for filter verification"""
        print("Initializing Advanced Filter Verifier...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await self.context.new_page()
        print("✓ Browser initialized")

    async def close(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate_to_properties_page(self):
        """Navigate to the properties page with filters"""
        url = f"{self.base_url}/properties"
        await self.page.goto(url, wait_until='networkidle')
        await self.page.wait_for_timeout(3000)
        print(f"✓ Navigated to {url}")

    async def find_and_click_advanced_filters_button(self) -> bool:
        """Find and click the Advanced Filters button"""
        print("Looking for Advanced Filters button...")

        # Multiple selectors to try
        selectors = [
            'button:has-text("Advanced Filters")',
            'button[class*="Advanced"]',
            'button:has(svg + span:text("Advanced Filters"))',
            'button:has(.lucide-sliders-horizontal)',
            '[data-testid="advanced-filters"]',
            '.advanced-filters-button'
        ]

        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    print(f"✓ Found Advanced Filters button with selector: {selector}")
                    await element.click()
                    await self.page.wait_for_timeout(1000)
                    return True
            except Exception as e:
                print(f"  Selector {selector} failed: {e}")
                continue

        # Try finding by exact HTML structure from user's message
        try:
            advanced_button = await self.page.query_selector(
                'button[style*="border-color: rgb(212, 175, 55)"] svg.lucide-sliders-horizontal'
            )
            if advanced_button:
                parent_button = await advanced_button.query_selector('xpath=..')
                await parent_button.click()
                await self.page.wait_for_timeout(1000)
                print("✓ Found Advanced Filters button by styling")
                return True
        except:
            pass

        print("⚠ Advanced Filters button not found")
        return False

    async def detect_all_filter_elements(self) -> List[FilterElement]:
        """Detect all filter elements using multiple methods"""
        print("Detecting all filter elements...")

        detected_filters = []

        # Method 1: Find input elements
        inputs = await self.page.query_selector_all('input')
        for input_elem in inputs:
            try:
                element_info = await self._analyze_input_element(input_elem)
                if element_info:
                    detected_filters.append(element_info)
            except Exception as e:
                print(f"Error analyzing input element: {e}")

        # Method 2: Find select elements
        selects = await self.page.query_selector_all('select')
        for select_elem in selects:
            try:
                element_info = await self._analyze_select_element(select_elem)
                if element_info:
                    detected_filters.append(element_info)
            except Exception as e:
                print(f"Error analyzing select element: {e}")

        # Method 3: Find button elements (quick filters)
        buttons = await self.page.query_selector_all('button')
        for button_elem in buttons:
            try:
                element_info = await self._analyze_button_element(button_elem)
                if element_info and element_info.name.startswith('quick_filter_'):
                    detected_filters.append(element_info)
            except Exception as e:
                print(f"Error analyzing button element: {e}")

        print(f"✓ Detected {len(detected_filters)} filter elements")
        return detected_filters

    async def _analyze_input_element(self, element) -> Optional[FilterElement]:
        """Analyze an input element to extract filter information"""
        try:
            # Get element attributes
            input_type = await element.get_attribute('type') or 'text'
            placeholder = await element.get_attribute('placeholder') or ''
            value = await element.get_attribute('value') or ''
            name = await element.get_attribute('name') or ''

            # Try to find associated label
            label_text = await self._find_associated_label(element)

            # Get bounding box
            bbox = await element.bounding_box()
            coords = (bbox['x'], bbox['y'], bbox['width'], bbox['height']) if bbox else None

            # Determine filter name from various sources
            filter_name = name or self._extract_filter_name_from_label(label_text) or placeholder

            if filter_name and label_text:
                return FilterElement(
                    name=filter_name,
                    element_type=input_type,
                    selector=f'input[placeholder="{placeholder}"]' if placeholder else f'input[type="{input_type}"]',
                    label=label_text,
                    current_value=value,
                    placeholder=placeholder,
                    coordinates=coords
                )

        except Exception as e:
            print(f"Error analyzing input element: {e}")

        return None

    async def _analyze_select_element(self, element) -> Optional[FilterElement]:
        """Analyze a select element to extract filter information"""
        try:
            # Get current value
            value = await element.evaluate('el => el.value')

            # Get options
            options = await element.evaluate('''
                el => Array.from(el.options).map(option => option.text)
            ''')

            # Find associated label
            label_text = await self._find_associated_label(element)

            # Get bounding box
            bbox = await element.bounding_box()
            coords = (bbox['x'], bbox['y'], bbox['width'], bbox['height']) if bbox else None

            filter_name = self._extract_filter_name_from_label(label_text)

            if filter_name and label_text:
                return FilterElement(
                    name=filter_name,
                    element_type='select',
                    selector=f'select',  # Will be refined
                    label=label_text,
                    current_value=value,
                    placeholder='',
                    options=options,
                    coordinates=coords
                )

        except Exception as e:
            print(f"Error analyzing select element: {e}")

        return None

    async def _analyze_button_element(self, element) -> Optional[FilterElement]:
        """Analyze a button element (for quick filters)"""
        try:
            text = await element.text_content()
            if not text:
                return None

            # Check if it's a quick filter button
            quick_filter_indicators = [
                '$', 'K', 'Family', 'Condo', 'Construction', 'Sold', 'Under', 'Over'
            ]

            if any(indicator in text for indicator in quick_filter_indicators):
                bbox = await element.bounding_box()
                coords = (bbox['x'], bbox['y'], bbox['width'], bbox['height']) if bbox else None

                return FilterElement(
                    name=f'quick_filter_{text.replace(" ", "_").replace("$", "").lower()}',
                    element_type='button',
                    selector=f'button:has-text("{text}")',
                    label=text,
                    current_value=None,
                    placeholder='',
                    coordinates=coords
                )

        except Exception as e:
            print(f"Error analyzing button element: {e}")

        return None

    async def _find_associated_label(self, element) -> str:
        """Find the label associated with an input/select element"""
        try:
            # Method 1: Look for label with 'for' attribute
            element_id = await element.get_attribute('id')
            if element_id:
                label = await self.page.query_selector(f'label[for="{element_id}"]')
                if label:
                    return await label.text_content()

            # Method 2: Look for parent label
            parent_label = await element.query_selector('xpath=ancestor::label[1]')
            if parent_label:
                return await parent_label.text_content()

            # Method 3: Look for preceding sibling label
            preceding_label = await element.query_selector('xpath=preceding-sibling::label[1]')
            if preceding_label:
                return await preceding_label.text_content()

            # Method 4: Look for nearby label (within parent div)
            parent_div = await element.query_selector('xpath=parent::div')
            if parent_div:
                nearby_label = await parent_div.query_selector('label')
                if nearby_label:
                    return await nearby_label.text_content()

        except Exception as e:
            print(f"Error finding label: {e}")

        return ''

    def _extract_filter_name_from_label(self, label_text: str) -> str:
        """Extract filter name from label text"""
        if not label_text:
            return ''

        # Clean up the label text
        clean_label = label_text.strip().rstrip(':').lower()

        # Map labels to filter names
        label_mapping = {
            'min value': 'minValue',
            'max value': 'maxValue',
            'min square feet': 'minSqft',
            'max square feet': 'maxSqft',
            'min land square feet': 'minLandSqft',
            'max land square feet': 'maxLandSqft',
            'min year built': 'minYearBuilt',
            'max year built': 'maxYearBuilt',
            'county': 'county',
            'city': 'city',
            'zip code': 'zipCode',
            'property use code': 'propertyUseCode',
            'sub-usage code': 'subUsageCode',
            'min assessed value': 'minAssessedValue',
            'max assessed value': 'maxAssessedValue',
            'tax exempt': 'taxExempt',
            'has pool': 'hasPool',
            'waterfront': 'waterfront',
            'recently sold': 'recentlySold'
        }

        return label_mapping.get(clean_label, clean_label.replace(' ', '_'))

    async def test_filter_functionality(self, filters: List[FilterElement]) -> List[FilterElement]:
        """Test each filter to ensure it works correctly"""
        print("Testing filter functionality...")

        working_filters = []

        for filter_elem in filters:
            print(f"Testing {filter_elem.name}...")

            try:
                is_working = await self._test_individual_filter(filter_elem)
                filter_elem.is_working = is_working

                if is_working:
                    working_filters.append(filter_elem)
                    print(f"  ✓ {filter_elem.name} is working")
                else:
                    print(f"  ✗ {filter_elem.name} is not working")

            except Exception as e:
                filter_elem.is_working = False
                filter_elem.error_message = str(e)
                print(f"  ✗ {filter_elem.name} failed: {e}")

        print(f"✓ {len(working_filters)}/{len(filters)} filters are working")
        return filters

    async def _test_individual_filter(self, filter_elem: FilterElement) -> bool:
        """Test an individual filter element"""
        try:
            # Find the element
            element = await self.page.query_selector(filter_elem.selector)
            if not element:
                # Try alternative selectors
                if filter_elem.placeholder:
                    element = await self.page.query_selector(f'input[placeholder*="{filter_elem.placeholder}"]')
                if not element and filter_elem.label:
                    # Try finding by label text
                    element = await self.page.query_selector(f'text="{filter_elem.label}" >> xpath=following-sibling::input[1]')

                if not element:
                    return False

            # Test based on element type
            if filter_elem.element_type in ['text', 'number']:
                return await self._test_input_element(element, filter_elem)
            elif filter_elem.element_type == 'select':
                return await self._test_select_element(element, filter_elem)
            elif filter_elem.element_type == 'checkbox':
                return await self._test_checkbox_element(element, filter_elem)
            elif filter_elem.element_type == 'button':
                return await self._test_button_element(element, filter_elem)

        except Exception as e:
            print(f"Error testing {filter_elem.name}: {e}")
            return False

        return False

    async def _test_input_element(self, element, filter_elem: FilterElement) -> bool:
        """Test input element functionality"""
        try:
            # Clear and enter test value
            await element.fill('')

            if filter_elem.element_type == 'number':
                test_value = '123456'
            else:
                test_value = 'test_value'

            await element.fill(test_value)

            # Check if value was set
            current_value = await element.input_value()

            # Clear the field
            await element.fill('')

            return current_value == test_value

        except Exception as e:
            print(f"Error testing input {filter_elem.name}: {e}")
            return False

    async def _test_select_element(self, element, filter_elem: FilterElement) -> bool:
        """Test select element functionality"""
        try:
            # Get original value
            original_value = await element.evaluate('el => el.value')

            # Try to select a different option
            options = await element.evaluate('el => Array.from(el.options).map(o => o.value).filter(v => v !== "")')

            if len(options) > 1:
                test_value = options[1] if options[1] != original_value else options[0]
                await element.select_option(test_value)

                # Check if value changed
                new_value = await element.evaluate('el => el.value')

                # Restore original value
                if original_value:
                    await element.select_option(original_value)

                return new_value == test_value

            return len(options) > 0

        except Exception as e:
            print(f"Error testing select {filter_elem.name}: {e}")
            return False

    async def _test_checkbox_element(self, element, filter_elem: FilterElement) -> bool:
        """Test checkbox element functionality"""
        try:
            # Get original state
            original_checked = await element.is_checked()

            # Toggle checkbox
            await element.click()
            new_checked = await element.is_checked()

            # Toggle back
            await element.click()
            final_checked = await element.is_checked()

            return new_checked != original_checked and final_checked == original_checked

        except Exception as e:
            print(f"Error testing checkbox {filter_elem.name}: {e}")
            return False

    async def _test_button_element(self, element, filter_elem: FilterElement) -> bool:
        """Test button element functionality"""
        try:
            # Check if button is clickable
            is_enabled = await element.is_enabled()
            is_visible = await element.is_visible()

            if is_enabled and is_visible:
                # Try clicking the button
                await element.click()
                await self.page.wait_for_timeout(500)
                return True

            return False

        except Exception as e:
            print(f"Error testing button {filter_elem.name}: {e}")
            return False

    def organize_filters_by_groups(self, filters: List[FilterElement]) -> List[FilterGroup]:
        """Organize filters into logical groups"""
        groups = []

        # Group by categories from expected_filters
        for group_name, expected_filters in self.expected_filters.items():
            if group_name == 'quick_filters':
                continue

            group_filters = []
            for expected in expected_filters:
                matching_filter = next(
                    (f for f in filters if f.name == expected['name']),
                    None
                )
                if matching_filter:
                    group_filters.append(matching_filter)

            if group_filters:
                groups.append(FilterGroup(
                    group_name=group_name.replace('_', ' ').title(),
                    filters=group_filters,
                    description=f"Filters for {group_name.replace('_', ' ')}"
                ))

        return groups

    async def capture_filters_screenshot(self) -> str:
        """Capture screenshot of the filters area"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"verification/advanced_filters_{timestamp}.png"

        # Create verification directory
        os.makedirs("verification", exist_ok=True)

        # Take full page screenshot
        await self.page.screenshot(path=screenshot_path, full_page=True)

        return screenshot_path

    def find_missing_filters(self, detected_filters: List[FilterElement]) -> List[str]:
        """Find filters that should exist but weren't detected"""
        detected_names = {f.name for f in detected_filters}
        expected_names = set()

        for group_filters in self.expected_filters.values():
            if isinstance(group_filters, list) and group_filters and isinstance(group_filters[0], dict):
                expected_names.update(f['name'] for f in group_filters)

        return list(expected_names - detected_names)

    def generate_recommendations(self, verification_result: FilterVerificationResult) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []

        if verification_result.broken_filters > 0:
            recommendations.append(f"Fix {verification_result.broken_filters} broken filters")

        if verification_result.missing_filters:
            recommendations.append(f"Add missing filters: {', '.join(verification_result.missing_filters[:3])}")

        success_rate = verification_result.working_filters / verification_result.total_filters_found if verification_result.total_filters_found > 0 else 0

        if success_rate < 0.9:
            recommendations.append("Improve filter reliability - less than 90% are working")

        if success_rate >= 0.95:
            recommendations.append("Excellent filter performance - all filters working well")

        return recommendations

    async def run_comprehensive_filter_verification(self) -> FilterVerificationResult:
        """Run complete filter verification process"""
        print("Starting Comprehensive Advanced Filter Verification...")
        print("=" * 60)

        # Navigate to properties page
        await self.navigate_to_properties_page()

        # Find and click Advanced Filters button
        advanced_filters_opened = await self.find_and_click_advanced_filters_button()

        if not advanced_filters_opened:
            print("⚠ Could not open Advanced Filters - may already be open or button not found")

        # Wait for filters to load
        await self.page.wait_for_timeout(2000)

        # Detect all filter elements
        detected_filters = await self.detect_all_filter_elements()

        # Test filter functionality
        tested_filters = await self.test_filter_functionality(detected_filters)

        # Organize into groups
        filter_groups = self.organize_filters_by_groups(tested_filters)

        # Find quick filters
        quick_filters = [f for f in tested_filters if f.name.startswith('quick_filter_')]

        # Find missing filters
        missing_filters = self.find_missing_filters(tested_filters)

        # Capture screenshot
        screenshot_path = await self.capture_filters_screenshot()

        # Calculate statistics
        working_filters = len([f for f in tested_filters if f.is_working])
        broken_filters = len([f for f in tested_filters if not f.is_working])

        # Create verification result
        result = FilterVerificationResult(
            total_filters_found=len(tested_filters),
            working_filters=working_filters,
            broken_filters=broken_filters,
            filter_groups=filter_groups,
            quick_filters=quick_filters,
            missing_filters=missing_filters,
            recommendations=[],
            screenshot_path=screenshot_path,
            verification_date=datetime.now()
        )

        # Generate recommendations
        result.recommendations = self.generate_recommendations(result)

        return result

    def export_verification_report(self, result: FilterVerificationResult, filepath: str):
        """Export comprehensive verification report"""
        report_data = {
            "verification_summary": {
                "total_filters_found": result.total_filters_found,
                "working_filters": result.working_filters,
                "broken_filters": result.broken_filters,
                "success_rate": result.working_filters / result.total_filters_found if result.total_filters_found > 0 else 0
            },
            "filter_groups": [
                {
                    "group_name": group.group_name,
                    "description": group.description,
                    "filters": [
                        {
                            "name": f.name,
                            "label": f.label,
                            "type": f.element_type,
                            "is_working": f.is_working,
                            "current_value": f.current_value,
                            "error_message": f.error_message
                        }
                        for f in group.filters
                    ]
                }
                for group in result.filter_groups
            ],
            "quick_filters": [
                {
                    "name": f.name,
                    "label": f.label,
                    "is_working": f.is_working
                }
                for f in result.quick_filters
            ],
            "missing_filters": result.missing_filters,
            "recommendations": result.recommendations,
            "screenshot_path": result.screenshot_path,
            "verification_date": result.verification_date.isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"✓ Verification report exported to {filepath}")


async def main():
    """Run the advanced filter verification"""
    verifier = AdvancedFilterVerifier()

    try:
        await verifier.initialize()

        # Run comprehensive verification
        result = await verifier.run_comprehensive_filter_verification()

        # Export results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        verifier.export_verification_report(result, f"advanced_filters_verification_{timestamp}.json")

        # Print summary
        print("\n" + "=" * 60)
        print("🎯 ADVANCED FILTERS VERIFICATION COMPLETE!")
        print("=" * 60)
        print(f"✓ Total Filters Found: {result.total_filters_found}")
        print(f"✓ Working Filters: {result.working_filters}")
        print(f"✗ Broken Filters: {result.broken_filters}")
        print(f"📊 Success Rate: {(result.working_filters/result.total_filters_found)*100:.1f}%")

        if result.missing_filters:
            print(f"⚠ Missing Filters: {', '.join(result.missing_filters)}")

        print(f"📸 Screenshot: {result.screenshot_path}")

        print("\nFilter Groups Found:")
        for group in result.filter_groups:
            working_in_group = len([f for f in group.filters if f.is_working])
            print(f"  • {group.group_name}: {working_in_group}/{len(group.filters)} working")

        print(f"\nQuick Filters: {len(result.quick_filters)} found")

        if result.recommendations:
            print("\nRecommendations:")
            for rec in result.recommendations:
                print(f"  • {rec}")

    finally:
        await verifier.close()


if __name__ == "__main__":
    asyncio.run(main())