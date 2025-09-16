"""
Comprehensive Data Field Mapper and Verifier
Uses NumPy for numerical validation, Playwright MCP for UI testing,
and OpenCV for visual verification of data placement
"""

import numpy as np
import pandas as pd
from playwright.async_api import async_playwright
import cv2
import asyncio
import json
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import hashlib
import logging
from dataclasses import dataclass
from enum import Enum
import re
import pytesseract
from PIL import Image
import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TabType(Enum):
    """Define all tabs and subtabs in the UI"""
    OVERVIEW = "overview"
    CORE_PROPERTY = "core-property"
    VALUATION = "valuation"
    PERMIT = "permit"
    SUNBIZ = "sunbiz"
    TAXES = "taxes"
    SALES_TAX_DEED = "sales-tax-deed"
    TAX_DEED_SALES = "tax-deed-sales"
    OWNER = "owner"
    SALES_HISTORY = "sales"
    BUILDING = "building"
    LAND_LEGAL = "land"
    EXEMPTIONS = "exemptions"
    NOTES = "notes"


@dataclass
class FieldMapping:
    """Represents a mapping between database field and UI location"""
    db_table: str
    db_field: str
    ui_tab: TabType
    ui_section: str
    ui_field_id: str
    ui_field_label: str
    data_type: str
    validation_rules: Dict[str, Any]
    transformation: Optional[str] = None


