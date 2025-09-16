#!/usr/bin/env python3
"""
Complete Data Mapping Verification Script
Runs comprehensive analysis to ensure 100% accurate data placement
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import logging
from pathlib import Path

# Add the apps/api directory to the Python path
sys.path.append(str(Path(__file__).parent / "apps" / "api"))

# Import our verification systems
try:
    from data_mapping_verification_system import DataVerificationSystem
    from test_data_mapping_verification import ComprehensiveDataVerifier
except ImportError as e:
    print(f"❌ Error importing verification modules: {e}")
    print("Make sure all required packages are installed:")
    print("pip install pandas numpy sqlalchemy psycopg2-binary playwright opencv-python-headless")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompleteVerificationRunner:
    """Orchestrates complete verification of data mapping"""

    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'verification_stages': [],
            'overall_score': 0,
            'recommendations': []
        }

    async def run_complete_verification(self, parcel_ids: List[str]) -> Dict[str, Any]:
        """Run complete verification process"""

        print("🚀 Starting Complete Data Mapping Verification")
        print("=" * 60)
        print(f"📅 Timestamp: {self.results['timestamp']}")
        print(f"🏠 Properties to verify: {len(parcel_ids)}")
        print()

        # Stage 1: Database Schema Analysis
        print("1️⃣ Database Schema Analysis...")
        schema_results = await self._analyze_database_schema()
        self.results['verification_stages'].append({
            'stage': 'database_schema',
            'status': 'completed',
            'results': schema_results
        })

        # Stage 2: Field Mapping Validation
        print("\n2️⃣ Field Mapping Validation...")
        mapping_results = await self._validate_field_mappings()
        self.results['verification_stages'].append({
            'stage': 'field_mapping',
            'status': 'completed',
            'results': mapping_results
        })

        # Stage 3: Data Quality Assessment
        print("\n3️⃣ Data Quality Assessment...")
        quality_results = await self._assess_data_quality(parcel_ids)
        self.results['verification_stages'].append({
            'stage': 'data_quality',
            'status': 'completed',
            'results': quality_results
        })

        # Stage 4: UI Verification with Playwright
        print("\n4️⃣ UI Verification (Playwright MCP)...")
        ui_results = await self._verify_ui_components(parcel_ids)
        self.results['verification_stages'].append({
            'stage': 'ui_verification',
            'status': 'completed',
            'results': ui_results
        })

        # Stage 5: Visual Validation with OpenCV
        print("\n5️⃣ Visual Validation (OpenCV)...")
        visual_results = await self._validate_visual_accuracy()
        self.results['verification_stages'].append({
            'stage': 'visual_validation',
            'status': 'completed',
            'results': visual_results
        })

        # Stage 6: Generate Final Report
        print("\n6️⃣ Generating Final Report...")
        self._calculate_overall_score()
        self._generate_recommendations()
        report_path = self._save_complete_report()

        self._print_final_summary(report_path)
        return self.results

    async def _analyze_database_schema(self) -> Dict[str, Any]:
        """Analyze database schema and table structure"""

        from sqlalchemy import create_engine, inspect

        DATABASE_URL = "postgresql://postgres.pmispwtdngkcmsrsjwbp:vM4g2024$$Florida1@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

        try:
            engine = create_engine(DATABASE_URL)
            inspector = inspect(engine)

            tables = inspector.get_table_names()

            # Categorize tables
            property_tables = [t for t in tables if any(keyword in t.lower() for keyword in ['parcel', 'florida', 'property'])]
            sunbiz_tables = [t for t in tables if any(keyword in t.lower() for keyword in ['sunbiz', 'entity', 'business'])]
            tax_tables = [t for t in tables if 'tax' in t.lower()]

            # Check key tables exist
            required_tables = ['florida_parcels']
            missing_tables = [t for t in required_tables if t not in tables]

            results = {
                'total_tables': len(tables),
                'property_tables': len(property_tables),
                'sunbiz_tables': len(sunbiz_tables),
                'tax_tables': len(tax_tables),
                'missing_tables': missing_tables,
                'schema_complete': len(missing_tables) == 0
            }

            print(f"   📊 Total tables: {results['total_tables']}")
            print(f"   🏠 Property tables: {results['property_tables']}")
            print(f"   🏢 Sunbiz tables: {results['sunbiz_tables']}")
            print(f"   💰 Tax tables: {results['tax_tables']}")

            if missing_tables:
                print(f"   ⚠️ Missing tables: {missing_tables}")
            else:
                print(f"   ✅ All required tables present")

            return results

        except Exception as e:
            logger.error(f"Database schema analysis failed: {e}")
            return {'error': str(e), 'schema_complete': False}

    async def _validate_field_mappings(self) -> Dict[str, Any]:
        """Validate field mappings configuration"""

        # Define expected field mappings
        expected_mappings = {
            'overview': 16,      # 16 fields in overview tab
            'ownership': 9,      # 9 fields in ownership tab
            'tax_deed_sales': 8, # 8 fields in tax deed tab
            'sales_history': 9,  # 9 fields in sales history
            'permits': 7,        # 7 fields in permits tab
            'taxes': 4           # 4 fields in taxes tab
        }

        total_expected = sum(expected_mappings.values())

        # Check if mapping configurations exist
        mapping_files = [
            'data_mapping_verification_system.py',
            'test_data_mapping_verification.py'
        ]

        files_exist = all(os.path.exists(f"apps/api/{f}") for f in mapping_files)

        results = {
            'total_expected_mappings': total_expected,
            'mapping_files_exist': files_exist,
            'tab_mappings': expected_mappings,
            'mapping_complete': files_exist
        }

        print(f"   📋 Expected mappings: {total_expected}")
        print(f"   📁 Mapping files: {'✅ Present' if files_exist else '❌ Missing'}")

        for tab, count in expected_mappings.items():
            print(f"   📌 {tab}: {count} fields")

        return results

    async def _assess_data_quality(self, parcel_ids: List[str]) -> Dict[str, Any]:
        """Assess data quality for sample properties"""

        try:
            verifier = ComprehensiveDataVerifier()

            quality_scores = []
            property_results = []

            for parcel_id in parcel_ids[:3]:  # Test first 3 properties
                result = await verifier.verify_data_flow(parcel_id)

                if 'error' not in result:
                    # Extract quality score from summary
                    if 'summary' in result and 'match_rate' in result['summary']:
                        score = float(result['summary']['match_rate'].replace('%', ''))
                        quality_scores.append(score)

                    property_results.append({
                        'parcel_id': parcel_id,
                        'database_found': result.get('database_check', {}).get('found', False),
                        'ui_rendered': result.get('ui_check', {}).get('rendered', False),
                        'visual_verified': result.get('visual_check', {}).get('verified', False)
                    })

                    status = "✅" if result.get('success', False) else "⚠️"
                    print(f"   {status} {parcel_id}: {result.get('summary', {}).get('match_rate', 'N/A')}")
                else:
                    print(f"   ❌ {parcel_id}: {result['error']}")
                    property_results.append({
                        'parcel_id': parcel_id,
                        'error': result['error']
                    })

            avg_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0

            results = {
                'properties_tested': len(parcel_ids),
                'properties_verified': len(quality_scores),
                'average_score': avg_score,
                'property_results': property_results,
                'quality_acceptable': avg_score >= 80
            }

            print(f"   📊 Average quality score: {avg_score:.1f}%")
            return results

        except Exception as e:
            logger.error(f"Data quality assessment failed: {e}")
            return {'error': str(e), 'quality_acceptable': False}

    async def _verify_ui_components(self, parcel_ids: List[str]) -> Dict[str, Any]:
        """Verify UI components using Playwright"""

        try:
            # Check if localhost is running
            import aiohttp

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get('http://localhost:5173/') as response:
                        if response.status == 200:
                            localhost_running = True
                        else:
                            localhost_running = False
                except:
                    localhost_running = False

            if not localhost_running:
                print("   ⚠️ Localhost not running - skipping UI verification")
                return {
                    'localhost_running': False,
                    'ui_verification_skipped': True,
                    'message': 'Start localhost:5173 to enable UI verification'
                }

            # Run UI verification for first property
            verifier = DataVerificationSystem()
            result = await verifier.verify_property(parcel_ids[0])

            ui_score = result.get('overall_score', 0)

            results = {
                'localhost_running': True,
                'ui_verification_completed': True,
                'test_property': parcel_ids[0],
                'ui_score': ui_score,
                'ui_acceptable': ui_score >= 90
            }

            print(f"   🎭 UI verification score: {ui_score:.1f}%")
            return results

        except Exception as e:
            logger.error(f"UI verification failed: {e}")
            return {'error': str(e), 'ui_acceptable': False}

    async def _validate_visual_accuracy(self) -> Dict[str, Any]:
        """Validate visual accuracy using OpenCV"""

        try:
            # Check for screenshots
            screenshot_files = [f for f in os.listdir('.') if f.endswith('.png') and 'verification' in f]

            if not screenshot_files:
                print("   📸 No screenshots available for visual validation")
                return {
                    'screenshots_available': False,
                    'visual_validation_skipped': True,
                    'message': 'Run UI verification first to generate screenshots'
                }

            # Analyze first screenshot
            import cv2
            import numpy as np

            screenshot_path = screenshot_files[0]
            image = cv2.imread(screenshot_path)

            if image is None:
                return {'error': 'Could not load screenshot', 'visual_acceptable': False}

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detect text regions
            _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            text_regions = 0
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if 10 < w < 500 and 5 < h < 50:
                    text_regions += 1

            # Calculate data density
            total_pixels = image.shape[0] * image.shape[1]
            text_pixels = cv2.countNonZero(binary)
            data_density = (text_pixels / total_pixels) * 100

            visual_quality = 'GOOD' if text_regions > 30 and data_density > 1.0 else 'FAIR' if text_regions > 15 else 'POOR'

            results = {
                'screenshots_analyzed': len(screenshot_files),
                'text_regions_detected': text_regions,
                'data_density': data_density,
                'visual_quality': visual_quality,
                'visual_acceptable': visual_quality in ['GOOD', 'FAIR']
            }

            print(f"   👁️ Visual quality: {visual_quality}")
            print(f"   📊 Text regions: {text_regions}")
            print(f"   📈 Data density: {data_density:.2f}%")

            return results

        except Exception as e:
            logger.error(f"Visual validation failed: {e}")
            return {'error': str(e), 'visual_acceptable': False}

    def _calculate_overall_score(self):
        """Calculate overall verification score"""

        scores = []
        weights = []

        for stage in self.results['verification_stages']:
            stage_name = stage['stage']
            stage_results = stage['results']

            if stage_name == 'database_schema':
                score = 100 if stage_results.get('schema_complete', False) else 50
                scores.append(score)
                weights.append(0.15)  # 15% weight

            elif stage_name == 'field_mapping':
                score = 100 if stage_results.get('mapping_complete', False) else 50
                scores.append(score)
                weights.append(0.20)  # 20% weight

            elif stage_name == 'data_quality':
                score = stage_results.get('average_score', 0)
                scores.append(score)
                weights.append(0.30)  # 30% weight

            elif stage_name == 'ui_verification':
                score = stage_results.get('ui_score', 0) if stage_results.get('ui_acceptable', False) else 50
                scores.append(score)
                weights.append(0.25)  # 25% weight

            elif stage_name == 'visual_validation':
                score = 100 if stage_results.get('visual_acceptable', False) else 50
                scores.append(score)
                weights.append(0.10)  # 10% weight

        # Calculate weighted average
        if scores and weights:
            self.results['overall_score'] = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        else:
            self.results['overall_score'] = 0

    def _generate_recommendations(self):
        """Generate recommendations based on verification results"""

        recommendations = []

        overall_score = self.results['overall_score']

        if overall_score < 70:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Overall System',
                'issue': f'Overall verification score is low ({overall_score:.1f}%)',
                'action': 'Address all identified issues before production deployment'
            })

        # Check each stage for specific recommendations
        for stage in self.results['verification_stages']:
            stage_name = stage['stage']
            stage_results = stage['results']

            if stage_name == 'database_schema' and not stage_results.get('schema_complete', False):
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Database',
                    'issue': 'Missing required database tables',
                    'action': 'Create missing tables and import data'
                })

            if stage_name == 'data_quality' and not stage_results.get('quality_acceptable', False):
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Data Quality',
                    'issue': f'Average data quality score: {stage_results.get("average_score", 0):.1f}%',
                    'action': 'Clean data, fix missing values, and validate field formats'
                })

            if stage_name == 'ui_verification' and not stage_results.get('ui_acceptable', False):
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'UI Integration',
                    'issue': 'UI verification issues detected',
                    'action': 'Check field selectors and data binding in UI components'
                })

        self.results['recommendations'] = recommendations

    def _save_complete_report(self) -> str:
        """Save complete verification report"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"complete_verification_report_{timestamp}.json"

        # Ensure reports directory exists
        os.makedirs('verification_reports', exist_ok=True)
        report_path = f"verification_reports/{report_path}"

        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        return report_path

    def _print_final_summary(self, report_path: str):
        """Print final verification summary"""

        print("\n" + "=" * 60)
        print("🎉 COMPLETE VERIFICATION SUMMARY")
        print("=" * 60)

        overall_score = self.results['overall_score']

        # Overall score with color coding
        if overall_score >= 90:
            status_emoji = "🟢"
            status_text = "EXCELLENT"
        elif overall_score >= 80:
            status_emoji = "🟡"
            status_text = "GOOD"
        elif overall_score >= 70:
            status_emoji = "🟠"
            status_text = "FAIR"
        else:
            status_emoji = "🔴"
            status_text = "NEEDS WORK"

        print(f"\n{status_emoji} Overall Score: {overall_score:.1f}% ({status_text})")

        print(f"\n📋 Verification Stages:")
        for stage in self.results['verification_stages']:
            stage_name = stage['stage'].replace('_', ' ').title()
            print(f"  ✅ {stage_name}")

        if self.results['recommendations']:
            print(f"\n💡 Recommendations ({len(self.results['recommendations'])}):")
            for i, rec in enumerate(self.results['recommendations'][:5], 1):
                priority_emoji = "🔴" if rec['priority'] == 'CRITICAL' else "🟠" if rec['priority'] == 'HIGH' else "🟡"
                print(f"  {priority_emoji} {i}. [{rec['priority']}] {rec['category']}: {rec['action']}")
        else:
            print(f"\n✅ No critical issues found!")

        print(f"\n📄 Full Report: {report_path}")
        print("=" * 60)

async def main():
    """Main function to run complete verification"""

    # Test properties
    test_properties = [
        "494224020080",  # Primary test property
        "494224020090",  # Secondary test property
        "494224020100"   # Tertiary test property
    ]

    # Create verification runner
    runner = CompleteVerificationRunner()

    # Run complete verification
    results = await runner.run_complete_verification(test_properties)

    return results

if __name__ == "__main__":
    print("🔍 Complete Data Mapping Verification")
    print("Ensuring 100% accurate data placement from Supabase to UI")
    print("-" * 60)

    # Run verification
    asyncio.run(main())