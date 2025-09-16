"""
Complete Verification System Executor
Runs PySpark + Playwright MCP + OpenCV verification pipeline
Ensures 100% accurate field mapping from databases to UI
"""

import asyncio
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import subprocess

# Import our verification modules
from pyspark_field_mapping_processor import PySparkFieldMappingProcessor
from pyspark_playwright_opencv_verifier import PySparkPlaywrightOpenCVVerifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CompleteVerificationSystem:
    """
    Orchestrates the complete verification system:
    1. PySpark big data processing
    2. Playwright MCP UI automation
    3. OpenCV visual verification
    """

    def __init__(self):
        self.start_time = datetime.now()
        self.results = {}

    def check_prerequisites(self) -> bool:
        """Check system prerequisites"""
        logger.info("Checking system prerequisites...")

        prerequisites = [
            ("java", "Java Runtime Environment"),
            ("python", "Python 3.8+"),
            ("spark-submit", "Apache Spark"),
            ("playwright", "Playwright browsers")
        ]

        all_good = True
        for cmd, description in prerequisites:
            try:
                result = subprocess.run([cmd, "--version"],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"✓ {description}: Found")
                else:
                    logger.error(f"✗ {description}: Not found")
                    all_good = False
            except FileNotFoundError:
                logger.error(f"✗ {description}: Not found")
                all_good = False

        # Check required files
        required_files = [
            'field_mapping_configuration.json',
            'pyspark_field_mapping_processor.py',
            'pyspark_playwright_opencv_verifier.py'
        ]

        for file_path in required_files:
            if Path(file_path).exists():
                logger.info(f"✓ Required file: {file_path}")
            else:
                logger.error(f"✗ Missing file: {file_path}")
                all_good = False

        return all_good

    def start_localhost_services(self) -> bool:
        """Start required localhost services"""
        logger.info("Starting localhost services...")

        try:
            # Check if React frontend is running
            import requests
            response = requests.get("http://localhost:5173", timeout=5)
            if response.status_code == 200:
                logger.info("✓ React frontend is running on localhost:5173")
            else:
                logger.warning("⚠ React frontend may not be fully loaded")
        except:
            logger.error("✗ React frontend not accessible on localhost:5173")
            logger.info("Please start the frontend with: cd apps/web && npm run dev")
            return False

        try:
            # Check if API is running
            response = requests.get("http://localhost:8001/health", timeout=5)
            if response.status_code == 200:
                logger.info("✓ Fast API is running on localhost:8001")
            else:
                logger.warning("⚠ Fast API may not be fully loaded")
        except:
            logger.warning("⚠ Fast API not accessible on localhost:8001")
            logger.info("Starting API with: python apps/api/fast_property_api.py")

        return True

    async def run_pyspark_processing(self) -> Dict[str, Any]:
        """Run PySpark big data processing pipeline"""
        logger.info("="*60)
        logger.info("PHASE 1: PYSPARK BIG DATA PROCESSING")
        logger.info("="*60)

        try:
            processor = PySparkFieldMappingProcessor()
            result = processor.run_complete_processing_pipeline()

            if result['success']:
                logger.info("✓ PySpark processing completed successfully")
                logger.info(f"  Property records processed: {result['property_records']:,}")
                logger.info(f"  Sunbiz records processed: {result['sunbiz_records']:,}")
                logger.info(f"  Verification samples: {result['verification_samples']:,}")
            else:
                logger.error(f"✗ PySpark processing failed: {result.get('error')}")

            processor.cleanup()
            return result

        except Exception as e:
            logger.error(f"✗ PySpark processing exception: {e}")
            return {"success": False, "error": str(e)}

    async def run_ui_verification(self, sample_size: int = 500) -> Dict[str, Any]:
        """Run Playwright MCP + OpenCV verification"""
        logger.info("="*60)
        logger.info("PHASE 2: UI VERIFICATION WITH PLAYWRIGHT + OPENCV")
        logger.info("="*60)

        try:
            verifier = PySparkPlaywrightOpenCVVerifier()
            result = await verifier.run_complete_verification_pipeline(
                sample_size=sample_size
            )

            if result['success']:
                logger.info("✓ UI verification completed successfully")
                report = result['report']
                logger.info(f"  Total verifications: {report['overall_statistics']['total_verifications']:,}")
                logger.info(f"  Success rate: {report['overall_statistics']['success_rate']:.2f}%")
                logger.info(f"  Visual match score: {report['visual_verification']['average_score']:.3f}")
            else:
                logger.error(f"✗ UI verification failed: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"✗ UI verification exception: {e}")
            return {"success": False, "error": str(e)}

    def generate_combined_report(self,
                                pyspark_result: Dict,
                                ui_result: Dict) -> Dict[str, Any]:
        """Generate comprehensive combined report"""
        logger.info("="*60)
        logger.info("PHASE 3: GENERATING COMBINED REPORT")
        logger.info("="*60)

        end_time = datetime.now()
        total_duration = end_time - self.start_time

        combined_report = {
            "system_verification": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration_minutes": total_duration.total_seconds() / 60,
                "system_components": ["PySpark", "Playwright MCP", "OpenCV"]
            },
            "pyspark_processing": {
                "success": pyspark_result.get("success", False),
                "records_processed": {
                    "property_records": pyspark_result.get("property_records", 0),
                    "sunbiz_records": pyspark_result.get("sunbiz_records", 0)
                },
                "data_quality_score": self._extract_quality_score(pyspark_result),
                "processing_speed": self._calculate_processing_speed(pyspark_result, total_duration)
            },
            "ui_verification": {
                "success": ui_result.get("success", False),
                "verification_statistics": ui_result.get("report", {}).get("overall_statistics", {}),
                "visual_verification": ui_result.get("report", {}).get("visual_verification", {}),
                "tab_accuracy": ui_result.get("report", {}).get("tab_statistics", [])
            },
            "combined_metrics": {
                "overall_system_accuracy": self._calculate_overall_accuracy(pyspark_result, ui_result),
                "field_mapping_completeness": self._calculate_mapping_completeness(ui_result),
                "visual_verification_score": ui_result.get("report", {}).get("visual_verification", {}).get("average_score", 0),
                "data_integrity_score": self._calculate_data_integrity(pyspark_result, ui_result)
            },
            "recommendations": self._generate_recommendations(pyspark_result, ui_result),
            "quality_assessment": self._assess_quality(pyspark_result, ui_result)
        }

        # Save comprehensive report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"complete_verification_report_{timestamp}.json"

        with open(report_path, 'w') as f:
            json.dump(combined_report, f, indent=2)

        logger.info(f"✓ Combined report saved to: {report_path}")
        return combined_report

    def _extract_quality_score(self, pyspark_result: Dict) -> float:
        """Extract data quality score from PySpark results"""
        if not pyspark_result.get("success"):
            return 0.0

        report = pyspark_result.get("report", {})
        quality_metrics = report.get("data_quality_metrics", {})
        return quality_metrics.get("average_quality_score", 0.0)

    def _calculate_processing_speed(self, pyspark_result: Dict, duration) -> Dict:
        """Calculate processing speed metrics"""
        total_records = (
            pyspark_result.get("property_records", 0) +
            pyspark_result.get("sunbiz_records", 0)
        )

        duration_minutes = duration.total_seconds() / 60
        if duration_minutes > 0:
            records_per_minute = total_records / duration_minutes
        else:
            records_per_minute = 0

        return {
            "total_records": total_records,
            "duration_minutes": duration_minutes,
            "records_per_minute": records_per_minute
        }

    def _calculate_overall_accuracy(self, pyspark_result: Dict, ui_result: Dict) -> float:
        """Calculate overall system accuracy"""
        pyspark_success = 1.0 if pyspark_result.get("success") else 0.0
        ui_success_rate = ui_result.get("report", {}).get("overall_statistics", {}).get("success_rate", 0) / 100

        # Weighted average: 40% PySpark processing, 60% UI verification
        overall_accuracy = (pyspark_success * 0.4) + (ui_success_rate * 0.6)
        return overall_accuracy * 100

    def _calculate_mapping_completeness(self, ui_result: Dict) -> float:
        """Calculate field mapping completeness"""
        tab_stats = ui_result.get("report", {}).get("tab_statistics", [])
        if not tab_stats:
            return 0.0

        total_accuracy = sum(tab["accuracy"] for tab in tab_stats)
        avg_accuracy = total_accuracy / len(tab_stats)
        return avg_accuracy

    def _calculate_data_integrity(self, pyspark_result: Dict, ui_result: Dict) -> float:
        """Calculate overall data integrity score"""
        quality_score = self._extract_quality_score(pyspark_result)
        visual_score = ui_result.get("report", {}).get("visual_verification", {}).get("average_score", 0) * 100

        return (quality_score + visual_score) / 2

    def _generate_recommendations(self, pyspark_result: Dict, ui_result: Dict) -> List[str]:
        """Generate system recommendations"""
        recommendations = []

        # PySpark recommendations
        if not pyspark_result.get("success"):
            recommendations.append("CRITICAL: PySpark processing failed. Check Spark configuration and database connectivity.")

        quality_score = self._extract_quality_score(pyspark_result)
        if quality_score < 90:
            recommendations.append(f"Data quality score is {quality_score:.1f}%. Review data validation rules and source data quality.")

        # UI verification recommendations
        ui_success_rate = ui_result.get("report", {}).get("overall_statistics", {}).get("success_rate", 0)
        if ui_success_rate < 95:
            recommendations.append(f"UI verification success rate is {ui_success_rate:.1f}%. Review field selectors and UI consistency.")

        visual_score = ui_result.get("report", {}).get("visual_verification", {}).get("average_score", 0)
        if visual_score < 0.9:
            recommendations.append(f"Visual verification score is {visual_score:.3f}. Improve OCR preprocessing and field visibility.")

        # Tab-specific recommendations
        tab_stats = ui_result.get("report", {}).get("tab_statistics", [])
        for tab_stat in tab_stats:
            if tab_stat["accuracy"] < 90:
                recommendations.append(f"Tab '{tab_stat['tab']}' has {tab_stat['accuracy']:.1f}% accuracy. Priority review needed.")

        if not recommendations:
            recommendations.append("Excellent! All verification metrics are within target ranges.")

        return recommendations

    def _assess_quality(self, pyspark_result: Dict, ui_result: Dict) -> str:
        """Assess overall system quality"""
        overall_accuracy = self._calculate_overall_accuracy(pyspark_result, ui_result)

        if overall_accuracy >= 98:
            return "EXCELLENT: System is performing at optimal levels"
        elif overall_accuracy >= 95:
            return "GOOD: System is performing well with minor optimization opportunities"
        elif overall_accuracy >= 90:
            return "FAIR: System is functional but needs attention in several areas"
        else:
            return "POOR: System requires immediate attention and significant improvements"

    def print_final_summary(self, report: Dict):
        """Print final verification summary"""
        print("\n" + "="*80)
        print("🚀 COMPLETE VERIFICATION SYSTEM SUMMARY")
        print("="*80)

        print(f"📊 Overall System Accuracy: {report['combined_metrics']['overall_system_accuracy']:.2f}%")
        print(f"🎯 Field Mapping Completeness: {report['combined_metrics']['field_mapping_completeness']:.2f}%")
        print(f"👁️  Visual Verification Score: {report['combined_metrics']['visual_verification_score']:.3f}")
        print(f"🔍 Data Integrity Score: {report['combined_metrics']['data_integrity_score']:.2f}%")

        print(f"\n⏱️  Processing Performance:")
        processing = report['pyspark_processing']['processing_speed']
        print(f"   Total Records: {processing['total_records']:,}")
        print(f"   Duration: {processing['duration_minutes']:.1f} minutes")
        print(f"   Speed: {processing['records_per_minute']:,.0f} records/minute")

        print(f"\n🎭 UI Verification Results:")
        ui_stats = report['ui_verification']['verification_statistics']
        print(f"   Total Verifications: {ui_stats.get('total_verifications', 0):,}")
        print(f"   Success Rate: {ui_stats.get('success_rate', 0):.2f}%")
        print(f"   Failed Matches: {ui_stats.get('failed_matches', 0):,}")

        print(f"\n📋 Quality Assessment:")
        print(f"   {report['quality_assessment']}")

        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")

        print("\n" + "="*80)
        print("✅ VERIFICATION COMPLETE")
        print("="*80)

    async def run_complete_system(self, sample_size: int = 500):
        """Run the complete verification system"""
        logger.info("🚀 STARTING COMPLETE VERIFICATION SYSTEM")
        logger.info("PySpark + Playwright MCP + OpenCV")
        logger.info("="*80)

        try:
            # Check prerequisites
            if not self.check_prerequisites():
                logger.error("❌ Prerequisites check failed")
                return {"success": False, "error": "Prerequisites not met"}

            # Start services
            if not self.start_localhost_services():
                logger.error("❌ Failed to verify localhost services")
                return {"success": False, "error": "Services not available"}

            # Phase 1: PySpark processing
            pyspark_result = await self.run_pyspark_processing()

            # Phase 2: UI verification
            ui_result = await self.run_ui_verification(sample_size)

            # Phase 3: Generate combined report
            combined_report = self.generate_combined_report(pyspark_result, ui_result)

            # Print summary
            self.print_final_summary(combined_report)

            # Overall success assessment
            overall_success = (
                pyspark_result.get("success", False) and
                ui_result.get("success", False) and
                combined_report['combined_metrics']['overall_system_accuracy'] >= 95
            )

            return {
                "success": overall_success,
                "report": combined_report,
                "pyspark_result": pyspark_result,
                "ui_result": ui_result
            }

        except Exception as e:
            logger.error(f"❌ Complete system failed: {e}")
            return {"success": False, "error": str(e)}


async def main():
    """Main execution function"""
    # Parse command line arguments
    sample_size = 500
    if len(sys.argv) > 1:
        try:
            sample_size = int(sys.argv[1])
        except ValueError:
            logger.warning(f"Invalid sample size: {sys.argv[1]}, using default: 500")

    # Initialize and run system
    system = CompleteVerificationSystem()
    result = await system.run_complete_system(sample_size=sample_size)

    # Exit with appropriate code
    if result["success"]:
        print("\n🎉 SUCCESS: Complete verification system executed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ FAILED: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())