class DataFieldMapperVerifier:
    """Main class for mapping and verifying data field placement"""

    def __init__(self):
        self.field_mappings = self._initialize_field_mappings()
        self.browser = None
        self.page = None
        self.db_conn = None
        self.verification_results = []
        self.numpy_validator = NumPyDataValidator()
        self.visual_verifier = OpenCVVisualVerifier()

    def _initialize_field_mappings(self) -> List[FieldMapping]:
        """Initialize comprehensive field mappings for Property Appraiser and Sunbiz data"""

        mappings = [
            # ==================== OVERVIEW TAB ====================
            FieldMapping(
                db_table="florida_parcels",
                db_field="phy_addr1",
                ui_tab=TabType.OVERVIEW,
                ui_section="Property Location",
                ui_field_id="property-address",
                ui_field_label="Address",
                data_type="string",
                validation_rules={"required": True, "max_length": 255}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="phy_city",
                ui_tab=TabType.OVERVIEW,
                ui_section="Property Location",
                ui_field_id="property-city",
                ui_field_label="City",
                data_type="string",
                validation_rules={"required": True, "max_length": 100}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="phy_zipcd",
                ui_tab=TabType.OVERVIEW,
                ui_section="Property Location",
                ui_field_id="property-zip",
                ui_field_label="ZIP Code",
                data_type="string",
                validation_rules={"pattern": r"^\d{5}(-\d{4})?$"}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="parcel_id",
                ui_tab=TabType.OVERVIEW,
                ui_section="Property Location",
                ui_field_id="parcel-number",
                ui_field_label="Parcel ID",
                data_type="string",
                validation_rules={"required": True, "unique": True}
            ),

            # ==================== CORE PROPERTY TAB ====================
            FieldMapping(
                db_table="florida_parcels",
                db_field="dor_uc",
                ui_tab=TabType.CORE_PROPERTY,
                ui_section="Property Details",
                ui_field_id="use-code",
                ui_field_label="Use Code",
                data_type="string",
                validation_rules={"pattern": r"^\d{4}$"},
                transformation="map_use_code_to_description"
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="yr_blt",
                ui_tab=TabType.CORE_PROPERTY,
                ui_section="Property Details",
                ui_field_id="year-built",
                ui_field_label="Year Built",
                data_type="integer",
                validation_rules={"min": 1800, "max": datetime.now().year}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="act_yr_blt",
                ui_tab=TabType.CORE_PROPERTY,
                ui_section="Property Details",
                ui_field_id="actual-year-built",
                ui_field_label="Actual Year Built",
                data_type="integer",
                validation_rules={"min": 1800, "max": datetime.now().year}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="eff_yr_blt",
                ui_tab=TabType.CORE_PROPERTY,
                ui_section="Property Details",
                ui_field_id="effective-year-built",
                ui_field_label="Effective Year Built",
                data_type="integer",
                validation_rules={"min": 1800, "max": datetime.now().year}
            ),

            # ==================== VALUATION TAB ====================
            FieldMapping(
                db_table="florida_parcels",
                db_field="jv",
                ui_tab=TabType.VALUATION,
                ui_section="Current Values",
                ui_field_id="just-value",
                ui_field_label="Just Value",
                data_type="float",
                validation_rules={"min": 0, "format": "currency"}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="av_sd",
                ui_tab=TabType.VALUATION,
                ui_section="Current Values",
                ui_field_id="assessed-value",
                ui_field_label="Assessed Value",
                data_type="float",
                validation_rules={"min": 0, "format": "currency"}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="tv_sd",
                ui_tab=TabType.VALUATION,
                ui_section="Current Values",
                ui_field_id="taxable-value",
                ui_field_label="Taxable Value",
                data_type="float",
                validation_rules={"min": 0, "format": "currency"}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="lnd_val",
                ui_tab=TabType.VALUATION,
                ui_section="Value Breakdown",
                ui_field_id="land-value",
                ui_field_label="Land Value",
                data_type="float",
                validation_rules={"min": 0, "format": "currency"}
            ),

            # ==================== OWNER TAB ====================
            FieldMapping(
                db_table="florida_parcels",
                db_field="owner_name",
                ui_tab=TabType.OWNER,
                ui_section="Owner Information",
                ui_field_id="owner-name",
                ui_field_label="Owner Name",
                data_type="string",
                validation_rules={"required": True, "max_length": 255}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="owner_addr1",
                ui_tab=TabType.OWNER,
                ui_section="Owner Information",
                ui_field_id="owner-address1",
                ui_field_label="Owner Address",
                data_type="string",
                validation_rules={"max_length": 255}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="owner_city",
                ui_tab=TabType.OWNER,
                ui_section="Owner Information",
                ui_field_id="owner-city",
                ui_field_label="Owner City",
                data_type="string",
                validation_rules={"max_length": 100}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="owner_state",
                ui_tab=TabType.OWNER,
                ui_section="Owner Information",
                ui_field_id="owner-state",
                ui_field_label="Owner State",
                data_type="string",
                validation_rules={"pattern": r"^[A-Z]{2}$"}
            ),

            # ==================== BUILDING TAB ====================
            FieldMapping(
                db_table="florida_parcels",
                db_field="tot_lvg_area",
                ui_tab=TabType.BUILDING,
                ui_section="Building Details",
                ui_field_id="living-area",
                ui_field_label="Total Living Area",
                data_type="float",
                validation_rules={"min": 0, "format": "sqft"}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="bedroom_cnt",
                ui_tab=TabType.BUILDING,
                ui_section="Building Details",
                ui_field_id="bedrooms",
                ui_field_label="Bedrooms",
                data_type="integer",
                validation_rules={"min": 0, "max": 20}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="bathroom_cnt",
                ui_tab=TabType.BUILDING,
                ui_section="Building Details",
                ui_field_id="bathrooms",
                ui_field_label="Bathrooms",
                data_type="float",
                validation_rules={"min": 0, "max": 20}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="no_buldng",
                ui_tab=TabType.BUILDING,
                ui_section="Building Details",
                ui_field_id="num-buildings",
                ui_field_label="Number of Buildings",
                data_type="integer",
                validation_rules={"min": 0}
            ),

            # ==================== LAND & LEGAL TAB ====================
            FieldMapping(
                db_table="florida_parcels",
                db_field="lnd_sqfoot",
                ui_tab=TabType.LAND_LEGAL,
                ui_section="Land Information",
                ui_field_id="land-sqft",
                ui_field_label="Land Square Feet",
                data_type="float",
                validation_rules={"min": 0, "format": "sqft"}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="lgl_1",
                ui_tab=TabType.LAND_LEGAL,
                ui_section="Legal Description",
                ui_field_id="legal-desc1",
                ui_field_label="Legal Description Line 1",
                data_type="string",
                validation_rules={"max_length": 255}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="subdivision",
                ui_tab=TabType.LAND_LEGAL,
                ui_section="Legal Description",
                ui_field_id="subdivision",
                ui_field_label="Subdivision",
                data_type="string",
                validation_rules={"max_length": 255}
            ),

            # ==================== SALES HISTORY TAB ====================
            FieldMapping(
                db_table="florida_parcels",
                db_field="sale_prc1",
                ui_tab=TabType.SALES_HISTORY,
                ui_section="Most Recent Sale",
                ui_field_id="last-sale-price",
                ui_field_label="Last Sale Price",
                data_type="float",
                validation_rules={"min": 0, "format": "currency"}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="sale_yr1",
                ui_tab=TabType.SALES_HISTORY,
                ui_section="Most Recent Sale",
                ui_field_id="last-sale-year",
                ui_field_label="Last Sale Year",
                data_type="integer",
                validation_rules={"min": 1900, "max": datetime.now().year}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="qual_cd1",
                ui_tab=TabType.SALES_HISTORY,
                ui_section="Most Recent Sale",
                ui_field_id="qualification-code",
                ui_field_label="Qualification Code",
                data_type="string",
                validation_rules={"pattern": r"^[A-Z]\d?$"}
            ),

            # ==================== SUNBIZ TAB ====================
            FieldMapping(
                db_table="sunbiz_corporations",
                db_field="corp_name",
                ui_tab=TabType.SUNBIZ,
                ui_section="Business Entity",
                ui_field_id="corp-name",
                ui_field_label="Corporation Name",
                data_type="string",
                validation_rules={"max_length": 500}
            ),
            FieldMapping(
                db_table="sunbiz_corporations",
                db_field="status",
                ui_tab=TabType.SUNBIZ,
                ui_section="Business Entity",
                ui_field_id="corp-status",
                ui_field_label="Status",
                data_type="string",
                validation_rules={"enum": ["ACTIVE", "INACTIVE", "DISSOLVED"]}
            ),
            FieldMapping(
                db_table="sunbiz_corporations",
                db_field="filing_date",
                ui_tab=TabType.SUNBIZ,
                ui_section="Business Entity",
                ui_field_id="filing-date",
                ui_field_label="Filing Date",
                data_type="date",
                validation_rules={"format": "YYYY-MM-DD"}
            ),

            # ==================== TAX CERTIFICATES TAB ====================
            FieldMapping(
                db_table="tax_certificates",
                db_field="certificate_number",
                ui_tab=TabType.TAXES,
                ui_section="Tax Certificates",
                ui_field_id="cert-number",
                ui_field_label="Certificate Number",
                data_type="string",
                validation_rules={"required": True, "unique": True}
            ),
            FieldMapping(
                db_table="tax_certificates",
                db_field="certificate_amount",
                ui_tab=TabType.TAXES,
                ui_section="Tax Certificates",
                ui_field_id="cert-amount",
                ui_field_label="Certificate Amount",
                data_type="float",
                validation_rules={"min": 0, "format": "currency"}
            ),

            # ==================== TAX DEED SALES TAB ====================
            FieldMapping(
                db_table="tax_deed_sales",
                db_field="auction_date",
                ui_tab=TabType.TAX_DEED_SALES,
                ui_section="Auction Information",
                ui_field_id="auction-date",
                ui_field_label="Auction Date",
                data_type="date",
                validation_rules={"format": "YYYY-MM-DD"}
            ),
            FieldMapping(
                db_table="tax_deed_sales",
                db_field="minimum_bid",
                ui_tab=TabType.TAX_DEED_SALES,
                ui_section="Auction Information",
                ui_field_id="minimum-bid",
                ui_field_label="Minimum Bid",
                data_type="float",
                validation_rules={"min": 0, "format": "currency"}
            ),
            FieldMapping(
                db_table="tax_deed_sales",
                db_field="winning_bid",
                ui_tab=TabType.TAX_DEED_SALES,
                ui_section="Auction Information",
                ui_field_id="winning-bid",
                ui_field_label="Winning Bid",
                data_type="float",
                validation_rules={"min": 0, "format": "currency"}
            ),

            # ==================== EXEMPTIONS TAB ====================
            FieldMapping(
                db_table="florida_parcels",
                db_field="exempt_val",
                ui_tab=TabType.EXEMPTIONS,
                ui_section="Exemptions",
                ui_field_id="exemption-value",
                ui_field_label="Total Exemption Value",
                data_type="float",
                validation_rules={"min": 0, "format": "currency"}
            ),
            FieldMapping(
                db_table="florida_parcels",
                db_field="homestead_exemption",
                ui_tab=TabType.EXEMPTIONS,
                ui_section="Exemptions",
                ui_field_id="homestead",
                ui_field_label="Homestead Exemption",
                data_type="boolean",
                validation_rules={}
            ),
        ]

        return mappings

    async def initialize_browser(self):
        """Initialize Playwright browser for testing"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Set to True for production
            args=['--start-maximized']
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await context.new_page()

    async def connect_database(self):
        """Connect to Supabase database"""
        self.db_conn = await asyncpg.connect(
            host="aws-0-us-east-1.pooler.supabase.com",
            port=6543,
            user="postgres.pmispwtdngkcmsrsjwbp",
            password="vM4g2024$$Florida1",
            database="postgres"
        )

    async def verify_field_mapping(self,
                                  parcel_id: str,
                                  mapping: FieldMapping) -> Dict[str, Any]:
        """Verify a single field mapping"""

        # Get data from database
        db_value = await self._get_database_value(parcel_id, mapping)

        # Navigate to the correct tab in UI
        await self._navigate_to_tab(parcel_id, mapping.ui_tab)

        # Get value from UI
        ui_value = await self._get_ui_value(mapping)

        # Apply transformation if needed
        if mapping.transformation:
            db_value = self._apply_transformation(db_value, mapping.transformation)

        # Validate using NumPy
        is_valid, validation_details = self.numpy_validator.validate_field(
            db_value, ui_value, mapping
        )

        # Visual verification using OpenCV
        screenshot_path = await self._take_field_screenshot(mapping)
        visual_match = await self.visual_verifier.verify_field_display(
            screenshot_path, db_value, mapping
        )

        return {
            'field': mapping.db_field,
            'tab': mapping.ui_tab.value,
            'db_value': db_value,
            'ui_value': ui_value,
            'is_valid': is_valid,
            'visual_match': visual_match,
            'validation_details': validation_details,
            'timestamp': datetime.now().isoformat()
        }

    async def _get_database_value(self, parcel_id: str, mapping: FieldMapping) -> Any:
        """Get value from database"""
        query = f"""
            SELECT {mapping.db_field}
            FROM {mapping.db_table}
            WHERE parcel_id = $1
            LIMIT 1
        """
        result = await self.db_conn.fetchrow(query, parcel_id)
        return result[mapping.db_field] if result else None

    async def _navigate_to_tab(self, parcel_id: str, tab: TabType):
        """Navigate to specific tab in UI"""
        # Navigate to property page
        url = f"http://localhost:5173/property/{parcel_id}"
        await self.page.goto(url, wait_until='networkidle')

        # Click on the tab
        tab_selector = f'[data-tab="{tab.value}"], button:has-text("{tab.value.replace("-", " ").title()}")'
        await self.page.click(tab_selector)
        await self.page.wait_for_timeout(500)  # Wait for content to load

    async def _get_ui_value(self, mapping: FieldMapping) -> Any:
        """Get value from UI"""
        # Try multiple selector strategies
        selectors = [
            f'#{mapping.ui_field_id}',
            f'[data-field="{mapping.ui_field_id}"]',
            f'[aria-label="{mapping.ui_field_label}"]',
            f'text={mapping.ui_field_label}'
        ]

        for selector in selectors:
            element = await self.page.query_selector(selector)
            if element:
                # Get the value based on element type
                tag_name = await element.evaluate('el => el.tagName')

                if tag_name in ['INPUT', 'TEXTAREA', 'SELECT']:
                    return await element.input_value()
                else:
                    return await element.text_content()

        return None

    async def _take_field_screenshot(self, mapping: FieldMapping) -> str:
        """Take screenshot of specific field"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"field_verification_{mapping.db_field}_{timestamp}.png"

        # Find the field element
        element = await self.page.query_selector(f'#{mapping.ui_field_id}')
        if element:
            await element.screenshot(path=filename)
        else:
            # Take full page screenshot if element not found
            await self.page.screenshot(path=filename, full_page=True)

        return filename

    def _apply_transformation(self, value: Any, transformation: str) -> Any:
        """Apply transformation to database value"""
        transformations = {
            'map_use_code_to_description': self._map_use_code,
            'format_currency': lambda v: f"${v:,.2f}" if v else "$0.00",
            'format_date': lambda v: v.strftime('%Y-%m-%d') if v else None,
        }

        if transformation in transformations:
            return transformations[transformation](value)
        return value

    def _map_use_code(self, code: str) -> str:
        """Map property use code to description"""
        use_codes = {
            '0100': 'Single Family',
            '0101': 'Single Family - Detached',
            '0200': 'Multi Family',
            '1000': 'Commercial',
            '4000': 'Industrial',
            '5000': 'Agricultural',
            '0000': 'Vacant Land'
        }
        return use_codes.get(code, code)

    async def run_comprehensive_verification(self,
                                           sample_parcels: List[str]) -> Dict[str, Any]:
        """Run comprehensive verification on sample properties"""

        await self.initialize_browser()
        await self.connect_database()

        all_results = []
        summary_stats = {
            'total_fields': len(self.field_mappings),
            'total_properties': len(sample_parcels),
            'fields_verified': 0,
            'fields_matched': 0,
            'fields_mismatched': 0,
            'visual_matches': 0,
            'errors': []
        }

        for parcel_id in sample_parcels:
            logger.info(f"Verifying property: {parcel_id}")
            property_results = []

            for mapping in self.field_mappings:
                try:
                    result = await self.verify_field_mapping(parcel_id, mapping)
                    property_results.append(result)

                    summary_stats['fields_verified'] += 1
                    if result['is_valid']:
                        summary_stats['fields_matched'] += 1
                    else:
                        summary_stats['fields_mismatched'] += 1

                    if result['visual_match']:
                        summary_stats['visual_matches'] += 1

                except Exception as e:
                    logger.error(f"Error verifying {mapping.db_field}: {e}")
                    summary_stats['errors'].append({
                        'field': mapping.db_field,
                        'error': str(e)
                    })

            all_results.append({
                'parcel_id': parcel_id,
                'results': property_results
            })

        # Calculate accuracy
        summary_stats['accuracy'] = (
            summary_stats['fields_matched'] / summary_stats['fields_verified'] * 100
            if summary_stats['fields_verified'] > 0 else 0
        )

        # Generate report
        report = {
            'verification_date': datetime.now().isoformat(),
            'summary': summary_stats,
            'detailed_results': all_results,
            'recommendations': self._generate_recommendations(all_results)
        }

        # Save report
        with open('field_verification_report.json', 'w') as f:
            json.dump(report, f, indent=2)

        # Cleanup
        await self.browser.close()
        await self.db_conn.close()

        return report

    def _generate_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []

        # Analyze common issues
        mismatched_fields = {}
        for property_result in results:
            for field_result in property_result['results']:
                if not field_result['is_valid']:
                    field = field_result['field']
                    mismatched_fields[field] = mismatched_fields.get(field, 0) + 1

        # Generate recommendations
        for field, count in mismatched_fields.items():
            if count > len(results) * 0.5:  # More than 50% mismatch
                recommendations.append(
                    f"Critical: Field '{field}' has {count} mismatches. "
                    f"Check database mapping or UI display logic."
                )

        return recommendations


