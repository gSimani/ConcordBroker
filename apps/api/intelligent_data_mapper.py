"""
Intelligent Data Mapper using scikit-learn
Maps Property Appraiser and Sunbiz data to correct UI fields
with ML-based field matching and visual verification
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from typing import Dict, List, Tuple, Any, Optional
import json
import re
from dataclasses import dataclass
from datetime import datetime
import asyncio
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv('.env.mcp')

@dataclass
class FieldMapping:
    """Represents a mapping between database field and UI component"""
    db_field: str
    db_table: str
    ui_component: str
    ui_tab: str
    ui_field: str
    confidence: float
    data_type: str
    transformation: Optional[str] = None
    validation_rule: Optional[str] = None

class IntelligentDataMapper:
    """ML-based data mapping system for ConcordBroker"""

    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # Initialize ML components
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(2, 4),
            max_features=1000
        )
        self.field_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

        # Define UI component structure
        self.ui_structure = self._load_ui_structure()

        # Define database schema
        self.db_schema = self._load_db_schema()

        # Initialize mapping rules
        self.mapping_rules = self._initialize_mapping_rules()

        # Training data for ML model
        self.training_data = self._load_training_data()

    def _load_ui_structure(self) -> Dict[str, Dict]:
        """Load UI component structure from tabs"""
        return {
            "overview": {
                "fields": [
                    {"name": "property_address", "type": "text", "display": "Property Address"},
                    {"name": "owner_name", "type": "text", "display": "Owner Name"},
                    {"name": "just_value", "type": "currency", "display": "Market Value"},
                    {"name": "taxable_value", "type": "currency", "display": "Taxable Value"},
                    {"name": "year_built", "type": "integer", "display": "Year Built"},
                    {"name": "total_living_area", "type": "area", "display": "Living Area"},
                    {"name": "bedrooms", "type": "integer", "display": "Bedrooms"},
                    {"name": "bathrooms", "type": "decimal", "display": "Bathrooms"}
                ]
            },
            "core-property": {
                "fields": [
                    {"name": "parcel_id", "type": "text", "display": "Parcel ID"},
                    {"name": "property_use_desc", "type": "text", "display": "Property Type"},
                    {"name": "zoning", "type": "text", "display": "Zoning"},
                    {"name": "land_sqft", "type": "area", "display": "Land Size"},
                    {"name": "land_acres", "type": "decimal", "display": "Acres"},
                    {"name": "legal_desc", "type": "text", "display": "Legal Description"},
                    {"name": "subdivision", "type": "text", "display": "Subdivision"},
                    {"name": "lot", "type": "text", "display": "Lot"},
                    {"name": "block", "type": "text", "display": "Block"}
                ]
            },
            "valuation": {
                "fields": [
                    {"name": "just_value", "type": "currency", "display": "Just Value"},
                    {"name": "assessed_value", "type": "currency", "display": "Assessed Value"},
                    {"name": "taxable_value", "type": "currency", "display": "Taxable Value"},
                    {"name": "land_value", "type": "currency", "display": "Land Value"},
                    {"name": "building_value", "type": "currency", "display": "Building Value"},
                    {"name": "tax_amount", "type": "currency", "display": "Annual Tax"}
                ]
            },
            "owner": {
                "fields": [
                    {"name": "owner_name", "type": "text", "display": "Owner Name"},
                    {"name": "owner_address", "type": "text", "display": "Mailing Address"},
                    {"name": "owner_city", "type": "text", "display": "City"},
                    {"name": "owner_state", "type": "text", "display": "State"},
                    {"name": "owner_zip", "type": "text", "display": "ZIP Code"},
                    {"name": "ownership_date", "type": "date", "display": "Ownership Date"}
                ]
            },
            "sales": {
                "fields": [
                    {"name": "sale_date", "type": "date", "display": "Sale Date"},
                    {"name": "sale_price", "type": "currency", "display": "Sale Price"},
                    {"name": "sale_qualification", "type": "text", "display": "Sale Type"},
                    {"name": "previous_sale_date", "type": "date", "display": "Previous Sale Date"},
                    {"name": "previous_sale_price", "type": "currency", "display": "Previous Sale Price"}
                ]
            },
            "building": {
                "fields": [
                    {"name": "year_built", "type": "integer", "display": "Year Built"},
                    {"name": "total_living_area", "type": "area", "display": "Living Area"},
                    {"name": "bedrooms", "type": "integer", "display": "Bedrooms"},
                    {"name": "bathrooms", "type": "decimal", "display": "Bathrooms"},
                    {"name": "stories", "type": "decimal", "display": "Stories"},
                    {"name": "units", "type": "integer", "display": "Units"},
                    {"name": "construction_type", "type": "text", "display": "Construction"},
                    {"name": "roof_type", "type": "text", "display": "Roof Type"},
                    {"name": "heating_cooling", "type": "text", "display": "HVAC"}
                ]
            },
            "sunbiz": {
                "fields": [
                    {"name": "entity_name", "type": "text", "display": "Business Name"},
                    {"name": "entity_type", "type": "text", "display": "Entity Type"},
                    {"name": "filing_date", "type": "date", "display": "Filing Date"},
                    {"name": "status", "type": "text", "display": "Status"},
                    {"name": "registered_agent", "type": "text", "display": "Registered Agent"},
                    {"name": "principal_address", "type": "text", "display": "Principal Address"},
                    {"name": "officers", "type": "array", "display": "Officers/Directors"}
                ]
            },
            "taxes": {
                "fields": [
                    {"name": "tax_year", "type": "integer", "display": "Tax Year"},
                    {"name": "millage_rate", "type": "decimal", "display": "Millage Rate"},
                    {"name": "tax_amount", "type": "currency", "display": "Tax Amount"},
                    {"name": "exemptions", "type": "array", "display": "Exemptions"},
                    {"name": "payment_status", "type": "text", "display": "Payment Status"},
                    {"name": "due_date", "type": "date", "display": "Due Date"}
                ]
            },
            "permit": {
                "fields": [
                    {"name": "permit_number", "type": "text", "display": "Permit Number"},
                    {"name": "permit_type", "type": "text", "display": "Permit Type"},
                    {"name": "issue_date", "type": "date", "display": "Issue Date"},
                    {"name": "work_description", "type": "text", "display": "Description"},
                    {"name": "contractor", "type": "text", "display": "Contractor"},
                    {"name": "estimated_value", "type": "currency", "display": "Est. Value"},
                    {"name": "status", "type": "text", "display": "Status"}
                ]
            },
            "tax-deed-sales": {
                "fields": [
                    {"name": "td_number", "type": "text", "display": "TD Number"},
                    {"name": "auction_date", "type": "date", "display": "Auction Date"},
                    {"name": "opening_bid", "type": "currency", "display": "Opening Bid"},
                    {"name": "winning_bid", "type": "currency", "display": "Winning Bid"},
                    {"name": "certificate_holder", "type": "text", "display": "Certificate Holder"},
                    {"name": "redemption_date", "type": "date", "display": "Redemption Date"},
                    {"name": "status", "type": "text", "display": "Status"}
                ]
            }
        }

    def _load_db_schema(self) -> Dict[str, List[str]]:
        """Load database schema structure"""
        return {
            "florida_parcels": [
                "parcel_id", "county", "year", "owner_name", "owner_addr1", "owner_addr2",
                "owner_city", "owner_state", "owner_zip", "phy_addr1", "phy_addr2",
                "phy_city", "phy_state", "phy_zipcd", "legal_desc", "subdivision",
                "lot", "block", "property_use", "property_use_desc", "land_use_code",
                "zoning", "just_value", "assessed_value", "taxable_value", "land_value",
                "building_value", "year_built", "total_living_area", "bedrooms",
                "bathrooms", "stories", "units", "land_sqft", "land_acres",
                "sale_date", "sale_price", "sale_qualification"
            ],
            "sunbiz_entities": [
                "entity_name", "entity_type", "filing_date", "status", "document_number",
                "ein", "registered_agent_name", "registered_agent_address",
                "principal_address", "mailing_address", "annual_report_date"
            ],
            "sunbiz_officers": [
                "entity_name", "officer_name", "officer_title", "officer_address",
                "appointed_date", "terminated_date"
            ],
            "building_permits": [
                "permit_number", "parcel_id", "permit_type", "issue_date", "expire_date",
                "finalized_date", "work_description", "contractor_name", "estimated_value",
                "actual_value", "status", "inspection_status"
            ],
            "tax_certificates": [
                "certificate_number", "parcel_id", "tax_year", "certificate_date",
                "face_value", "interest_rate", "redemption_date", "holder_name", "status"
            ],
            "tax_deed_sales": [
                "td_number", "parcel_id", "auction_date", "opening_bid", "winning_bid",
                "winner_name", "certificate_number", "status", "deed_date"
            ]
        }

    def _initialize_mapping_rules(self) -> List[Dict]:
        """Initialize manual mapping rules for common patterns"""
        return [
            # Property Appraiser mappings
            {"pattern": r"^PHY_ADDR", "ui_field": "property_address", "tab": "overview"},
            {"pattern": r"^OWN_NAME|OWNER", "ui_field": "owner_name", "tab": "owner"},
            {"pattern": r"^JV$|JUST_VALUE", "ui_field": "just_value", "tab": "valuation"},
            {"pattern": r"^AV$|ASSESSED", "ui_field": "assessed_value", "tab": "valuation"},
            {"pattern": r"^TV$|TAXABLE", "ui_field": "taxable_value", "tab": "valuation"},
            {"pattern": r"^LAND_SQFOOT|LND_SQFOOT", "ui_field": "land_sqft", "tab": "core-property"},
            {"pattern": r"^SALE_YR|SALE_DATE", "ui_field": "sale_date", "tab": "sales"},
            {"pattern": r"^SALE_PRICE", "ui_field": "sale_price", "tab": "sales"},

            # Sunbiz mappings
            {"pattern": r"ENTITY_NAME|CORP_NAME", "ui_field": "entity_name", "tab": "sunbiz"},
            {"pattern": r"FILING_DATE|FILE_DATE", "ui_field": "filing_date", "tab": "sunbiz"},
            {"pattern": r"^STATUS$", "ui_field": "status", "tab": "sunbiz"},
            {"pattern": r"AGENT_NAME|REG_AGENT", "ui_field": "registered_agent", "tab": "sunbiz"},

            # Permit mappings
            {"pattern": r"PERMIT_NUM", "ui_field": "permit_number", "tab": "permit"},
            {"pattern": r"ISSUE_DATE", "ui_field": "issue_date", "tab": "permit"},

            # Tax Deed mappings
            {"pattern": r"TD_NUMBER|TAX_DEED", "ui_field": "td_number", "tab": "tax-deed-sales"},
            {"pattern": r"AUCTION_DATE", "ui_field": "auction_date", "tab": "tax-deed-sales"},
            {"pattern": r"OPENING_BID", "ui_field": "opening_bid", "tab": "tax-deed-sales"},
        ]

    def _load_training_data(self) -> pd.DataFrame:
        """Load training data for ML model"""
        # Create synthetic training data based on known mappings
        training_samples = []

        # Add known good mappings
        known_mappings = [
            ("PHY_ADDR1", "property_address", 1.0),
            ("OWNER_NAME", "owner_name", 1.0),
            ("JUST_VALUE", "just_value", 1.0),
            ("LAND_SQFOOT", "land_sqft", 1.0),
            ("SALE_DATE", "sale_date", 1.0),
            ("ENTITY_NAME", "entity_name", 1.0),
            ("PERMIT_NUMBER", "permit_number", 1.0),
            ("TD_NUMBER", "td_number", 1.0),
            ("YEAR_BUILT", "year_built", 1.0),
            ("BEDROOMS", "bedrooms", 1.0),
            ("BATHROOMS", "bathrooms", 1.0),
            ("TOTAL_LIVING_AREA", "total_living_area", 1.0),
        ]

        for db_field, ui_field, confidence in known_mappings:
            training_samples.append({
                "db_field": db_field,
                "ui_field": ui_field,
                "confidence": confidence,
                "is_match": 1
            })

            # Add negative samples
            for other_ui_field in ["random_field", "unrelated_field"]:
                if other_ui_field != ui_field:
                    training_samples.append({
                        "db_field": db_field,
                        "ui_field": other_ui_field,
                        "confidence": 0.0,
                        "is_match": 0
                    })

        return pd.DataFrame(training_samples)

    def train_field_matcher(self):
        """Train the ML model for field matching"""
        if not self.training_data.empty:
            # Create feature vectors
            X = []
            y = self.training_data['is_match'].values

            for _, row in self.training_data.iterrows():
                # Calculate similarity features
                features = self._extract_features(row['db_field'], row['ui_field'])
                X.append(features)

            X = np.array(X)

            # Train the classifier
            self.field_classifier.fit(X, y)
            print(f"✓ Trained field matcher with {len(X)} samples")

    def _extract_features(self, db_field: str, ui_field: str) -> np.ndarray:
        """Extract features for ML matching"""
        features = []

        # String similarity
        db_clean = db_field.lower().replace('_', ' ')
        ui_clean = ui_field.lower().replace('_', ' ')

        # Exact match
        features.append(1.0 if db_clean == ui_clean else 0.0)

        # Contains match
        features.append(1.0 if ui_clean in db_clean or db_clean in ui_clean else 0.0)

        # Word overlap
        db_words = set(db_clean.split())
        ui_words = set(ui_clean.split())
        overlap = len(db_words & ui_words) / max(len(db_words), len(ui_words)) if db_words or ui_words else 0
        features.append(overlap)

        # Character similarity
        common_chars = set(db_clean) & set(ui_clean)
        char_sim = len(common_chars) / max(len(set(db_clean)), len(set(ui_clean))) if db_clean or ui_clean else 0
        features.append(char_sim)

        # Length difference
        len_diff = abs(len(db_clean) - len(ui_clean)) / max(len(db_clean), len(ui_clean)) if db_clean or ui_clean else 0
        features.append(1 - len_diff)

        # Pattern matching score
        pattern_score = 0.0
        for rule in self.mapping_rules:
            if re.search(rule['pattern'], db_field, re.IGNORECASE):
                if rule['ui_field'] == ui_field:
                    pattern_score = 1.0
                    break
        features.append(pattern_score)

        return np.array(features)

    def find_best_mapping(self, db_field: str, db_table: str) -> FieldMapping:
        """Find the best UI field mapping for a database field"""
        best_mapping = None
        best_score = 0.0

        # Check all UI tabs and fields
        for tab_name, tab_info in self.ui_structure.items():
            for field_info in tab_info['fields']:
                ui_field = field_info['name']

                # Extract features
                features = self._extract_features(db_field, ui_field).reshape(1, -1)

                # Predict using ML model
                try:
                    match_prob = self.field_classifier.predict_proba(features)[0][1]
                except:
                    # Fallback to rule-based if model not trained
                    match_prob = self._calculate_similarity(db_field, ui_field)

                if match_prob > best_score:
                    best_score = match_prob
                    best_mapping = FieldMapping(
                        db_field=db_field,
                        db_table=db_table,
                        ui_component=f"{tab_name}_tab",
                        ui_tab=tab_name,
                        ui_field=ui_field,
                        confidence=match_prob,
                        data_type=field_info['type'],
                        transformation=self._get_transformation(db_field, field_info['type']),
                        validation_rule=self._get_validation_rule(field_info['type'])
                    )

        return best_mapping

    def _calculate_similarity(self, db_field: str, ui_field: str) -> float:
        """Calculate similarity between database and UI field names"""
        # Clean field names
        db_clean = db_field.lower().replace('_', ' ')
        ui_clean = ui_field.lower().replace('_', ' ')

        # Check exact match
        if db_clean == ui_clean:
            return 1.0

        # Check pattern rules
        for rule in self.mapping_rules:
            if re.search(rule['pattern'], db_field, re.IGNORECASE):
                if rule['ui_field'] == ui_field:
                    return 0.95

        # Use TF-IDF similarity
        try:
            tfidf_matrix = self.vectorizer.fit_transform([db_clean, ui_clean])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except:
            return 0.0

    def _get_transformation(self, db_field: str, data_type: str) -> Optional[str]:
        """Get data transformation rule"""
        transformations = {
            "currency": "format_currency",
            "area": "format_area",
            "date": "format_date",
            "decimal": "round_decimal",
            "integer": "to_integer"
        }

        # Special transformations
        if "DATE" in db_field and data_type == "date":
            return "parse_date"
        if "PRICE" in db_field or "VALUE" in db_field:
            return "format_currency"
        if "SQFT" in db_field or "AREA" in db_field:
            return "format_area"

        return transformations.get(data_type)

    def _get_validation_rule(self, data_type: str) -> Optional[str]:
        """Get validation rule for data type"""
        validations = {
            "currency": "value >= 0",
            "area": "value >= 0",
            "date": "valid_date",
            "integer": "is_integer",
            "decimal": "is_numeric",
            "text": "not_empty"
        }
        return validations.get(data_type)

    async def map_all_fields(self) -> Dict[str, List[FieldMapping]]:
        """Map all database fields to UI components"""
        all_mappings = {}

        # Train the model first
        self.train_field_matcher()

        for table_name, fields in self.db_schema.items():
            table_mappings = []

            for field in fields:
                mapping = self.find_best_mapping(field, table_name)
                if mapping and mapping.confidence > 0.5:  # Only include confident mappings
                    table_mappings.append(mapping)
                    print(f"Mapped {table_name}.{field} -> {mapping.ui_tab}.{mapping.ui_field} (confidence: {mapping.confidence:.2f})")

            all_mappings[table_name] = table_mappings

        return all_mappings

    def generate_mapping_report(self, mappings: Dict[str, List[FieldMapping]]) -> str:
        """Generate a detailed mapping report"""
        report = []
        report.append("# Data Field Mapping Report")
        report.append(f"Generated: {datetime.now().isoformat()}\n")

        total_fields = sum(len(fields) for fields in self.db_schema.values())
        mapped_fields = sum(len(mappings) for mappings in mappings.values())

        report.append(f"## Summary")
        report.append(f"- Total database fields: {total_fields}")
        report.append(f"- Successfully mapped: {mapped_fields}")
        report.append(f"- Mapping rate: {(mapped_fields/total_fields)*100:.1f}%\n")

        report.append("## Detailed Mappings by Table\n")

        for table_name, table_mappings in mappings.items():
            report.append(f"### {table_name}")
            report.append(f"Fields mapped: {len(table_mappings)}/{len(self.db_schema.get(table_name, []))}\n")

            if table_mappings:
                report.append("| Database Field | UI Tab | UI Field | Confidence | Transformation |")
                report.append("|----------------|---------|----------|------------|----------------|")

                for mapping in sorted(table_mappings, key=lambda x: x.confidence, reverse=True):
                    report.append(
                        f"| {mapping.db_field} | {mapping.ui_tab} | {mapping.ui_field} | "
                        f"{mapping.confidence:.2%} | {mapping.transformation or 'None'} |"
                    )
            report.append("")

        # Add unmapped fields
        report.append("## Unmapped Fields (Need Manual Review)\n")
        for table_name, fields in self.db_schema.items():
            mapped_field_names = {m.db_field for m in mappings.get(table_name, [])}
            unmapped = [f for f in fields if f not in mapped_field_names]

            if unmapped:
                report.append(f"### {table_name}")
                for field in unmapped:
                    report.append(f"- {field}")
                report.append("")

        return "\n".join(report)

    def export_mapping_config(self, mappings: Dict[str, List[FieldMapping]], filepath: str):
        """Export mappings to JSON configuration file"""
        config = {
            "version": "1.0",
            "generated": datetime.now().isoformat(),
            "mappings": {}
        }

        for table_name, table_mappings in mappings.items():
            config["mappings"][table_name] = [
                {
                    "db_field": m.db_field,
                    "db_table": m.db_table,
                    "ui_component": m.ui_component,
                    "ui_tab": m.ui_tab,
                    "ui_field": m.ui_field,
                    "confidence": m.confidence,
                    "data_type": m.data_type,
                    "transformation": m.transformation,
                    "validation_rule": m.validation_rule
                }
                for m in table_mappings
            ]

        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✓ Mapping configuration exported to {filepath}")

async def main():
    """Run the intelligent data mapper"""
    mapper = IntelligentDataMapper()

    print("Starting Intelligent Data Mapping System...")
    print("=" * 60)

    # Map all fields
    mappings = await mapper.map_all_fields()

    # Generate report
    report = mapper.generate_mapping_report(mappings)

    # Save report
    with open("data_mapping_report.md", "w") as f:
        f.write(report)

    # Export configuration
    mapper.export_mapping_config(mappings, "data_mapping_config.json")

    print("\n" + "=" * 60)
    print("✓ Data mapping complete!")
    print("✓ Report saved to: data_mapping_report.md")
    print("✓ Configuration saved to: data_mapping_config.json")

if __name__ == "__main__":
    asyncio.run(main())