"""
Run Complete Data Verification and Mapping System
Main execution script for ConcordBroker data verification
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import argparse
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent / 'apps' / 'api'))

# Import our verification modules
from comprehensive_data_mapper import ComprehensiveDataMapper
from playwright_visual_verifier import PlaywrightVisualVerifier
from automated_data_verification_suite import AutomatedDataVerificationSuite

load_dotenv('.env.mcp')

class DataVerificationRunner:
    """Main runner for data verification system"""

    def __init__(self):
        self.data_mapper = ComprehensiveDataMapper()
        self.visual_verifier = PlaywrightVisualVerifier()
        self.test_suite = AutomatedDataVerificationSuite()

        self.results_dir = Path("verification_results")
        self.results_dir.mkdir(exist_ok=True)

    async def run_data_mapping_analysis(self, sample_parcel: str = None):
        """Run data mapping and visualization"""
        print("\n" + "="*60)
        print("STEP 1: DATA MAPPING AND VISUALIZATION")
        print("="*60 + "\n")

        results = await self.data_mapper.run_complete_analysis(sample_parcel)

        print("\n✅ Data mapping analysis complete")
        print(f"   - Completeness heatmap generated")
        print(f"   - Data flow diagram created")
        print(f"   - Field coverage report available")

        return results

    async def run_visual_verification(self, sample_properties: list):
        """Run visual verification with Playwright and OpenCV"""
        print("\n" + "="*60)
        print("STEP 2: VISUAL VERIFICATION")
        print("="*60 + "\n")

        verification_results = []

        for property_data in sample_properties:
            parcel_id = property_data.get('parcel_id')
            if parcel_id:
                print(f"Verifying property: {parcel_id}")
                result = await self.visual_verifier.run_visual_verification(
                    parcel_id, property_data
                )
                verification_results.append(result)
                print(f"  Score: {result.get('overall_score', 0):.1%}")

        print("\n✅ Visual verification complete")
        return verification_results

    async def run_automated_tests(self):
        """Run automated testing suite"""
        print("\n" + "="*60)
        print("STEP 3: AUTOMATED TESTING SUITE")
        print("="*60 + "\n")

        test_results = await self.test_suite.run_complete_test_suite()

        return test_results

    async def generate_final_report(self, all_results):
        """Generate comprehensive final report"""
        print("\n" + "="*60)
        print("GENERATING FINAL REPORT")
        print("="*60 + "\n")

        report_lines = [
            "=" * 80,
            "CONCORDBROKER DATA VERIFICATION - FINAL REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            "",
            "EXECUTIVE SUMMARY",
            "-" * 40
        ]

        # Data Mapping Results
        if 'data_mapping' in all_results:
            completeness_data = all_results['data_mapping'].get('completeness_data', {})
            overall_completeness = []

            for tab_name, tab_data in completeness_data.items():
                overall_completeness.append(tab_data['overall_completeness'])

            avg_completeness = sum(overall_completeness) / len(overall_completeness) if overall_completeness else 0

            report_lines.extend([
                "",
                "DATA MAPPING ANALYSIS:",
                f"  • Overall System Completeness: {avg_completeness:.1%}",
                f"  • Tabs Analyzed: {len(completeness_data)}",
                ""
            ])

            # Tab-specific results
            report_lines.append("  Tab Completeness:")
            for tab_name, tab_data in completeness_data.items():
                completeness = tab_data['overall_completeness']
                status = "✅" if completeness > 0.8 else "⚠️" if completeness > 0.5 else "❌"
                report_lines.append(f"    {status} {tab_name.upper()}: {completeness:.1%}")

        # Visual Verification Results
        if 'visual_verification' in all_results:
            visual_results = all_results['visual_verification']
            if visual_results:
                avg_score = sum([r.get('overall_score', 0) for r in visual_results]) / len(visual_results)

                report_lines.extend([
                    "",
                    "VISUAL VERIFICATION:",
                    f"  • Properties Verified: {len(visual_results)}",
                    f"  • Average Accuracy: {avg_score:.1%}",
                    ""
                ])

        # Automated Test Results
        if 'automated_tests' in all_results:
            test_summary = all_results['automated_tests'].get('summary', {})

            report_lines.extend([
                "",
                "AUTOMATED TESTING:",
                f"  • Total Tests: {test_summary.get('total_tests', 0)}",
                f"  • Passed: {test_summary.get('total_passed', 0)}",
                f"  • Failed: {test_summary.get('total_failed', 0)}",
                f"  • Warnings: {test_summary.get('total_warnings', 0)}",
                f"  • Success Rate: {test_summary.get('success_rate', 0):.1%}",
                ""
            ])

        # Critical Issues
        report_lines.extend([
            "",
            "CRITICAL ISSUES IDENTIFIED:",
            "-" * 40
        ])

        critical_issues = []

        # Check for low completeness tabs
        if 'data_mapping' in all_results:
            completeness_data = all_results['data_mapping'].get('completeness_data', {})
            for tab_name, tab_data in completeness_data.items():
                if tab_data['overall_completeness'] < 0.5:
                    critical_issues.append(f"❌ {tab_name} tab has critical data gaps ({tab_data['overall_completeness']:.1%} complete)")

        # Check for failed tests
        if 'automated_tests' in all_results:
            test_summary = all_results['automated_tests'].get('summary', {})
            if test_summary.get('total_failed', 0) > 0:
                critical_issues.append(f"❌ {test_summary['total_failed']} automated tests failed")

        if critical_issues:
            for issue in critical_issues:
                report_lines.append(f"  {issue}")
        else:
            report_lines.append("  ✅ No critical issues identified")

        # Recommendations
        report_lines.extend([
            "",
            "",
            "RECOMMENDATIONS:",
            "-" * 40
        ])

        recommendations = []

        # Generate recommendations based on results
        if 'data_mapping' in all_results:
            completeness_data = all_results['data_mapping'].get('completeness_data', {})

            low_completeness = [tab for tab, data in completeness_data.items()
                              if data['overall_completeness'] < 0.8]

            if low_completeness:
                recommendations.append(f"1. Prioritize data population for: {', '.join(low_completeness)}")

        if 'automated_tests' in all_results:
            test_summary = all_results['automated_tests'].get('summary', {})

            if test_summary.get('total_warnings', 0) > 5:
                recommendations.append("2. Address data validation warnings to improve quality")

            if test_summary.get('success_rate', 1) < 0.9:
                recommendations.append("3. Investigate and fix failing tests")

        if 'visual_verification' in all_results:
            visual_results = all_results['visual_verification']

            if visual_results:
                low_scoring = [r for r in visual_results if r.get('overall_score', 0) < 0.8]
                if low_scoring:
                    recommendations.append("4. Review UI data display for properties with low visual verification scores")

        if recommendations:
            for rec in recommendations:
                report_lines.append(f"  {rec}")
        else:
            report_lines.append("  ✅ System performing well - maintain current standards")

        # Next Steps
        report_lines.extend([
            "",
            "",
            "NEXT STEPS:",
            "-" * 40,
            "  1. Review detailed reports in 'verification_results' directory",
            "  2. Address critical issues identified above",
            "  3. Implement recommendations",
            "  4. Re-run verification after fixes",
            "",
            "=" * 80,
            "END OF REPORT"
        ])

        # Save final report
        report_path = self.results_dir / f"final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_content = "\n".join(report_lines)

        with open(report_path, 'w') as f:
            f.write(report_content)

        print(f"Final report saved: {report_path}")
        print("\n" + report_content)

        return report_path

    async def run_complete_verification(self, options):
        """Run the complete verification process"""
        all_results = {
            'timestamp': datetime.now().isoformat(),
            'options': vars(options)
        }

        try:
            # Step 1: Data Mapping Analysis
            if not options.skip_mapping:
                mapping_results = await self.run_data_mapping_analysis(options.sample_parcel)
                all_results['data_mapping'] = mapping_results

            # Step 2: Visual Verification
            if not options.skip_visual:
                # Sample properties for visual verification
                sample_properties = [
                    {
                        'parcel_id': options.sample_parcel or '064210010010',
                        'overview': {
                            'property_address': '123 Main St, Miami, FL 33101',
                            'owner_name': 'Sample Owner'
                        }
                    }
                ]
                visual_results = await self.run_visual_verification(sample_properties)
                all_results['visual_verification'] = visual_results

            # Step 3: Automated Testing
            if not options.skip_tests:
                test_results = await self.run_automated_tests()
                all_results['automated_tests'] = test_results

            # Generate Final Report
            final_report_path = await self.generate_final_report(all_results)

            # Save complete results
            results_path = self.results_dir / f"complete_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_path, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)

            print("\n" + "="*60)
            print("✅ DATA VERIFICATION COMPLETE")
            print("="*60)
            print(f"\nResults saved to: {self.results_dir}")
            print(f"  - Complete results: {results_path}")
            print(f"  - Final report: {final_report_path}")

            return all_results

        except Exception as e:
            print(f"\n❌ Error during verification: {str(e)}")
            raise


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run ConcordBroker Data Verification')

    parser.add_argument('--sample-parcel', type=str, default='064210010010',
                       help='Sample parcel ID for testing')
    parser.add_argument('--skip-mapping', action='store_true',
                       help='Skip data mapping analysis')
    parser.add_argument('--skip-visual', action='store_true',
                       help='Skip visual verification')
    parser.add_argument('--skip-tests', action='store_true',
                       help='Skip automated tests')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick verification (mapping only)')

    args = parser.parse_args()

    # Apply quick mode settings
    if args.quick:
        args.skip_visual = True
        args.skip_tests = True

    print("\n" + "="*60)
    print("CONCORDBROKER DATA VERIFICATION SYSTEM")
    print("="*60)
    print(f"\nStarting verification at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sample Parcel: {args.sample_parcel}")
    print(f"Options:")
    print(f"  - Data Mapping: {'ENABLED' if not args.skip_mapping else 'SKIPPED'}")
    print(f"  - Visual Verification: {'ENABLED' if not args.skip_visual else 'SKIPPED'}")
    print(f"  - Automated Tests: {'ENABLED' if not args.skip_tests else 'SKIPPED'}")

    runner = DataVerificationRunner()
    results = await runner.run_complete_verification(args)

    return results


if __name__ == "__main__":
    asyncio.run(main())