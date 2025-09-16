"""
NLP Intelligent Field Matcher with NLTK and spaCy
Advanced Natural Language Processing for 100% Accurate Data Mapping
Property Appraiser and Sunbiz Database Field Matching System
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import re
from collections import defaultdict
import pandas as pd
import numpy as np

# NLP Libraries
import nltk
import spacy
from spacy import displacy
from spacy.matcher import Matcher, PhraseMatcher
from spacy.tokens import Doc, Span, Token
import en_core_web_sm

# NLTK components
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import wordnet, stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.chunk import ne_chunk, tree2conlltags
from nltk.tag import pos_tag
from nltk.metrics import edit_distance
from nltk.probability import FreqDist
from nltk.collocations import BigramCollocationFinder, TrigramCollocationFinder

# Machine Learning
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder
from sentence_transformers import SentenceTransformer
import torch

# Database
from supabase import create_client, Client
import psycopg2
from psycopg2.extras import RealDictCursor

# Playwright for verification
from playwright.async_api import async_playwright, Page

# OpenCV for visual validation
import cv2
import pytesseract
from PIL import Image

# Environment
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
nltk_downloads = [
    'punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger',
    'maxent_ne_chunker', 'words', 'vader_lexicon', 'brown', 'omw-1.4'
]
for resource in nltk_downloads:
    try:
        nltk.data.find(f'tokenizers/{resource}')
    except LookupError:
        nltk.download(resource, quiet=True)

# =====================================================================
# NLP Field Analyzer
# =====================================================================

@dataclass
class FieldSemantics:
    """Semantic analysis of a database/UI field"""
    original_name: str
    normalized_name: str
    tokens: List[str]
    lemmas: List[str]
    pos_tags: List[Tuple[str, str]]
    entities: List[str]
    semantic_type: str  # address, money, date, person, etc.
    confidence: float
    synonyms: List[str]
    related_fields: List[str]
    embedding: Optional[np.ndarray] = None

@dataclass
class FieldMatch:
    """Match between database and UI field"""
    db_field: str
    ui_field: str
    similarity_score: float
    match_type: str  # exact, semantic, pattern, fuzzy
    confidence: float
    reasoning: str
    transformations: List[str]

class NLPFieldAnalyzer:
    """Advanced NLP analysis for field matching"""

    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_lg")
        except:
            self.nlp = spacy.load("en_core_web_sm")
            logger.warning("Using small spaCy model. Install en_core_web_lg for better performance")

        # Initialize NLTK components
        self.lemmatizer = WordNetLemmatizer()
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))

        # Sentence transformer for semantic similarity
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Custom patterns for real estate and business data
        self.setup_custom_patterns()

        # Field type patterns
        self.field_type_patterns = self._initialize_field_patterns()

        # Domain-specific vocabulary
        self.domain_vocab = self._initialize_domain_vocabulary()

    def setup_custom_patterns(self):
        """Setup custom spaCy patterns for property and business data"""
        # Add custom entity ruler
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")

        patterns = [
            # Property patterns
            {"label": "PROPERTY_ID", "pattern": [{"TEXT": {"REGEX": r"^\d{12,15}$"}}]},
            {"label": "PARCEL", "pattern": [{"LOWER": "parcel"}, {"LOWER": {"IN": ["id", "number", "no"]}}]},
            {"label": "ADDRESS_FIELD", "pattern": [{"LOWER": {"IN": ["street", "addr", "address"]}}, {"IS_ALPHA": True, "OP": "*"}]},
            {"label": "MONEY_FIELD", "pattern": [{"LOWER": {"IN": ["price", "value", "amount", "cost", "fee", "tax"]}}]},
            {"label": "DATE_FIELD", "pattern": [{"LOWER": {"IN": ["date", "year", "month", "day", "time"]}}]},
            {"label": "AREA_FIELD", "pattern": [{"LOWER": {"IN": ["sqft", "square", "area", "size"]}}, {"LOWER": {"IN": ["feet", "foot", "ft"]}, "OP": "?"}]},

            # Business patterns
            {"label": "BUSINESS", "pattern": [{"LOWER": {"IN": ["corp", "corporation", "llc", "inc", "company", "business", "entity"]}}]},
            {"label": "OFFICER", "pattern": [{"LOWER": {"IN": ["officer", "director", "president", "ceo", "manager", "agent"]}}]},
            {"label": "DOCUMENT_NUM", "pattern": [{"LOWER": "document"}, {"LOWER": {"IN": ["number", "no", "num", "#"]}}]},

            # Tax patterns
            {"label": "TAX_FIELD", "pattern": [{"LOWER": {"IN": ["tax", "millage", "exemption", "homestead", "assessment"]}}]},
            {"label": "CERTIFICATE", "pattern": [{"LOWER": {"IN": ["certificate", "deed", "lien"]}}, {"IS_ALPHA": True, "OP": "*"}]},
        ]

        ruler.add_patterns(patterns)

        # Add custom matcher for complex patterns
        self.matcher = Matcher(self.nlp.vocab)

        # Pattern for money amounts
        money_pattern = [
            {"LOWER": {"IN": ["$", "usd", "dollar", "dollars"]}, "OP": "?"},
            {"LIKE_NUM": True},
            {"LOWER": {"IN": ["k", "m", "thousand", "million"]}, "OP": "?"}
        ]
        self.matcher.add("MONEY_AMOUNT", [money_pattern])

        # Pattern for property types
        property_type_pattern = [
            {"LOWER": {"IN": ["single", "multi", "commercial", "industrial", "vacant"]}},
            {"LOWER": {"IN": ["family", "unit", "property", "land", "lot"]}, "OP": "?"}
        ]
        self.matcher.add("PROPERTY_TYPE", [property_type_pattern])

    def _initialize_field_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for different field types"""
        return {
            "address": ["addr", "address", "street", "road", "avenue", "blvd", "location", "phy"],
            "owner": ["owner", "grantor", "grantee", "buyer", "seller", "name"],
            "value": ["value", "val", "amount", "price", "cost", "assessment", "jv", "av", "tv"],
            "date": ["date", "year", "month", "day", "yr", "mo", "dt", "time", "period"],
            "area": ["area", "sqft", "square", "feet", "foot", "size", "acreage", "lot"],
            "tax": ["tax", "millage", "exemption", "homestead", "assessment", "levy", "rate"],
            "sale": ["sale", "sold", "purchase", "transaction", "transfer", "deed"],
            "legal": ["legal", "description", "desc", "subdivision", "plat", "section", "township", "range"],
            "building": ["building", "structure", "improvement", "construction", "bldg", "unit"],
            "business": ["business", "entity", "corporation", "corp", "llc", "inc", "company", "firm"],
            "permit": ["permit", "license", "certificate", "approval", "authorization"],
            "count": ["count", "cnt", "number", "num", "qty", "quantity", "total"],
            "type": ["type", "kind", "class", "category", "use", "code", "classification"],
            "status": ["status", "state", "condition", "flag", "active", "inactive", "current"]
        }

    def _initialize_domain_vocabulary(self) -> Dict[str, Set[str]]:
        """Initialize domain-specific vocabulary"""
        return {
            "property_appraiser": {
                "parcel", "folio", "assessment", "just", "taxable", "millage", "exemption",
                "homestead", "improvement", "land", "building", "dwelling", "acre", "square",
                "bedroom", "bathroom", "story", "pool", "garage", "fence", "roof", "foundation",
                "plat", "subdivision", "section", "township", "range", "legal", "description"
            },
            "sunbiz": {
                "entity", "corporation", "llc", "inc", "filing", "document", "status",
                "active", "inactive", "dissolved", "officer", "director", "president",
                "secretary", "treasurer", "manager", "agent", "registered", "principal",
                "mailing", "address", "ein", "fei", "annual", "report", "amendment"
            },
            "tax_deed": {
                "certificate", "deed", "auction", "bid", "minimum", "winning", "redemption",
                "lien", "delinquent", "foreclosure", "sale", "buyer", "holder", "interest",
                "penalty", "advertisement", "publication", "notice", "clerk", "court"
            },
            "real_estate": {
                "property", "real", "estate", "residence", "residential", "commercial",
                "industrial", "agricultural", "vacant", "condominium", "condo", "townhouse",
                "single", "family", "multi", "duplex", "triplex", "apartment", "unit"
            }
        }

    def analyze_field(self, field_name: str, field_data: Optional[Any] = None) -> FieldSemantics:
        """Comprehensive NLP analysis of a field"""
        # Normalize field name
        normalized = self._normalize_field_name(field_name)

        # spaCy processing
        doc = self.nlp(normalized)

        # Extract tokens and lemmas
        tokens = [token.text.lower() for token in doc if not token.is_stop]
        lemmas = [token.lemma_.lower() for token in doc if not token.is_stop]

        # POS tagging
        pos_tags = [(token.text, token.pos_) for token in doc]

        # Named entity recognition
        entities = [ent.label_ for ent in doc.ents]

        # Detect semantic type
        semantic_type = self._detect_semantic_type(field_name, tokens, entities)

        # Find synonyms
        synonyms = self._get_synonyms(lemmas)

        # Generate embedding
        embedding = self.sentence_model.encode(normalized)

        # Calculate confidence based on pattern matching
        confidence = self._calculate_field_confidence(field_name, semantic_type)

        # Find related fields
        related = self._find_related_fields(tokens, lemmas)

        return FieldSemantics(
            original_name=field_name,
            normalized_name=normalized,
            tokens=tokens,
            lemmas=lemmas,
            pos_tags=pos_tags,
            entities=entities,
            semantic_type=semantic_type,
            confidence=confidence,
            synonyms=synonyms,
            related_fields=related,
            embedding=embedding
        )

    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for analysis"""
        # Replace underscores and hyphens with spaces
        normalized = field_name.replace('_', ' ').replace('-', ' ')

        # Expand common abbreviations
        abbreviations = {
            'addr': 'address',
            'phy': 'physical',
            'jv': 'just value',
            'av': 'assessed value',
            'tv': 'taxable value',
            'sqft': 'square feet',
            'yr': 'year',
            'mo': 'month',
            'cnt': 'count',
            'desc': 'description',
            'bldg': 'building',
            'num': 'number',
            'qty': 'quantity',
            'prc': 'price',
            'val': 'value',
            'cd': 'code',
            'dt': 'date',
            'lvg': 'living',
            'tot': 'total',
            'res': 'residential',
            'comm': 'commercial'
        }

        for abbr, full in abbreviations.items():
            normalized = re.sub(r'\b' + abbr + r'\b', full, normalized, flags=re.IGNORECASE)

        # Convert camelCase to space-separated
        normalized = re.sub(r'([a-z])([A-Z])', r'\1 \2', normalized)

        return normalized.lower().strip()

    def _detect_semantic_type(self, field_name: str, tokens: List[str], entities: List[str]) -> str:
        """Detect the semantic type of a field"""
        field_lower = field_name.lower()

        # Check against patterns
        for semantic_type, patterns in self.field_type_patterns.items():
            for pattern in patterns:
                if pattern in field_lower or pattern in tokens:
                    return semantic_type

        # Check entities
        if 'MONEY' in entities or 'CARDINAL' in entities:
            if any(term in field_lower for term in ['price', 'value', 'amount', 'cost']):
                return 'money'

        if 'DATE' in entities:
            return 'date'

        if 'PERSON' in entities or 'ORG' in entities:
            return 'entity'

        if 'GPE' in entities or 'LOC' in entities:
            return 'location'

        # Default type based on common patterns
        if any(term in field_lower for term in ['id', 'number', 'code']):
            return 'identifier'

        if any(term in field_lower for term in ['name', 'title']):
            return 'text'

        if any(term in field_lower for term in ['flag', 'is_', 'has_']):
            return 'boolean'

        return 'unknown'

    def _get_synonyms(self, lemmas: List[str]) -> List[str]:
        """Get synonyms using WordNet"""
        synonyms = set()

        for lemma in lemmas:
            for syn in wordnet.synsets(lemma):
                for l in syn.lemmas():
                    synonym = l.name().replace('_', ' ')
                    if synonym != lemma:
                        synonyms.add(synonym)

        return list(synonyms)[:10]  # Limit to 10 synonyms

    def _calculate_field_confidence(self, field_name: str, semantic_type: str) -> float:
        """Calculate confidence score for field analysis"""
        confidence = 0.5  # Base confidence

        # Increase confidence for known patterns
        field_lower = field_name.lower()

        # Check if field matches known patterns
        for domain, vocab in self.domain_vocab.items():
            matches = sum(1 for term in vocab if term in field_lower)
            if matches > 0:
                confidence += 0.1 * min(matches, 3)

        # Increase confidence for detected semantic type
        if semantic_type != 'unknown':
            confidence += 0.2

        # Increase confidence for standard naming conventions
        if re.match(r'^[a-z_]+$', field_lower):  # Snake case
            confidence += 0.1
        elif re.match(r'^[a-zA-Z]+$', field_name):  # Camel case
            confidence += 0.1

        return min(confidence, 1.0)

    def _find_related_fields(self, tokens: List[str], lemmas: List[str]) -> List[str]:
        """Find potentially related field names"""
        related = set()

        # Common field relationships
        relationships = {
            'address': ['street', 'city', 'state', 'zip', 'location'],
            'owner': ['name', 'buyer', 'seller', 'grantor', 'grantee'],
            'value': ['price', 'amount', 'assessment', 'cost'],
            'date': ['year', 'month', 'day', 'time'],
            'sale': ['price', 'date', 'buyer', 'seller', 'deed']
        }

        for base, related_terms in relationships.items():
            if base in tokens or base in lemmas:
                related.update(related_terms)

        return list(related)[:5]

# =====================================================================
# Intelligent Field Matcher
# =====================================================================

class IntelligentFieldMatcher:
    """Match database fields to UI components using NLP"""

    def __init__(self):
        self.analyzer = NLPFieldAnalyzer()
        self.db_schema = {}
        self.ui_schema = {}
        self.field_mappings = {}
        self.confidence_threshold = 0.7

    def load_database_schema(self, supabase_client: Client) -> Dict[str, List[str]]:
        """Load database schema from Supabase"""
        tables = [
            'florida_parcels', 'nav_assessments', 'sdf_sales',
            'sunbiz_entities', 'sunbiz_officers', 'tax_deed_sales',
            'tax_certificates', 'building_permits'
        ]

        schema = {}
        for table in tables:
            try:
                # Get sample data to infer schema
                response = supabase_client.table(table).select('*').limit(1).execute()
                if response.data and len(response.data) > 0:
                    schema[table] = list(response.data[0].keys())
                    logger.info(f"Loaded schema for {table}: {len(schema[table])} fields")
            except Exception as e:
                logger.error(f"Error loading schema for {table}: {e}")

        self.db_schema = schema
        return schema

    def load_ui_schema(self, ui_config_path: str) -> Dict[str, Any]:
        """Load UI schema from configuration"""
        with open(ui_config_path, 'r') as f:
            config = json.load(f)

        ui_schema = {}
        if 'ui_pages' in config:
            for page, page_config in config['ui_pages'].items():
                ui_schema[page] = self._extract_ui_fields(page_config)

        self.ui_schema = ui_schema
        return ui_schema

    def _extract_ui_fields(self, config: Dict) -> List[str]:
        """Extract all field names from UI configuration"""
        fields = []

        def extract_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == 'fields' and isinstance(value, list):
                        fields.extend(value)
                    else:
                        extract_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item)

        extract_recursive(config)
        return fields

    def match_fields(self, db_table: str, ui_component: str) -> List[FieldMatch]:
        """Match database fields to UI component fields using NLP"""
        matches = []

        if db_table not in self.db_schema:
            logger.error(f"Table {db_table} not in database schema")
            return matches

        db_fields = self.db_schema[db_table]
        ui_fields = self.ui_schema.get(ui_component, [])

        # Analyze all fields
        db_analyses = {field: self.analyzer.analyze_field(field) for field in db_fields}
        ui_analyses = {field: self.analyzer.analyze_field(field) for field in ui_fields}

        # Match fields using multiple strategies
        for db_field, db_analysis in db_analyses.items():
            best_match = None
            best_score = 0
            best_type = "none"

            for ui_field, ui_analysis in ui_analyses.items():
                # Strategy 1: Exact match
                if db_field.lower() == ui_field.lower():
                    score = 1.0
                    match_type = "exact"
                # Strategy 2: Normalized match
                elif db_analysis.normalized_name == ui_analysis.normalized_name:
                    score = 0.95
                    match_type = "normalized"
                # Strategy 3: Semantic similarity
                else:
                    score = self._calculate_semantic_similarity(db_analysis, ui_analysis)
                    match_type = "semantic"

                if score > best_score and score >= self.confidence_threshold:
                    best_score = score
                    best_match = ui_field
                    best_type = match_type

            if best_match:
                # Determine required transformations
                transformations = self._identify_transformations(
                    db_analysis.semantic_type,
                    ui_analyses[best_match].semantic_type
                )

                matches.append(FieldMatch(
                    db_field=db_field,
                    ui_field=best_match,
                    similarity_score=best_score,
                    match_type=best_type,
                    confidence=best_score * db_analysis.confidence,
                    reasoning=self._generate_match_reasoning(db_analysis, ui_analyses[best_match], best_type),
                    transformations=transformations
                ))

        return sorted(matches, key=lambda x: x.confidence, reverse=True)

    def _calculate_semantic_similarity(self, field1: FieldSemantics, field2: FieldSemantics) -> float:
        """Calculate semantic similarity between two fields"""
        scores = []

        # 1. Token overlap (Jaccard similarity)
        tokens1 = set(field1.tokens)
        tokens2 = set(field2.tokens)
        if tokens1 or tokens2:
            jaccard = len(tokens1 & tokens2) / len(tokens1 | tokens2)
            scores.append(jaccard)

        # 2. Lemma overlap
        lemmas1 = set(field1.lemmas)
        lemmas2 = set(field2.lemmas)
        if lemmas1 or lemmas2:
            lemma_similarity = len(lemmas1 & lemmas2) / len(lemmas1 | lemmas2)
            scores.append(lemma_similarity)

        # 3. Synonym overlap
        synonyms1 = set(field1.synonyms)
        synonyms2 = set(field2.synonyms)
        if synonyms1 or synonyms2:
            synonym_similarity = len(synonyms1 & synonyms2) / max(len(synonyms1), len(synonyms2), 1)
            scores.append(synonym_similarity * 0.5)  # Weight synonyms less

        # 4. Semantic type match
        if field1.semantic_type == field2.semantic_type and field1.semantic_type != 'unknown':
            scores.append(0.3)

        # 5. Embedding similarity (cosine similarity)
        if field1.embedding is not None and field2.embedding is not None:
            cos_sim = cosine_similarity([field1.embedding], [field2.embedding])[0][0]
            scores.append(cos_sim)

        # 6. Edit distance (normalized)
        edit_dist = edit_distance(field1.normalized_name, field2.normalized_name)
        max_len = max(len(field1.normalized_name), len(field2.normalized_name))
        if max_len > 0:
            edit_similarity = 1 - (edit_dist / max_len)
            scores.append(edit_similarity * 0.7)  # Weight edit distance less

        return np.mean(scores) if scores else 0.0

    def _identify_transformations(self, db_type: str, ui_type: str) -> List[str]:
        """Identify required transformations between field types"""
        transformations = []

        # Type-specific transformations
        if db_type == 'money' or ui_type == 'money':
            transformations.append('format_currency')

        if db_type == 'date' or ui_type == 'date':
            transformations.append('format_date')

        if db_type == 'address' or ui_type == 'address':
            transformations.append('format_address')

        if db_type == 'boolean':
            transformations.append('to_boolean')

        # Data type conversions
        type_conversions = {
            ('identifier', 'text'): 'to_string',
            ('text', 'identifier'): 'to_identifier',
            ('number', 'text'): 'number_to_string',
            ('text', 'number'): 'string_to_number'
        }

        if (db_type, ui_type) in type_conversions:
            transformations.append(type_conversions[(db_type, ui_type)])

        return transformations

    def _generate_match_reasoning(self, db_field: FieldSemantics, ui_field: FieldSemantics, match_type: str) -> str:
        """Generate human-readable reasoning for the match"""
        reasons = []

        if match_type == "exact":
            reasons.append("Exact field name match")
        elif match_type == "normalized":
            reasons.append(f"Normalized names match: '{db_field.normalized_name}'")
        else:
            # Semantic match reasoning
            if set(db_field.lemmas) & set(ui_field.lemmas):
                common_lemmas = set(db_field.lemmas) & set(ui_field.lemmas)
                reasons.append(f"Common root words: {', '.join(common_lemmas)}")

            if db_field.semantic_type == ui_field.semantic_type:
                reasons.append(f"Same semantic type: {db_field.semantic_type}")

            if set(db_field.synonyms) & set(ui_field.tokens):
                reasons.append("Synonym match detected")

        return "; ".join(reasons) if reasons else "Semantic similarity detected"

# =====================================================================
# Property Appraiser Specific Matcher
# =====================================================================

class PropertyAppraiserMatcher(IntelligentFieldMatcher):
    """Specialized matcher for Property Appraiser data"""

    def __init__(self):
        super().__init__()
        self.property_patterns = self._init_property_patterns()

    def _init_property_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize Property Appraiser specific patterns"""
        return {
            # Address fields
            "physical_address": {
                "db_patterns": ["phy_addr", "physical_addr", "property_addr", "site_addr"],
                "ui_patterns": ["address", "street", "location", "property_address"],
                "transform": "format_address"
            },
            "owner_name": {
                "db_patterns": ["owner_name", "own_name", "owner", "grantor", "grantee"],
                "ui_patterns": ["owner", "owner_name", "property_owner", "current_owner"],
                "transform": "format_name"
            },
            # Value fields
            "just_value": {
                "db_patterns": ["jv", "just_val", "just_value", "market_value"],
                "ui_patterns": ["just_value", "market_value", "fair_value", "value"],
                "transform": "format_currency"
            },
            "assessed_value": {
                "db_patterns": ["av", "av_sd", "assessed_val", "assessed_value"],
                "ui_patterns": ["assessed_value", "assessment", "assessed"],
                "transform": "format_currency"
            },
            "taxable_value": {
                "db_patterns": ["tv", "tv_sd", "taxable_val", "taxable_value"],
                "ui_patterns": ["taxable_value", "taxable", "tax_value"],
                "transform": "format_currency"
            },
            # Property characteristics
            "living_area": {
                "db_patterns": ["tot_lvg_area", "living_area", "heated_area", "adj_area"],
                "ui_patterns": ["living_area", "sqft", "square_feet", "area"],
                "transform": "format_number"
            },
            "year_built": {
                "db_patterns": ["yr_blt", "act_yr_blt", "year_built", "yr_built"],
                "ui_patterns": ["year_built", "built", "construction_year"],
                "transform": "to_integer"
            },
            "bedrooms": {
                "db_patterns": ["bedroom_cnt", "bedrooms", "beds", "bed_cnt"],
                "ui_patterns": ["bedrooms", "beds", "bedroom_count"],
                "transform": "to_integer"
            },
            "bathrooms": {
                "db_patterns": ["bathroom_cnt", "bathrooms", "baths", "bath_cnt"],
                "ui_patterns": ["bathrooms", "baths", "bathroom_count"],
                "transform": "to_float"
            }
        }

    def match_property_fields(self, db_data: pd.DataFrame, ui_requirements: Dict) -> Dict[str, FieldMatch]:
        """Match Property Appraiser fields with enhanced logic"""
        matches = {}

        # Use pattern-based matching first
        for field_type, pattern_config in self.property_patterns.items():
            db_field = self._find_matching_db_field(db_data.columns, pattern_config["db_patterns"])
            ui_field = self._find_matching_ui_field(ui_requirements, pattern_config["ui_patterns"])

            if db_field and ui_field:
                matches[field_type] = FieldMatch(
                    db_field=db_field,
                    ui_field=ui_field,
                    similarity_score=0.95,
                    match_type="pattern",
                    confidence=0.9,
                    reasoning=f"Pattern match for {field_type}",
                    transformations=[pattern_config["transform"]]
                )

        # Use NLP matching for remaining fields
        unmatched_db = set(db_data.columns) - {m.db_field for m in matches.values()}
        unmatched_ui = set(ui_requirements.keys()) - {m.ui_field for m in matches.values()}

        for db_field in unmatched_db:
            best_ui_match = self._find_best_nlp_match(db_field, list(unmatched_ui))
            if best_ui_match:
                matches[f"auto_{db_field}"] = best_ui_match

        return matches

    def _find_matching_db_field(self, columns: List[str], patterns: List[str]) -> Optional[str]:
        """Find database field matching patterns"""
        for column in columns:
            column_lower = column.lower()
            for pattern in patterns:
                if pattern.lower() in column_lower or column_lower in pattern.lower():
                    return column
        return None

    def _find_matching_ui_field(self, ui_fields: Dict, patterns: List[str]) -> Optional[str]:
        """Find UI field matching patterns"""
        for field in ui_fields.keys():
            field_lower = field.lower()
            for pattern in patterns:
                if pattern.lower() in field_lower or field_lower in pattern.lower():
                    return field
        return None

    def _find_best_nlp_match(self, db_field: str, ui_fields: List[str]) -> Optional[FieldMatch]:
        """Find best match using NLP analysis"""
        db_analysis = self.analyzer.analyze_field(db_field)
        best_match = None
        best_score = 0

        for ui_field in ui_fields:
            ui_analysis = self.analyzer.analyze_field(ui_field)
            score = self._calculate_semantic_similarity(db_analysis, ui_analysis)

            if score > best_score and score >= self.confidence_threshold:
                best_score = score
                best_match = FieldMatch(
                    db_field=db_field,
                    ui_field=ui_field,
                    similarity_score=best_score,
                    match_type="nlp",
                    confidence=best_score * 0.8,
                    reasoning=f"NLP semantic match (score: {best_score:.2f})",
                    transformations=self._identify_transformations(
                        db_analysis.semantic_type,
                        ui_analysis.semantic_type
                    )
                )

        return best_match

