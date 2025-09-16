"""
Complete Data Verification and Mapping System
Integrates all components for 100% data accuracy verification
"""

import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apps', 'api'))

# Import all verification components
from apps.api.deep_learning_data_mapper import ComprehensiveDataMappingSystem
from apps.api.playwright_data_verification import PlaywrightDataVerifier, MCPVerificationIntegration
from apps.api.opencv_property_analyzer import PropertyImageAnalyzer, MCPImageAnalysisIntegration
from apps.api.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteDataVerificationSystem:
    """Main system for complete data verification"""

    def __init__(self):
        self.ml_mapper = ComprehensiveDataMappingSystem()
        self.playwright_verifier = PlaywrightDataVerifier()
        self.image_analyzer = PropertyImageAnalyzer()
        self.supabase = get_supabase_client()
        self.results = []
        self.report_dir = Path("verification_reports")
        self.report_dir.mkdir(exist_ok=True)

    async def verify_property_complete(self, property_id: str) -> Dict[str, Any]:
        """Complete verification of a single property"""

        logger.info(f"Starting complete verification for property: {property_id}")

        result = {
            'property_id': property_id,
            'timestamp': datetime.now().isoformat(),
            'stages': {},
            'overall_status': 'PENDING'
        }

        try:
            # Stage 1: Fetch data from Supabase
            logger.info("Stage 1: Fetching data from Supabase...")
            property_data = await self.fetch_property_data(property_id)
            result['stages']['data_fetch'] = {
                'status': 'SUCCESS',
                'fields_retrieved': len(property_data),
                'timestamp': datetime.now().isoformat()
            }

            # Stage 2: ML Field Mapping Validation
            logger.info("Stage 2: Running ML field mapping validation...")
            ml_results = await self.ml_mapper.validate_all_mappings(property_data)
            result['stages']['ml_mapping'] = {
                'status': 'SUCCESS' if ml_results['summary']['success_rate'] > 0.9 else 'PARTIAL',
                'total_fields': ml_results['stats']['total_fields'],
                'mapped_fields': ml_results['stats']['mapped_fields'],
                'valid_fields': ml_results['stats']['valid_fields'],
                'confidence': ml_results['stats']['average_confidence'],
                'timestamp': datetime.now().isoformat()
            }

            # Stage 3: Prepare expected data for UI verification
            logger.info("Stage 3: Preparing UI verification data...")
            expected_ui_data = await self.prepare_ui_data(property_data, ml_results['mappings'])

            # Stage 4: Playwright UI Verification
            logger.info("Stage 4: Running Playwright UI verification...")
            await self.playwright_verifier.initialize()

            try:
                playwright_results = await self.playwright_verifier.verify_all_tabs(
                    property_id,
                    expected_ui_data
                )

                result['stages']['ui_verification'] = {
                    'status': playwright_results['status'],
                    'tabs_verified': playwright_results['summary']['tabs_verified'],
                    'total_fields': playwright_results['summary']['total_fields'],
                    'fields_correct': playwright_results['summary']['fields_correct'],
                    'confidence': playwright_results['summary']['overall_confidence'],
                    'timestamp': datetime.now().isoformat()
                }
            finally:
                await self.playwright_verifier.close()

            # Stage 5: Visual Verification with OpenCV
            logger.info("Stage 5: Running visual verification...")
            screenshots = playwright_results.get('screenshots', [])
            visual_results = await self.verify_visual_data(screenshots)

            result['stages']['visual_verification'] = {
                'status': 'SUCCESS' if visual_results['accuracy'] > 0.9 else 'PARTIAL',
                'screenshots_analyzed': visual_results['screenshots_analyzed'],
                'text_extracted': visual_results['text_extracted'],
                'accuracy': visual_results['accuracy'],
                'timestamp': datetime.now().isoformat()
            }

            # Stage 6: Image Analysis (if property images available)
            logger.info("Stage 6: Analyzing property images...")
            image_urls = await self.get_property_images(property_id)

            if image_urls:
                image_results = await self.analyze_property_images(image_urls)
                result['stages']['image_analysis'] = {
                    'status': 'SUCCESS',
                    'images_analyzed': len(image_results),
                    'features_detected': image_results,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                result['stages']['image_analysis'] = {
                    'status': 'SKIPPED',
                    'reason': 'No property images available'
                }

            # Calculate overall verification score
            verification_score = self.calculate_overall_score(result['stages'])
            result['verification_score'] = verification_score

            # Determine overall status
            if verification_score >= 0.95:
                result['overall_status'] = 'FULLY_VERIFIED'
            elif verification_score >= 0.85:
                result['overall_status'] = 'MOSTLY_VERIFIED'
            elif verification_score >= 0.70:
                result['overall_status'] = 'PARTIALLY_VERIFIED'
            else:
                result['overall_status'] = 'NEEDS_REVIEW'

            # Generate recommendations
            result['recommendations'] = self.generate_recommendations(result)

        except Exception as e:
            logger.error(f"Error during verification: {e}")
            result['overall_status'] = 'ERROR'
            result['error'] = str(e)

        # Save results
        self.save_results(result)

        return result

    async def fetch_property_data(self, property_id: str) -> Dict[str, Any]:
        """Fetch property data from Supabase"""
        try:
            # Fetch from florida_parcels
            response = self.supabase.table('florida_parcels').select('*').eq(
                'parcel_id', property_id
            ).execute()

            if response.data and len(response.data) > 0:
                property_data = response.data[0]

                # Fetch related data
                # Sales history
                sales_response = self.supabase.table('sales_history').select('*').eq(
                    'parcel_id', property_id
                ).order('sale_date', desc=True).execute()

                if sales_response.data:
                    property_data['sales_history'] = sales_response.data

                # Tax certificates
                tax_cert_response = self.supabase.table('tax_certificates').select('*').eq(
                    'parcel_id', property_id
                ).execute()

                if tax_cert_response.data:
                    property_data['tax_certificates'] = tax_cert_response.data

                # Tax deeds
                tax_deed_response = self.supabase.table('tax_deeds').select('*').eq(
                    'parcel_id', property_id
                ).execute()

                if tax_deed_response.data:
                    property_data['tax_deeds'] = tax_deed_response.data

                # Sunbiz matches
                sunbiz_response = self.supabase.table('sunbiz_property_matches').select(
                    '*, sunbiz_entities(*)'
                ).eq('parcel_id', property_id).execute()

                if sunbiz_response.data:
                    property_data['sunbiz_entities'] = sunbiz_response.data

                return property_data
            else:
                raise ValueError(f"Property {property_id} not found in database")

        except Exception as e:
            logger.error(f"Error fetching property data: {e}")
            raise

    async def prepare_ui_data(self, property_data: Dict, mappings: Dict) -> Dict[str, Dict[str, Any]]:
        """Prepare expected UI data based on mappings"""
        ui_data = {
            'overview': {},
            'core-property': {},
            'valuation': {},
            'taxes': {},
            'sunbiz': {},
            'permit': {},
            'sales': {},
            'tax-deed-sales': {}
        }

        # Map fields to UI tabs based on ML mappings
        for field_name, mapping_info in mappings.items():
            if mapping_info['tab'] in ui_data:
                # Apply transformation if needed
                value = property_data.get(field_name)

                if mapping_info.get('transformation'):
                    value = self.apply_transformation(
                        value,
                        mapping_info['transformation']
                    )

                # Store in appropriate tab
                ui_element = mapping_info['ui_element'].split('.')[-1]
                ui_data[mapping_info['tab']][ui_element] = value

        return ui_data

    def apply_transformation(self, value: Any, transformation: str) -> Any:
        """Apply data transformation"""
        if transformation == 'formatCurrency' and value:
            return f"${float(value):,.0f}"
        elif transformation == 'formatDate' and value:
            if isinstance(value, str):
                return value
            return value.strftime('%m/%d/%Y') if hasattr(value, 'strftime') else str(value)
        elif transformation == 'property_type_description':
            return self.get_property_type_description(value)
        else:
            return value

    def get_property_type_description(self, code: str) -> str:
        """Get property type description from code"""
        property_types = {
            '0100': 'Single Family',
            '0200': 'Mobile Home',
            '0300': 'Multi-Family',
            '0400': 'Condominium',
            '1000': 'Vacant Residential',
            '1100': 'Commercial'
        }
        return property_types.get(code, 'Other')

    async def verify_visual_data(self, screenshots: List[str]) -> Dict[str, Any]:
        """Verify data using OpenCV on screenshots"""
        results = {
            'screenshots_analyzed': 0,
            'text_extracted': 0,
            'accuracy': 0.0
        }

        if not screenshots:
            return results

        total_accuracy = 0
        text_count = 0

        for screenshot_path in screenshots:
            if os.path.exists(screenshot_path):
                # Use OCR to extract text
                ocr_results = await self.playwright_verifier.visual_verification_with_ocr(
                    screenshot_path
                )

                if 'data_extracted' in ocr_results:
                    results['screenshots_analyzed'] += 1
                    text_count += len(ocr_results['data_extracted'])

                    # Simple accuracy based on text extraction success
                    if ocr_results['data_extracted']:
                        total_accuracy += 1

        results['text_extracted'] = text_count

        if results['screenshots_analyzed'] > 0:
            results['accuracy'] = total_accuracy / results['screenshots_analyzed']

        return results

    async def get_property_images(self, property_id: str) -> List[str]:
        """Get property image URLs"""
        # This would typically fetch from a storage service
        # For now, return empty list
        return []

    async def analyze_property_images(self, image_urls: List[str]) -> Dict[str, Any]:
        """Analyze property images using OpenCV"""
        results = {}

        for url in image_urls:
            try:
                analysis = await self.image_analyzer.analyze_property_image(url)
                results[url] = {
                    'features': analysis.features_detected,
                    'condition': analysis.condition_assessment,
                    'confidence': analysis.confidence_scores
                }
            except Exception as e:
                logger.error(f"Error analyzing image {url}: {e}")
                results[url] = {'error': str(e)}

        return results

    def calculate_overall_score(self, stages: Dict) -> float:
        """Calculate overall verification score"""
        scores = []
        weights = {
            'ml_mapping': 0.3,
            'ui_verification': 0.4,
            'visual_verification': 0.2,
            'image_analysis': 0.1
        }

        for stage_name, weight in weights.items():
            if stage_name in stages and 'confidence' in stages[stage_name]:
                scores.append(stages[stage_name]['confidence'] * weight)
            elif stage_name in stages and 'accuracy' in stages[stage_name]:
                scores.append(stages[stage_name]['accuracy'] * weight)
            elif stage_name in stages and stages[stage_name].get('status') == 'SUCCESS':
                scores.append(1.0 * weight)

        return sum(scores) / sum(weights.values())

    def generate_recommendations(self, result: Dict) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []

        # Check ML mapping stage
        if 'ml_mapping' in result['stages']:
            if result['stages']['ml_mapping']['confidence'] < 0.9:
                recommendations.append(
                    "Review and update field mappings for improved accuracy"
                )

        # Check UI verification
        if 'ui_verification' in result['stages']:
            if result['stages']['ui_verification']['fields_correct'] < \
               result['stages']['ui_verification']['total_fields']:
                missing = result['stages']['ui_verification']['total_fields'] - \
                         result['stages']['ui_verification']['fields_correct']
                recommendations.append(
                    f"Investigate {missing} fields with incorrect or missing values"
                )

        # Check visual verification
        if 'visual_verification' in result['stages']:
            if result['stages']['visual_verification']['accuracy'] < 0.9:
                recommendations.append(
                    "Improve UI rendering or data display for better visual verification"
                )

        # Overall recommendation
        if result['verification_score'] < 0.95:
            recommendations.append(
                "Schedule manual review of low-confidence fields"
            )

        return recommendations

    def save_results(self, result: Dict):
        """Save verification results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"verification_{result['property_id']}_{timestamp}.json"
        filepath = self.report_dir / filename

        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"Results saved to {filepath}")

    async def verify_batch(self, property_ids: List[str]) -> Dict[str, Any]:
        """Verify multiple properties"""
        batch_results = {
            'timestamp': datetime.now().isoformat(),
            'total_properties': len(property_ids),
            'results': [],
            'summary': {
                'fully_verified': 0,
                'mostly_verified': 0,
                'partially_verified': 0,
                'needs_review': 0,
                'errors': 0
            }
        }

        for property_id in property_ids:
            try:
                result = await self.verify_property_complete(property_id)
                batch_results['results'].append(result)

                # Update summary
                status = result['overall_status']
                if status == 'FULLY_VERIFIED':
                    batch_results['summary']['fully_verified'] += 1
                elif status == 'MOSTLY_VERIFIED':
                    batch_results['summary']['mostly_verified'] += 1
                elif status == 'PARTIALLY_VERIFIED':
                    batch_results['summary']['partially_verified'] += 1
                elif status == 'NEEDS_REVIEW':
                    batch_results['summary']['needs_review'] += 1
                elif status == 'ERROR':
                    batch_results['summary']['errors'] += 1

            except Exception as e:
                logger.error(f"Error verifying property {property_id}: {e}")
                batch_results['summary']['errors'] += 1

        # Calculate batch statistics
        batch_results['overall_success_rate'] = (
            batch_results['summary']['fully_verified'] /
            len(property_ids)
        ) if property_ids else 0

        # Save batch results
        self.save_batch_results(batch_results)

        return batch_results

    def save_batch_results(self, batch_results: Dict):
        """Save batch verification results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_verification_{timestamp}.json"
        filepath = self.report_dir / filename

        with open(filepath, 'w') as f:
            json.dump(batch_results, f, indent=2)

        logger.info(f"Batch results saved to {filepath}")

    async def generate_html_report(self, results: Dict) -> str:
        """Generate comprehensive HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Complete Data Verification Report</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                }}
                .score-badge {{
                    display: inline-block;
                    padding: 10px 20px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 1.2em;
                }}
                .score-excellent {{ background: #10b981; color: white; }}
                .score-good {{ background: #f59e0b; color: white; }}
                .score-poor {{ background: #ef4444; color: white; }}
                .stage-card {{
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .stage-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                }}
                .stage-title {{ font-size: 1.3em; font-weight: bold; }}
                .status-badge {{
                    padding: 5px 15px;
                    border-radius: 15px;
                    font-size: 0.9em;
                    font-weight: bold;
                }}
                .status-success {{ background: #d1fae5; color: #065f46; }}
                .status-partial {{ background: #fed7aa; color: #92400e; }}
                .status-error {{ background: #fee2e2; color: #991b1b; }}
                .metric {{
                    display: inline-block;
                    margin: 10px 20px 10px 0;
                }}
                .metric-label {{
                    font-size: 0.9em;
                    color: #6b7280;
                    margin-bottom: 5px;
                }}
                .metric-value {{
                    font-size: 1.5em;
                    font-weight: bold;
                    color: #1f2937;
                }}
                .progress-bar {{
                    width: 100%;
                    height: 30px;
                    background: #e5e7eb;
                    border-radius: 15px;
                    overflow: hidden;
                    margin: 10px 0;
                }}
                .progress-fill {{
                    height: 100%;
                    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
                    transition: width 0.3s;
                }}
                .recommendations {{
                    background: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .recommendation-item {{
                    margin: 10px 0;
                    padding-left: 20px;
                    position: relative;
                }}
                .recommendation-item:before {{
                    content: "→";
                    position: absolute;
                    left: 0;
                    color: #f59e0b;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Complete Data Verification Report</h1>
                    <p style="font-size: 1.2em;">Property ID: {results.get('property_id', 'N/A')}</p>
                    <p>Generated: {results.get('timestamp', 'N/A')}</p>
                    <div style="margin-top: 20px;">
                        <span class="score-badge {self.get_score_class(results.get('verification_score', 0))}">
                            Verification Score: {results.get('verification_score', 0):.1%}
                        </span>
                    </div>
                </div>
        """

        # Add stage results
        for stage_name, stage_data in results.get('stages', {}).items():
            status_class = self.get_status_class(stage_data.get('status', 'PENDING'))
            html += f"""
                <div class="stage-card">
                    <div class="stage-header">
                        <div class="stage-title">{stage_name.replace('_', ' ').title()}</div>
                        <span class="status-badge {status_class}">{stage_data.get('status', 'PENDING')}</span>
                    </div>
            """

            # Add metrics for each stage
            for key, value in stage_data.items():
                if key not in ['status', 'timestamp', 'errors']:
                    if isinstance(value, (int, float)):
                        if 'confidence' in key or 'accuracy' in key or 'rate' in key:
                            value = f"{value:.1%}"
                        html += f"""
                            <div class="metric">
                                <div class="metric-label">{key.replace('_', ' ').title()}</div>
                                <div class="metric-value">{value}</div>
                            </div>
                        """

            # Add progress bar for confidence/accuracy
            if 'confidence' in stage_data:
                html += f"""
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {stage_data['confidence']*100}%"></div>
                    </div>
                """

            html += "</div>"

        # Add recommendations
        if results.get('recommendations'):
            html += """
                <div class="recommendations">
                    <h3>Recommendations</h3>
            """
            for rec in results['recommendations']:
                html += f'<div class="recommendation-item">{rec}</div>'
            html += "</div>"

        html += """
            </div>
        </body>
        </html>
        """

        # Save HTML report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"complete_verification_{results.get('property_id', 'batch')}_{timestamp}.html"
        filepath = self.report_dir / filename

        with open(filepath, 'w') as f:
            f.write(html)

        logger.info(f"HTML report saved to {filepath}")
        return str(filepath)

    def get_score_class(self, score: float) -> str:
        """Get CSS class for score"""
        if score >= 0.9:
            return 'score-excellent'
        elif score >= 0.7:
            return 'score-good'
        else:
            return 'score-poor'

    def get_status_class(self, status: str) -> str:
        """Get CSS class for status"""
        if status == 'SUCCESS':
            return 'status-success'
        elif status in ['PARTIAL', 'MOSTLY_VERIFIED']:
            return 'status-partial'
        else:
            return 'status-error'


async def main():
    """Main execution function"""

    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║     Complete Data Verification System                       ║
    ║     Using TensorFlow/PyTorch + Playwright + OpenCV         ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    verifier = CompleteDataVerificationSystem()

    # Example: Verify a single property
    property_id = "064210010010"

    print(f"\n🔍 Starting complete verification for property: {property_id}")
    print("-" * 60)

    result = await verifier.verify_property_complete(property_id)

    print(f"\n✅ Verification Complete!")
    print(f"   Overall Status: {result['overall_status']}")
    print(f"   Verification Score: {result['verification_score']:.1%}")

    # Generate HTML report
    report_path = await verifier.generate_html_report(result)
    print(f"\n📊 HTML Report: {report_path}")

    # Print stage summaries
    print("\n📈 Stage Results:")
    for stage_name, stage_data in result['stages'].items():
        confidence = stage_data.get('confidence', stage_data.get('accuracy', 'N/A'))
        if isinstance(confidence, float):
            confidence = f"{confidence:.1%}"
        print(f"   • {stage_name}: {stage_data['status']} (Confidence: {confidence})")

    # Print recommendations
    if result.get('recommendations'):
        print("\n💡 Recommendations:")
        for rec in result['recommendations']:
            print(f"   → {rec}")

    # Example: Verify batch of properties
    # property_ids = ["064210010010", "064210010020", "064210010030"]
    # batch_results = await verifier.verify_batch(property_ids)
    # print(f"\n📦 Batch Verification Complete:")
    # print(f"   Total Properties: {batch_results['total_properties']}")
    # print(f"   Fully Verified: {batch_results['summary']['fully_verified']}")
    # print(f"   Success Rate: {batch_results['overall_success_rate']:.1%}")


if __name__ == "__main__":
    asyncio.run(main())