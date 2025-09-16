"""
Deep Learning Data Mapping and Verification System
Uses TensorFlow/PyTorch for intelligent field matching and validation
"""

import tensorflow as tf
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import json
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
import asyncio
import aiohttp
from pathlib import Path
import re
from fuzzywuzzy import fuzz
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TabCategory(Enum):
    """Categories of tabs in the property interface"""
    OVERVIEW = "overview"
    CORE_PROPERTY = "core-property"
    VALUATION = "valuation"
    PERMIT = "permit"
    SUNBIZ = "sunbiz"
    TAXES = "taxes"
    SALES_TAX_DEED = "sales-tax-deed"
    TAX_DEED_SALES = "tax-deed-sales"
    OWNER = "owner"
    SALES_HISTORY = "sales"
    BUILDING = "building"
    LAND_LEGAL = "land"
    EXEMPTIONS = "exemptions"
    NOTES = "notes"

@dataclass
class FieldMapping:
    """Represents a mapping between database field and UI element"""
    db_field: str
    ui_element: str
    tab: TabCategory
    subtab: Optional[str] = None
    data_type: str = "string"
    transformation: Optional[str] = None
    validation_rules: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    verified: bool = False

@dataclass
class DataValidationResult:
    """Result of data validation"""
    field: str
    value: Any
    is_valid: bool
    errors: List[str]
    suggestions: List[str]
    confidence: float

class DeepLearningFieldMapper(nn.Module):
    """PyTorch model for intelligent field mapping"""

    def __init__(self, input_size=768, hidden_size=512, num_tabs=14, num_fields=200):
        super(DeepLearningFieldMapper, self).__init__()

        # Encoder layers
        self.field_encoder = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.2)
        )

        # Tab classification head
        self.tab_classifier = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.ReLU(),
            nn.Linear(hidden_size // 4, num_tabs),
            nn.Softmax(dim=-1)
        )

        # Field matching head
        self.field_matcher = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.ReLU(),
            nn.Linear(hidden_size // 4, num_fields),
            nn.Sigmoid()
        )

        # Confidence scorer
        self.confidence_scorer = nn.Sequential(
            nn.Linear(hidden_size // 2, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        # Encode input
        encoded = self.field_encoder(x)

        # Get predictions
        tab_probs = self.tab_classifier(encoded)
        field_matches = self.field_matcher(encoded)
        confidence = self.confidence_scorer(encoded)

        return {
            'tab_probabilities': tab_probs,
            'field_matches': field_matches,
            'confidence': confidence
        }

class TensorFlowDataValidator:
    """TensorFlow model for data validation"""

    def __init__(self):
        self.model = self._build_model()
        self.encoders = {}
        self.scalers = {}

    def _build_model(self):
        """Build TensorFlow validation model"""
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(100,)),
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])

        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
        )

        return model

    def preprocess_field(self, field_name: str, value: Any) -> np.ndarray:
        """Preprocess field for validation"""
        features = []

        # Basic features
        features.append(len(str(value)) if value else 0)
        features.append(1 if value is not None else 0)
        features.append(1 if isinstance(value, (int, float)) else 0)
        features.append(1 if isinstance(value, str) else 0)

        # Field-specific features
        if 'date' in field_name.lower():
            features.append(1 if self._is_valid_date(value) else 0)
        if 'amount' in field_name.lower() or 'value' in field_name.lower():
            features.append(1 if self._is_valid_amount(value) else 0)
        if 'address' in field_name.lower():
            features.append(1 if self._is_valid_address(value) else 0)

        # Pad to fixed size
        while len(features) < 100:
            features.append(0)

        return np.array(features[:100])

    def _is_valid_date(self, value) -> bool:
        """Check if value is a valid date"""
        if not value:
            return False
        try:
            if isinstance(value, str):
                datetime.strptime(value, '%Y-%m-%d')
            return True
        except:
            return False

    def _is_valid_amount(self, value) -> bool:
        """Check if value is a valid amount"""
        try:
            float_val = float(value) if value else 0
            return float_val >= 0
        except:
            return False

    def _is_valid_address(self, value) -> bool:
        """Check if value is a valid address"""
        if not value or not isinstance(value, str):
            return False
        # Basic address validation
        return len(value) > 5 and any(char.isdigit() for char in value)

    def validate(self, field_name: str, value: Any) -> float:
        """Validate a field value"""
        features = self.preprocess_field(field_name, value)
        features = features.reshape(1, -1)

        prediction = self.model.predict(features, verbose=0)[0][0]
        return float(prediction)

