"""
Advanced Neural Network Field Mapper using Keras
Deep learning solution for intelligent data field matching and verification
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, callbacks
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import json
import re
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import asyncio

load_dotenv('.env.mcp')

@dataclass
class FieldMatch:
    """Enhanced field matching result with neural network confidence"""
    db_field: str
    db_table: str
    ui_tab: str
    ui_field: str
    confidence: float
    neural_score: float
    semantic_similarity: float
    pattern_match: float
    data_type: str
    transformation: Optional[str] = None

class NeuralFieldMapper:
    """Advanced neural network-based field mapping system"""

    def __init__(self):
        # Database connection
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # Neural network models
        self.field_classifier = None
        self.semantic_encoder = None
        self.pattern_detector = None

        # Preprocessing components
        self.label_encoder = LabelEncoder()
        self.scaler = StandardScaler()

        # Feature extractors
        self.char_vocab = {}
        self.word_vocab = {}
        self.pattern_vocab = {}

        # Configuration
        self.max_field_length = 50
        self.embedding_dim = 128
        self.hidden_units = 256

        # Load schema definitions
        self.db_schema = self._load_enhanced_schema()
        self.ui_schema = self._load_enhanced_ui_schema()

    def _load_enhanced_schema(self) -> Dict:
        """Load comprehensive database schema with metadata"""
        return {
            "florida_parcels": {
                "fields": {
                    # Core identification
                    "parcel_id": {"type": "varchar", "semantic": "identifier", "pattern": "ID_PATTERN"},
                    "county": {"type": "varchar", "semantic": "location", "pattern": "NAME_PATTERN"},
                    "year": {"type": "integer", "semantic": "temporal", "pattern": "YEAR_PATTERN"},

                    # Owner information
                    "owner_name": {"type": "varchar", "semantic": "person_name", "pattern": "NAME_PATTERN"},
                    "owner_addr1": {"type": "varchar", "semantic": "address", "pattern": "ADDRESS_PATTERN"},
                    "owner_addr2": {"type": "varchar", "semantic": "address", "pattern": "ADDRESS_PATTERN"},
                    "owner_city": {"type": "varchar", "semantic": "location", "pattern": "NAME_PATTERN"},
                    "owner_state": {"type": "varchar", "semantic": "location", "pattern": "STATE_PATTERN"},
                    "owner_zip": {"type": "varchar", "semantic": "postal", "pattern": "ZIP_PATTERN"},

                    # Physical address
                    "phy_addr1": {"type": "varchar", "semantic": "address", "pattern": "ADDRESS_PATTERN"},
                    "phy_addr2": {"type": "varchar", "semantic": "address", "pattern": "ADDRESS_PATTERN"},
                    "phy_city": {"type": "varchar", "semantic": "location", "pattern": "NAME_PATTERN"},
                    "phy_state": {"type": "varchar", "semantic": "location", "pattern": "STATE_PATTERN"},
                    "phy_zipcd": {"type": "varchar", "semantic": "postal", "pattern": "ZIP_PATTERN"},

                    # Legal description
                    "legal_desc": {"type": "text", "semantic": "description", "pattern": "TEXT_PATTERN"},
                    "subdivision": {"type": "varchar", "semantic": "location", "pattern": "NAME_PATTERN"},
                    "lot": {"type": "varchar", "semantic": "identifier", "pattern": "LOT_PATTERN"},
                    "block": {"type": "varchar", "semantic": "identifier", "pattern": "BLOCK_PATTERN"},

                    # Property characteristics
                    "property_use": {"type": "varchar", "semantic": "category", "pattern": "CODE_PATTERN"},
                    "property_use_desc": {"type": "varchar", "semantic": "description", "pattern": "TEXT_PATTERN"},
                    "land_use_code": {"type": "varchar", "semantic": "category", "pattern": "CODE_PATTERN"},
                    "zoning": {"type": "varchar", "semantic": "category", "pattern": "ZONE_PATTERN"},

                    # Valuations
                    "just_value": {"type": "float", "semantic": "currency", "pattern": "MONEY_PATTERN"},
                    "assessed_value": {"type": "float", "semantic": "currency", "pattern": "MONEY_PATTERN"},
                    "taxable_value": {"type": "float", "semantic": "currency", "pattern": "MONEY_PATTERN"},
                    "land_value": {"type": "float", "semantic": "currency", "pattern": "MONEY_PATTERN"},
                    "building_value": {"type": "float", "semantic": "currency", "pattern": "MONEY_PATTERN"},

                    # Property details
                    "year_built": {"type": "integer", "semantic": "temporal", "pattern": "YEAR_PATTERN"},
                    "total_living_area": {"type": "float", "semantic": "measurement", "pattern": "AREA_PATTERN"},
                    "bedrooms": {"type": "integer", "semantic": "count", "pattern": "COUNT_PATTERN"},
                    "bathrooms": {"type": "float", "semantic": "count", "pattern": "COUNT_PATTERN"},
                    "stories": {"type": "float", "semantic": "count", "pattern": "COUNT_PATTERN"},
                    "units": {"type": "integer", "semantic": "count", "pattern": "COUNT_PATTERN"},

                    # Land measurements
                    "land_sqft": {"type": "float", "semantic": "measurement", "pattern": "AREA_PATTERN"},
                    "land_acres": {"type": "float", "semantic": "measurement", "pattern": "AREA_PATTERN"},

                    # Sales information
                    "sale_date": {"type": "timestamp", "semantic": "temporal", "pattern": "DATE_PATTERN"},
                    "sale_price": {"type": "float", "semantic": "currency", "pattern": "MONEY_PATTERN"},
                    "sale_qualification": {"type": "varchar", "semantic": "category", "pattern": "CODE_PATTERN"}
                }
            },

            "sunbiz_entities": {
                "fields": {
                    "entity_name": {"type": "varchar", "semantic": "business_name", "pattern": "BUSINESS_PATTERN"},
                    "entity_type": {"type": "varchar", "semantic": "category", "pattern": "TYPE_PATTERN"},
                    "filing_date": {"type": "timestamp", "semantic": "temporal", "pattern": "DATE_PATTERN"},
                    "status": {"type": "varchar", "semantic": "status", "pattern": "STATUS_PATTERN"},
                    "document_number": {"type": "varchar", "semantic": "identifier", "pattern": "DOC_PATTERN"},
                    "ein": {"type": "varchar", "semantic": "identifier", "pattern": "EIN_PATTERN"},
                    "registered_agent_name": {"type": "varchar", "semantic": "person_name", "pattern": "NAME_PATTERN"},
                    "registered_agent_address": {"type": "varchar", "semantic": "address", "pattern": "ADDRESS_PATTERN"},
                    "principal_address": {"type": "varchar", "semantic": "address", "pattern": "ADDRESS_PATTERN"},
                    "mailing_address": {"type": "varchar", "semantic": "address", "pattern": "ADDRESS_PATTERN"}
                }
            },

            "building_permits": {
                "fields": {
                    "permit_number": {"type": "varchar", "semantic": "identifier", "pattern": "PERMIT_PATTERN"},
                    "parcel_id": {"type": "varchar", "semantic": "identifier", "pattern": "ID_PATTERN"},
                    "permit_type": {"type": "varchar", "semantic": "category", "pattern": "TYPE_PATTERN"},
                    "issue_date": {"type": "timestamp", "semantic": "temporal", "pattern": "DATE_PATTERN"},
                    "work_description": {"type": "text", "semantic": "description", "pattern": "TEXT_PATTERN"},
                    "contractor_name": {"type": "varchar", "semantic": "business_name", "pattern": "BUSINESS_PATTERN"},
                    "estimated_value": {"type": "float", "semantic": "currency", "pattern": "MONEY_PATTERN"}
                }
            },

            "tax_deed_sales": {
                "fields": {
                    "td_number": {"type": "varchar", "semantic": "identifier", "pattern": "TD_PATTERN"},
                    "parcel_id": {"type": "varchar", "semantic": "identifier", "pattern": "ID_PATTERN"},
                    "auction_date": {"type": "timestamp", "semantic": "temporal", "pattern": "DATE_PATTERN"},
                    "opening_bid": {"type": "float", "semantic": "currency", "pattern": "MONEY_PATTERN"},
                    "winning_bid": {"type": "float", "semantic": "currency", "pattern": "MONEY_PATTERN"},
                    "winner_name": {"type": "varchar", "semantic": "person_name", "pattern": "NAME_PATTERN"},
                    "status": {"type": "varchar", "semantic": "status", "pattern": "STATUS_PATTERN"}
                }
            }
        }

    def _load_enhanced_ui_schema(self) -> Dict:
        """Load comprehensive UI schema with semantic information"""
        return {
            "overview": {
                "semantic_category": "summary",
                "fields": {
                    "property_address": {"semantic": "address", "display_type": "text", "importance": 1.0},
                    "owner_name": {"semantic": "person_name", "display_type": "text", "importance": 1.0},
                    "market_value": {"semantic": "currency", "display_type": "currency", "importance": 0.9},
                    "taxable_value": {"semantic": "currency", "display_type": "currency", "importance": 0.9},
                    "year_built": {"semantic": "temporal", "display_type": "year", "importance": 0.7},
                    "living_area": {"semantic": "measurement", "display_type": "area", "importance": 0.8},
                    "bedrooms": {"semantic": "count", "display_type": "integer", "importance": 0.6},
                    "bathrooms": {"semantic": "count", "display_type": "decimal", "importance": 0.6}
                }
            },

            "core-property": {
                "semantic_category": "identification",
                "fields": {
                    "parcel_id": {"semantic": "identifier", "display_type": "text", "importance": 1.0},
                    "property_type": {"semantic": "category", "display_type": "text", "importance": 0.9},
                    "zoning": {"semantic": "category", "display_type": "text", "importance": 0.8},
                    "land_size": {"semantic": "measurement", "display_type": "area", "importance": 0.8},
                    "land_acres": {"semantic": "measurement", "display_type": "decimal", "importance": 0.7},
                    "legal_description": {"semantic": "description", "display_type": "text", "importance": 0.6},
                    "subdivision": {"semantic": "location", "display_type": "text", "importance": 0.7},
                    "lot_number": {"semantic": "identifier", "display_type": "text", "importance": 0.6},
                    "block_number": {"semantic": "identifier", "display_type": "text", "importance": 0.6}
                }
            },

            "valuation": {
                "semantic_category": "financial",
                "fields": {
                    "just_value": {"semantic": "currency", "display_type": "currency", "importance": 1.0},
                    "assessed_value": {"semantic": "currency", "display_type": "currency", "importance": 0.9},
                    "taxable_value": {"semantic": "currency", "display_type": "currency", "importance": 1.0},
                    "land_value": {"semantic": "currency", "display_type": "currency", "importance": 0.8},
                    "building_value": {"semantic": "currency", "display_type": "currency", "importance": 0.8},
                    "annual_tax": {"semantic": "currency", "display_type": "currency", "importance": 0.7}
                }
            },

            "owner": {
                "semantic_category": "ownership",
                "fields": {
                    "owner_name": {"semantic": "person_name", "display_type": "text", "importance": 1.0},
                    "mailing_address": {"semantic": "address", "display_type": "text", "importance": 0.9},
                    "city": {"semantic": "location", "display_type": "text", "importance": 0.8},
                    "state": {"semantic": "location", "display_type": "text", "importance": 0.8},
                    "zip_code": {"semantic": "postal", "display_type": "text", "importance": 0.8}
                }
            },

            "building": {
                "semantic_category": "structure",
                "fields": {
                    "year_built": {"semantic": "temporal", "display_type": "year", "importance": 0.9},
                    "living_area": {"semantic": "measurement", "display_type": "area", "importance": 0.9},
                    "bedrooms": {"semantic": "count", "display_type": "integer", "importance": 0.8},
                    "bathrooms": {"semantic": "count", "display_type": "decimal", "importance": 0.8},
                    "stories": {"semantic": "count", "display_type": "decimal", "importance": 0.6},
                    "units": {"semantic": "count", "display_type": "integer", "importance": 0.7}
                }
            },

            "sales": {
                "semantic_category": "transactions",
                "fields": {
                    "sale_date": {"semantic": "temporal", "display_type": "date", "importance": 1.0},
                    "sale_price": {"semantic": "currency", "display_type": "currency", "importance": 1.0},
                    "sale_type": {"semantic": "category", "display_type": "text", "importance": 0.7}
                }
            },

            "sunbiz": {
                "semantic_category": "business",
                "fields": {
                    "business_name": {"semantic": "business_name", "display_type": "text", "importance": 1.0},
                    "entity_type": {"semantic": "category", "display_type": "text", "importance": 0.9},
                    "filing_date": {"semantic": "temporal", "display_type": "date", "importance": 0.8},
                    "status": {"semantic": "status", "display_type": "text", "importance": 0.9},
                    "registered_agent": {"semantic": "person_name", "display_type": "text", "importance": 0.7},
                    "principal_address": {"semantic": "address", "display_type": "text", "importance": 0.8}
                }
            },

            "permit": {
                "semantic_category": "regulatory",
                "fields": {
                    "permit_number": {"semantic": "identifier", "display_type": "text", "importance": 1.0},
                    "permit_type": {"semantic": "category", "display_type": "text", "importance": 0.9},
                    "issue_date": {"semantic": "temporal", "display_type": "date", "importance": 0.8},
                    "description": {"semantic": "description", "display_type": "text", "importance": 0.7},
                    "contractor": {"semantic": "business_name", "display_type": "text", "importance": 0.6},
                    "estimated_value": {"semantic": "currency", "display_type": "currency", "importance": 0.7}
                }
            },

            "tax-deed-sales": {
                "semantic_category": "auctions",
                "fields": {
                    "td_number": {"semantic": "identifier", "display_type": "text", "importance": 1.0},
                    "auction_date": {"semantic": "temporal", "display_type": "date", "importance": 1.0},
                    "opening_bid": {"semantic": "currency", "display_type": "currency", "importance": 0.9},
                    "winning_bid": {"semantic": "currency", "display_type": "currency", "importance": 0.9},
                    "winner": {"semantic": "person_name", "display_type": "text", "importance": 0.8},
                    "status": {"semantic": "status", "display_type": "text", "importance": 0.8}
                }
            }
        }

    def build_neural_networks(self):
        """Build and compile multiple neural networks for different aspects"""
        print("Building neural network architectures...")

        # 1. Field Classification Network
        self.field_classifier = self._build_field_classifier()

        # 2. Semantic Similarity Network
        self.semantic_encoder = self._build_semantic_encoder()

        # 3. Pattern Detection Network
        self.pattern_detector = self._build_pattern_detector()

        print("✓ Neural networks built successfully")

    def _build_field_classifier(self) -> keras.Model:
        """Build main field classification network"""
        # Input layers
        db_field_input = layers.Input(shape=(self.max_field_length,), name='db_field')
        ui_field_input = layers.Input(shape=(self.max_field_length,), name='ui_field')
        semantic_input = layers.Input(shape=(10,), name='semantic_features')

        # Character-level embeddings
        char_embedding = layers.Embedding(256, self.embedding_dim, mask_zero=True)

        # Process database field
        db_embedded = char_embedding(db_field_input)
        db_lstm = layers.LSTM(self.hidden_units, return_sequences=True)(db_embedded)
        db_attention = layers.GlobalAveragePooling1D()(db_lstm)

        # Process UI field
        ui_embedded = char_embedding(ui_field_input)
        ui_lstm = layers.LSTM(self.hidden_units, return_sequences=True)(ui_embedded)
        ui_attention = layers.GlobalAveragePooling1D()(ui_lstm)

        # Combine features
        combined = layers.Concatenate()([db_attention, ui_attention, semantic_input])

        # Deep classification layers
        dense1 = layers.Dense(512, activation='relu')(combined)
        dropout1 = layers.Dropout(0.3)(dense1)
        dense2 = layers.Dense(256, activation='relu')(dropout1)
        dropout2 = layers.Dropout(0.2)(dense2)
        dense3 = layers.Dense(128, activation='relu')(dropout2)

        # Output layer (binary classification: match/no-match)
        output = layers.Dense(1, activation='sigmoid', name='match_probability')(dense3)

        model = keras.Model(
            inputs=[db_field_input, ui_field_input, semantic_input],
            outputs=output
        )

        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )

        return model

    def _build_semantic_encoder(self) -> keras.Model:
        """Build semantic similarity encoder"""
        input_text = layers.Input(shape=(self.max_field_length,), name='text_input')

        # Character embedding
        embedding = layers.Embedding(256, 64, mask_zero=True)(input_text)

        # Bidirectional LSTM
        lstm = layers.Bidirectional(layers.LSTM(128, return_sequences=True))(embedding)

        # Self-attention mechanism
        attention = layers.MultiHeadAttention(num_heads=8, key_dim=64)(lstm, lstm)
        attention = layers.GlobalAveragePooling1D()(attention)

        # Semantic encoding
        semantic_vector = layers.Dense(128, activation='tanh', name='semantic_encoding')(attention)

        model = keras.Model(inputs=input_text, outputs=semantic_vector)
        return model

    def _build_pattern_detector(self) -> keras.Model:
        """Build pattern detection network"""
        input_field = layers.Input(shape=(self.max_field_length,), name='field_input')

        # Convolutional layers for pattern detection
        conv1 = layers.Conv1D(64, 3, activation='relu', padding='same')(
            layers.Embedding(256, 32)(input_field)
        )
        pool1 = layers.MaxPooling1D(2)(conv1)

        conv2 = layers.Conv1D(128, 3, activation='relu', padding='same')(pool1)
        pool2 = layers.MaxPooling1D(2)(conv2)

        conv3 = layers.Conv1D(256, 3, activation='relu', padding='same')(pool2)
        global_pool = layers.GlobalMaxPooling1D()(conv3)

        # Pattern classification
        dense = layers.Dense(128, activation='relu')(global_pool)
        pattern_output = layers.Dense(len(self._get_pattern_types()), activation='softmax')(dense)

        model = keras.Model(inputs=input_field, outputs=pattern_output)
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

        return model

    def _get_pattern_types(self) -> List[str]:
        """Get list of pattern types for classification"""
        return [
            'ID_PATTERN', 'NAME_PATTERN', 'ADDRESS_PATTERN', 'DATE_PATTERN',
            'MONEY_PATTERN', 'AREA_PATTERN', 'COUNT_PATTERN', 'CODE_PATTERN',
            'ZIP_PATTERN', 'STATE_PATTERN', 'YEAR_PATTERN', 'TEXT_PATTERN'
        ]

    def generate_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate comprehensive training data for neural networks"""
        print("Generating training data...")

        training_samples = []
        labels = []

        # Generate positive samples (correct mappings)
        for table_name, table_info in self.db_schema.items():
            for db_field, field_info in table_info["fields"].items():
                semantic_type = field_info["semantic"]

                # Find matching UI fields
                for tab_name, tab_info in self.ui_schema.items():
                    for ui_field, ui_info in tab_info["fields"].items():
                        if ui_info["semantic"] == semantic_type:
                            # This is a positive match
                            features = self._extract_neural_features(
                                db_field, ui_field, table_name, tab_name
                            )
                            training_samples.append(features)
                            labels.append(1)

                            # Generate negative samples
                            for other_tab, other_tab_info in self.ui_schema.items():
                                for other_ui_field, other_ui_info in other_tab_info["fields"].items():
                                    if (other_ui_info["semantic"] != semantic_type and
                                        np.random.random() < 0.1):  # Sample 10% of negative cases
                                        neg_features = self._extract_neural_features(
                                            db_field, other_ui_field, table_name, other_tab
                                        )
                                        training_samples.append(neg_features)
                                        labels.append(0)

        X = np.array(training_samples)
        y = np.array(labels)

        print(f"✓ Generated {len(X)} training samples ({sum(y)} positive, {len(y)-sum(y)} negative)")
        return X, y

    def _extract_neural_features(self, db_field: str, ui_field: str,
                                table_name: str, tab_name: str) -> List[float]:
        """Extract comprehensive features for neural network"""
        features = []

        # String similarity features
        features.extend(self._string_similarity_features(db_field, ui_field))

        # Semantic features
        features.extend(self._semantic_features(db_field, ui_field, table_name, tab_name))

        # Pattern features
        features.extend(self._pattern_features(db_field))

        # Context features
        features.extend(self._context_features(table_name, tab_name))

        return features

    def _string_similarity_features(self, db_field: str, ui_field: str) -> List[float]:
        """Extract string similarity features"""
        features = []

        # Exact match
        features.append(1.0 if db_field.lower() == ui_field.lower() else 0.0)

        # Substring match
        features.append(1.0 if ui_field.lower() in db_field.lower() or
                       db_field.lower() in ui_field.lower() else 0.0)

        # Word overlap
        db_words = set(re.findall(r'\w+', db_field.lower()))
        ui_words = set(re.findall(r'\w+', ui_field.lower()))
        overlap = len(db_words & ui_words) / max(len(db_words | ui_words), 1)
        features.append(overlap)

        # Character overlap
        db_chars = set(db_field.lower())
        ui_chars = set(ui_field.lower())
        char_overlap = len(db_chars & ui_chars) / max(len(db_chars | ui_chars), 1)
        features.append(char_overlap)

        # Length similarity
        len_sim = 1 - abs(len(db_field) - len(ui_field)) / max(len(db_field), len(ui_field), 1)
        features.append(len_sim)

        return features

    def _semantic_features(self, db_field: str, ui_field: str,
                          table_name: str, tab_name: str) -> List[float]:
        """Extract semantic similarity features"""
        features = []

        # Get semantic types
        db_semantic = self.db_schema.get(table_name, {}).get("fields", {}).get(db_field, {}).get("semantic", "unknown")
        ui_semantic = self.ui_schema.get(tab_name, {}).get("fields", {}).get(ui_field, {}).get("semantic", "unknown")

        # Semantic type match
        features.append(1.0 if db_semantic == ui_semantic else 0.0)

        # Category compatibility
        category_map = {
            "currency": ["currency", "financial"],
            "measurement": ["measurement", "area"],
            "temporal": ["temporal", "date", "year"],
            "location": ["location", "address"],
            "identifier": ["identifier", "id"],
            "person_name": ["person_name", "name"],
            "business_name": ["business_name", "name"]
        }

        compatibility = 0.0
        for category, types in category_map.items():
            if db_semantic in types and ui_semantic in types:
                compatibility = 1.0
                break
            elif db_semantic in types or ui_semantic in types:
                compatibility = 0.5

        features.append(compatibility)

        # UI importance weight
        importance = self.ui_schema.get(tab_name, {}).get("fields", {}).get(ui_field, {}).get("importance", 0.5)
        features.append(importance)

        return features

    def _pattern_features(self, db_field: str) -> List[float]:
        """Extract pattern-based features"""
        features = []

        # Common patterns
        patterns = {
            'has_id': r'id|num|number',
            'has_name': r'name|nm',
            'has_addr': r'addr|address',
            'has_date': r'date|dt|yr|year',
            'has_value': r'value|val|amount|price',
            'has_area': r'sqft|area|acr|acre',
            'has_count': r'count|cnt|bed|bath',
            'has_code': r'code|cd|type|use'
        }

        for pattern_name, pattern in patterns.items():
            match = 1.0 if re.search(pattern, db_field.lower()) else 0.0
            features.append(match)

        return features

    def _context_features(self, table_name: str, tab_name: str) -> List[float]:
        """Extract contextual features"""
        features = []

        # Table-tab compatibility
        table_contexts = {
            "florida_parcels": ["overview", "core-property", "valuation", "owner", "building", "sales"],
            "sunbiz_entities": ["sunbiz"],
            "building_permits": ["permit"],
            "tax_deed_sales": ["tax-deed-sales"]
        }

        compatibility = 1.0 if tab_name in table_contexts.get(table_name, []) else 0.0
        features.append(compatibility)

        return features

    def train_neural_networks(self):
        """Train all neural networks"""
        print("Training neural networks...")

        # Generate training data
        X, y = self.generate_training_data()

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Prepare inputs for main classifier
        db_fields_train = np.array([self._encode_field(sample[0]) for sample in X_train])
        ui_fields_train = np.array([self._encode_field(sample[1]) for sample in X_train])
        semantic_features_train = np.array([sample[2:] for sample in X_train])

        # Train main classifier
        callbacks_list = [
            keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(patience=5, factor=0.5)
        ]

        history = self.field_classifier.fit(
            [db_fields_train, ui_fields_train, semantic_features_train],
            y_train,
            validation_split=0.2,
            epochs=100,
            batch_size=32,
            callbacks=callbacks_list,
            verbose=1
        )

        # Evaluate model
        predictions = self.field_classifier.predict([
            np.array([self._encode_field(sample[0]) for sample in X_test]),
            np.array([self._encode_field(sample[1]) for sample in X_test]),
            np.array([sample[2:] for sample in X_test])
        ])

        y_pred = (predictions > 0.5).astype(int).flatten()

        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))

        # Save models
        self.field_classifier.save('models/field_classifier.h5')
        print("✓ Neural networks trained and saved")

        return history

    def _encode_field(self, field_name: str) -> np.ndarray:
        """Encode field name for neural network input"""
        # Convert to character indices
        encoded = np.zeros(self.max_field_length, dtype=int)
        for i, char in enumerate(field_name[:self.max_field_length]):
            encoded[i] = ord(char) if ord(char) < 256 else 0
        return encoded

    async def find_optimal_mappings(self) -> Dict[str, List[FieldMatch]]:
        """Find optimal field mappings using neural networks"""
        print("Finding optimal field mappings...")

        all_mappings = {}

        for table_name, table_info in self.db_schema.items():
            table_mappings = []

            for db_field, field_info in table_info["fields"].items():
                best_match = None
                best_score = 0.0

                # Test against all UI fields
                for tab_name, tab_info in self.ui_schema.items():
                    for ui_field, ui_info in tab_info["fields"].items():

                        # Extract features
                        features = self._extract_neural_features(
                            db_field, ui_field, table_name, tab_name
                        )

                        # Get neural network prediction
                        db_encoded = self._encode_field(db_field).reshape(1, -1)
                        ui_encoded = self._encode_field(ui_field).reshape(1, -1)
                        semantic_features = np.array(features).reshape(1, -1)

                        neural_score = self.field_classifier.predict([
                            db_encoded, ui_encoded, semantic_features
                        ])[0][0]

                        # Calculate composite score
                        semantic_sim = features[5] if len(features) > 5 else 0.0
                        pattern_match = sum(features[8:16]) / 8 if len(features) > 15 else 0.0

                        composite_score = (
                            neural_score * 0.6 +
                            semantic_sim * 0.3 +
                            pattern_match * 0.1
                        )

                        if composite_score > best_score and composite_score > 0.7:
                            best_score = composite_score
                            best_match = FieldMatch(
                                db_field=db_field,
                                db_table=table_name,
                                ui_tab=tab_name,
                                ui_field=ui_field,
                                confidence=composite_score,
                                neural_score=neural_score,
                                semantic_similarity=semantic_sim,
                                pattern_match=pattern_match,
                                data_type=ui_info.get("display_type", "text"),
                                transformation=self._get_transformation(
                                    field_info.get("type"), ui_info.get("display_type")
                                )
                            )

                if best_match:
                    table_mappings.append(best_match)
                    print(f"✓ {table_name}.{db_field} → {best_match.ui_tab}.{best_match.ui_field} "
                          f"(score: {best_match.confidence:.3f})")

            all_mappings[table_name] = table_mappings

        return all_mappings

    def _get_transformation(self, db_type: str, ui_type: str) -> Optional[str]:
        """Determine required data transformation"""
        transformations = {
            ("float", "currency"): "format_currency",
            ("float", "area"): "format_area",
            ("timestamp", "date"): "format_date",
            ("integer", "year"): "format_year",
            ("float", "decimal"): "round_decimal"
        }
        return transformations.get((db_type, ui_type))

    def export_neural_mappings(self, mappings: Dict[str, List[FieldMatch]], filepath: str):
        """Export neural network mappings to JSON"""
        export_data = {
            "version": "2.0",
            "model_type": "keras_neural_network",
            "generated": datetime.now().isoformat(),
            "mappings": {}
        }

        for table_name, table_mappings in mappings.items():
            export_data["mappings"][table_name] = [
                {
                    "db_field": m.db_field,
                    "db_table": m.db_table,
                    "ui_tab": m.ui_tab,
                    "ui_field": m.ui_field,
                    "confidence": float(m.confidence),
                    "neural_score": float(m.neural_score),
                    "semantic_similarity": float(m.semantic_similarity),
                    "pattern_match": float(m.pattern_match),
                    "data_type": m.data_type,
                    "transformation": m.transformation
                }
                for m in table_mappings
            ]

        # Create models directory
        os.makedirs("models", exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"✓ Neural network mappings exported to {filepath}")


async def main():
    """Run the neural field mapper"""
    mapper = NeuralFieldMapper()

    print("Starting Keras Neural Network Field Mapper...")
    print("=" * 60)

    # Build neural networks
    mapper.build_neural_networks()

    # Train networks
    mapper.train_neural_networks()

    # Find optimal mappings
    mappings = await mapper.find_optimal_mappings()

    # Export results
    mapper.export_neural_mappings(mappings, "models/neural_field_mappings.json")

    print("\n" + "=" * 60)
    print("✓ Neural network field mapping complete!")
    print("✓ Models saved to: models/")
    print("✓ Mappings saved to: models/neural_field_mappings.json")


if __name__ == "__main__":
    asyncio.run(main())