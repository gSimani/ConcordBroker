"""
Comprehensive Data Mapper and Visualizer for ConcordBroker
Maps database fields to UI components and verifies data accuracy
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv
import cv2
import base64
from io import BytesIO
from PIL import Image
import requests

# Configure matplotlib and seaborn
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

load_dotenv('.env.mcp')

class ComprehensiveDataMapper:
    """Maps and verifies data flow from database to UI components"""

    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # UI Tab to Database Table Mapping
        self.tab_mappings = {
            'overview': {
                'tables': ['florida_parcels', 'nav_assessments'],
                'fields': {
                    'property_address': ['phy_addr1', 'phy_addr2', 'phy_city', 'phy_zip'],
                    'owner_name': ['own_name'],
                    'parcel_id': ['parcel_id'],
                    'land_sqft': ['land_sqft'],
                    'building_sqft': ['tot_sqft'],
                    'year_built': ['year_built'],
                    'just_value': ['just_value'],
                    'assessed_value': ['av_nsd'],
                    'taxable_value': ['txbl_val'],
                    'property_use': ['dor_uc', 'pa_uc'],
                    'bedrooms': ['bedrooms'],
                    'bathrooms': ['bathrooms'],
                    'pool': ['pool'],
                    'neighborhood': ['nbhd_code']
                }
            },
            'ownership': {
                'tables': ['florida_parcels', 'sunbiz_entities'],
                'fields': {
                    'owner_name': ['own_name'],
                    'owner_address': ['owner_addr1', 'owner_addr2', 'owner_city', 'owner_state', 'owner_zip'],
                    'mailing_address': ['mail_addr1', 'mail_addr2', 'mail_city', 'mail_state', 'mail_zipcode'],
                    'entity_name': ['entity_name'],
                    'entity_status': ['status'],
                    'entity_type': ['entity_type'],
                    'incorporation_date': ['file_date'],
                    'principal_address': ['principal_addr1', 'principal_addr2'],
                    'registered_agent': ['agent_name'],
                    'officers': ['officer_data']
                }
            },
            'sales_history': {
                'tables': ['sdf_sales', 'sales_history'],
                'fields': {
                    'sale_date': ['sale_date', 'sale_yr', 'sale_mo'],
                    'sale_price': ['sale_price', 'vi_sale_price'],
                    'seller_name': ['seller_name', 'grantor'],
                    'buyer_name': ['buyer_name', 'grantee'],
                    'doc_number': ['doc_nbr', 'or_book', 'or_page'],
                    'qualification': ['qual_code', 'vi_code'],
                    'vacant_at_sale': ['vi_vacant'],
                    'sale_type': ['sl_type_1', 'sale_type']
                }
            },
            'tax_deed': {
                'tables': ['tax_deed_sales', 'tax_certificates'],
                'fields': {
                    'td_number': ['td_number'],
                    'auction_date': ['auction_date'],
                    'auction_status': ['auction_status'],
                    'certificate_year': ['certificate_year'],
                    'face_value': ['face_value'],
                    'winning_bid': ['winning_bid'],
                    'bidder_number': ['bidder_number'],
                    'redeemed': ['redeemed'],
                    'redeemed_date': ['redeemed_date'],
                    'certificate_holder': ['certificate_holder'],
                    'opening_bid': ['opening_bid'],
                    'sold_amount': ['sold_amount']
                }
            },
            'taxes': {
                'tables': ['nav_assessments', 'tax_bills'],
                'fields': {
                    'millage_rate': ['millage_rate'],
                    'tax_amount': ['tax_amount', 'tot_tax_amt'],
                    'exemptions': ['hmstd_exempt', 'widow_exempt', 'senior_exempt', 'veteran_exempt'],
                    'tax_year': ['tax_year'],
                    'school_assessed': ['sch_av_nsd'],
                    'school_taxable': ['sch_txbl_val'],
                    'non_school_assessed': ['av_nsd'],
                    'non_school_taxable': ['txbl_val'],
                    'special_assessments': ['spec_assessments']
                }
            },
            'permits': {
                'tables': ['building_permits'],
                'fields': {
                    'permit_number': ['permit_number'],
                    'permit_type': ['permit_type'],
                    'issue_date': ['issue_date'],
                    'status': ['status'],
                    'description': ['description'],
                    'contractor': ['contractor'],
                    'estimated_value': ['estimated_value'],
                    'completion_date': ['completion_date'],
                    'inspection_status': ['inspection_status']
                }
            },
            'sunbiz': {
                'tables': ['sunbiz_entities', 'sunbiz_officers', 'sunbiz_filings'],
                'fields': {
                    'entity_name': ['entity_name'],
                    'document_number': ['document_number'],
                    'status': ['status'],
                    'entity_type': ['entity_type'],
                    'officers': ['officer_name', 'officer_title', 'officer_address'],
                    'annual_reports': ['report_year', 'file_date'],
                    'registered_agent': ['agent_name', 'agent_address'],
                    'principal_address': ['principal_addr1', 'principal_addr2', 'principal_city', 'principal_state'],
                    'mailing_address': ['mail_addr1', 'mail_addr2', 'mail_city', 'mail_state']
                }
            },
            'analysis': {
                'tables': ['market_analysis', 'comparables', 'nav_assessments'],
                'fields': {
                    'market_value': ['just_value'],
                    'price_sqft': ['price_per_sqft'],
                    'roi_estimate': ['roi_estimate'],
                    'rental_estimate': ['rental_estimate'],
                    'cap_rate': ['cap_rate'],
                    'appreciation': ['appreciation_rate'],
                    'comparable_sales': ['comp_sales'],
                    'market_trend': ['trend_direction'],
                    'investment_score': ['investment_score']
                }
            }
        }

        self.visualization_dir = Path("data_mapping_visualizations")
        self.visualization_dir.mkdir(exist_ok=True)

    async def analyze_data_completeness(self) -> Dict[str, Any]:
        """Analyze data completeness across all tables and fields"""
        completeness_report = {}

        for tab_name, tab_config in self.tab_mappings.items():
            tab_report = {
                'tables': {},
                'overall_completeness': 0,
                'missing_fields': []
            }

            for table in tab_config['tables']:
                try:
                    # Sample data from table
                    result = self.supabase.table(table).select('*').limit(1000).execute()

                    if result.data:
                        df = pd.DataFrame(result.data)

                        # Calculate completeness for each field
                        field_completeness = {}
                        for ui_field, db_fields in tab_config['fields'].items():
                            field_coverage = []
                            for db_field in db_fields:
                                if db_field in df.columns:
                                    non_null_ratio = df[db_field].notna().mean()
                                    field_coverage.append(non_null_ratio)

                            if field_coverage:
                                field_completeness[ui_field] = np.mean(field_coverage)
                            else:
                                field_completeness[ui_field] = 0
                                tab_report['missing_fields'].append(f"{ui_field} (no db fields found)")

                        tab_report['tables'][table] = {
                            'record_count': len(df),
                            'field_completeness': field_completeness,
                            'avg_completeness': np.mean(list(field_completeness.values()))
                        }
                    else:
                        tab_report['tables'][table] = {
                            'record_count': 0,
                            'field_completeness': {},
                            'avg_completeness': 0
                        }

                except Exception as e:
                    tab_report['tables'][table] = {
                        'error': str(e),
                        'avg_completeness': 0
                    }

            # Calculate overall tab completeness
            completeness_values = [
                t.get('avg_completeness', 0)
                for t in tab_report['tables'].values()
            ]
            tab_report['overall_completeness'] = np.mean(completeness_values) if completeness_values else 0

            completeness_report[tab_name] = tab_report

        return completeness_report

    def create_completeness_heatmap(self, completeness_data: Dict[str, Any]):
        """Create a heatmap visualization of data completeness"""
        fig, axes = plt.subplots(3, 3, figsize=(20, 16))
        fig.suptitle('Data Completeness Heatmap by Tab and Field', fontsize=16, fontweight='bold')

        tab_names = list(self.tab_mappings.keys())

        for idx, (ax, tab_name) in enumerate(zip(axes.flat, tab_names)):
            if tab_name in completeness_data:
                tab_data = completeness_data[tab_name]

                # Prepare data for heatmap
                heatmap_data = []
                field_names = []

                for table_name, table_data in tab_data['tables'].items():
                    if 'field_completeness' in table_data:
                        for field, completeness in table_data['field_completeness'].items():
                            if field not in field_names:
                                field_names.append(field)

                        row = [table_data['field_completeness'].get(field, 0) for field in field_names]
                        heatmap_data.append(row)

                if heatmap_data:
                    # Create heatmap
                    sns.heatmap(
                        heatmap_data,
                        ax=ax,
                        annot=True,
                        fmt='.2f',
                        cmap='RdYlGn',
                        vmin=0,
                        vmax=1,
                        cbar_kws={'label': 'Completeness'},
                        xticklabels=field_names[:10],  # Limit to 10 fields for readability
                        yticklabels=list(tab_data['tables'].keys())
                    )
                    ax.set_title(f'{tab_name.upper()} Tab (Overall: {tab_data["overall_completeness"]:.2%})')
                    ax.set_xlabel('UI Fields')
                    ax.set_ylabel('Database Tables')

                    # Rotate x labels
                    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
                else:
                    ax.text(0.5, 0.5, f'No data for {tab_name}', ha='center', va='center')
                    ax.set_title(f'{tab_name.upper()} Tab')
            else:
                ax.axis('off')

        plt.tight_layout()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plt.savefig(self.visualization_dir / f'completeness_heatmap_{timestamp}.png', dpi=150)
        plt.close()

        return str(self.visualization_dir / f'completeness_heatmap_{timestamp}.png')

    def create_data_flow_diagram(self):
        """Create a visual diagram of data flow from database to UI"""
        fig, ax = plt.subplots(figsize=(16, 10))

        # Create Sankey-style diagram
        tab_positions = {}
        y_offset = 0.9

        for idx, (tab_name, tab_config) in enumerate(self.tab_mappings.items()):
            y_pos = y_offset - (idx * 0.12)
            tab_positions[tab_name] = y_pos

            # Draw tab box
            tab_box = plt.Rectangle((0.7, y_pos - 0.04), 0.25, 0.08,
                                   fill=True, facecolor='lightblue',
                                   edgecolor='navy', linewidth=2)
            ax.add_patch(tab_box)
            ax.text(0.825, y_pos, tab_name.upper(), ha='center', va='center',
                   fontweight='bold', fontsize=10)

            # Draw connections to tables
            table_x = 0.3
            table_y_start = y_pos + 0.03 * (len(tab_config['tables']) - 1)

            for tidx, table in enumerate(tab_config['tables']):
                table_y = table_y_start - (tidx * 0.06)

                # Draw table box
                table_box = plt.Rectangle((0.05, table_y - 0.025), 0.25, 0.05,
                                        fill=True, facecolor='lightgreen',
                                        edgecolor='darkgreen', linewidth=1)
                ax.add_patch(table_box)
                ax.text(0.175, table_y, table[:20], ha='center', va='center',
                       fontsize=8)

                # Draw arrow from table to tab
                ax.arrow(0.3, table_y, 0.38, y_pos - table_y,
                        head_width=0.015, head_length=0.02,
                        fc='gray', ec='gray', alpha=0.3)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_title('Data Flow: Database Tables → UI Tabs', fontsize=14, fontweight='bold')

        # Add legend
        ax.text(0.175, 0.02, 'DATABASE TABLES', ha='center', fontweight='bold',
               color='darkgreen', fontsize=10)
        ax.text(0.825, 0.02, 'UI TABS', ha='center', fontweight='bold',
               color='navy', fontsize=10)

        plt.tight_layout()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plt.savefig(self.visualization_dir / f'data_flow_diagram_{timestamp}.png', dpi=150)
        plt.close()

        return str(self.visualization_dir / f'data_flow_diagram_{timestamp}.png')

    def create_field_coverage_report(self, completeness_data: Dict[str, Any]):
        """Create detailed field coverage charts"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Field Coverage Analysis by Category', fontsize=14, fontweight='bold')

        # Group tabs by category
        categories = {
            'Property Info': ['overview', 'taxes', 'permits'],
            'Ownership': ['ownership', 'sunbiz'],
            'Transactions': ['sales_history', 'tax_deed'],
            'Analytics': ['analysis']
        }

        for idx, (ax, (category, tabs)) in enumerate(zip(axes.flat, categories.items())):
            coverage_data = []
            labels = []

            for tab in tabs:
                if tab in completeness_data:
                    coverage = completeness_data[tab]['overall_completeness']
                    coverage_data.append(coverage)
                    labels.append(tab.replace('_', ' ').title())

            if coverage_data:
                # Create bar chart
                bars = ax.bar(labels, coverage_data, color=sns.color_palette("husl", len(labels)))

                # Add value labels on bars
                for bar, value in zip(bars, coverage_data):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                           f'{value:.1%}', ha='center', va='bottom')

                ax.set_title(f'{category} Coverage')
                ax.set_ylabel('Completeness %')
                ax.set_ylim(0, 1.1)
                ax.axhline(y=0.8, color='green', linestyle='--', alpha=0.5, label='Target (80%)')
                ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='Minimum (50%)')
                ax.legend(loc='upper right')

                # Add grid
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, f'No data for {category}', ha='center', va='center')
                ax.set_title(category)

        plt.tight_layout()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plt.savefig(self.visualization_dir / f'field_coverage_report_{timestamp}.png', dpi=150)
        plt.close()

        return str(self.visualization_dir / f'field_coverage_report_{timestamp}.png')

    async def verify_sample_property(self, parcel_id: str) -> Dict[str, Any]:
        """Verify data mapping for a specific property"""
        verification_report = {
            'parcel_id': parcel_id,
            'timestamp': datetime.now().isoformat(),
            'tab_verification': {}
        }

        for tab_name, tab_config in self.tab_mappings.items():
            tab_data = {
                'found_fields': {},
                'missing_fields': [],
                'data_sources': {}
            }

            for table in tab_config['tables']:
                try:
                    # Query table for this parcel
                    result = self.supabase.table(table).select('*').eq('parcel_id', parcel_id).execute()

                    if result.data:
                        record = result.data[0]
                        tab_data['data_sources'][table] = True

                        # Check each field mapping
                        for ui_field, db_fields in tab_config['fields'].items():
                            for db_field in db_fields:
                                if db_field in record and record[db_field] is not None:
                                    if ui_field not in tab_data['found_fields']:
                                        tab_data['found_fields'][ui_field] = {}
                                    tab_data['found_fields'][ui_field][db_field] = record[db_field]
                    else:
                        tab_data['data_sources'][table] = False

                except Exception as e:
                    tab_data['data_sources'][table] = f"Error: {str(e)}"

            # Identify missing fields
            for ui_field in tab_config['fields'].keys():
                if ui_field not in tab_data['found_fields']:
                    tab_data['missing_fields'].append(ui_field)

            verification_report['tab_verification'][tab_name] = tab_data

        return verification_report

    def generate_mapping_report(self, completeness_data: Dict[str, Any],
                               sample_verification: Optional[Dict[str, Any]] = None) -> str:
        """Generate comprehensive mapping report"""
        report_lines = [
            "# COMPREHENSIVE DATA MAPPING REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            ""
        ]

        # Overall Summary
        report_lines.extend([
            "## OVERALL DATA COMPLETENESS SUMMARY",
            "-" * 40
        ])

        overall_completeness = []
        for tab_name, tab_data in completeness_data.items():
            completeness = tab_data['overall_completeness']
            overall_completeness.append(completeness)
            status = "✅" if completeness > 0.8 else "⚠️" if completeness > 0.5 else "❌"
            report_lines.append(f"{status} {tab_name.upper()}: {completeness:.1%}")

        avg_completeness = np.mean(overall_completeness)
        report_lines.extend([
            "",
            f"**OVERALL SYSTEM COMPLETENESS: {avg_completeness:.1%}**",
            "",
            "=" * 80,
            ""
        ])

        # Detailed Tab Analysis
        report_lines.extend([
            "## DETAILED TAB ANALYSIS",
            "-" * 40,
            ""
        ])

        for tab_name, tab_data in completeness_data.items():
            report_lines.extend([
                f"### {tab_name.upper()} TAB",
                f"Overall Completeness: {tab_data['overall_completeness']:.1%}",
                ""
            ])

            # Table details
            report_lines.append("**Database Tables:**")
            for table_name, table_data in tab_data['tables'].items():
                if 'error' not in table_data:
                    report_lines.append(f"  - {table_name}:")
                    report_lines.append(f"    - Records: {table_data.get('record_count', 0):,}")
                    report_lines.append(f"    - Avg Completeness: {table_data.get('avg_completeness', 0):.1%}")
                else:
                    report_lines.append(f"  - {table_name}: ERROR - {table_data['error']}")

            # Missing fields
            if tab_data.get('missing_fields'):
                report_lines.extend([
                    "",
                    "**Missing Fields:**"
                ])
                for field in tab_data['missing_fields']:
                    report_lines.append(f"  ⚠️ {field}")

            report_lines.extend(["", "-" * 40, ""])

        # Sample Verification
        if sample_verification:
            report_lines.extend([
                "## SAMPLE PROPERTY VERIFICATION",
                f"Parcel ID: {sample_verification['parcel_id']}",
                "-" * 40,
                ""
            ])

            for tab_name, tab_data in sample_verification['tab_verification'].items():
                found_count = len(tab_data['found_fields'])
                missing_count = len(tab_data['missing_fields'])
                total_count = found_count + missing_count

                report_lines.extend([
                    f"**{tab_name.upper()}**: {found_count}/{total_count} fields populated",
                    f"  Data Sources: {', '.join([k for k, v in tab_data['data_sources'].items() if v is True])}",
                    ""
                ])

        # Recommendations
        report_lines.extend([
            "=" * 80,
            "",
            "## RECOMMENDATIONS",
            "-" * 40
        ])

        critical_tabs = [tab for tab, data in completeness_data.items()
                        if data['overall_completeness'] < 0.5]
        warning_tabs = [tab for tab, data in completeness_data.items()
                       if 0.5 <= data['overall_completeness'] < 0.8]

        if critical_tabs:
            report_lines.extend([
                "",
                "**CRITICAL - Immediate Action Required:**"
            ])
            for tab in critical_tabs:
                report_lines.append(f"  ❌ {tab}: Requires data population")

        if warning_tabs:
            report_lines.extend([
                "",
                "**WARNING - Improvement Needed:**"
            ])
            for tab in warning_tabs:
                report_lines.append(f"  ⚠️ {tab}: Below target completeness")

        report_lines.extend([
            "",
            "=" * 80,
            "END OF REPORT"
        ])

        # Save report
        report_path = self.visualization_dir / f"mapping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_content = "\n".join(report_lines)

        with open(report_path, 'w') as f:
            f.write(report_content)

        return report_content

    async def run_complete_analysis(self, sample_parcel_id: Optional[str] = None):
        """Run complete data mapping analysis"""
        print("Starting comprehensive data mapping analysis...")

        # Analyze data completeness
        print("Analyzing data completeness across all tables...")
        completeness_data = await self.analyze_data_completeness()

        # Create visualizations
        print("Creating data visualizations...")
        heatmap_path = self.create_completeness_heatmap(completeness_data)
        print(f"  - Completeness heatmap saved: {heatmap_path}")

        flow_diagram_path = self.create_data_flow_diagram()
        print(f"  - Data flow diagram saved: {flow_diagram_path}")

        coverage_report_path = self.create_field_coverage_report(completeness_data)
        print(f"  - Field coverage report saved: {coverage_report_path}")

        # Verify sample property if provided
        sample_verification = None
        if sample_parcel_id:
            print(f"Verifying sample property: {sample_parcel_id}")
            sample_verification = await self.verify_sample_property(sample_parcel_id)

        # Generate report
        print("Generating comprehensive mapping report...")
        report = self.generate_mapping_report(completeness_data, sample_verification)

        # Save analysis results
        results = {
            'timestamp': datetime.now().isoformat(),
            'completeness_data': completeness_data,
            'sample_verification': sample_verification,
            'visualizations': {
                'heatmap': heatmap_path,
                'flow_diagram': flow_diagram_path,
                'coverage_report': coverage_report_path
            }
        }

        results_path = self.visualization_dir / f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\nAnalysis complete! Results saved to: {results_path}")
        print("\nSUMMARY:")
        print("-" * 40)

        overall_completeness = np.mean([d['overall_completeness'] for d in completeness_data.values()])
        print(f"Overall System Completeness: {overall_completeness:.1%}")

        return results


async def main():
    """Main execution function"""
    mapper = ComprehensiveDataMapper()

    # Run complete analysis with optional sample property
    # You can specify a real parcel_id from your database here
    sample_parcel_id = "064210010010"  # Example parcel ID

    results = await mapper.run_complete_analysis(sample_parcel_id)

    print("\n" + "=" * 60)
    print("DATA MAPPING ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Check the '{mapper.visualization_dir}' directory for:")
    print("  - Completeness heatmaps")
    print("  - Data flow diagrams")
    print("  - Field coverage reports")
    print("  - Detailed mapping report")


if __name__ == "__main__":
    asyncio.run(main())