class NumPyDataValidator:
    """Use NumPy for numerical validation and statistical analysis"""

    def validate_field(self,
                      db_value: Any,
                      ui_value: Any,
                      mapping: FieldMapping) -> Tuple[bool, Dict]:
        """Validate field value using NumPy operations"""

        validation_details = {
            'type_check': False,
            'value_match': False,
            'format_valid': False,
            'rules_passed': []
        }

        # Type validation
        if mapping.data_type == 'float':
            db_val, ui_val = self._to_float(db_value), self._to_float(ui_value)
            if db_val is not None and ui_val is not None:
                validation_details['type_check'] = True
                # Use NumPy for comparison with tolerance
                validation_details['value_match'] = np.allclose(
                    [db_val], [ui_val], rtol=1e-5, atol=1e-2
                )

        elif mapping.data_type == 'integer':
            db_val, ui_val = self._to_int(db_value), self._to_int(ui_value)
            if db_val is not None and ui_val is not None:
                validation_details['type_check'] = True
                validation_details['value_match'] = db_val == ui_val

        elif mapping.data_type == 'string':
            validation_details['type_check'] = True
            # Normalize strings for comparison
            db_str = str(db_value or '').strip().upper()
            ui_str = str(ui_value or '').strip().upper()
            validation_details['value_match'] = db_str == ui_str

        # Apply validation rules
        for rule, value in mapping.validation_rules.items():
            if rule == 'min' and db_value is not None:
                passed = float(db_value) >= value
                validation_details['rules_passed'].append({rule: passed})

            elif rule == 'max' and db_value is not None:
                passed = float(db_value) <= value
                validation_details['rules_passed'].append({rule: passed})

            elif rule == 'pattern' and db_value is not None:
                passed = bool(re.match(value, str(db_value)))
                validation_details['rules_passed'].append({rule: passed})

        # Overall validation
        is_valid = (
            validation_details['type_check'] and
            validation_details['value_match'] and
            all(list(r.values())[0] for r in validation_details['rules_passed'])
        )

        return is_valid, validation_details

    def _to_float(self, value: Any) -> Optional[float]:
        """Convert value to float"""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = re.sub(r'[$,]', '', value)
            try:
                return float(cleaned)
            except:
                return None
        return None

    def _to_int(self, value: Any) -> Optional[int]:
        """Convert value to integer"""
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except:
                return None
        return None

    def analyze_numerical_consistency(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze numerical data consistency using NumPy"""

        numerical_columns = data.select_dtypes(include=[np.number]).columns
        analysis = {}

        for col in numerical_columns:
            values = data[col].dropna().values
            if len(values) > 0:
                analysis[col] = {
                    'mean': np.mean(values),
                    'median': np.median(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'outliers': self._detect_outliers(values),
                    'missing_pct': (data[col].isna().sum() / len(data)) * 100
                }

        return analysis

    def _detect_outliers(self, values: np.ndarray) -> List[float]:
        """Detect outliers using IQR method"""
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = values[(values < lower_bound) | (values > upper_bound)]
        return outliers.tolist()


class OpenCVVisualVerifier:
    """Use OpenCV for visual verification of data display"""

    async def verify_field_display(self,
                                  screenshot_path: str,
                                  expected_value: Any,
                                  mapping: FieldMapping) -> bool:
        """Verify field display using computer vision"""

        # Read screenshot
        img = cv2.imread(screenshot_path)
        if img is None:
            return False

        # Convert to grayscale for OCR
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply preprocessing for better OCR
        processed = self._preprocess_for_ocr(gray)

        # Extract text using OCR
        extracted_text = pytesseract.image_to_string(processed)

        # Clean and normalize text
        extracted_text = extracted_text.strip().upper()
        expected_str = str(expected_value or '').strip().upper()

        # Check if expected value is in extracted text
        if mapping.data_type == 'float' and expected_value:
            # For numbers, check both raw and formatted versions
            formatted = f"${expected_value:,.2f}"
            return (
                expected_str in extracted_text or
                formatted.upper() in extracted_text or
                str(int(expected_value)) in extracted_text
            )
        else:
            return expected_str in extracted_text

    def _preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""

        # Apply thresholding
        _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Denoise
        denoised = cv2.medianBlur(thresh, 3)

        # Dilate to connect text
        kernel = np.ones((1, 1), np.uint8)
        dilated = cv2.dilate(denoised, kernel, iterations=1)

        return dilated

    def analyze_ui_layout(self, screenshot_path: str) -> Dict[str, Any]:
        """Analyze UI layout for consistency"""

        img = cv2.imread(screenshot_path)
        if img is None:
            return {}

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect edges for layout analysis
        edges = cv2.Canny(gray, 50, 150)

        # Find contours (UI elements)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Analyze layout
        ui_elements = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 50 and h > 20:  # Filter small elements
                ui_elements.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'area': int(w * h)
                })

        # Sort by position
        ui_elements.sort(key=lambda e: (e['y'], e['x']))

        return {
            'total_elements': len(ui_elements),
            'elements': ui_elements[:20],  # Top 20 elements
            'layout_score': self._calculate_layout_score(ui_elements)
        }

    def _calculate_layout_score(self, elements: List[Dict]) -> float:
        """Calculate layout consistency score"""
        if len(elements) < 2:
            return 0.0

        # Check alignment
        x_positions = [e['x'] for e in elements]
        y_positions = [e['y'] for e in elements]

        # Calculate standard deviation for alignment
        x_std = np.std(x_positions) if len(x_positions) > 1 else 0
        y_spacing = np.diff(sorted(y_positions))
        y_std = np.std(y_spacing) if len(y_spacing) > 0 else 0

        # Lower std means better alignment
        alignment_score = max(0, 100 - (x_std / 10))
        spacing_score = max(0, 100 - (y_std / 5))

        return (alignment_score + spacing_score) / 2


async def main():
    """Main execution function"""

    # Initialize verifier
    verifier = DataFieldMapperVerifier()

    # Sample properties to verify
    sample_parcels = [
        '064210010010',  # Example parcel ID
        '064210010020',
        '064210010030'
    ]

    # Run comprehensive verification
    logger.info("Starting comprehensive field verification...")
    report = await verifier.run_comprehensive_verification(sample_parcels)

    # Print summary
    print("\n" + "="*60)
    print("FIELD VERIFICATION REPORT")
    print("="*60)
    print(f"Total Fields Checked: {report['summary']['fields_verified']}")
    print(f"Fields Matched: {report['summary']['fields_matched']}")
    print(f"Fields Mismatched: {report['summary']['fields_mismatched']}")
    print(f"Accuracy: {report['summary']['accuracy']:.2f}%")
    print(f"Visual Matches: {report['summary']['visual_matches']}")

    if report['recommendations']:
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")

    print(f"\nDetailed report saved to: field_verification_report.json")


if __name__ == "__main__":
    asyncio.run(main())