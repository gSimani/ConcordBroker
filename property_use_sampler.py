#!/usr/bin/env python3
"""
Property Use Sampler - Analyzes property uses from a sample of the database
Uses the existing production API to avoid database connection issues
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime
import time
from collections import Counter, defaultdict
from typing import Dict, List, Any

# Production API endpoints
PRODUCTION_API = "https://concordbroker-production.up.railway.app"
LOCAL_API = "http://localhost:3001"

class PropertyUseSampler:
    """Sample-based property use analyzer"""

    def __init__(self):
        self.api_base = PRODUCTION_API
        self.property_data = []
        self.property_uses = Counter()
        self.category_mappings = {}

        # Current filter categories
        self.current_categories = [
            "Residential", "Commercial", "Industrial", "Agricultural",
            "Vacant Land", "Government", "Conservation", "Religious",
            "Vacant/Special", "Tax Deed Sales"
        ]

        # Comprehensive mapping rules
        self.mapping_rules = {
            "Residential": [
                "SINGLE FAMILY", "CONDO", "MOBILE", "TOWNHOUSE", "DUPLEX",
                "APARTMENT", "RESIDENTIAL", "HOME", "HOUSE", "DWELLING",
                "MULTI FAMILY", "TRIPLEX", "FOURPLEX", "COOPERATIVE", "CONDOMINIUM"
            ],
            "Commercial": [
                "RETAIL", "OFFICE", "STORE", "SHOPPING", "COMMERCIAL", "BUSINESS",
                "RESTAURANT", "HOTEL", "MOTEL", "WAREHOUSE", "PARKING",
                "SERVICE", "BANK", "GAS STATION", "AUTO", "MIXED USE", "MALL"
            ],
            "Industrial": [
                "INDUSTRIAL", "MANUFACTURING", "FACTORY", "PLANT", "DISTRIBUTION",
                "PROCESSING", "PRODUCTION", "UTILITY", "MINING", "QUARRY", "MILL"
            ],
            "Agricultural": [
                "AGRICULTURAL", "FARM", "RANCH", "GROVE", "PASTURE", "CROP",
                "LIVESTOCK", "DAIRY", "POULTRY", "TIMBER", "ORCHARD", "VINEYARD", "BARN"
            ],
            "Vacant Land": [
                "VACANT", "UNDEVELOPED", "RAW LAND", "IMPROVED VACANT",
                "ACREAGE", "LOT", "UNIMPROVED", "LAND"
            ],
            "Government": [
                "GOVERNMENT", "PUBLIC", "MUNICIPAL", "COUNTY", "STATE", "FEDERAL",
                "SCHOOL", "LIBRARY", "FIRE", "POLICE", "MILITARY", "COURTHOUSE", "CITY"
            ],
            "Conservation": [
                "CONSERVATION", "PRESERVE", "ENVIRONMENTAL", "WETLAND",
                "NATURAL", "PARK", "RECREATION", "FOREST", "WILDLIFE", "NATURE"
            ],
            "Religious": [
                "CHURCH", "RELIGIOUS", "TEMPLE", "MOSQUE", "SYNAGOGUE",
                "MONASTERY", "CONVENT", "CHAPEL", "PARISH"
            ],
            "Infrastructure": [
                "ROAD", "BRIDGE", "CANAL", "DRAINAGE", "RIGHT OF WAY",
                "EASEMENT", "RAILROAD", "HIGHWAY", "PIPELINE", "STREET"
            ],
            "Institutional": [
                "HOSPITAL", "NURSING", "MEDICAL", "HEALTH", "CLINIC",
                "UNIVERSITY", "COLLEGE", "EDUCATIONAL", "INSTITUTIONAL"
            ],
            "Recreation": [
                "GOLF", "CLUB", "STADIUM", "ARENA", "THEATER", "ENTERTAINMENT",
                "SPORTS", "MARINA", "BEACH", "RESORT", "RECREATION"
            ],
            "Special Use": [
                "CEMETERY", "AIRPORT", "LANDFILL", "WASTE", "COMMUNICATION",
                "TOWER", "SUBSTATION", "FUNERAL", "CREMATORY"
            ],
            "Transportation": [
                "TRANSIT", "BUS", "TRAIN", "TRANSPORTATION", "PARKING",
                "GARAGE", "TERMINAL", "DEPOT"
            ]
        }

    def sample_properties_from_api(self, sample_size: int = 10000) -> List[Dict]:
        """Sample properties from the production API"""
        print(f"Sampling {sample_size} properties from production API...")

        properties = []
        page = 1
        per_page = 100

        while len(properties) < sample_size:
            try:
                url = f"{self.api_base}/api/properties"
                params = {
                    'page': page,
                    'per_page': per_page,
                    'include_property_use': 'true'
                }

                print(f"Fetching page {page}... ({len(properties)} properties so far)")
                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    page_properties = data.get('properties', [])

                    if not page_properties:
                        print("No more properties found")
                        break

                    # Filter for properties with property_use
                    valid_properties = [
                        p for p in page_properties
                        if p.get('property_use') and p.get('property_use').strip()
                    ]

                    properties.extend(valid_properties)
                    page += 1

                    # Respect rate limits
                    time.sleep(0.1)

                else:
                    print(f"API error: {response.status_code}")
                    break

            except Exception as e:
                print(f"Error fetching page {page}: {e}")
                time.sleep(1)
                continue

        print(f"Collected {len(properties)} properties with property_use data")
        return properties[:sample_size]

    def analyze_property_uses(self, properties: List[Dict]) -> Dict[str, Any]:
        """Analyze property uses from the sample"""
        print("Analyzing property uses...")

        # Count property uses
        for prop in properties:
            use = prop.get('property_use', '').strip()
            if use:
                self.property_uses[use] += 1

        print(f"Found {len(self.property_uses)} unique property use types")

        # Create analysis
        total_properties = len(properties)
        use_analysis = []

        for use, count in self.property_uses.most_common():
            percentage = (count / total_properties) * 100
            use_analysis.append({
                'property_use': use,
                'count': count,
                'percentage': round(percentage, 4),
                'sample_size': total_properties
            })

        return {
            'total_sample_size': total_properties,
            'unique_uses': len(self.property_uses),
            'use_analysis': use_analysis
        }

    def create_category_mappings(self, use_analysis: List[Dict]) -> Dict[str, Any]:
        """Map property uses to categories"""
        print("Creating category mappings...")

        category_mappings = {}
        matched_uses = set()
        total_sample = sum(item['count'] for item in use_analysis)

        for category, keywords in self.mapping_rules.items():
            category_uses = []
            category_count = 0

            for item in use_analysis:
                use = item['property_use'].upper()
                if any(keyword in use for keyword in keywords):
                    category_uses.append(item['property_use'])
                    category_count += item['count']
                    matched_uses.add(item['property_use'])

            if category_uses:
                percentage = (category_count / total_sample) * 100
                category_mappings[category] = {
                    'uses': category_uses,
                    'count': category_count,
                    'percentage': round(percentage, 4),
                    'unique_uses': len(category_uses)
                }

        # Find unmatched uses
        unmatched_uses = []
        for item in use_analysis:
            if item['property_use'] not in matched_uses:
                unmatched_uses.append(item)

        return {
            'category_mappings': category_mappings,
            'unmatched_uses': unmatched_uses,
            'mapping_stats': {
                'mapped_uses': len(matched_uses),
                'total_uses': len(use_analysis),
                'mapped_percentage': round((len(matched_uses) / len(use_analysis)) * 100, 2),
                'mapped_properties': sum(data['count'] for data in category_mappings.values()),
                'total_properties': total_sample,
                'coverage_percentage': round((sum(data['count'] for data in category_mappings.values()) / total_sample) * 100, 2)
            }
        }

    def generate_recommendations(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations for filter improvements"""
        unmatched_uses = category_data['unmatched_uses']
        category_mappings = category_data['category_mappings']

        # High-volume unmatched uses
        high_volume_unmatched = [
            use for use in unmatched_uses
            if use['count'] >= 10  # At least 10 in sample
        ]

        # Missing categories
        current_filter_categories = set(self.current_categories)
        identified_categories = set(category_mappings.keys())
        missing_categories = identified_categories - current_filter_categories

        recommendations = {
            "missing_filter_categories": [
                {
                    "category": category,
                    "count": category_mappings[category]['count'],
                    "percentage": category_mappings[category]['percentage'],
                    "justification": f"Represents {category_mappings[category]['percentage']:.2f}% of sample"
                }
                for category in missing_categories
            ],
            "high_volume_unmatched": sorted(high_volume_unmatched, key=lambda x: x['count'], reverse=True)[:20],
            "current_vs_identified": {
                "current_categories": self.current_categories,
                "identified_categories": list(identified_categories),
                "missing_from_filters": list(missing_categories)
            }
        }

        return recommendations

    def run_analysis(self, sample_size: int = 10000) -> Dict[str, Any]:
        """Run complete analysis"""
        print("Starting comprehensive property use analysis from sample...")
        start_time = datetime.now()

        # Sample properties
        properties = self.sample_properties_from_api(sample_size)

        if not properties:
            print("Failed to collect any properties")
            return {}

        # Analyze uses
        use_data = self.analyze_property_uses(properties)

        # Create mappings
        category_data = self.create_category_mappings(use_data['use_analysis'])

        # Generate recommendations
        recommendations = self.generate_recommendations(category_data)

        # Create final report
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        report = {
            "analysis_metadata": {
                "timestamp": end_time.isoformat(),
                "sample_size": len(properties),
                "unique_property_uses": use_data['unique_uses'],
                "analysis_duration_seconds": duration,
                "data_source": "Production API Sample"
            },
            "property_use_analysis": use_data,
            "category_mappings": category_data,
            "recommendations": recommendations,
            "summary": {
                "total_categories_identified": len(category_data['category_mappings']),
                "mapping_coverage": category_data['mapping_stats']['coverage_percentage'],
                "missing_filter_categories": len(recommendations['missing_filter_categories']),
                "high_volume_unmatched": len(recommendations['high_volume_unmatched'])
            }
        }

        return report

    def save_report(self, report: Dict[str, Any]) -> str:
        """Save analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"property_use_analysis_sample_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"Report saved to: {filename}")
        return filename

    def print_summary(self, report: Dict[str, Any]):
        """Print analysis summary"""
        metadata = report['analysis_metadata']
        mappings = report['category_mappings']['category_mappings']
        recommendations = report['recommendations']
        summary = report['summary']

        print("\n" + "="*80)
        print("PROPERTY USE ANALYSIS SUMMARY (SAMPLE-BASED)")
        print("="*80)
        print(f"Sample Size: {metadata['sample_size']:,} properties")
        print(f"Unique Property Uses: {metadata['unique_property_uses']:,}")
        print(f"Analysis Duration: {metadata['analysis_duration_seconds']:.1f} seconds")
        print(f"Categories Identified: {summary['total_categories_identified']}")
        print(f"Mapping Coverage: {summary['mapping_coverage']:.1f}% of properties")

        print(f"\nCATEGORY BREAKDOWN:")
        for category, data in sorted(mappings.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"  {category:<20} {data['count']:>6} props ({data['percentage']:>6.2f}%) - {data['unique_uses']:>3} use types")

        print(f"\nCURRENT FILTER CATEGORIES:")
        for i, cat in enumerate(self.current_categories, 1):
            print(f"  {i:2d}. {cat}")

        if recommendations['missing_filter_categories']:
            print(f"\nRECOMMENDED NEW FILTER CATEGORIES:")
            for i, rec in enumerate(recommendations['missing_filter_categories'], 1):
                print(f"  {i:2d}. {rec['category']} ({rec['count']} props, {rec['percentage']:.2f}%)")

        if recommendations['high_volume_unmatched']:
            print(f"\nHIGH-VOLUME UNMATCHED USES (Top 10):")
            for i, use in enumerate(recommendations['high_volume_unmatched'][:10], 1):
                print(f"  {i:2d}. {use['property_use']:<40} {use['count']:>6} props ({use['percentage']:>6.2f}%)")

        print("="*80)

def main():
    """Main execution"""
    sampler = PropertyUseSampler()

    # Run analysis with 10,000 property sample
    report = sampler.run_analysis(sample_size=10000)

    if report:
        # Save report
        filename = sampler.save_report(report)

        # Print summary
        sampler.print_summary(report)

        print(f"\nComplete analysis saved to: {filename}")
        return report
    else:
        print("Analysis failed - no data collected")
        return None

if __name__ == "__main__":
    main()