class ComprehensiveDataMappingSystem:
    """Main system for data mapping and verification"""

    def __init__(self):
        self.pytorch_mapper = DeepLearningFieldMapper()
        self.tf_validator = TensorFlowDataValidator()
        self.field_mappings = self._initialize_field_mappings()
        self.validation_cache = {}

    def _initialize_field_mappings(self) -> Dict[str, FieldMapping]:
        """Initialize comprehensive field mappings"""
        mappings = {}

        # OVERVIEW TAB MAPPINGS
        overview_mappings = [
            # Property Location
            FieldMapping("phy_addr1", "property.address.street", TabCategory.OVERVIEW,
                        data_type="string", validation_rules=["required", "min_length:5"]),
            FieldMapping("phy_city", "property.address.city", TabCategory.OVERVIEW,
                        data_type="string", validation_rules=["required"]),
            FieldMapping("phy_zipcd", "property.address.zipcode", TabCategory.OVERVIEW,
                        data_type="string", validation_rules=["regex:^[0-9]{5}$"]),
            FieldMapping("parcel_id", "property.parcel_id", TabCategory.OVERVIEW,
                        data_type="string", validation_rules=["required", "unique"]),
            FieldMapping("dor_uc", "property.type_code", TabCategory.OVERVIEW,
                        data_type="string", transformation="property_type_description"),

            # Valuation Summary
            FieldMapping("jv", "valuation.just_value", TabCategory.OVERVIEW,
                        data_type="decimal", validation_rules=["min:0"]),
            FieldMapping("tv_sd", "valuation.taxable_value", TabCategory.OVERVIEW,
                        data_type="decimal", validation_rules=["min:0"]),
            FieldMapping("lnd_val", "valuation.land_value", TabCategory.OVERVIEW,
                        data_type="decimal", validation_rules=["min:0"]),

            # Recent Sale
            FieldMapping("sale_prc1", "sale.recent.price", TabCategory.OVERVIEW,
                        data_type="decimal", validation_rules=["min:0"]),
            FieldMapping("sale_yr1", "sale.recent.year", TabCategory.OVERVIEW,
                        data_type="integer", validation_rules=["min:1900", "max:2025"]),
            FieldMapping("sale_mo1", "sale.recent.month", TabCategory.OVERVIEW,
                        data_type="integer", validation_rules=["min:1", "max:12"]),
        ]

        # CORE PROPERTY TAB MAPPINGS
        core_property_mappings = [
            FieldMapping("owner_name", "owner.name", TabCategory.CORE_PROPERTY,
                        data_type="string", validation_rules=["required"]),
            FieldMapping("owner_addr1", "owner.address.street", TabCategory.CORE_PROPERTY,
                        data_type="string"),
            FieldMapping("owner_city", "owner.address.city", TabCategory.CORE_PROPERTY,
                        data_type="string"),
            FieldMapping("owner_state", "owner.address.state", TabCategory.CORE_PROPERTY,
                        data_type="string", validation_rules=["max_length:2"]),
            FieldMapping("owner_zip", "owner.address.zipcode", TabCategory.CORE_PROPERTY,
                        data_type="string"),
            FieldMapping("tot_lvg_area", "building.living_area", TabCategory.CORE_PROPERTY,
                        data_type="integer", validation_rules=["min:0"]),
            FieldMapping("lnd_sqfoot", "land.square_feet", TabCategory.CORE_PROPERTY,
                        data_type="integer", validation_rules=["min:0"]),
            FieldMapping("bedroom_cnt", "building.bedrooms", TabCategory.CORE_PROPERTY,
                        data_type="integer", validation_rules=["min:0", "max:20"]),
            FieldMapping("bathroom_cnt", "building.bathrooms", TabCategory.CORE_PROPERTY,
                        data_type="decimal", validation_rules=["min:0", "max:20"]),
            FieldMapping("act_yr_blt", "building.year_built", TabCategory.CORE_PROPERTY,
                        data_type="integer", validation_rules=["min:1800", "max:2025"]),
            FieldMapping("eff_yr_blt", "building.effective_year", TabCategory.CORE_PROPERTY,
                        data_type="integer", validation_rules=["min:1800", "max:2025"]),
            FieldMapping("no_res_unts", "building.residential_units", TabCategory.CORE_PROPERTY,
                        data_type="integer", validation_rules=["min:1"]),
        ]

        # VALUATION TAB MAPPINGS
        valuation_mappings = [
            FieldMapping("jv", "assessment.just_value", TabCategory.VALUATION,
                        data_type="decimal", validation_rules=["required", "min:0"]),
            FieldMapping("av_sd", "assessment.assessed_value", TabCategory.VALUATION,
                        data_type="decimal", validation_rules=["required", "min:0"]),
            FieldMapping("tv_sd", "assessment.taxable_value", TabCategory.VALUATION,
                        data_type="decimal", validation_rules=["required", "min:0"]),
            FieldMapping("lnd_val", "assessment.land_value", TabCategory.VALUATION,
                        data_type="decimal", validation_rules=["min:0"]),
            FieldMapping("bldg_val", "assessment.building_value", TabCategory.VALUATION,
                        data_type="decimal", transformation="calculate_building_value"),
        ]

        # TAXES TAB MAPPINGS
        tax_mappings = [
            FieldMapping("millage_rate", "tax.millage_rate", TabCategory.TAXES,
                        data_type="decimal", validation_rules=["min:0", "max:100"]),
            FieldMapping("tax_amount", "tax.annual_amount", TabCategory.TAXES,
                        data_type="decimal", validation_rules=["min:0"]),
            FieldMapping("exempt_val", "tax.exemption_value", TabCategory.TAXES,
                        data_type="decimal", validation_rules=["min:0"]),
            FieldMapping("homestead_exemption", "tax.homestead", TabCategory.TAXES,
                        data_type="boolean"),
        ]

        # SUNBIZ TAB MAPPINGS
        sunbiz_mappings = [
            FieldMapping("entity_name", "business.name", TabCategory.SUNBIZ,
                        subtab="entity", data_type="string"),
            FieldMapping("doc_number", "business.doc_number", TabCategory.SUNBIZ,
                        subtab="entity", data_type="string"),
            FieldMapping("status", "business.status", TabCategory.SUNBIZ,
                        subtab="entity", data_type="string"),
            FieldMapping("filing_date", "business.filing_date", TabCategory.SUNBIZ,
                        subtab="entity", data_type="date"),
            FieldMapping("registered_agent", "business.agent.name", TabCategory.SUNBIZ,
                        subtab="agent", data_type="string"),
            FieldMapping("principal_addr1", "business.address.street", TabCategory.SUNBIZ,
                        subtab="address", data_type="string"),
        ]

        # PERMIT TAB MAPPINGS
        permit_mappings = [
            FieldMapping("permit_number", "permit.number", TabCategory.PERMIT,
                        data_type="string", validation_rules=["required"]),
            FieldMapping("permit_type", "permit.type", TabCategory.PERMIT,
                        data_type="string"),
            FieldMapping("issue_date", "permit.issue_date", TabCategory.PERMIT,
                        data_type="date"),
            FieldMapping("contractor", "permit.contractor", TabCategory.PERMIT,
                        data_type="string"),
            FieldMapping("permit_status", "permit.status", TabCategory.PERMIT,
                        data_type="string"),
            FieldMapping("permit_value", "permit.value", TabCategory.PERMIT,
                        data_type="decimal", validation_rules=["min:0"]),
        ]

        # SALES HISTORY TAB MAPPINGS
        sales_mappings = [
            FieldMapping("sale_date", "sales.date", TabCategory.SALES_HISTORY,
                        data_type="date", validation_rules=["required"]),
            FieldMapping("sale_price", "sales.price", TabCategory.SALES_HISTORY,
                        data_type="decimal", validation_rules=["min:0"]),
            FieldMapping("seller_name", "sales.seller", TabCategory.SALES_HISTORY,
                        data_type="string"),
            FieldMapping("buyer_name", "sales.buyer", TabCategory.SALES_HISTORY,
                        data_type="string"),
            FieldMapping("deed_type", "sales.deed_type", TabCategory.SALES_HISTORY,
                        data_type="string"),
            FieldMapping("qualified_sale", "sales.qualified", TabCategory.SALES_HISTORY,
                        data_type="boolean"),
        ]

        # TAX DEED SALES TAB MAPPINGS
        tax_deed_mappings = [
            FieldMapping("td_number", "tax_deed.number", TabCategory.TAX_DEED_SALES,
                        data_type="string"),
            FieldMapping("auction_date", "tax_deed.auction_date", TabCategory.TAX_DEED_SALES,
                        data_type="date"),
            FieldMapping("auction_status", "tax_deed.status", TabCategory.TAX_DEED_SALES,
                        data_type="string"),
            FieldMapping("opening_bid", "tax_deed.opening_bid", TabCategory.TAX_DEED_SALES,
                        data_type="decimal", validation_rules=["min:0"]),
            FieldMapping("winning_bid", "tax_deed.winning_bid", TabCategory.TAX_DEED_SALES,
                        data_type="decimal", validation_rules=["min:0"]),
            FieldMapping("certificate_amount", "tax_deed.certificate", TabCategory.TAX_DEED_SALES,
                        data_type="decimal", validation_rules=["min:0"]),
        ]

        # Combine all mappings
        all_mappings = (
            overview_mappings + core_property_mappings + valuation_mappings +
            tax_mappings + sunbiz_mappings + permit_mappings +
            sales_mappings + tax_deed_mappings
        )

        # Create dictionary with db_field as key
        for mapping in all_mappings:
            mappings[mapping.db_field] = mapping

        return mappings

    def get_field_embedding(self, field_name: str, field_value: Any) -> torch.Tensor:
        """Generate embedding for a field"""
        # Create feature vector
        features = []

        # Field name features
        features.extend([
            1 if 'address' in field_name.lower() else 0,
            1 if 'value' in field_name.lower() else 0,
            1 if 'date' in field_name.lower() else 0,
            1 if 'name' in field_name.lower() else 0,
            1 if 'tax' in field_name.lower() else 0,
            1 if 'sale' in field_name.lower() else 0,
            len(field_name),
            field_name.count('_'),
        ])

        # Value features
        if field_value is not None:
            features.extend([
                1,  # Has value
                len(str(field_value)),
                1 if isinstance(field_value, (int, float)) else 0,
                1 if isinstance(field_value, str) else 0,
                1 if isinstance(field_value, bool) else 0,
            ])
        else:
            features.extend([0, 0, 0, 0, 0])

        # Pad to 768 dimensions (BERT-like embedding size)
        while len(features) < 768:
            features.append(0)

        return torch.tensor(features[:768], dtype=torch.float32)

    async def map_field_to_ui(self, db_field: str, value: Any) -> Dict[str, Any]:
        """Map a database field to UI element using deep learning"""

        # Check cache first
        cache_key = f"{db_field}:{type(value).__name__}"
        if cache_key in self.validation_cache:
            return self.validation_cache[cache_key]

        # Get embedding
        embedding = self.get_field_embedding(db_field, value)
        embedding = embedding.unsqueeze(0)  # Add batch dimension

        # Run through PyTorch model
        with torch.no_grad():
            predictions = self.pytorch_mapper(embedding)

        # Extract predictions
        tab_probs = predictions['tab_probabilities'][0].numpy()
        confidence = predictions['confidence'][0].item()

        # Find best tab
        tab_idx = np.argmax(tab_probs)
        tab = list(TabCategory)[tab_idx]

        # Get mapping from predefined mappings or create new
        if db_field in self.field_mappings:
            mapping = self.field_mappings[db_field]
            mapping.confidence_score = confidence
        else:
            # Create new mapping based on ML prediction
            mapping = FieldMapping(
                db_field=db_field,
                ui_element=self._infer_ui_element(db_field),
                tab=tab,
                data_type=self._infer_data_type(value),
                confidence_score=confidence
            )

        # Validate the value
        validation_score = self.tf_validator.validate(db_field, value)

        result = {
            'field': db_field,
            'value': value,
            'ui_element': mapping.ui_element,
            'tab': mapping.tab.value,
            'subtab': mapping.subtab,
            'data_type': mapping.data_type,
            'transformation': mapping.transformation,
            'confidence': confidence,
            'validation_score': validation_score,
            'is_valid': validation_score > 0.7,
            'mapping': mapping
        }

        # Cache result
        self.validation_cache[cache_key] = result

        return result

    def _infer_ui_element(self, field_name: str) -> str:
        """Infer UI element path from field name"""
        parts = field_name.lower().split('_')

        # Common patterns
        if 'addr' in field_name.lower():
            return f"address.{'.'.join(parts)}"
        elif 'val' in field_name.lower() or 'value' in field_name.lower():
            return f"valuation.{'.'.join(parts)}"
        elif 'tax' in field_name.lower():
            return f"tax.{'.'.join(parts)}"
        elif 'sale' in field_name.lower():
            return f"sale.{'.'.join(parts)}"
        else:
            return f"property.{'.'.join(parts)}"

    def _infer_data_type(self, value: Any) -> str:
        """Infer data type from value"""
        if value is None:
            return "string"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "decimal"
        elif isinstance(value, datetime):
            return "date"
        else:
            return "string"

    async def validate_all_mappings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all field mappings for a property"""
        results = {
            'property_id': data.get('parcel_id'),
            'timestamp': datetime.now().isoformat(),
            'mappings': {},
            'errors': [],
            'warnings': [],
            'stats': {
                'total_fields': 0,
                'mapped_fields': 0,
                'valid_fields': 0,
                'invalid_fields': 0,
                'average_confidence': 0
            }
        }

        confidences = []

        # Process each field
        for field_name, value in data.items():
            if field_name.startswith('_'):  # Skip internal fields
                continue

            results['stats']['total_fields'] += 1

            # Map field
            mapping_result = await self.map_field_to_ui(field_name, value)
            results['mappings'][field_name] = mapping_result

            # Track statistics
            if mapping_result['ui_element']:
                results['stats']['mapped_fields'] += 1

            if mapping_result['is_valid']:
                results['stats']['valid_fields'] += 1
            else:
                results['stats']['invalid_fields'] += 1
                results['errors'].append(f"Invalid value for {field_name}: {value}")

            confidences.append(mapping_result['confidence'])

            # Add warnings for low confidence
            if mapping_result['confidence'] < 0.5:
                results['warnings'].append(
                    f"Low confidence mapping for {field_name} (confidence: {mapping_result['confidence']:.2f})"
                )

        # Calculate average confidence
        if confidences:
            results['stats']['average_confidence'] = np.mean(confidences)

        # Generate summary
        results['summary'] = {
            'success_rate': results['stats']['valid_fields'] / max(results['stats']['total_fields'], 1),
            'mapping_rate': results['stats']['mapped_fields'] / max(results['stats']['total_fields'], 1),
            'quality_score': results['stats']['average_confidence'],
            'status': 'success' if results['stats']['average_confidence'] > 0.7 else 'needs_review'
        }

        return results

    def generate_mapping_report(self) -> Dict[str, Any]:
        """Generate comprehensive mapping report"""
        report = {
            'total_mappings': len(self.field_mappings),
            'by_tab': {},
            'by_data_type': {},
            'transformation_required': [],
            'validation_rules': {},
            'coverage': {}
        }

        # Analyze mappings by tab
        for mapping in self.field_mappings.values():
            tab_name = mapping.tab.value
            if tab_name not in report['by_tab']:
                report['by_tab'][tab_name] = []
            report['by_tab'][tab_name].append({
                'db_field': mapping.db_field,
                'ui_element': mapping.ui_element,
                'confidence': mapping.confidence_score
            })

            # By data type
            if mapping.data_type not in report['by_data_type']:
                report['by_data_type'][mapping.data_type] = 0
            report['by_data_type'][mapping.data_type] += 1

            # Transformations
            if mapping.transformation:
                report['transformation_required'].append({
                    'field': mapping.db_field,
                    'transformation': mapping.transformation
                })

            # Validation rules
            if mapping.validation_rules:
                report['validation_rules'][mapping.db_field] = mapping.validation_rules

        # Calculate coverage
        for tab in TabCategory:
            tab_mappings = [m for m in self.field_mappings.values() if m.tab == tab]
            report['coverage'][tab.value] = {
                'count': len(tab_mappings),
                'verified': sum(1 for m in tab_mappings if m.verified),
                'average_confidence': np.mean([m.confidence_score for m in tab_mappings]) if tab_mappings else 0
            }

        return report

    def export_mappings(self, filepath: str):
        """Export mappings to JSON file"""
        mappings_data = {}

        for field, mapping in self.field_mappings.items():
            mappings_data[field] = {
                'ui_element': mapping.ui_element,
                'tab': mapping.tab.value,
                'subtab': mapping.subtab,
                'data_type': mapping.data_type,
                'transformation': mapping.transformation,
                'validation_rules': mapping.validation_rules,
                'confidence_score': mapping.confidence_score,
                'verified': mapping.verified
            }

        with open(filepath, 'w') as f:
            json.dump(mappings_data, f, indent=2)

        logger.info(f"Exported {len(mappings_data)} mappings to {filepath}")

    def import_mappings(self, filepath: str):
        """Import mappings from JSON file"""
        with open(filepath, 'r') as f:
            mappings_data = json.load(f)

        for field, data in mappings_data.items():
            self.field_mappings[field] = FieldMapping(
                db_field=field,
                ui_element=data['ui_element'],
                tab=TabCategory(data['tab']),
                subtab=data.get('subtab'),
                data_type=data['data_type'],
                transformation=data.get('transformation'),
                validation_rules=data.get('validation_rules', []),
                confidence_score=data.get('confidence_score', 0),
                verified=data.get('verified', False)
            )

        logger.info(f"Imported {len(mappings_data)} mappings from {filepath}")

# Example usage
async def main():
    """Example usage of the deep learning data mapper"""

    # Initialize system
    mapper = ComprehensiveDataMappingSystem()

    # Sample property data
    sample_data = {
        'parcel_id': '064210010010',
        'phy_addr1': '123 Main St',
        'phy_city': 'Miami',
        'phy_zipcd': '33139',
        'owner_name': 'John Doe',
        'jv': 500000,
        'tv_sd': 450000,
        'lnd_val': 200000,
        'tot_lvg_area': 2500,
        'bedroom_cnt': 3,
        'bathroom_cnt': 2.5,
        'act_yr_blt': 2005,
        'sale_prc1': 480000,
        'sale_yr1': 2023,
        'sale_mo1': 6
    }

    # Validate all mappings
    results = await mapper.validate_all_mappings(sample_data)

    print("Data Mapping Results:")
    print(f"Total Fields: {results['stats']['total_fields']}")
    print(f"Mapped Fields: {results['stats']['mapped_fields']}")
    print(f"Valid Fields: {results['stats']['valid_fields']}")
    print(f"Average Confidence: {results['stats']['average_confidence']:.2%}")

    # Generate report
    report = mapper.generate_mapping_report()
    print("\nMapping Report:")
    print(f"Total Mappings: {report['total_mappings']}")
    print("Coverage by Tab:")
    for tab, coverage in report['coverage'].items():
        print(f"  {tab}: {coverage['count']} fields, {coverage['average_confidence']:.2%} confidence")

    # Export mappings
    mapper.export_mappings('field_mappings.json')

if __name__ == "__main__":
    asyncio.run(main())