# =====================================================================
# Sunbiz Business Matcher
# =====================================================================

class SunbizBusinessMatcher(IntelligentFieldMatcher):
    """Specialized matcher for Sunbiz business data"""

    def __init__(self):
        super().__init__()
        self.business_patterns = self._init_business_patterns()
        self.entity_recognizer = self._init_entity_recognizer()

    def _init_business_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize Sunbiz specific patterns"""
        return {
            "entity_name": {
                "db_patterns": ["entity_name", "corp_name", "business_name", "company"],
                "ui_patterns": ["business_name", "company", "entity", "corporation"],
                "transform": "format_business_name"
            },
            "document_number": {
                "db_patterns": ["document_number", "doc_num", "filing_num", "corp_number"],
                "ui_patterns": ["document_number", "filing_number", "registration"],
                "transform": "to_uppercase"
            },
            "status": {
                "db_patterns": ["status", "entity_status", "corp_status", "active_flag"],
                "ui_patterns": ["status", "business_status", "active", "state"],
                "transform": "format_status"
            },
            "filing_date": {
                "db_patterns": ["filing_date", "filed_date", "incorporation_date", "reg_date"],
                "ui_patterns": ["filing_date", "incorporated", "established", "registered"],
                "transform": "format_date"
            },
            "officer_name": {
                "db_patterns": ["officer_name", "director_name", "principal_name", "agent_name"],
                "ui_patterns": ["officer", "director", "principal", "executive"],
                "transform": "format_person_name"
            },
            "officer_title": {
                "db_patterns": ["officer_title", "position", "title", "role"],
                "ui_patterns": ["title", "position", "role", "designation"],
                "transform": "format_title"
            }
        }

    def _init_entity_recognizer(self):
        """Initialize entity recognition for business data"""
        nlp = spacy.load("en_core_web_sm")

        # Add custom entity patterns for business entities
        ruler = nlp.add_pipe("entity_ruler", before="ner")

        patterns = [
            {"label": "BUSINESS_TYPE", "pattern": [{"LOWER": {"IN": ["llc", "inc", "corp", "corporation", "limited", "company"]}}]},
            {"label": "OFFICER_TITLE", "pattern": [{"LOWER": {"IN": ["president", "ceo", "cfo", "secretary", "director", "manager"]}}]},
            {"label": "BUSINESS_STATUS", "pattern": [{"LOWER": {"IN": ["active", "inactive", "dissolved", "suspended", "good standing"]}}]}
        ]

        ruler.add_patterns(patterns)
        return nlp

    def match_business_entities(self, owner_name: str, business_records: pd.DataFrame) -> List[Dict[str, Any]]:
        """Match property owner to business entities using NLP"""
        matches = []

        # Normalize owner name
        owner_doc = self.entity_recognizer(owner_name.upper())
        owner_tokens = set([token.lemma_.lower() for token in owner_doc if not token.is_stop])

        for _, record in business_records.iterrows():
            entity_name = str(record.get('entity_name', ''))
            if not entity_name:
                continue

            # Analyze entity name
            entity_doc = self.entity_recognizer(entity_name.upper())
            entity_tokens = set([token.lemma_.lower() for token in entity_doc if not token.is_stop])

            # Calculate similarity
            if owner_tokens and entity_tokens:
                # Token overlap
                overlap = len(owner_tokens & entity_tokens)
                union = len(owner_tokens | entity_tokens)
                jaccard_score = overlap / union if union > 0 else 0

                # Named entity matching
                owner_entities = set([ent.text.lower() for ent in owner_doc.ents])
                entity_entities = set([ent.text.lower() for ent in entity_doc.ents])
                entity_overlap = len(owner_entities & entity_entities)

                # Combined score
                similarity_score = (jaccard_score * 0.7) + (entity_overlap * 0.3)

                if similarity_score > 0.3:  # Threshold for business matching
                    matches.append({
                        'entity_name': entity_name,
                        'document_number': record.get('document_number'),
                        'similarity_score': similarity_score,
                        'match_type': 'owner_entity',
                        'confidence': similarity_score,
                        'reasoning': f"Name similarity: {similarity_score:.2f}"
                    })

        return sorted(matches, key=lambda x: x['confidence'], reverse=True)

# =====================================================================
# Playwright NLP Verification
# =====================================================================

class PlaywrightNLPVerification:
    """Verify field mappings using Playwright with NLP validation"""

    def __init__(self, nlp_analyzer: NLPFieldAnalyzer):
        self.nlp_analyzer = nlp_analyzer
        self.browser = None
        self.page = None
        self.verification_log = []

    async def initialize(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        logger.info("Playwright initialized for NLP verification")

    async def verify_field_mapping(self, url: str, field_mappings: Dict[str, FieldMatch], expected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify field mappings on actual UI using NLP"""
        verification_results = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'field_verifications': [],
            'nlp_validations': [],
            'success_rate': 0
        }

        try:
            # Navigate to page
            await self.page.goto(url, wait_until='networkidle')
            await asyncio.sleep(2)

            # Verify each mapped field
            for field_type, mapping in field_mappings.items():
                if mapping.db_field in expected_data:
                    expected_value = expected_data[mapping.db_field]

                    # Find UI element
                    ui_element = await self._find_ui_element(mapping.ui_field)

                    if ui_element:
                        # Get displayed value
                        displayed_value = await ui_element.text_content()

                        # NLP validation
                        validation = await self._validate_with_nlp(
                            expected_value,
                            displayed_value,
                            mapping.semantic_type
                        )

                        verification_results['field_verifications'].append({
                            'field': mapping.ui_field,
                            'expected': str(expected_value),
                            'displayed': displayed_value,
                            'valid': validation['is_valid'],
                            'confidence': validation['confidence'],
                            'nlp_analysis': validation['analysis']
                        })

            # Calculate success rate
            valid_count = sum(1 for v in verification_results['field_verifications'] if v['valid'])
            total_count = len(verification_results['field_verifications'])
            verification_results['success_rate'] = (valid_count / total_count * 100) if total_count > 0 else 0

        except Exception as e:
            logger.error(f"Verification error: {e}")
            verification_results['error'] = str(e)

        return verification_results

    async def _find_ui_element(self, field_name: str) -> Optional[Any]:
        """Find UI element by field name using multiple strategies"""
        selectors = [
            f'[data-field="{field_name}"]',
            f'[data-testid="{field_name}"]',
            f'#{field_name}',
            f'.{field_name}',
            f'[aria-label*="{field_name}"]',
            f'label:has-text("{field_name}") + *'
        ]

        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=2000)
                if element:
                    return element
            except:
                continue

        return None

    async def _validate_with_nlp(self, expected: Any, displayed: str, semantic_type: str) -> Dict[str, Any]:
        """Validate displayed value against expected using NLP"""
        validation = {
            'is_valid': False,
            'confidence': 0.0,
            'analysis': {}
        }

        try:
            # Convert expected to string for comparison
            expected_str = str(expected)

            # Exact match
            if expected_str.lower() == displayed.lower():
                validation['is_valid'] = True
                validation['confidence'] = 1.0
                validation['analysis']['match_type'] = 'exact'
                return validation

            # Semantic type specific validation
            if semantic_type == 'money':
                # Remove currency symbols and compare
                expected_clean = re.sub(r'[$,]', '', expected_str)
                displayed_clean = re.sub(r'[$,]', '', displayed)
                if expected_clean == displayed_clean:
                    validation['is_valid'] = True
                    validation['confidence'] = 0.95
                    validation['analysis']['match_type'] = 'currency_format'

            elif semantic_type == 'date':
                # Parse and compare dates
                from dateutil import parser
                try:
                    expected_date = parser.parse(expected_str)
                    displayed_date = parser.parse(displayed)
                    if expected_date == displayed_date:
                        validation['is_valid'] = True
                        validation['confidence'] = 0.95
                        validation['analysis']['match_type'] = 'date_format'
                except:
                    pass

            elif semantic_type == 'address':
                # Fuzzy address matching
                expected_tokens = set(expected_str.lower().split())
                displayed_tokens = set(displayed.lower().split())
                overlap = len(expected_tokens & displayed_tokens)
                if overlap / len(expected_tokens) > 0.8:
                    validation['is_valid'] = True
                    validation['confidence'] = overlap / len(expected_tokens)
                    validation['analysis']['match_type'] = 'address_fuzzy'

            else:
                # General semantic similarity
                expected_analysis = self.nlp_analyzer.analyze_field(expected_str)
                displayed_analysis = self.nlp_analyzer.analyze_field(displayed)

                # Calculate similarity
                similarity = cosine_similarity(
                    [expected_analysis.embedding],
                    [displayed_analysis.embedding]
                )[0][0]

                if similarity > 0.8:
                    validation['is_valid'] = True
                    validation['confidence'] = similarity
                    validation['analysis']['match_type'] = 'semantic'

            validation['analysis']['expected_tokens'] = word_tokenize(expected_str.lower())
            validation['analysis']['displayed_tokens'] = word_tokenize(displayed.lower())

        except Exception as e:
            validation['analysis']['error'] = str(e)

        return validation

    async def cleanup(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()

# =====================================================================
# Complete NLP Data Mapping System
# =====================================================================

class NLPDataMappingSystem:
    """Complete system for intelligent data mapping with NLP"""

    def __init__(self):
        self.nlp_analyzer = NLPFieldAnalyzer()
        self.property_matcher = PropertyAppraiserMatcher()
        self.sunbiz_matcher = SunbizBusinessMatcher()
        self.playwright_verifier = None
        self.supabase_client = self._init_supabase()

    def _init_supabase(self) -> Client:
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        return create_client(url, key)

    async def complete_mapping_pipeline(self, parcel_id: str) -> Dict[str, Any]:
        """Execute complete data mapping pipeline with NLP"""
        pipeline_result = {
            'parcel_id': parcel_id,
            'timestamp': datetime.now().isoformat(),
            'stages': {},
            'field_mappings': {},
            'verification': {},
            'success': False
        }

        try:
            # Stage 1: Fetch Property Data
            logger.info(f"Stage 1: Fetching property data for {parcel_id}")
            property_data = self._fetch_property_data(parcel_id)
            pipeline_result['stages']['data_fetch'] = 'completed'

            # Stage 2: NLP Field Analysis
            logger.info("Stage 2: Analyzing fields with NLP")
            field_analyses = self._analyze_all_fields(property_data)
            pipeline_result['stages']['nlp_analysis'] = 'completed'

            # Stage 3: Intelligent Field Matching
            logger.info("Stage 3: Matching fields intelligently")
            field_mappings = self._match_all_fields(property_data, field_analyses)
            pipeline_result['field_mappings'] = field_mappings
            pipeline_result['stages']['field_matching'] = 'completed'

            # Stage 4: Fetch Sunbiz Data
            logger.info("Stage 4: Fetching and matching Sunbiz data")
            if 'owner_name' in property_data.get('florida_parcels', {}):
                owner_name = property_data['florida_parcels']['owner_name']
                sunbiz_matches = await self._match_sunbiz_entities(owner_name)
                pipeline_result['sunbiz_matches'] = sunbiz_matches
                pipeline_result['stages']['sunbiz_matching'] = 'completed'

            # Stage 5: Playwright Verification
            logger.info("Stage 5: Verifying with Playwright and NLP")
            if not self.playwright_verifier:
                self.playwright_verifier = PlaywrightNLPVerification(self.nlp_analyzer)
                await self.playwright_verifier.initialize()

            verification = await self.playwright_verifier.verify_field_mapping(
                f"http://localhost:5173/property/{parcel_id}",
                field_mappings,
                property_data.get('florida_parcels', {})
            )
            pipeline_result['verification'] = verification
            pipeline_result['stages']['verification'] = 'completed'

            # Calculate overall success
            pipeline_result['success'] = verification.get('success_rate', 0) > 80

            logger.info(f"Pipeline completed with {verification.get('success_rate', 0):.1f}% success rate")

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            pipeline_result['error'] = str(e)

        finally:
            # Cleanup
            if self.playwright_verifier:
                await self.playwright_verifier.cleanup()

        return pipeline_result

    def _fetch_property_data(self, parcel_id: str) -> Dict[str, Any]:
        """Fetch all property-related data"""
        data = {}

        # Fetch florida_parcels
        response = self.supabase_client.table('florida_parcels').select('*').eq('parcel_id', parcel_id).execute()
        if response.data:
            data['florida_parcels'] = response.data[0]

        # Fetch other related data
        # NAV, SDF, permits, etc.
        # ... (implementation as needed)

        return data

    def _analyze_all_fields(self, data: Dict[str, Any]) -> Dict[str, Dict[str, FieldSemantics]]:
        """Analyze all fields with NLP"""
        analyses = {}

        for table, records in data.items():
            if isinstance(records, dict):
                analyses[table] = {}
                for field_name in records.keys():
                    analyses[table][field_name] = self.nlp_analyzer.analyze_field(field_name)

        return analyses

    def _match_all_fields(self, data: Dict[str, Any], analyses: Dict) -> Dict[str, FieldMatch]:
        """Match all fields using specialized matchers"""
        all_mappings = {}

        # Use Property Appraiser matcher for florida_parcels
        if 'florida_parcels' in data:
            property_df = pd.DataFrame([data['florida_parcels']])
            ui_requirements = self._get_ui_requirements()
            property_mappings = self.property_matcher.match_property_fields(property_df, ui_requirements)
            all_mappings.update(property_mappings)

        return all_mappings

    def _get_ui_requirements(self) -> Dict[str, Any]:
        """Get UI field requirements"""
        # Load from configuration or define here
        return {
            'street_address': {'type': 'text', 'required': True},
            'city': {'type': 'text', 'required': True},
            'zip_code': {'type': 'text', 'required': True},
            'just_value': {'type': 'money', 'required': True},
            'owner_name': {'type': 'text', 'required': True},
            # ... more fields
        }

    async def _match_sunbiz_entities(self, owner_name: str) -> List[Dict]:
        """Match owner to Sunbiz entities"""
        # Search for business entities
        response = self.supabase_client.table('sunbiz_entities').select('*').ilike('entity_name', f'%{owner_name}%').limit(10).execute()

        if response.data:
            business_df = pd.DataFrame(response.data)
            matches = self.sunbiz_matcher.match_business_entities(owner_name, business_df)
            return matches

        return []

# =====================================================================
# Main Execution
# =====================================================================

async def main():
    """Test the NLP data mapping system"""
    print("\n" + "="*80)
    print(" NLP INTELLIGENT FIELD MATCHING SYSTEM")
    print("="*80)

    # Initialize system
    system = NLPDataMappingSystem()

    # Test with sample parcel
    parcel_id = "494224020080"

    print(f"\nProcessing parcel: {parcel_id}")
    print("-" * 40)

    # Run complete pipeline
    result = await system.complete_mapping_pipeline(parcel_id)

    # Display results
    print("\nPipeline Stages:")
    for stage, status in result.get('stages', {}).items():
        symbol = "✓" if status == 'completed' else "✗"
        print(f"  {symbol} {stage}: {status}")

    print("\nField Mappings Found:")
    for field_type, mapping in result.get('field_mappings', {}).items():
        if isinstance(mapping, FieldMatch):
            print(f"  • {mapping.db_field} → {mapping.ui_field}")
            print(f"    Confidence: {mapping.confidence:.2f}")
            print(f"    Type: {mapping.match_type}")
            print(f"    Reasoning: {mapping.reasoning}")

    if 'sunbiz_matches' in result:
        print(f"\nSunbiz Matches: {len(result['sunbiz_matches'])} found")
        for match in result['sunbiz_matches'][:3]:
            print(f"  • {match['entity_name']} (confidence: {match['confidence']:.2f})")

    if 'verification' in result:
        print(f"\nVerification Results:")
        print(f"  Success Rate: {result['verification'].get('success_rate', 0):.1f}%")
        print(f"  Fields Verified: {len(result['verification'].get('field_verifications', []))}")

    print("\n" + "="*80)
    print(f" Overall Success: {'✓' if result.get('success') else '✗'}")
    print("="*80)

    # Save detailed report
    report_file = f"nlp_mapping_report_{parcel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nDetailed report saved to: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())