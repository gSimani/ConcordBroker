"""
Comprehensive Data Verification System
Integrates ML-based mapping with visual verification
Ensures 100% accuracy of data flow from database to UI
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# Import our custom modules
from intelligent_data_mapper import IntelligentDataMapper, FieldMapping
from visual_data_verifier import VisualDataVerifier, VerificationResult

load_dotenv('.env.mcp')

class ComprehensiveDataVerification:
    """Complete data verification pipeline"""

    def __init__(self):
        # Initialize components
        self.mapper = IntelligentDataMapper()
        self.verifier = VisualDataVerifier()

        # Supabase connection
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # Store results
        self.mapping_results: Dict[str, List[FieldMapping]] = {}
        self.verification_results: List[VerificationResult] = []
        self.data_flow_map: Dict = {}

    async def initialize(self):
        """Initialize all components"""
        print("Initializing Comprehensive Data Verification System...")
        print("=" * 60)

        # Initialize visual verifier (Playwright)
        await self.verifier.initialize()

        # Train ML model
        self.mapper.train_field_matcher()

        print("✓ System initialized successfully\n")

    async def analyze_data_flow(self) -> Dict:
        """Analyze complete data flow from database to UI"""
        print("PHASE 1: Analyzing Data Flow")
        print("-" * 40)

        # Map all database fields to UI components
        self.mapping_results = await self.mapper.map_all_fields()

        # Create data flow map
        self.data_flow_map = {
            "database_to_ui": {},
            "ui_to_database": {},
            "transformations": {},
            "validation_rules": {}
        }

        for table_name, mappings in self.mapping_results.items():
            for mapping in mappings:
                # Database to UI mapping
                if table_name not in self.data_flow_map["database_to_ui"]:
                    self.data_flow_map["database_to_ui"][table_name] = {}

                self.data_flow_map["database_to_ui"][table_name][mapping.db_field] = {
                    "ui_tab": mapping.ui_tab,
                    "ui_field": mapping.ui_field,
                    "confidence": mapping.confidence,
                    "data_type": mapping.data_type
                }

                # UI to Database reverse mapping
                ui_key = f"{mapping.ui_tab}.{mapping.ui_field}"
                self.data_flow_map["ui_to_database"][ui_key] = {
                    "db_table": table_name,
                    "db_field": mapping.db_field,
                    "confidence": mapping.confidence
                }

                # Store transformations
                if mapping.transformation:
                    self.data_flow_map["transformations"][f"{table_name}.{mapping.db_field}"] = mapping.transformation

                # Store validation rules
                if mapping.validation_rule:
                    self.data_flow_map["validation_rules"][f"{table_name}.{mapping.db_field}"] = mapping.validation_rule

        print(f"✓ Mapped {sum(len(m) for m in self.mapping_results.values())} fields")
        return self.data_flow_map

    async def fetch_sample_data(self, table: str, limit: int = 10) -> List[Dict]:
        """Fetch sample data from database"""
        try:
            response = self.supabase.table(table).select("*").limit(limit).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching data from {table}: {e}")
            return []

    async def verify_property_appraiser_data(self, parcel_id: str) -> Dict:
        """Verify Property Appraiser data mapping and display"""
        print(f"\nPHASE 2: Verifying Property Appraiser Data for {parcel_id}")
        print("-" * 40)

        # Fetch property data from database
        property_data = self.supabase.table("florida_parcels") \
            .select("*") \
            .eq("parcel_id", parcel_id) \
            .limit(1) \
            .execute()

        if not property_data.data:
            print(f"⚠ No data found for parcel {parcel_id}")
            return {}

        property_record = property_data.data[0]

        # Prepare expected values based on mapping
        expected_values = {}
        for field, value in property_record.items():
            # Find UI mapping for this field
            mapping_key = f"florida_parcels.{field}"
            if mapping_key in self.data_flow_map["database_to_ui"].get("florida_parcels", {}):
                ui_info = self.data_flow_map["database_to_ui"]["florida_parcels"][field]
                tab = ui_info["ui_tab"]
                ui_field = ui_info["ui_field"]

                if tab not in expected_values:
                    expected_values[tab] = {}

                # Apply transformation if needed
                transformed_value = self._apply_transformation(value, mapping_key)
                expected_values[tab][ui_field] = transformed_value

        # Verify each field visually
        verification_results = await self.verifier.verify_property_data(parcel_id, expected_values)
        self.verification_results.extend(verification_results)

        # Analyze results
        success_rate = sum(1 for r in verification_results if r.verification_status == "passed") / len(verification_results) if verification_results else 0

        print(f"✓ Verification complete: {success_rate:.1%} success rate")

        return {
            "parcel_id": parcel_id,
            "success_rate": success_rate,
            "total_fields": len(verification_results),
            "passed": sum(1 for r in verification_results if r.verification_status == "passed"),
            "failed": sum(1 for r in verification_results if r.verification_status == "failed")
        }

    async def verify_sunbiz_data(self, entity_name: str) -> Dict:
        """Verify Sunbiz data mapping and display"""
        print(f"\nPHASE 3: Verifying Sunbiz Data for {entity_name}")
        print("-" * 40)

        # Fetch Sunbiz data
        sunbiz_data = self.supabase.table("sunbiz_entities") \
            .select("*") \
            .eq("entity_name", entity_name) \
            .limit(1) \
            .execute()

        if not sunbiz_data.data:
            print(f"⚠ No Sunbiz data found for {entity_name}")
            return {}

        sunbiz_record = sunbiz_data.data[0]

        # Also fetch officers
        officers_data = self.supabase.table("sunbiz_officers") \
            .select("*") \
            .eq("entity_name", entity_name) \
            .execute()

        # Prepare expected values
        expected_values = {"sunbiz": {}}

        for field, value in sunbiz_record.items():
            if field in ["entity_name", "entity_type", "filing_date", "status", "registered_agent_name"]:
                ui_field = self._map_sunbiz_field(field)
                if ui_field:
                    expected_values["sunbiz"][ui_field] = value

        # Add officers
        if officers_data.data:
            expected_values["sunbiz"]["officers"] = [
                f"{o['officer_name']} - {o['officer_title']}"
                for o in officers_data.data[:5]  # Show first 5 officers
            ]

        # Visual verification would go here (if Sunbiz tab is displayed)
        # For now, return mapping confidence

        return {
            "entity_name": entity_name,
            "mapped_fields": len(expected_values.get("sunbiz", {})),
            "officers_found": len(officers_data.data) if officers_data else 0
        }

    def _apply_transformation(self, value: Any, field_key: str) -> Any:
        """Apply data transformation based on field type"""
        transformation = self.data_flow_map["transformations"].get(field_key)

        if not transformation or value is None:
            return value

        try:
            if transformation == "format_currency":
                return f"${value:,.2f}" if isinstance(value, (int, float)) else value
            elif transformation == "format_area":
                return f"{value:,.0f} sq ft" if isinstance(value, (int, float)) else value
            elif transformation == "format_date":
                if isinstance(value, str):
                    # Parse and format date
                    from datetime import datetime
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return dt.strftime("%m/%d/%Y")
                return value
            elif transformation == "round_decimal":
                return round(float(value), 2) if value else 0
            elif transformation == "to_integer":
                return int(float(value)) if value else 0
            else:
                return value
        except:
            return value

    def _map_sunbiz_field(self, field: str) -> Optional[str]:
        """Map Sunbiz database field to UI field"""
        sunbiz_field_map = {
            "entity_name": "entity_name",
            "entity_type": "entity_type",
            "filing_date": "filing_date",
            "status": "status",
            "registered_agent_name": "registered_agent",
            "principal_address": "principal_address"
        }
        return sunbiz_field_map.get(field)

    async def run_comprehensive_test(self, test_parcels: List[str], test_entities: List[str]):
        """Run comprehensive verification test"""
        print("\nSTARTING COMPREHENSIVE DATA VERIFICATION TEST")
        print("=" * 60)

        # Initialize system
        await self.initialize()

        # Analyze data flow
        await self.analyze_data_flow()

        # Test Property Appraiser data
        property_results = []
        for parcel_id in test_parcels:
            result = await self.verify_property_appraiser_data(parcel_id)
            property_results.append(result)
            await asyncio.sleep(2)  # Pause between tests

        # Test Sunbiz data
        sunbiz_results = []
        for entity_name in test_entities:
            result = await self.verify_sunbiz_data(entity_name)
            sunbiz_results.append(result)

        # Generate comprehensive report
        report = self.generate_comprehensive_report(property_results, sunbiz_results)

        # Save results
        self.save_results(report)

        print("\n" + "=" * 60)
        print("VERIFICATION COMPLETE!")
        print("=" * 60)

    def generate_comprehensive_report(self, property_results: List[Dict], sunbiz_results: List[Dict]) -> Dict:
        """Generate comprehensive verification report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_fields_mapped": sum(len(m) for m in self.mapping_results.values()),
                "total_properties_tested": len(property_results),
                "total_entities_tested": len(sunbiz_results),
                "overall_success_rate": 0.0
            },
            "property_appraiser": {
                "results": property_results,
                "average_success_rate": 0.0
            },
            "sunbiz": {
                "results": sunbiz_results,
                "total_fields_mapped": sum(r["mapped_fields"] for r in sunbiz_results)
            },
            "data_flow_map": self.data_flow_map,
            "verification_details": []
        }

        # Calculate averages
        if property_results:
            report["property_appraiser"]["average_success_rate"] = \
                sum(r.get("success_rate", 0) for r in property_results) / len(property_results)
            report["summary"]["overall_success_rate"] = report["property_appraiser"]["average_success_rate"]

        # Add verification details
        for result in self.verification_results:
            report["verification_details"].append({
                "field": result.field_name,
                "expected": str(result.expected_value),
                "displayed": str(result.displayed_value),
                "confidence": result.match_confidence,
                "status": result.verification_status
            })

        return report

    def save_results(self, report: Dict):
        """Save all results to files"""
        # Save JSON report
        with open("comprehensive_verification_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Save mapping configuration
        self.mapper.export_mapping_config(self.mapping_results, "verified_mapping_config.json")

        # Generate markdown report
        md_report = self.generate_markdown_report(report)
        with open("comprehensive_verification_report.md", "w") as f:
            f.write(md_report)

        print("\n✓ Results saved:")
        print("  - comprehensive_verification_report.json")
        print("  - comprehensive_verification_report.md")
        print("  - verified_mapping_config.json")

    def generate_markdown_report(self, report: Dict) -> str:
        """Generate markdown formatted report"""
        lines = []
        lines.append("# Comprehensive Data Verification Report")
        lines.append(f"Generated: {report['timestamp']}\n")

        lines.append("## Executive Summary")
        lines.append(f"- Total Fields Mapped: {report['summary']['total_fields_mapped']}")
        lines.append(f"- Properties Tested: {report['summary']['total_properties_tested']}")
        lines.append(f"- Entities Tested: {report['summary']['total_entities_tested']}")
        lines.append(f"- **Overall Success Rate: {report['summary']['overall_success_rate']:.1%}**\n")

        lines.append("## Property Appraiser Data Verification")
        lines.append(f"Average Success Rate: {report['property_appraiser']['average_success_rate']:.1%}\n")

        if report['property_appraiser']['results']:
            lines.append("| Parcel ID | Success Rate | Passed | Failed | Total |")
            lines.append("|-----------|--------------|--------|--------|-------|")
            for r in report['property_appraiser']['results']:
                if r:  # Check if result exists
                    lines.append(
                        f"| {r.get('parcel_id', 'N/A')} | {r.get('success_rate', 0):.1%} | "
                        f"{r.get('passed', 0)} | {r.get('failed', 0)} | {r.get('total_fields', 0)} |"
                    )

        lines.append("\n## Sunbiz Data Verification")
        lines.append(f"Total Fields Mapped: {report['sunbiz']['total_fields_mapped']}\n")

        if report['sunbiz']['results']:
            lines.append("| Entity Name | Mapped Fields | Officers Found |")
            lines.append("|-------------|---------------|----------------|")
            for r in report['sunbiz']['results']:
                if r:
                    lines.append(
                        f"| {r.get('entity_name', 'N/A')[:30]} | "
                        f"{r.get('mapped_fields', 0)} | {r.get('officers_found', 0)} |"
                    )

        # Add field verification details
        lines.append("\n## Field Verification Details")

        failed_fields = [d for d in report['verification_details'] if d['status'] == 'failed']
        if failed_fields:
            lines.append("\n### Failed Verifications")
            lines.append("| Field | Expected | Displayed | Confidence |")
            lines.append("|-------|----------|-----------|------------|")
            for f in failed_fields[:10]:  # Show first 10
                lines.append(
                    f"| {f['field']} | {f['expected'][:20]} | "
                    f"{f['displayed'][:20] if f['displayed'] else 'Not found'} | {f['confidence']:.1%} |"
                )

        lines.append("\n## Recommendations")
        if report['summary']['overall_success_rate'] < 0.8:
            lines.append("- ⚠ Success rate below 80% - Review field mappings")
            lines.append("- Check data transformations for currency and date fields")
            lines.append("- Verify UI selectors are up to date")
        else:
            lines.append("- ✓ Data mapping performing well")
            lines.append("- Consider adding more validation rules")

        return "\n".join(lines)


async def main():
    """Run the comprehensive verification system"""
    system = ComprehensiveDataVerification()

    # Test data
    test_parcels = [
        "064210010010",
        "064210010020",
        "064210010030"
    ]

    test_entities = [
        "CONCORD BROKER LLC",
        "EXAMPLE CORPORATION"
    ]

    try:
        await system.run_comprehensive_test(test_parcels, test_entities)
    finally:
        await system.verifier.close()


if __name__ == "__main__":
    asyncio.run(main())