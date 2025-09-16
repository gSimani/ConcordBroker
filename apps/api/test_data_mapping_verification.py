"""
Test Script for Data Mapping Verification
Validates that all data flows correctly from Supabase to UI
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import logging
from playwright.async_api import async_playwright
import cv2
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql://postgres.pmispwtdngkcmsrsjwbp:vM4g2024$$Florida1@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

class ComprehensiveDataVerifier:
    """Complete data verification system"""

    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.test_results = []
        self.field_mappings = self._load_field_mappings()

    def _load_field_mappings(self) -> Dict[str, Dict]:
        """Load comprehensive field mappings"""
        return {
            # Overview Tab Mappings
            "overview": {
                "database_to_ui": {
                    # Property Location Card
                    "florida_parcels.phy_addr1": "property-address-line1",
                    "florida_parcels.phy_addr2": "property-address-line2",
                    "florida_parcels.phy_city": "property-city",
                    "florida_parcels.phy_zipcode": "property-zip",
                    "florida_parcels.use_code": "property-type",
                    "florida_parcels.year_built": "year-built",

                    # Property Values Card
                    "florida_parcels.just_value": "market-value",
                    "florida_parcels.assessed_value": "assessed-value",
                    "florida_parcels.taxable_value": "taxable-value",
                    "florida_parcels.land_value": "land-value",
                    "florida_parcels.building_value": "building-value",

                    # Property Details Card
                    "florida_parcels.total_living_area": "living-area",
                    "florida_parcels.bedrooms": "bedrooms",
                    "florida_parcels.bathrooms": "bathrooms",
                    "florida_parcels.land_sqft": "lot-size",

                    # Last Sale Card
                    "florida_parcels.sale_date": "last-sale-date",
                    "florida_parcels.sale_price": "last-sale-price",
                    "florida_parcels.or_book": "or-book",
                    "florida_parcels.or_page": "or-page",
                }
            },

            # Ownership Tab Mappings
            "ownership": {
                "database_to_ui": {
                    # Current Owner Section
                    "florida_parcels.owner_name": "owner-name",
                    "florida_parcels.owner_addr1": "owner-mailing-address1",
                    "florida_parcels.owner_addr2": "owner-mailing-address2",
                    "florida_parcels.owner_city": "owner-mailing-city",
                    "florida_parcels.owner_state": "owner-mailing-state",
                    "florida_parcels.owner_zipcode": "owner-mailing-zip",

                    # Business Entity Section (Sunbiz)
                    "sunbiz_entities.entity_name": "business-entity-name",
                    "sunbiz_entities.document_number": "document-number",
                    "sunbiz_entities.status": "entity-status",
                    "sunbiz_entities.entity_type": "entity-type",
                    "sunbiz_entities.filing_date": "filing-date",
                    "sunbiz_entities.principal_address": "principal-address",
                    "sunbiz_entities.registered_agent": "registered-agent",
                    "sunbiz_entities.agent_address": "agent-address",
                    "sunbiz_entities.officers": "officers-list",
                }
            },

            # Tax Deed Sales Tab Mappings
            "tax_deed_sales": {
                "database_to_ui": {
                    # Auction Information
                    "tax_deed_sales.td_number": "td-number",
                    "tax_deed_sales.certificate_number": "certificate-number",
                    "tax_deed_sales.auction_date": "auction-date",
                    "tax_deed_sales.auction_status": "auction-status",

                    # Bid Information
                    "tax_deed_sales.minimum_bid": "minimum-bid",
                    "tax_deed_sales.winning_bid": "winning-bid",
                    "tax_deed_sales.assessed_value": "td-assessed-value",

                    # Property Information
                    "tax_deed_sales.property_address": "td-property-address",
                    "tax_deed_sales.property_use": "td-property-use",
                }
            },

            # Sales History Tab Mappings
            "sales_history": {
                "database_to_ui": {
                    "sales_history.sale_date": "sale-date",
                    "sales_history.sale_price": "sale-price",
                    "sales_history.seller_name": "seller-name",
                    "sales_history.buyer_name": "buyer-name",
                    "sales_history.sale_type": "sale-type",
                    "sales_history.qualified": "qualified-sale",
                    "sales_history.or_book": "sale-or-book",
                    "sales_history.or_page": "sale-or-page",
                    "sales_history.instrument_number": "instrument-number",
                }
            },

            # Permits Tab Mappings
            "permits": {
                "database_to_ui": {
                    "building_permits.permit_number": "permit-number",
                    "building_permits.permit_type": "permit-type",
                    "building_permits.description": "permit-description",
                    "building_permits.issue_date": "issue-date",
                    "building_permits.finalize_date": "finalize-date",
                    "building_permits.status": "permit-status",
                    "building_permits.contractor": "contractor-name",
                    "building_permits.estimated_value": "estimated-value",
                    "building_permits.actual_value": "actual-value",
                }
            },

            # Taxes Tab Mappings
            "taxes": {
                "database_to_ui": {
                    "florida_parcels.taxable_value": "tax-taxable-value",
                    "florida_parcels.millage_rate": "millage-rate",
                    "florida_parcels.tax_amount": "tax-amount",
                    "florida_parcels.exemptions": "exemptions",
                }
            }
        }

    async def verify_data_flow(self, parcel_id: str) -> Dict[str, Any]:
        """Verify complete data flow for a property"""
        logger.info(f"Starting data flow verification for parcel: {parcel_id}")

        results = {
            "parcel_id": parcel_id,
            "timestamp": datetime.now().isoformat(),
            "database_check": {},
            "ui_check": {},
            "visual_check": {},
            "field_matches": {},
            "errors": [],
            "warnings": [],
            "success": True
        }

        # Step 1: Verify data in database
        logger.info("Step 1: Checking database data...")
        db_data = self._check_database_data(parcel_id)
        results["database_check"] = db_data

        if not db_data["found"]:
            results["success"] = False
            results["errors"].append(f"Property {parcel_id} not found in database")
            return results

        # Step 2: Verify UI rendering
        logger.info("Step 2: Checking UI rendering...")
        ui_results = await self._check_ui_rendering(parcel_id, db_data["data"])
        results["ui_check"] = ui_results

        # Step 3: Visual verification with OpenCV
        logger.info("Step 3: Performing visual verification...")
        visual_results = await self._check_visual_accuracy(parcel_id)
        results["visual_check"] = visual_results

        # Step 4: Field-by-field matching
        logger.info("Step 4: Verifying field mappings...")
        field_results = await self._verify_field_mappings(parcel_id, db_data["data"])
        results["field_matches"] = field_results

        # Calculate overall success
        total_fields = field_results.get("total_fields", 0)
        matched_fields = field_results.get("matched_fields", 0)
        match_rate = (matched_fields / total_fields * 100) if total_fields > 0 else 0

        results["summary"] = {
            "total_fields": total_fields,
            "matched_fields": matched_fields,
            "match_rate": f"{match_rate:.1f}%",
            "database_complete": db_data.get("completeness", 0) > 80,
            "ui_rendered": ui_results.get("rendered", False),
            "visual_verified": visual_results.get("verified", False)
        }

        if match_rate < 90:
            results["warnings"].append(f"Field match rate below 90%: {match_rate:.1f}%")

        logger.info(f"Verification complete. Match rate: {match_rate:.1f}%")
        return results

    def _check_database_data(self, parcel_id: str) -> Dict[str, Any]:
        """Check if data exists in database"""
        with self.engine.connect() as conn:
            # Check main property table
            result = conn.execute(text("""
                SELECT * FROM florida_parcels
                WHERE parcel_id = :parcel_id
            """), {"parcel_id": parcel_id})

            property_data = result.fetchone()

            if not property_data:
                return {"found": False}

            # Convert to dict
            property_dict = dict(property_data._mapping)

            # Check related tables
            tax_deed_result = conn.execute(text("""
                SELECT * FROM tax_deed_sales
                WHERE parcel_id = :parcel_id
            """), {"parcel_id": parcel_id})
            tax_deed_data = [dict(row._mapping) for row in tax_deed_result]

            sunbiz_result = conn.execute(text("""
                SELECT * FROM sunbiz_entities
                WHERE parcel_id = :parcel_id
                OR owner_name = :owner_name
            """), {"parcel_id": parcel_id, "owner_name": property_dict.get("owner_name", "")})
            sunbiz_data = [dict(row._mapping) for row in sunbiz_result]

            permits_result = conn.execute(text("""
                SELECT * FROM building_permits
                WHERE parcel_id = :parcel_id
            """), {"parcel_id": parcel_id})
            permits_data = [dict(row._mapping) for row in permits_result]

            sales_result = conn.execute(text("""
                SELECT * FROM sales_history
                WHERE parcel_id = :parcel_id
                ORDER BY sale_date DESC
            """), {"parcel_id": parcel_id})
            sales_data = [dict(row._mapping) for row in sales_result]

            # Calculate data completeness
            total_fields = len(property_dict.keys())
            filled_fields = sum(1 for v in property_dict.values() if v is not None and v != "")
            completeness = (filled_fields / total_fields * 100) if total_fields > 0 else 0

            return {
                "found": True,
                "data": {
                    "florida_parcels": property_dict,
                    "tax_deed_sales": tax_deed_data,
                    "sunbiz_entities": sunbiz_data,
                    "building_permits": permits_data,
                    "sales_history": sales_data
                },
                "completeness": completeness,
                "stats": {
                    "property_fields": filled_fields,
                    "tax_deeds": len(tax_deed_data),
                    "sunbiz_entities": len(sunbiz_data),
                    "permits": len(permits_data),
                    "sales": len(sales_data)
                }
            }

    async def _check_ui_rendering(self, parcel_id: str, db_data: Dict) -> Dict[str, Any]:
        """Check if UI renders the data correctly using Playwright"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Navigate to property page
                url = f"http://localhost:5173/property/{parcel_id}"
                await page.goto(url, wait_until="networkidle")

                # Check if page loaded
                title = await page.title()

                # Check for key elements
                elements_found = {}

                # Check Overview tab elements
                await page.click('[data-tab="overview"]')
                await page.wait_for_timeout(500)

                # Property address
                address_elem = await page.query_selector('[data-field="property-address"]')
                elements_found["property_address"] = address_elem is not None

                # Market value
                value_elem = await page.query_selector('[data-field="market-value"]')
                elements_found["market_value"] = value_elem is not None

                # Owner name
                await page.click('[data-tab="ownership"]')
                await page.wait_for_timeout(500)
                owner_elem = await page.query_selector('[data-field="owner-name"]')
                elements_found["owner_name"] = owner_elem is not None

                # Take screenshot for visual verification
                screenshot_path = f"verification_screenshots/{parcel_id}_ui_check.png"
                os.makedirs("verification_screenshots", exist_ok=True)
                await page.screenshot(path=screenshot_path, full_page=True)

                await browser.close()

                return {
                    "rendered": True,
                    "title": title,
                    "elements_found": elements_found,
                    "screenshot": screenshot_path,
                    "url": url
                }

            except Exception as e:
                await browser.close()
                return {
                    "rendered": False,
                    "error": str(e)
                }

    async def _check_visual_accuracy(self, parcel_id: str) -> Dict[str, Any]:
        """Use OpenCV to verify visual accuracy"""
        screenshot_path = f"verification_screenshots/{parcel_id}_ui_check.png"

        if not os.path.exists(screenshot_path):
            return {"verified": False, "error": "Screenshot not found"}

        # Load image
        image = cv2.imread(screenshot_path)

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Check for text regions
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Count text regions
        text_regions = 0
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 20 and h > 10 and w < 1000 and h < 100:
                text_regions += 1

        # Check for empty areas that should have data
        height, width = image.shape[:2]
        sections = [
            (0, 0, width//2, height//3),      # Top left
            (width//2, 0, width, height//3),  # Top right
            (0, height//3, width//2, height*2//3),  # Middle left
            (width//2, height//3, width, height*2//3),  # Middle right
        ]

        empty_sections = 0
        for x1, y1, x2, y2 in sections:
            roi = gray[y1:y2, x1:x2]
            if np.mean(roi) > 240:  # Mostly white/empty
                empty_sections += 1

        # Create annotated image
        annotated = image.copy()
        cv2.putText(annotated, f"Text Regions: {text_regions}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(annotated, f"Empty Sections: {empty_sections}/4", (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        annotated_path = screenshot_path.replace(".png", "_annotated.png")
        cv2.imwrite(annotated_path, annotated)

        return {
            "verified": text_regions > 20 and empty_sections < 2,
            "text_regions": text_regions,
            "empty_sections": empty_sections,
            "annotated_image": annotated_path,
            "quality_score": (text_regions / 100 * 100) if text_regions < 100 else 100
        }

    async def _verify_field_mappings(self, parcel_id: str, db_data: Dict) -> Dict[str, Any]:
        """Verify each field mapping"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Navigate to property
                url = f"http://localhost:5173/property/{parcel_id}"
                await page.goto(url, wait_until="networkidle")

                field_results = {
                    "total_fields": 0,
                    "matched_fields": 0,
                    "mismatched_fields": [],
                    "details": {}
                }

                # Check each tab
                for tab_name, mappings in self.field_mappings.items():
                    tab_results = {
                        "checked": 0,
                        "matched": 0,
                        "mismatches": []
                    }

                    # Click on tab
                    try:
                        await page.click(f'[data-tab="{tab_name}"]')
                        await page.wait_for_timeout(500)
                    except:
                        logger.warning(f"Tab {tab_name} not found")
                        continue

                    # Check each field mapping
                    for db_field, ui_field in mappings["database_to_ui"].items():
                        table, column = db_field.split(".")

                        # Get expected value from database
                        expected_value = None
                        if table in db_data and db_data[table]:
                            if isinstance(db_data[table], list) and len(db_data[table]) > 0:
                                expected_value = db_data[table][0].get(column)
                            elif isinstance(db_data[table], dict):
                                expected_value = db_data[table].get(column)

                        # Get actual value from UI
                        try:
                            element = await page.query_selector(f'[data-field="{ui_field}"]')
                            actual_value = await element.text_content() if element else None
                        except:
                            actual_value = None

                        # Compare values
                        field_results["total_fields"] += 1
                        tab_results["checked"] += 1

                        # Clean and compare
                        expected_str = str(expected_value).strip() if expected_value else ""
                        actual_str = str(actual_value).strip() if actual_value else ""

                        # Handle currency formatting
                        if "$" in actual_str and expected_str.replace(".", "").isdigit():
                            actual_str = actual_str.replace("$", "").replace(",", "").strip()

                        if expected_str and actual_str and (
                            expected_str == actual_str or
                            expected_str in actual_str or
                            actual_str in expected_str
                        ):
                            field_results["matched_fields"] += 1
                            tab_results["matched"] += 1
                        else:
                            field_results["mismatched_fields"].append({
                                "field": ui_field,
                                "expected": expected_str[:50],
                                "actual": actual_str[:50]
                            })
                            tab_results["mismatches"].append(ui_field)

                    field_results["details"][tab_name] = tab_results

                await browser.close()
                return field_results

            except Exception as e:
                await browser.close()
                return {
                    "error": str(e),
                    "total_fields": 0,
                    "matched_fields": 0
                }

    async def generate_comprehensive_report(self, parcel_ids: List[str]) -> Dict[str, Any]:
        """Generate comprehensive verification report for multiple properties"""
        logger.info(f"Starting comprehensive verification for {len(parcel_ids)} properties")

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_properties": len(parcel_ids),
            "properties_verified": [],
            "summary": {
                "fully_verified": 0,
                "partial_verification": 0,
                "failed": 0,
                "average_match_rate": 0
            },
            "field_statistics": {},
            "common_issues": []
        }

        match_rates = []

        for parcel_id in parcel_ids:
            logger.info(f"Verifying property {parcel_id}...")
            result = await self.verify_data_flow(parcel_id)

            report["properties_verified"].append(result)

            # Update summary
            if result["success"]:
                match_rate = float(result["summary"]["match_rate"].replace("%", ""))
                match_rates.append(match_rate)

                if match_rate >= 95:
                    report["summary"]["fully_verified"] += 1
                elif match_rate >= 70:
                    report["summary"]["partial_verification"] += 1
                else:
                    report["summary"]["failed"] += 1
            else:
                report["summary"]["failed"] += 1

        # Calculate average match rate
        if match_rates:
            report["summary"]["average_match_rate"] = f"{np.mean(match_rates):.1f}%"

        # Analyze common issues
        all_mismatches = []
        for prop in report["properties_verified"]:
            if "field_matches" in prop and "mismatched_fields" in prop["field_matches"]:
                all_mismatches.extend(prop["field_matches"]["mismatched_fields"])

        # Find most common mismatched fields
        field_counts = {}
        for mismatch in all_mismatches:
            field = mismatch["field"]
            field_counts[field] = field_counts.get(field, 0) + 1

        report["common_issues"] = sorted(
            [{"field": k, "occurrences": v} for k, v in field_counts.items()],
            key=lambda x: x["occurrences"],
            reverse=True
        )[:10]

        # Save report
        report_path = f"verification_reports/comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("verification_reports", exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        self._print_summary(report)

        return report

    def _print_summary(self, report: Dict[str, Any]):
        """Print a formatted summary of the verification report"""
        print("\n" + "="*80)
        print("DATA MAPPING VERIFICATION REPORT")
        print("="*80)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Total Properties Tested: {report['total_properties']}")
        print("\n" + "-"*40)
        print("SUMMARY:")
        print("-"*40)
        print(f"✅ Fully Verified (>95% match): {report['summary']['fully_verified']}")
        print(f"⚠️  Partial Verification (70-95%): {report['summary']['partial_verification']}")
        print(f"❌ Failed (<70% match): {report['summary']['failed']}")
        print(f"📊 Average Match Rate: {report['summary']['average_match_rate']}")

        if report["common_issues"]:
            print("\n" + "-"*40)
            print("COMMON ISSUES:")
            print("-"*40)
            for issue in report["common_issues"][:5]:
                print(f"  • {issue['field']}: {issue['occurrences']} occurrences")

        print("\n" + "-"*40)
        print("PROPERTY DETAILS:")
        print("-"*40)
        for prop in report["properties_verified"]:
            if "summary" in prop:
                status = "✅" if float(prop["summary"]["match_rate"].replace("%", "")) >= 95 else "⚠️"
                print(f"{status} {prop['parcel_id']}: {prop['summary']['match_rate']} match rate")
                if prop.get("errors"):
                    for error in prop["errors"]:
                        print(f"    ERROR: {error}")
                if prop.get("warnings"):
                    for warning in prop["warnings"]:
                        print(f"    WARNING: {warning}")

        print("\n" + "="*80)
        print(f"Report saved to: verification_reports/")
        print("="*80 + "\n")

async def main():
    """Main test function"""
    verifier = ComprehensiveDataVerifier()

    # Test with sample properties
    test_properties = [
        "494224020080",  # Example parcel ID
        # Add more test properties as needed
    ]

    # Run comprehensive verification
    report = await verifier.generate_comprehensive_report(test_properties)

    return report

if __name__ == "__main__":
    print("Starting Data Mapping Verification System...")
    print("This will verify that all data flows correctly from Supabase to the UI")
    print("-"*60)

    # Run the verification
    asyncio.run(main())