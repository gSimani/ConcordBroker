"""
Sunbiz AI Agent System
Adds semantic reasoning, cross-dataset linking, anomaly detection, and adaptive learning
"""
from typing import Dict, List, Optional, Tuple
import json
import re
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MatchContext:
    """Context for AI-enhanced matching decisions"""
    property_address: str
    property_city: str
    property_zip: str
    property_value: Optional[float] = None
    property_type: Optional[str] = None
    nearby_properties: List[Dict] = None
    historical_matches: List[Dict] = None

@dataclass
class EntityProfile:
    """Enhanced entity profile with AI insights"""
    entity_name: str
    status: str
    entity_type: str
    filing_date: str
    principal_address: str
    confidence_score: float
    match_reasoning: str
    risk_flags: List[str] = None
    related_entities: List[str] = None
    ownership_network: Dict = None

class SunbizAIAgent:
    """AI-powered Sunbiz matching with semantic reasoning and learning"""

    def __init__(self):
        self.learning_history = {}
        self.entity_network = {}
        self.anomaly_patterns = []
        self.context_rules = {}

        # Initialize with pattern recognition
        self._initialize_semantic_patterns()
        self._initialize_anomaly_detection()

    def _initialize_semantic_patterns(self):
        """Initialize semantic matching patterns"""
        self.semantic_patterns = {
            # Company name variations
            'company_synonyms': {
                'DEV': ['DEVELOPMENT', 'DEVELOPER', 'DEVELOPERS'],
                'MGMT': ['MANAGEMENT', 'MANAGER', 'MANAGING'],
                'PROP': ['PROPERTY', 'PROPERTIES'],
                'REAL': ['REALTY', 'REAL ESTATE'],
                'INVEST': ['INVESTMENT', 'INVESTMENTS', 'INVESTORS'],
                'HOLD': ['HOLDING', 'HOLDINGS'],
                'GROUP': ['GROUPS', 'GRP'],
                'CORP': ['CORPORATION', 'CORPORATE'],
                'ASSOC': ['ASSOCIATES', 'ASSOCIATION'],
                'PART': ['PARTNERS', 'PARTNERSHIP']
            },
            # Geographic indicators
            'location_indicators': {
                'SOUTH': ['S', 'SO', 'SOUTHERN'],
                'NORTH': ['N', 'NO', 'NORTHERN'],
                'EAST': ['E', 'EASTERN'],
                'WEST': ['W', 'WESTERN'],
                'FLORIDA': ['FL', 'FLA'],
                'MIAMI': ['MIA'],
                'BROWARD': ['BROW', 'BRW']
            },
            # Business type indicators
            'business_types': {
                'RESIDENTIAL': ['RES', 'RESI', 'HOME', 'HOMES'],
                'COMMERCIAL': ['COMM', 'OFFICE', 'RETAIL'],
                'INDUSTRIAL': ['IND', 'WAREHOUSE', 'LOGISTICS'],
                'HOSPITALITY': ['HOTEL', 'RESORT', 'HOSPITALITY']
            }
        }

    def _initialize_anomaly_detection(self):
        """Initialize anomaly detection patterns"""
        self.anomaly_patterns = [
            {
                'name': 'inactive_entity_owning_property',
                'description': 'Inactive corporation still listed as property owner',
                'severity': 'high',
                'check': lambda entity, context: entity.get('status') != 'ACTIVE'
            },
            {
                'name': 'address_mismatch',
                'description': 'Entity address far from property location',
                'severity': 'medium',
                'check': self._check_address_proximity
            },
            {
                'name': 'recent_entity_old_property',
                'description': 'Recently formed entity owns old property',
                'severity': 'low',
                'check': self._check_entity_age_consistency
            },
            {
                'name': 'high_volume_owner',
                'description': 'Entity owns unusually many properties',
                'severity': 'medium',
                'check': self._check_ownership_volume
            }
        ]

    def semantic_name_match(self, owner_name: str, entity_name: str, context: MatchContext) -> Tuple[float, str]:
        """Enhanced semantic matching with AI reasoning"""

        # Start with baseline fuzzy score
        baseline_score = self._calculate_fuzzy_score(owner_name, entity_name)

        # Apply semantic enhancements
        semantic_boost = 0.0
        reasoning_parts = []

        # 1. Synonym expansion
        synonym_score = self._apply_synonym_matching(owner_name, entity_name)
        if synonym_score > 0:
            semantic_boost += synonym_score * 0.15
            reasoning_parts.append(f"synonym match (+{synonym_score*0.15:.2f})")

        # 2. Geographic context
        geo_score = self._apply_geographic_context(owner_name, entity_name, context)
        if geo_score > 0:
            semantic_boost += geo_score * 0.10
            reasoning_parts.append(f"geographic context (+{geo_score*0.10:.2f})")

        # 3. Business type alignment
        business_score = self._apply_business_type_context(owner_name, entity_name, context)
        if business_score > 0:
            semantic_boost += business_score * 0.08
            reasoning_parts.append(f"business type match (+{business_score*0.08:.2f})")

        # 4. Historical learning
        history_score = self._apply_historical_learning(owner_name, entity_name)
        if history_score != 0:
            semantic_boost += history_score * 0.12
            reasoning_parts.append(f"historical learning ({history_score*0.12:+.2f})")

        final_score = min(1.0, baseline_score + semantic_boost)

        reasoning = f"Baseline: {baseline_score:.2f}"
        if reasoning_parts:
            reasoning += f" + AI enhancements: {', '.join(reasoning_parts)}"
        reasoning += f" = {final_score:.2f}"

        return final_score, reasoning

    def _apply_synonym_matching(self, owner_name: str, entity_name: str) -> float:
        """Apply synonym-based semantic matching"""
        score = 0.0

        for category, synonyms in self.semantic_patterns['company_synonyms'].items():
            # Check if owner uses abbreviation and entity uses full form
            for synonym in synonyms:
                if category in owner_name.upper() and synonym in entity_name.upper():
                    score += 0.3
                elif synonym in owner_name.upper() and category in entity_name.upper():
                    score += 0.3

        return min(1.0, score)

    def _apply_geographic_context(self, owner_name: str, entity_name: str, context: MatchContext) -> float:
        """Apply geographic context matching"""
        if not context or not context.property_city:
            return 0.0

        score = 0.0
        property_city = context.property_city.upper()

        # Check if entity name contains city name
        if property_city in entity_name.upper():
            score += 0.4

        # Check for geographic abbreviations
        for full_name, abbreviations in self.semantic_patterns['location_indicators'].items():
            if full_name in property_city:
                for abbrev in abbreviations:
                    if abbrev in entity_name.upper():
                        score += 0.2

        return min(1.0, score)

    def _apply_business_type_context(self, owner_name: str, entity_name: str, context: MatchContext) -> float:
        """Apply business type context matching"""
        if not context or not context.property_type:
            return 0.0

        score = 0.0
        property_type = context.property_type.upper()

        # Match business type indicators
        for biz_type, indicators in self.semantic_patterns['business_types'].items():
            if biz_type in property_type:
                for indicator in indicators:
                    if indicator in entity_name.upper():
                        score += 0.3

        return min(1.0, score)

    def _apply_historical_learning(self, owner_name: str, entity_name: str) -> float:
        """Apply learning from historical matches"""
        key = f"{owner_name.upper()}:{entity_name.upper()}"

        if key in self.learning_history:
            history = self.learning_history[key]
            confidence_adjustment = (history['confirmations'] - history['rejections']) * 0.1
            return max(-0.3, min(0.3, confidence_adjustment))

        return 0.0

    def detect_anomalies(self, entity: Dict, context: MatchContext) -> List[Dict]:
        """Detect anomalies in entity-property relationships"""
        anomalies = []

        for pattern in self.anomaly_patterns:
            try:
                if pattern['check'](entity, context):
                    anomalies.append({
                        'type': pattern['name'],
                        'description': pattern['description'],
                        'severity': pattern['severity'],
                        'detected_at': datetime.now().isoformat()
                    })
            except Exception as e:
                logger.warning(f"Anomaly check '{pattern['name']}' failed: {e}")

        return anomalies

    def _check_address_proximity(self, entity: Dict, context: MatchContext) -> bool:
        """Check if entity address is suspiciously far from property"""
        if not context or not context.property_city:
            return False

        entity_address = entity.get('principal_address', '').upper()
        property_city = context.property_city.upper()

        # Simple heuristic: flag if entity is in different major city
        major_cities = ['MIAMI', 'FORT LAUDERDALE', 'HOLLYWOOD', 'PEMBROKE', 'DAVIE']

        entity_city = None
        for city in major_cities:
            if city in entity_address:
                entity_city = city
                break

        property_major_city = None
        for city in major_cities:
            if city in property_city:
                property_major_city = city
                break

        if entity_city and property_major_city and entity_city != property_major_city:
            return True

        return False

    def _check_entity_age_consistency(self, entity: Dict, context: MatchContext) -> bool:
        """Check for entity age vs property relationship consistency"""
        filing_date_str = entity.get('filing_date')
        if not filing_date_str:
            return False

        try:
            filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d')
            # Flag if entity formed very recently (less than 30 days)
            if datetime.now() - filing_date < timedelta(days=30):
                return True
        except:
            pass

        return False

    def _check_ownership_volume(self, entity: Dict, context: MatchContext) -> bool:
        """Check if entity owns suspiciously many properties"""
        # This would require querying property database
        # For now, return False (would implement with actual property count query)
        return False

    def build_entity_network(self, entities: List[Dict]) -> Dict:
        """Build network of related entities using AI analysis"""
        network = {
            'nodes': [],
            'edges': [],
            'clusters': []
        }

        # Add nodes
        for entity in entities:
            network['nodes'].append({
                'id': entity['entity_name'],
                'type': entity['entity_type'],
                'status': entity['status'],
                'filing_date': entity['filing_date']
            })

        # Detect relationships
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i+1:], i+1):
                relationship = self._detect_entity_relationship(entity1, entity2)
                if relationship:
                    network['edges'].append({
                        'source': entity1['entity_name'],
                        'target': entity2['entity_name'],
                        'relationship': relationship['type'],
                        'confidence': relationship['confidence']
                    })

        return network

    def _detect_entity_relationship(self, entity1: Dict, entity2: Dict) -> Optional[Dict]:
        """Detect relationship between two entities"""
        name1 = entity1['entity_name'].upper()
        name2 = entity2['entity_name'].upper()

        # Check for shared words (potential related companies)
        words1 = set(w for w in name1.split() if len(w) > 3)
        words2 = set(w for w in name2.split() if len(w) > 3)
        shared_words = words1.intersection(words2)

        if len(shared_words) >= 2:
            return {
                'type': 'potential_related_entity',
                'confidence': len(shared_words) / max(len(words1), len(words2)),
                'shared_terms': list(shared_words)
            }

        # Check for same address (potential subsidiaries)
        addr1 = entity1.get('principal_address', '').upper()
        addr2 = entity2.get('principal_address', '').upper()

        if addr1 and addr2 and addr1 == addr2:
            return {
                'type': 'same_address',
                'confidence': 0.8,
                'shared_address': addr1
            }

        return None

    def learn_from_feedback(self, owner_name: str, entity_name: str, confirmed: bool):
        """Learn from human feedback to improve matching"""
        key = f"{owner_name.upper()}:{entity_name.upper()}"

        if key not in self.learning_history:
            self.learning_history[key] = {
                'confirmations': 0,
                'rejections': 0,
                'last_updated': datetime.now().isoformat()
            }

        if confirmed:
            self.learning_history[key]['confirmations'] += 1
        else:
            self.learning_history[key]['rejections'] += 1

        self.learning_history[key]['last_updated'] = datetime.now().isoformat()

        logger.info(f"Learning update: {key} -> {'confirmed' if confirmed else 'rejected'}")

    def _calculate_fuzzy_score(self, owner_name: str, entity_name: str) -> float:
        """Calculate baseline fuzzy matching score"""
        owner_clean = re.sub(r'[,.\s]+', ' ', owner_name.upper()).strip()
        entity_clean = re.sub(r'[,.\s]+', ' ', entity_name.upper()).strip()

        if owner_clean == entity_clean:
            return 1.0

        owner_words = set(word for word in owner_clean.split() if len(word) > 2)
        entity_words = set(word for word in entity_clean.split() if len(word) > 2)

        if not owner_words or not entity_words:
            return 0.0

        common_words = owner_words.intersection(entity_words)
        return len(common_words) / max(len(owner_words), len(entity_words))

    def generate_match_report(self, matches: List[Dict], context: MatchContext) -> Dict:
        """Generate comprehensive AI analysis report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'context': {
                'property_address': context.property_address if context else None,
                'property_city': context.property_city if context else None
            },
            'matches_analyzed': len(matches),
            'ai_insights': {
                'high_confidence_matches': len([m for m in matches if m.get('confidence_score', 0) >= 0.8]),
                'semantic_enhancements': 0,
                'anomalies_detected': 0,
                'learning_applications': 0
            },
            'recommendations': [],
            'risk_assessment': 'low'
        }

        # Analyze matches
        for match in matches:
            if match.get('match_reasoning'):
                if 'AI enhancements' in match['match_reasoning']:
                    report['ai_insights']['semantic_enhancements'] += 1
                if 'historical learning' in match['match_reasoning']:
                    report['ai_insights']['learning_applications'] += 1

            if match.get('risk_flags'):
                report['ai_insights']['anomalies_detected'] += len(match['risk_flags'])

        # Generate recommendations
        if report['ai_insights']['anomalies_detected'] > 0:
            report['recommendations'].append("Review flagged anomalies for data quality issues")
            report['risk_assessment'] = 'medium'

        if report['ai_insights']['semantic_enhancements'] > 2:
            report['recommendations'].append("High semantic matching success - consider expanding AI patterns")

        return report

# Global AI agent instance
sunbiz_ai_agent = SunbizAIAgent()

# API Integration Functions
def enhance_match_with_ai(owner_name: str, entity_data: Dict, context: MatchContext = None) -> EntityProfile:
    """Enhance a basic match with AI analysis"""

    if not context:
        context = MatchContext(
            property_address="",
            property_city="",
            property_zip=""
        )

    # Get AI-enhanced confidence and reasoning
    ai_score, reasoning = sunbiz_ai_agent.semantic_name_match(
        owner_name,
        entity_data['entity_name'],
        context
    )

    # Detect anomalies
    anomalies = sunbiz_ai_agent.detect_anomalies(entity_data, context)

    # Create enhanced profile
    profile = EntityProfile(
        entity_name=entity_data['entity_name'],
        status=entity_data['status'],
        entity_type=entity_data['entity_type'],
        filing_date=entity_data['filing_date'],
        principal_address=entity_data['principal_address'],
        confidence_score=ai_score,
        match_reasoning=reasoning,
        risk_flags=[a['description'] for a in anomalies] if anomalies else []
    )

    return profile

def get_ai_match_insights(matches: List[Dict], context: MatchContext = None) -> Dict:
    """Get AI insights for a set of matches"""
    return sunbiz_ai_agent.generate_match_report(matches, context)

def train_ai_agent(owner_name: str, entity_name: str, confirmed: bool):
    """Train the AI agent with human feedback"""
    sunbiz_ai_agent.learn_from_feedback(owner_name, entity_name, confirmed)

def get_entity_network_analysis(entities: List[Dict]) -> Dict:
    """Get network analysis of entities"""
    return sunbiz_ai_agent.build_entity_network(entities)