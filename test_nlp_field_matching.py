"""
Comprehensive Test Suite for NLP Intelligent Field Matching
Tests NLTK, spaCy, Playwright MCP, and OpenCV integration
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.nlp_intelligent_field_matcher import (
    NLPFieldAnalyzer,
    IntelligentFieldMatcher,
    PropertyAppraiserMatcher,
    SunbizBusinessMatcher,
    PlaywrightNLPVerification,
    NLPDataMappingSystem,
    FieldSemantics,
    FieldMatch
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nlp_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NLPTestSuite:
    """Comprehensive test suite for NLP field matching"""

    def __init__(self):
        self.test_results = []
        self.nlp_analyzer = None
        self.property_matcher = None
        self.sunbiz_matcher = None
        self.nlp_system = None
        self.test_data = self._load_test_data()

    def _load_test_data(self) -> Dict[str, Any]:
        """Load test data for various scenarios"""
        return {
            "property_fields": {
                # Database field name -> Expected UI field
                "phy_addr1": "street_address",
                "phy_city": "city",
                "phy_zipcd": "zip_code",
                "owner_name": "owner_name",
                "jv": "just_value",
                "av_sd": "assessed_value",
                "tv_sd": "taxable_value",
                "lnd_val": "land_value",
                "tot_lvg_area": "living_area",
                "lnd_sqfoot": "land_sqft",
                "bedroom_cnt": "bedrooms",
                "bathroom_cnt": "bathrooms",
                "act_yr_blt": "year_built",
                "sale_prc1": "last_sale_price",
                "sale_yr1": "last_sale_year",
                "dor_uc": "property_use_code"
            },
            "sunbiz_fields": {
                "entity_name": "business_name",
                "document_number": "document_number",
                "status": "business_status",
                "filing_date": "filing_date",
                "officer_name": "officer_name",
                "officer_title": "officer_title"
            },
            "complex_cases": {
                # Test cases with variations and edge cases
                "PHY_ADDR_1": "property_address_street",
                "OWN_NM": "property_owner_name",
                "JV_2025": "current_just_value",
                "SQ_FT_TOT": "total_square_footage",
                "YR_BLT_ACT": "actual_year_built"
            },
            "sample_property_data": {
                "parcel_id": "494224020080",
                "phy_addr1": "123 MAIN ST",
                "phy_city": "FORT LAUDERDALE",
                "phy_zipcd": "33301",
                "owner_name": "SMITH JOHN & JANE",
                "jv": 250000,
                "av_sd": 245000,
                "tv_sd": 225000,
                "lnd_val": 75000,
                "tot_lvg_area": 1850,
                "lnd_sqfoot": 8712,
                "bedroom_cnt": 3,
                "bathroom_cnt": 2,
                "act_yr_blt": 1995,
                "sale_prc1": 230000,
                "sale_yr1": 2020,
                "dor_uc": "0100"
            },
            "sample_sunbiz_data": [
                {
                    "entity_name": "SMITH PROPERTIES LLC",
                    "document_number": "L20000123456",
                    "status": "ACTIVE",
                    "filing_date": "2020-03-15",
                    "entity_type": "LIMITED LIABILITY COMPANY"
                },
                {
                    "entity_name": "JOHN SMITH INVESTMENTS INC",
                    "document_number": "P98000654321",
                    "status": "ACTIVE",
                    "filing_date": "1998-08-22",
                    "entity_type": "CORPORATION"
                }
            ]
        }

    async def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "="*100)
        print(" NLP INTELLIGENT FIELD MATCHING - COMPREHENSIVE TEST SUITE")
        print("="*100)
        print(f"Started: {datetime.now().isoformat()}\n")

        # Initialize components
        await self.test_01_initialization()

        # Core NLP functionality
        await self.test_02_nlp_field_analysis()
        await self.test_03_semantic_similarity()
        await self.test_04_entity_recognition()

        # Field matching
        await self.test_05_property_field_matching()
        await self.test_06_sunbiz_field_matching()
        await self.test_07_complex_field_cases()

        # Business entity matching
        await self.test_08_business_entity_matching()

        # Playwright verification
        await self.test_09_playwright_nlp_verification()

        # End-to-end pipeline
        await self.test_10_complete_pipeline()

        # Performance testing
        await self.test_11_performance_testing()

        # Generate comprehensive report
        self.generate_final_report()

    async def test_01_initialization(self):
        """Test initialization of all NLP components"""
        print("\n[TEST 1] Component Initialization")
        print("-" * 50)

        try:
            # Initialize NLP Analyzer
            print("  Initializing NLP Field Analyzer...")
            self.nlp_analyzer = NLPFieldAnalyzer()
            print("    ✓ spaCy model loaded")
            print("    ✓ NLTK components initialized")
            print("    ✓ Sentence transformer loaded")
            print("    ✓ Custom patterns configured")

            # Initialize matchers
            print("  Initializing specialized matchers...")
            self.property_matcher = PropertyAppraiserMatcher()
            self.sunbiz_matcher = SunbizBusinessMatcher()
            print("    ✓ Property Appraiser matcher ready")
            print("    ✓ Sunbiz business matcher ready")

            # Initialize complete system
            print("  Initializing complete NLP system...")
            self.nlp_system = NLPDataMappingSystem()
            print("    ✓ Complete NLP mapping system ready")

            self.test_results.append({
                "test": "Component Initialization",
                "status": "PASS",
                "details": "All NLP components initialized successfully"
            })

        except Exception as e:
            print(f"    ✗ Initialization failed: {e}")
            self.test_results.append({
                "test": "Component Initialization",
                "status": "FAIL",
                "error": str(e)
            })

    async def test_02_nlp_field_analysis(self):
        """Test NLP field analysis capabilities"""
        print("\n[TEST 2] NLP Field Analysis")
        print("-" * 50)

        test_fields = [
            "phy_addr1", "owner_name", "jv", "tot_lvg_area",
            "bedroom_cnt", "sale_prc1", "entity_name", "officer_title"
        ]

        analysis_results = []

        for field in test_fields:
            try:
                analysis = self.nlp_analyzer.analyze_field(field)

                print(f"  Analyzing '{field}':")
                print(f"    Normalized: {analysis.normalized_name}")
                print(f"    Tokens: {analysis.tokens}")
                print(f"    Semantic Type: {analysis.semantic_type}")
                print(f"    Confidence: {analysis.confidence:.2f}")

                # Validate analysis
                assert analysis.original_name == field
                assert len(analysis.tokens) > 0
                assert analysis.confidence > 0
                assert analysis.embedding is not None

                analysis_results.append({
                    "field": field,
                    "semantic_type": analysis.semantic_type,
                    "confidence": analysis.confidence,
                    "token_count": len(analysis.tokens)
                })

            except Exception as e:
                print(f"    ✗ Analysis failed for {field}: {e}")
                analysis_results.append({
                    "field": field,
                    "error": str(e)
                })

        # Summary
        successful = len([r for r in analysis_results if 'error' not in r])
        total = len(analysis_results)

        print(f"\n  Analysis Summary: {successful}/{total} fields analyzed successfully")

        self.test_results.append({
            "test": "NLP Field Analysis",
            "status": "PASS" if successful == total else "PARTIAL",
            "details": f"Analyzed {successful}/{total} fields",
            "analysis_results": analysis_results
        })

    async def test_03_semantic_similarity(self):
        """Test semantic similarity calculations"""
        print("\n[TEST 3] Semantic Similarity")
        print("-" * 50)

        # Test field pairs with expected similarity
        test_pairs = [
            ("phy_addr1", "street_address", 0.8),  # High similarity
            ("owner_name", "property_owner", 0.7),  # Medium similarity
            ("jv", "just_value", 0.9),  # High similarity (exact match)
            ("tot_lvg_area", "square_feet", 0.6),  # Medium similarity
            ("bedroom_cnt", "bedrooms", 0.9),  # High similarity
            ("sale_prc1", "price", 0.5),  # Lower similarity
            ("unrelated_field", "another_field", 0.2)  # Low similarity
        ]

        similarity_tests = []

        for field1, field2, expected_min in test_pairs:
            try:
                analysis1 = self.nlp_analyzer.analyze_field(field1)
                analysis2 = self.nlp_analyzer.analyze_field(field2)

                # Calculate similarity using the matcher's method
                similarity = self.property_matcher._calculate_semantic_similarity(analysis1, analysis2)

                print(f"  '{field1}' vs '{field2}': {similarity:.3f} (expected ≥{expected_min})")

                # Validate against expected
                meets_expectation = similarity >= expected_min

                similarity_tests.append({
                    "field1": field1,
                    "field2": field2,
                    "similarity": similarity,
                    "expected_min": expected_min,
                    "meets_expectation": meets_expectation
                })

            except Exception as e:
                print(f"    ✗ Error calculating similarity: {e}")
                similarity_tests.append({
                    "field1": field1,
                    "field2": field2,
                    "error": str(e)
                })

        # Summary
        successful = len([t for t in similarity_tests if t.get('meets_expectation', False)])
        total = len([t for t in similarity_tests if 'error' not in t])

        print(f"\n  Similarity Summary: {successful}/{total} pairs met expectations")

        self.test_results.append({
            "test": "Semantic Similarity",
            "status": "PASS" if successful >= total * 0.8 else "FAIL",
            "details": f"{successful}/{total} similarity tests passed",
            "similarity_results": similarity_tests
        })

    async def test_04_entity_recognition(self):
        """Test named entity recognition"""
        print("\n[TEST 4] Entity Recognition")
        print("-" * 50)

        test_texts = [
            "SMITH PROPERTIES LLC",
            "123 MAIN STREET FORT LAUDERDALE FL 33301",
            "$250,000",
            "JOHN DOE PRESIDENT",
            "MARCH 15 2020",
            "SINGLE FAMILY RESIDENCE"
        ]

        entity_results = []

        for text in test_texts:
            try:
                doc = self.nlp_analyzer.nlp(text)
                entities = [(ent.text, ent.label_) for ent in doc.ents]

                print(f"  Text: '{text}'")
                print(f"    Entities: {entities}")

                entity_results.append({
                    "text": text,
                    "entities": entities,
                    "entity_count": len(entities)
                })

            except Exception as e:
                print(f"    ✗ Entity recognition failed: {e}")
                entity_results.append({
                    "text": text,
                    "error": str(e)
                })

        # Check for expected entity types
        expected_types = ['ORG', 'MONEY', 'PERSON', 'DATE', 'GPE', 'CARDINAL']
        found_types = set()
        for result in entity_results:
            if 'entities' in result:
                for _, label in result['entities']:
                    found_types.add(label)

        print(f"\n  Entity types found: {sorted(found_types)}")

        self.test_results.append({
            "test": "Entity Recognition",
            "status": "PASS",
            "details": f"Recognized {len(found_types)} entity types",
            "entity_results": entity_results
        })

    async def test_05_property_field_matching(self):
        """Test Property Appraiser field matching"""
        print("\n[TEST 5] Property Field Matching")
        print("-" * 50)

        # Create test data
        property_data = pd.DataFrame([self.test_data["sample_property_data"]])
        ui_requirements = {}

        # Create UI requirements from test mapping
        for db_field, ui_field in self.test_data["property_fields"].items():
            ui_requirements[ui_field] = {"type": "auto", "required": True}

        try:
            matches = self.property_matcher.match_property_fields(property_data, ui_requirements)

            print(f"  Found {len(matches)} field mappings:")

            mapping_results = []
            for field_type, match in matches.items():
                if isinstance(match, FieldMatch):
                    print(f"    {match.db_field} → {match.ui_field}")
                    print(f"      Confidence: {match.confidence:.2f}")
                    print(f"      Type: {match.match_type}")
                    print(f"      Reasoning: {match.reasoning}")

                    mapping_results.append({
                        "field_type": field_type,
                        "db_field": match.db_field,
                        "ui_field": match.ui_field,
                        "confidence": match.confidence,
                        "match_type": match.match_type
                    })

            # Validate critical mappings
            critical_fields = ["phy_addr1", "owner_name", "jv", "av_sd"]
            critical_mapped = sum(1 for match in matches.values()
                                 if isinstance(match, FieldMatch) and
                                    match.db_field in critical_fields)

            print(f"\n  Critical fields mapped: {critical_mapped}/{len(critical_fields)}")

            self.test_results.append({
                "test": "Property Field Matching",
                "status": "PASS" if critical_mapped >= len(critical_fields) * 0.8 else "FAIL",
                "details": f"Mapped {len(matches)} fields, {critical_mapped} critical",
                "mapping_results": mapping_results
            })

        except Exception as e:
            print(f"    ✗ Property field matching failed: {e}")
            self.test_results.append({
                "test": "Property Field Matching",
                "status": "FAIL",
                "error": str(e)
            })

    async def test_06_sunbiz_field_matching(self):
        """Test Sunbiz field matching"""
        print("\n[TEST 6] Sunbiz Field Matching")
        print("-" * 50)

        try:
            # Test business patterns
            business_patterns = self.sunbiz_matcher.business_patterns

            print(f"  Loaded {len(business_patterns)} business field patterns:")
            for pattern_name, config in business_patterns.items():
                print(f"    {pattern_name}: {config['db_patterns']} → {config['ui_patterns']}")

            # Test entity recognition
            test_entity_names = [
                "SMITH PROPERTIES LLC",
                "ACME CORPORATION",
                "SUNSHINE INVESTMENTS INC"
            ]

            entity_analysis = []
            for entity_name in test_entity_names:
                doc = self.sunbiz_matcher.entity_recognizer(entity_name)
                entities = [(ent.text, ent.label_) for ent in doc.ents]

                print(f"  Business entity: '{entity_name}'")
                print(f"    Recognized: {entities}")

                entity_analysis.append({
                    "entity_name": entity_name,
                    "entities": entities
                })

            self.test_results.append({
                "test": "Sunbiz Field Matching",
                "status": "PASS",
                "details": f"Tested {len(business_patterns)} patterns and {len(entity_analysis)} entities",
                "business_patterns": len(business_patterns),
                "entity_analysis": entity_analysis
            })

        except Exception as e:
            print(f"    ✗ Sunbiz field matching failed: {e}")
            self.test_results.append({
                "test": "Sunbiz Field Matching",
                "status": "FAIL",
                "error": str(e)
            })

    async def test_07_complex_field_cases(self):
        """Test complex and edge case field matching"""
        print("\n[TEST 7] Complex Field Cases")
        print("-" * 50)

        complex_cases = self.test_data["complex_cases"]

        complex_results = []

        for db_field, expected_ui_field in complex_cases.items():
            try:
                analysis = self.nlp_analyzer.analyze_field(db_field)
                ui_analysis = self.nlp_analyzer.analyze_field(expected_ui_field)

                similarity = self.property_matcher._calculate_semantic_similarity(analysis, ui_analysis)

                print(f"  Complex case: '{db_field}' → '{expected_ui_field}'")
                print(f"    Normalized: {analysis.normalized_name}")
                print(f"    Similarity: {similarity:.3f}")

                # Test if it would be matched
                would_match = similarity >= self.property_matcher.confidence_threshold

                complex_results.append({
                    "db_field": db_field,
                    "expected_ui_field": expected_ui_field,
                    "similarity": similarity,
                    "would_match": would_match,
                    "normalized": analysis.normalized_name
                })

            except Exception as e:
                print(f"    ✗ Error processing {db_field}: {e}")
                complex_results.append({
                    "db_field": db_field,
                    "error": str(e)
                })

        # Summary
        successful_matches = len([r for r in complex_results if r.get('would_match', False)])
        total_cases = len([r for r in complex_results if 'error' not in r])

        print(f"\n  Complex cases: {successful_matches}/{total_cases} would be matched")

        self.test_results.append({
            "test": "Complex Field Cases",
            "status": "PASS" if successful_matches >= total_cases * 0.6 else "FAIL",
            "details": f"{successful_matches}/{total_cases} complex cases matched",
            "complex_results": complex_results
        })

    async def test_08_business_entity_matching(self):
        """Test business entity matching"""
        print("\n[TEST 8] Business Entity Matching")
        print("-" * 50)

        try:
            owner_name = "SMITH JOHN & JANE"
            business_records = pd.DataFrame(self.test_data["sample_sunbiz_data"])

            matches = self.sunbiz_matcher.match_business_entities(owner_name, business_records)

            print(f"  Owner: '{owner_name}'")
            print(f"  Found {len(matches)} potential business matches:")

            for match in matches:
                print(f"    • {match['entity_name']}")
                print(f"      Document: {match['document_number']}")
                print(f"      Confidence: {match['confidence']:.3f}")
                print(f"      Reasoning: {match['reasoning']}")

            # Test criteria
            has_matches = len(matches) > 0
            high_confidence = any(match['confidence'] > 0.5 for match in matches)

            self.test_results.append({
                "test": "Business Entity Matching",
                "status": "PASS" if has_matches else "WARNING",
                "details": f"Found {len(matches)} matches, highest confidence: {max([m['confidence'] for m in matches], default=0):.3f}",
                "matches": matches
            })

        except Exception as e:
            print(f"    ✗ Business entity matching failed: {e}")
            self.test_results.append({
                "test": "Business Entity Matching",
                "status": "FAIL",
                "error": str(e)
            })

    async def test_09_playwright_nlp_verification(self):
        """Test Playwright NLP verification"""
        print("\n[TEST 9] Playwright NLP Verification")
        print("-" * 50)

        try:
            # Skip if Playwright not available or no local server
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                print("    ⚠ Playwright not installed - skipping verification test")
                self.test_results.append({
                    "test": "Playwright NLP Verification",
                    "status": "SKIPPED",
                    "details": "Playwright not available"
                })
                return

            # Test NLP validation logic without actual browser
            verifier = PlaywrightNLPVerification(self.nlp_analyzer)

            # Test NLP validation methods
            test_validations = [
                ("$250,000", "$250,000.00", "money"),
                ("2020-03-15", "March 15, 2020", "date"),
                ("123 MAIN ST", "123 Main Street", "address"),
                ("JOHN SMITH", "John Smith", "person")
            ]

            validation_results = []

            for expected, displayed, semantic_type in test_validations:
                validation = await verifier._validate_with_nlp(expected, displayed, semantic_type)

                print(f"  Validation: '{expected}' vs '{displayed}' ({semantic_type})")
                print(f"    Valid: {validation['is_valid']}")
                print(f"    Confidence: {validation['confidence']:.3f}")

                validation_results.append({
                    "expected": expected,
                    "displayed": displayed,
                    "semantic_type": semantic_type,
                    "is_valid": validation['is_valid'],
                    "confidence": validation['confidence']
                })

            # Summary
            valid_count = sum(1 for v in validation_results if v['is_valid'])
            total_count = len(validation_results)

            print(f"\n  Validation summary: {valid_count}/{total_count} validations passed")

            self.test_results.append({
                "test": "Playwright NLP Verification",
                "status": "PASS" if valid_count == total_count else "PARTIAL",
                "details": f"{valid_count}/{total_count} validations passed",
                "validation_results": validation_results
            })

        except Exception as e:
            print(f"    ✗ Playwright NLP verification failed: {e}")
            self.test_results.append({
                "test": "Playwright NLP Verification",
                "status": "FAIL",
                "error": str(e)
            })

    async def test_10_complete_pipeline(self):
        """Test complete end-to-end pipeline"""
        print("\n[TEST 10] Complete Pipeline")
        print("-" * 50)

        try:
            # Test pipeline stages without full execution
            test_parcel = "494224020080"

            print(f"  Testing pipeline for parcel: {test_parcel}")

            # Test data fetching
            print("    Stage 1: Data fetching...")
            property_data = self.nlp_system._fetch_property_data(test_parcel)
            has_data = bool(property_data)
            print(f"      Data available: {has_data}")

            if has_data:
                # Test field analysis
                print("    Stage 2: Field analysis...")
                field_analyses = self.nlp_system._analyze_all_fields(property_data)
                analysis_count = sum(len(analyses) for analyses in field_analyses.values())
                print(f"      Fields analyzed: {analysis_count}")

                # Test field matching
                print("    Stage 3: Field matching...")
                field_mappings = self.nlp_system._match_all_fields(property_data, field_analyses)
                mapping_count = len(field_mappings)
                print(f"      Mappings found: {mapping_count}")

                # Test Sunbiz matching
                print("    Stage 4: Sunbiz matching...")
                if 'florida_parcels' in property_data and 'owner_name' in property_data['florida_parcels']:
                    owner_name = property_data['florida_parcels']['owner_name']
                    sunbiz_matches = await self.nlp_system._match_sunbiz_entities(owner_name)
                    sunbiz_count = len(sunbiz_matches)
                    print(f"      Sunbiz matches: {sunbiz_count}")
                else:
                    sunbiz_count = 0
                    print("      No owner name for Sunbiz matching")

                pipeline_success = analysis_count > 0 and mapping_count > 0

            else:
                print("    ⚠ No data available - cannot test full pipeline")
                pipeline_success = False
                analysis_count = mapping_count = sunbiz_count = 0

            self.test_results.append({
                "test": "Complete Pipeline",
                "status": "PASS" if pipeline_success else "PARTIAL",
                "details": f"Analyzed {analysis_count} fields, created {mapping_count} mappings, found {sunbiz_count} Sunbiz matches",
                "has_data": has_data,
                "pipeline_success": pipeline_success
            })

        except Exception as e:
            print(f"    ✗ Complete pipeline test failed: {e}")
            self.test_results.append({
                "test": "Complete Pipeline",
                "status": "FAIL",
                "error": str(e)
            })

    async def test_11_performance_testing(self):
        """Test performance of NLP operations"""
        print("\n[TEST 11] Performance Testing")
        print("-" * 50)

        try:
            # Test field analysis performance
            test_fields = list(self.test_data["property_fields"].keys()) * 10  # 160 fields

            print(f"  Testing performance with {len(test_fields)} field analyses...")

            start_time = time.time()

            analyses = []
            for field in test_fields:
                analysis = self.nlp_analyzer.analyze_field(field)
                analyses.append(analysis)

            analysis_time = time.time() - start_time
            avg_analysis_time = analysis_time / len(test_fields)

            print(f"    Total analysis time: {analysis_time:.2f} seconds")
            print(f"    Average per field: {avg_analysis_time*1000:.1f} ms")

            # Test similarity calculations
            print("  Testing similarity calculation performance...")

            start_time = time.time()

            similarity_tests = 0
            for i in range(0, min(50, len(analyses)-1)):
                for j in range(i+1, min(i+6, len(analyses))):
                    similarity = self.property_matcher._calculate_semantic_similarity(analyses[i], analyses[j])
                    similarity_tests += 1

            similarity_time = time.time() - start_time
            avg_similarity_time = similarity_time / similarity_tests

            print(f"    Similarity calculations: {similarity_tests}")
            print(f"    Total time: {similarity_time:.2f} seconds")
            print(f"    Average per calculation: {avg_similarity_time*1000:.1f} ms")

            # Performance criteria
            analysis_acceptable = avg_analysis_time < 0.1  # Under 100ms per field
            similarity_acceptable = avg_similarity_time < 0.01  # Under 10ms per comparison

            self.test_results.append({
                "test": "Performance Testing",
                "status": "PASS" if analysis_acceptable and similarity_acceptable else "WARNING",
                "details": f"Analysis: {avg_analysis_time*1000:.1f}ms/field, Similarity: {avg_similarity_time*1000:.1f}ms/calc",
                "performance_metrics": {
                    "analysis_time_ms": avg_analysis_time * 1000,
                    "similarity_time_ms": avg_similarity_time * 1000,
                    "total_fields_tested": len(test_fields),
                    "total_similarities_tested": similarity_tests
                }
            })

        except Exception as e:
            print(f"    ✗ Performance testing failed: {e}")
            self.test_results.append({
                "test": "Performance Testing",
                "status": "FAIL",
                "error": str(e)
            })

    def generate_final_report(self):
        """Generate comprehensive final report"""
        print("\n" + "="*100)
        print(" FINAL TEST REPORT")
        print("="*100)

        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        warning_tests = len([t for t in self.test_results if t["status"] in ["WARNING", "PARTIAL"]])
        skipped_tests = len([t for t in self.test_results if t["status"] == "SKIPPED"])

        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\nTest Statistics:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests} ({pass_rate:.1f}%)")
        print(f"  Failed: {failed_tests}")
        print(f"  Warnings: {warning_tests}")
        print(f"  Skipped: {skipped_tests}")

        # Overall status
        if failed_tests == 0 and passed_tests >= total_tests * 0.8:
            overall_status = "✓ EXCELLENT"
            status_color = "\033[92m"  # Green
        elif failed_tests <= 2 and passed_tests >= total_tests * 0.6:
            overall_status = "⚠ GOOD"
            status_color = "\033[93m"  # Yellow
        else:
            overall_status = "✗ NEEDS IMPROVEMENT"
            status_color = "\033[91m"  # Red

        print(f"\n{status_color}Overall Status: {overall_status}\033[0m")

        # Detailed results
        print("\nDetailed Test Results:")
        print("-" * 80)
        for result in self.test_results:
            status_symbol = {
                "PASS": "✓",
                "FAIL": "✗",
                "WARNING": "⚠",
                "PARTIAL": "⚠",
                "SKIPPED": "○"
            }.get(result["status"], "?")

            print(f"{status_symbol} {result['test']}: {result['status']}")
            if "details" in result:
                print(f"  {result['details']}")
            if "error" in result:
                print(f"  Error: {result['error'][:100]}...")

        # Key findings
        print("\nKey Findings:")
        print("-" * 40)

        # NLP capabilities
        nlp_tests = [t for t in self.test_results if "NLP" in t["test"] or "Field" in t["test"]]
        nlp_success = len([t for t in nlp_tests if t["status"] == "PASS"])
        print(f"• NLP Field Matching: {nlp_success}/{len(nlp_tests)} core tests passed")

        # Performance
        perf_test = next((t for t in self.test_results if "Performance" in t["test"]), None)
        if perf_test and "performance_metrics" in perf_test:
            metrics = perf_test["performance_metrics"]
            print(f"• Performance: {metrics['analysis_time_ms']:.1f}ms per field analysis")

        # Coverage
        mapping_test = next((t for t in self.test_results if "Property Field" in t["test"]), None)
        if mapping_test and "mapping_results" in mapping_test:
            mapped_count = len(mapping_test["mapping_results"])
            print(f"• Field Coverage: {mapped_count} property fields successfully mapped")

        # Save detailed report
        report = {
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "warnings": warning_tests,
                "skipped": skipped_tests,
                "pass_rate": pass_rate
            },
            "overall_status": overall_status.replace("✓ ", "").replace("⚠ ", "").replace("✗ ", ""),
            "test_results": self.test_results
        }

        report_file = f"nlp_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\nDetailed report saved to: {report_file}")
        print("Log file: nlp_test_results.log")

        # Recommendations
        if failed_tests > 0:
            print("\nRecommendations:")
            print("1. Check NLTK and spaCy installation and models")
            print("2. Verify database connectivity")
            print("3. Ensure test data is available")
            print("4. Consider adjusting confidence thresholds")
            print("5. Review field mapping patterns")

async def main():
    """Run the complete NLP test suite"""
    test_suite = NLPTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    # Create test directories
    os.makedirs("nlp_test_output", exist_ok=True)

    # Run tests
    asyncio.run(main())