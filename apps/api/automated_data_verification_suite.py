"""
Automated Data Verification Suite for ConcordBroker
Complete testing and verification system for data accuracy
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from supabase import create_client, Client
from dotenv import load_dotenv
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from colorama import init, Fore, Back, Style

# Initialize colorama for colored console output
init(autoreset=True)

# Import our custom modules
sys.path.append(str(Path(__file__).parent))
from comprehensive_data_mapper import ComprehensiveDataMapper
from playwright_visual_verifier import PlaywrightVisualVerifier

load_dotenv('.env.mcp')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_verification_suite.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutomatedDataVerificationSuite:
    """Complete automated testing suite for data verification"""

    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        self.data_mapper = ComprehensiveDataMapper()
        self.visual_verifier = PlaywrightVisualVerifier()

        self.results_dir = Path("verification_results")
        self.results_dir.mkdir(exist_ok=True)

        # Test configurations
        self.test_configs = {
            'property_appraiser': {
                'tables': ['florida_parcels', 'nav_assessments', 'nap_characteristics'],
                'required_fields': [
                    'parcel_id', 'county', 'own_name', 'phy_addr1',
                    'just_value', 'land_value', 'tot_sqft'
                ],
                'validation_rules': {
                    'parcel_id': {'type': 'string', 'pattern': r'^\d{10,}$'},
                    'just_value': {'type': 'numeric', 'min': 0},
                    'county': {'type': 'string', 'values': self.get_florida_counties()},
                    'year': {'type': 'numeric', 'min': 2020, 'max': 2025}
                }
            },
            'sunbiz': {
                'tables': ['sunbiz_entities', 'sunbiz_officers', 'sunbiz_filings'],
                'required_fields': [
                    'entity_name', 'document_number', 'status', 'entity_type'
                ],
                'validation_rules': {
                    'document_number': {'type': 'string', 'pattern': r'^[A-Z]\d{11}$'},
                    'status': {'type': 'string', 'values': ['ACTIVE', 'INACTIVE', 'DISSOLVED']},
                    'entity_type': {'type': 'string', 'values': ['CORP', 'LLC', 'LP', 'LLP', 'NONPROFIT']}
                }
            },
            'tax_deed': {
                'tables': ['tax_deed_sales', 'tax_certificates'],
                'required_fields': [
                    'td_number', 'parcel_id', 'auction_date', 'auction_status'
                ],
                'validation_rules': {
                    'auction_status': {'type': 'string', 'values': ['UPCOMING', 'CANCELLED', 'COMPLETED', 'REDEEMED']},
                    'td_number': {'type': 'string', 'pattern': r'^TD-\d{4}-\d+$'},
                    'face_value': {'type': 'numeric', 'min': 0}
                }
            }
        }

    def get_florida_counties(self) -> List[str]:
        """Get list of Florida counties"""
        return [
            'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD',
            'CALHOUN', 'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA',
            'DESOTO', 'DIXIE', 'DUVAL', 'ESCAMBIA', 'FLAGLER', 'FRANKLIN',
            'GADSDEN', 'GILCHRIST', 'GLADES', 'GULF', 'HAMILTON', 'HARDEE',
            'HENDRY', 'HERNANDO', 'HIGHLANDS', 'HILLSBOROUGH', 'HOLMES',
            'INDIAN RIVER', 'JACKSON', 'JEFFERSON', 'LAFAYETTE', 'LAKE',
            'LEE', 'LEON', 'LEVY', 'LIBERTY', 'MADISON', 'MANATEE', 'MARION',
            'MARTIN', 'MIAMI-DADE', 'MONROE', 'NASSAU', 'OKALOOSA', 'OKEECHOBEE',
            'ORANGE', 'OSCEOLA', 'PALM BEACH', 'PASCO', 'PINELLAS', 'POLK',
            'PUTNAM', 'SANTA ROSA', 'SARASOTA', 'SEMINOLE', 'ST. JOHNS',
            'ST. LUCIE', 'SUMTER', 'SUWANNEE', 'TAYLOR', 'UNION', 'VOLUSIA',
            'WAKULLA', 'WALTON', 'WASHINGTON'
        ]

    async def test_data_integrity(self, table_name: str, sample_size: int = 1000) -> Dict[str, Any]:
        """Test data integrity for a specific table"""
        logger.info(f"Testing data integrity for table: {table_name}")

        test_results = {
            'table': table_name,
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }

        try:
            # Fetch sample data
            result = self.supabase.table(table_name).select('*').limit(sample_size).execute()

            if not result.data:
                test_results['tests']['data_exists'] = {
                    'status': 'FAILED',
                    'message': 'No data found in table'
                }
                test_results['failed'] += 1
                return test_results

            df = pd.DataFrame(result.data)

            # Test 1: Check for required fields
            config = self.find_table_config(table_name)
            if config:
                required_fields = config.get('required_fields', [])
                missing_fields = [f for f in required_fields if f not in df.columns]

                if missing_fields:
                    test_results['tests']['required_fields'] = {
                        'status': 'FAILED',
                        'missing': missing_fields
                    }
                    test_results['failed'] += 1
                else:
                    test_results['tests']['required_fields'] = {'status': 'PASSED'}
                    test_results['passed'] += 1

            # Test 2: Check for nulls in critical fields
            null_counts = df.isnull().sum()
            critical_nulls = null_counts[null_counts > len(df) * 0.1]  # More than 10% null

            if not critical_nulls.empty:
                test_results['tests']['null_values'] = {
                    'status': 'WARNING',
                    'fields_with_nulls': critical_nulls.to_dict()
                }
                test_results['warnings'] += 1
            else:
                test_results['tests']['null_values'] = {'status': 'PASSED'}
                test_results['passed'] += 1

            # Test 3: Check for duplicates
            if 'parcel_id' in df.columns:
                duplicate_count = df['parcel_id'].duplicated().sum()
                if duplicate_count > 0:
                    test_results['tests']['duplicates'] = {
                        'status': 'WARNING',
                        'duplicate_count': int(duplicate_count)
                    }
                    test_results['warnings'] += 1
                else:
                    test_results['tests']['duplicates'] = {'status': 'PASSED'}
                    test_results['passed'] += 1

            # Test 4: Validate data types and patterns
            if config and 'validation_rules' in config:
                for field, rules in config['validation_rules'].items():
                    if field in df.columns:
                        validation_result = self.validate_field(df[field], rules)
                        test_results['tests'][f'validate_{field}'] = validation_result

                        if validation_result['status'] == 'PASSED':
                            test_results['passed'] += 1
                        elif validation_result['status'] == 'WARNING':
                            test_results['warnings'] += 1
                        else:
                            test_results['failed'] += 1

            # Test 5: Check data freshness
            if 'created_at' in df.columns:
                latest_date = pd.to_datetime(df['created_at']).max()
                days_old = (datetime.now() - latest_date).days

                if days_old > 30:
                    test_results['tests']['data_freshness'] = {
                        'status': 'WARNING',
                        'days_old': days_old
                    }
                    test_results['warnings'] += 1
                else:
                    test_results['tests']['data_freshness'] = {
                        'status': 'PASSED',
                        'days_old': days_old
                    }
                    test_results['passed'] += 1

        except Exception as e:
            test_results['tests']['error'] = {
                'status': 'FAILED',
                'message': str(e)
            }
            test_results['failed'] += 1

        return test_results

    def find_table_config(self, table_name: str) -> Optional[Dict]:
        """Find configuration for a table"""
        for config_name, config in self.test_configs.items():
            if table_name in config['tables']:
                return config
        return None

    def validate_field(self, series: pd.Series, rules: Dict) -> Dict[str, Any]:
        """Validate a field against rules"""
        result = {'status': 'PASSED', 'details': {}}

        try:
            if rules['type'] == 'string':
                # Check pattern if specified
                if 'pattern' in rules:
                    import re
                    pattern = rules['pattern']
                    non_matching = series.dropna().apply(
                        lambda x: not bool(re.match(pattern, str(x)))
                    ).sum()

                    if non_matching > 0:
                        result['status'] = 'WARNING'
                        result['details']['non_matching_pattern'] = int(non_matching)

                # Check allowed values if specified
                if 'values' in rules:
                    invalid = ~series.dropna().isin(rules['values'])
                    if invalid.sum() > 0:
                        result['status'] = 'WARNING'
                        result['details']['invalid_values'] = int(invalid.sum())

            elif rules['type'] == 'numeric':
                # Convert to numeric
                numeric_series = pd.to_numeric(series, errors='coerce')

                # Check min value
                if 'min' in rules:
                    below_min = (numeric_series < rules['min']).sum()
                    if below_min > 0:
                        result['status'] = 'WARNING'
                        result['details']['below_min'] = int(below_min)

                # Check max value
                if 'max' in rules:
                    above_max = (numeric_series > rules['max']).sum()
                    if above_max > 0:
                        result['status'] = 'WARNING'
                        result['details']['above_max'] = int(above_max)

        except Exception as e:
            result['status'] = 'FAILED'
            result['details']['error'] = str(e)

        return result

    async def test_data_relationships(self) -> Dict[str, Any]:
        """Test relationships between tables"""
        logger.info("Testing data relationships between tables")

        relationship_tests = {
            'timestamp': datetime.now().isoformat(),
            'relationships': {},
            'orphaned_records': {}
        }

        # Test 1: Florida parcels to NAV assessments relationship
        try:
            parcels = self.supabase.table('florida_parcels').select('parcel_id').limit(100).execute()
            parcel_ids = [p['parcel_id'] for p in parcels.data]

            nav = self.supabase.table('nav_assessments').select('parcel_id').in_('parcel_id', parcel_ids).execute()
            nav_parcel_ids = [n['parcel_id'] for n in nav.data]

            missing_in_nav = set(parcel_ids) - set(nav_parcel_ids)

            relationship_tests['relationships']['parcels_to_nav'] = {
                'total_parcels': len(parcel_ids),
                'found_in_nav': len(nav_parcel_ids),
                'missing_in_nav': len(missing_in_nav),
                'coverage': len(nav_parcel_ids) / len(parcel_ids) if parcel_ids else 0
            }

        except Exception as e:
            relationship_tests['relationships']['parcels_to_nav'] = {'error': str(e)}

        # Test 2: Tax deed sales to florida parcels relationship
        try:
            tax_deeds = self.supabase.table('tax_deed_sales').select('parcel_id').limit(100).execute()
            td_parcel_ids = [td['parcel_id'] for td in tax_deeds.data if td.get('parcel_id')]

            parcels = self.supabase.table('florida_parcels').select('parcel_id').in_('parcel_id', td_parcel_ids).execute()
            found_parcel_ids = [p['parcel_id'] for p in parcels.data]

            orphaned_tax_deeds = set(td_parcel_ids) - set(found_parcel_ids)

            relationship_tests['relationships']['tax_deed_to_parcels'] = {
                'total_tax_deeds': len(td_parcel_ids),
                'found_parcels': len(found_parcel_ids),
                'orphaned': len(orphaned_tax_deeds),
                'coverage': len(found_parcel_ids) / len(td_parcel_ids) if td_parcel_ids else 0
            }

            if orphaned_tax_deeds:
                relationship_tests['orphaned_records']['tax_deeds'] = list(orphaned_tax_deeds)[:10]

        except Exception as e:
            relationship_tests['relationships']['tax_deed_to_parcels'] = {'error': str(e)}

        return relationship_tests

    async def test_api_endpoints(self) -> Dict[str, Any]:
        """Test API endpoints for data retrieval"""
        logger.info("Testing API endpoints")

        api_tests = {
            'timestamp': datetime.now().isoformat(),
            'endpoints': {},
            'response_times': []
        }

        endpoints_to_test = [
            {'url': 'http://localhost:8000/api/properties', 'method': 'GET'},
            {'url': 'http://localhost:8000/api/property/064210010010', 'method': 'GET'},
            {'url': 'http://localhost:3005/api/supabase/florida_parcels', 'method': 'GET',
             'headers': {'x-api-key': os.getenv('MCP_API_KEY', 'concordbroker-mcp-key-claude')}},
        ]

        for endpoint in endpoints_to_test:
            start_time = datetime.now()

            try:
                response = requests.request(
                    endpoint['method'],
                    endpoint['url'],
                    headers=endpoint.get('headers', {}),
                    timeout=10
                )

                response_time = (datetime.now() - start_time).total_seconds()
                api_tests['response_times'].append(response_time)

                api_tests['endpoints'][endpoint['url']] = {
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code == 200,
                    'data_received': len(response.json()) if response.status_code == 200 else 0
                }

            except Exception as e:
                api_tests['endpoints'][endpoint['url']] = {
                    'error': str(e),
                    'success': False
                }

        # Calculate average response time
        if api_tests['response_times']:
            api_tests['avg_response_time'] = np.mean(api_tests['response_times'])
            api_tests['max_response_time'] = max(api_tests['response_times'])

        return api_tests

    def create_test_summary_dashboard(self, all_results: Dict[str, Any]):
        """Create visual dashboard of test results"""
        fig = plt.figure(figsize=(20, 12))

        # Overall summary
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # Test Status Overview
        ax1 = fig.add_subplot(gs[0, :])
        status_data = {
            'Passed': all_results['summary']['total_passed'],
            'Failed': all_results['summary']['total_failed'],
            'Warnings': all_results['summary']['total_warnings']
        }

        colors = ['green', 'red', 'orange']
        bars = ax1.bar(status_data.keys(), status_data.values(), color=colors)
        ax1.set_title('Overall Test Results', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Number of Tests')

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontsize=12)

        # Data Completeness by Table
        ax2 = fig.add_subplot(gs[1, 0])
        if 'data_completeness' in all_results:
            completeness_data = all_results['data_completeness']
            tables = list(completeness_data.keys())[:10]
            values = [completeness_data[t]['overall_completeness'] for t in tables]

            ax2.barh(tables, values, color='skyblue')
            ax2.set_xlabel('Completeness %')
            ax2.set_title('Data Completeness by Table')
            ax2.set_xlim(0, 1)

            # Add percentage labels
            for i, v in enumerate(values):
                ax2.text(v + 0.01, i, f'{v:.0%}', va='center')

        # Relationship Coverage
        ax3 = fig.add_subplot(gs[1, 1])
        if 'relationship_tests' in all_results:
            relationships = all_results['relationship_tests']['relationships']
            rel_names = []
            coverages = []

            for rel_name, rel_data in relationships.items():
                if 'coverage' in rel_data:
                    rel_names.append(rel_name.replace('_', ' ').title())
                    coverages.append(rel_data['coverage'])

            if rel_names:
                ax3.pie(coverages, labels=rel_names, autopct='%1.1f%%',
                       startangle=90, colors=sns.color_palette('husl', len(rel_names)))
                ax3.set_title('Data Relationship Coverage')

        # API Response Times
        ax4 = fig.add_subplot(gs[1, 2])
        if 'api_tests' in all_results:
            api_data = all_results['api_tests']
            if 'response_times' in api_data and api_data['response_times']:
                ax4.hist(api_data['response_times'], bins=10, color='purple', alpha=0.7, edgecolor='black')
                ax4.set_xlabel('Response Time (seconds)')
                ax4.set_ylabel('Frequency')
                ax4.set_title('API Response Time Distribution')
                ax4.axvline(api_data.get('avg_response_time', 0), color='red',
                          linestyle='--', label=f"Avg: {api_data.get('avg_response_time', 0):.2f}s")
                ax4.legend()

        # Test Timeline
        ax5 = fig.add_subplot(gs[2, :])
        if 'test_timeline' in all_results:
            timeline = all_results['test_timeline']
            times = [t['timestamp'] for t in timeline]
            durations = [t['duration'] for t in timeline]

            ax5.plot(times, durations, marker='o', linestyle='-', color='teal')
            ax5.set_xlabel('Test Execution Order')
            ax5.set_ylabel('Duration (seconds)')
            ax5.set_title('Test Execution Timeline')
            ax5.grid(True, alpha=0.3)

            # Rotate x-axis labels
            plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45, ha='right')

        # Add overall summary text
        fig.text(0.5, 0.02, f"Test Suite Executed: {all_results['timestamp']} | Total Tests: {all_results['summary']['total_tests']} | Success Rate: {all_results['summary']['success_rate']:.1%}",
                ha='center', fontsize=12, fontweight='bold')

        plt.suptitle('ConcordBroker Data Verification Test Results', fontsize=18, fontweight='bold')

        # Save dashboard
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dashboard_path = self.results_dir / f'test_dashboard_{timestamp}.png'
        plt.savefig(dashboard_path, dpi=150, bbox_inches='tight')
        plt.close()

        return str(dashboard_path)

    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run the complete test suite"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}STARTING AUTOMATED DATA VERIFICATION SUITE")
        print(f"{Fore.CYAN}{'='*60}\n")

        all_results = {
            'timestamp': datetime.now().isoformat(),
            'test_timeline': [],
            'summary': {
                'total_tests': 0,
                'total_passed': 0,
                'total_failed': 0,
                'total_warnings': 0,
                'success_rate': 0
            }
        }

        # 1. Test Data Integrity
        print(f"\n{Fore.YELLOW}[1/5] Testing Data Integrity...")
        print(f"{Fore.YELLOW}{'-'*40}")

        integrity_results = {}
        tables_to_test = ['florida_parcels', 'nav_assessments', 'tax_deed_sales', 'sunbiz_entities']

        for table in tables_to_test:
            start_time = datetime.now()
            result = await self.test_data_integrity(table)
            duration = (datetime.now() - start_time).total_seconds()

            integrity_results[table] = result
            all_results['summary']['total_tests'] += len(result['tests'])
            all_results['summary']['total_passed'] += result['passed']
            all_results['summary']['total_failed'] += result['failed']
            all_results['summary']['total_warnings'] += result['warnings']

            all_results['test_timeline'].append({
                'test': f'integrity_{table}',
                'timestamp': datetime.now().isoformat(),
                'duration': duration
            })

            # Print results
            status_color = Fore.GREEN if result['failed'] == 0 else Fore.RED
            print(f"  {status_color}✓ {table}: {result['passed']} passed, {result['failed']} failed, {result['warnings']} warnings")

        all_results['integrity_tests'] = integrity_results

        # 2. Test Data Completeness
        print(f"\n{Fore.YELLOW}[2/5] Testing Data Completeness...")
        print(f"{Fore.YELLOW}{'-'*40}")

        start_time = datetime.now()
        completeness_data = await self.data_mapper.analyze_data_completeness()
        duration = (datetime.now() - start_time).total_seconds()

        all_results['data_completeness'] = completeness_data
        all_results['test_timeline'].append({
            'test': 'data_completeness',
            'timestamp': datetime.now().isoformat(),
            'duration': duration
        })

        for tab_name, tab_data in completeness_data.items():
            completeness = tab_data['overall_completeness']
            status_color = Fore.GREEN if completeness > 0.8 else Fore.YELLOW if completeness > 0.5 else Fore.RED
            print(f"  {status_color}✓ {tab_name}: {completeness:.1%} complete")

        # 3. Test Data Relationships
        print(f"\n{Fore.YELLOW}[3/5] Testing Data Relationships...")
        print(f"{Fore.YELLOW}{'-'*40}")

        start_time = datetime.now()
        relationship_results = await self.test_data_relationships()
        duration = (datetime.now() - start_time).total_seconds()

        all_results['relationship_tests'] = relationship_results
        all_results['test_timeline'].append({
            'test': 'relationships',
            'timestamp': datetime.now().isoformat(),
            'duration': duration
        })

        for rel_name, rel_data in relationship_results['relationships'].items():
            if 'coverage' in rel_data:
                coverage = rel_data['coverage']
                status_color = Fore.GREEN if coverage > 0.8 else Fore.YELLOW if coverage > 0.5 else Fore.RED
                print(f"  {status_color}✓ {rel_name}: {coverage:.1%} coverage")

        # 4. Test API Endpoints
        print(f"\n{Fore.YELLOW}[4/5] Testing API Endpoints...")
        print(f"{Fore.YELLOW}{'-'*40}")

        start_time = datetime.now()
        api_results = await self.test_api_endpoints()
        duration = (datetime.now() - start_time).total_seconds()

        all_results['api_tests'] = api_results
        all_results['test_timeline'].append({
            'test': 'api_endpoints',
            'timestamp': datetime.now().isoformat(),
            'duration': duration
        })

        for endpoint, result in api_results['endpoints'].items():
            if result.get('success'):
                print(f"  {Fore.GREEN}✓ {endpoint}: {result.get('response_time', 0):.2f}s")
            else:
                print(f"  {Fore.RED}✗ {endpoint}: {result.get('error', 'Failed')}")

        # 5. Visual Verification (optional sample)
        print(f"\n{Fore.YELLOW}[5/5] Running Visual Verification Sample...")
        print(f"{Fore.YELLOW}{'-'*40}")

        # Run visual verification on a sample property
        sample_parcel = '064210010010'
        try:
            start_time = datetime.now()
            visual_result = await self.visual_verifier.run_visual_verification(
                sample_parcel,
                {'overview': {'parcel_id': sample_parcel}}
            )
            duration = (datetime.now() - start_time).total_seconds()

            all_results['visual_verification_sample'] = visual_result
            all_results['test_timeline'].append({
                'test': 'visual_verification',
                'timestamp': datetime.now().isoformat(),
                'duration': duration
            })

            score = visual_result.get('overall_score', 0)
            status_color = Fore.GREEN if score > 0.8 else Fore.YELLOW if score > 0.5 else Fore.RED
            print(f"  {status_color}✓ Visual Verification Score: {score:.1%}")

        except Exception as e:
            print(f"  {Fore.YELLOW}⚠ Visual verification skipped: {str(e)}")

        # Calculate overall success rate
        total = all_results['summary']['total_tests']
        if total > 0:
            all_results['summary']['success_rate'] = all_results['summary']['total_passed'] / total

        # Create visualizations
        print(f"\n{Fore.CYAN}Creating Test Summary Dashboard...")
        dashboard_path = self.create_test_summary_dashboard(all_results)
        print(f"  {Fore.GREEN}✓ Dashboard saved: {dashboard_path}")

        # Generate detailed report
        print(f"\n{Fore.CYAN}Generating Detailed Report...")
        report_path = self.generate_detailed_report(all_results)
        print(f"  {Fore.GREEN}✓ Report saved: {report_path}")

        # Save complete results
        results_path = self.results_dir / f'complete_test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(results_path, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)

        # Print summary
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TEST SUITE COMPLETED")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"\n{Fore.WHITE}SUMMARY:")
        print(f"  Total Tests: {all_results['summary']['total_tests']}")
        print(f"  {Fore.GREEN}Passed: {all_results['summary']['total_passed']}")
        print(f"  {Fore.RED}Failed: {all_results['summary']['total_failed']}")
        print(f"  {Fore.YELLOW}Warnings: {all_results['summary']['total_warnings']}")
        print(f"  {Fore.CYAN}Success Rate: {all_results['summary']['success_rate']:.1%}")
        print(f"\n{Fore.WHITE}Results saved to: {results_path}")

        return all_results

    def generate_detailed_report(self, all_results: Dict[str, Any]) -> str:
        """Generate detailed text report of all test results"""
        report_lines = [
            "=" * 80,
            "CONCORDBROKER DATA VERIFICATION SUITE - DETAILED REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            "",
            "EXECUTIVE SUMMARY",
            "-" * 40,
            f"Total Tests Executed: {all_results['summary']['total_tests']}",
            f"Tests Passed: {all_results['summary']['total_passed']}",
            f"Tests Failed: {all_results['summary']['total_failed']}",
            f"Warnings: {all_results['summary']['total_warnings']}",
            f"Overall Success Rate: {all_results['summary']['success_rate']:.1%}",
            "",
            "=" * 80,
            ""
        ]

        # Data Integrity Section
        if 'integrity_tests' in all_results:
            report_lines.extend([
                "DATA INTEGRITY TESTS",
                "-" * 40,
                ""
            ])

            for table, results in all_results['integrity_tests'].items():
                report_lines.append(f"Table: {table}")
                report_lines.append(f"  Status: {results['passed']} passed, {results['failed']} failed, {results['warnings']} warnings")

                for test_name, test_result in results['tests'].items():
                    status = test_result.get('status', 'UNKNOWN')
                    icon = "✓" if status == "PASSED" else "✗" if status == "FAILED" else "⚠"
                    report_lines.append(f"    {icon} {test_name}: {status}")

                    if 'details' in test_result:
                        for key, value in test_result['details'].items():
                            report_lines.append(f"      - {key}: {value}")

                report_lines.append("")

        # Data Completeness Section
        if 'data_completeness' in all_results:
            report_lines.extend([
                "DATA COMPLETENESS ANALYSIS",
                "-" * 40,
                ""
            ])

            for tab_name, tab_data in all_results['data_completeness'].items():
                completeness = tab_data['overall_completeness']
                status = "✓" if completeness > 0.8 else "⚠" if completeness > 0.5 else "✗"
                report_lines.append(f"{status} {tab_name.upper()}: {completeness:.1%} complete")

                if tab_data.get('missing_fields'):
                    report_lines.append(f"  Missing fields: {', '.join(tab_data['missing_fields'][:5])}")

                report_lines.append("")

        # Relationship Tests Section
        if 'relationship_tests' in all_results:
            report_lines.extend([
                "DATA RELATIONSHIP TESTS",
                "-" * 40,
                ""
            ])

            for rel_name, rel_data in all_results['relationship_tests']['relationships'].items():
                if 'error' not in rel_data:
                    coverage = rel_data.get('coverage', 0)
                    status = "✓" if coverage > 0.8 else "⚠" if coverage > 0.5 else "✗"
                    report_lines.append(f"{status} {rel_name}:")
                    report_lines.append(f"  Coverage: {coverage:.1%}")

                    if 'total_parcels' in rel_data:
                        report_lines.append(f"  Total records: {rel_data['total_parcels']}")
                        report_lines.append(f"  Found matches: {rel_data.get('found_in_nav', 0)}")
                        report_lines.append(f"  Missing: {rel_data.get('missing_in_nav', 0)}")
                else:
                    report_lines.append(f"✗ {rel_name}: ERROR - {rel_data['error']}")

                report_lines.append("")

        # API Tests Section
        if 'api_tests' in all_results:
            report_lines.extend([
                "API ENDPOINT TESTS",
                "-" * 40,
                ""
            ])

            for endpoint, result in all_results['api_tests']['endpoints'].items():
                if result.get('success'):
                    report_lines.append(f"✓ {endpoint}")
                    report_lines.append(f"  Response time: {result.get('response_time', 0):.2f}s")
                    report_lines.append(f"  Status code: {result.get('status_code')}")
                else:
                    report_lines.append(f"✗ {endpoint}")
                    report_lines.append(f"  Error: {result.get('error', 'Unknown error')}")

                report_lines.append("")

        # Recommendations
        report_lines.extend([
            "=" * 80,
            "",
            "RECOMMENDATIONS",
            "-" * 40,
            ""
        ])

        # Generate recommendations based on results
        if all_results['summary']['total_failed'] > 0:
            report_lines.append("CRITICAL ISSUES:")
            report_lines.append("  • Address failed tests immediately")
            report_lines.append("  • Review data integrity issues")
            report_lines.append("")

        if all_results['summary']['total_warnings'] > 10:
            report_lines.append("WARNINGS:")
            report_lines.append("  • High number of warnings detected")
            report_lines.append("  • Review data validation rules")
            report_lines.append("  • Consider data cleanup processes")
            report_lines.append("")

        # Performance recommendations
        if 'api_tests' in all_results and 'avg_response_time' in all_results['api_tests']:
            avg_time = all_results['api_tests']['avg_response_time']
            if avg_time > 2:
                report_lines.append("PERFORMANCE:")
                report_lines.append(f"  • API response times are slow (avg: {avg_time:.2f}s)")
                report_lines.append("  • Consider implementing caching")
                report_lines.append("  • Review database indexes")
                report_lines.append("")

        report_lines.extend([
            "=" * 80,
            "END OF REPORT"
        ])

        # Save report
        report_path = self.results_dir / f'detailed_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        report_content = "\n".join(report_lines)

        with open(report_path, 'w') as f:
            f.write(report_content)

        return str(report_path)


async def main():
    """Main execution function"""
    suite = AutomatedDataVerificationSuite()

    # Run complete test suite
    results = await suite.run_complete_test_suite()

    return results


if __name__ == "__main__":
    asyncio.run(main())