"""
Advanced Chain-of-Thought Optimization System
Maximum accuracy through ensemble learning, advanced caching, and continuous improvement
"""

import asyncio
import hashlib
import pickle
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import redis
from collections import defaultdict, deque
import json
import logging
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from fuzzywuzzy import fuzz
import jellyfish  # For advanced string matching
import usaddress  # For address parsing
import nameparser  # For name parsing
from geopy.distance import geodesic
import networkx as nx
from scipy.stats import entropy
import re

logger = logging.getLogger(__name__)

# =====================================================
# ADVANCED CONFIDENCE SCORING WITH ML
# =====================================================

class MLConfidenceScorer:
    """Machine learning-based confidence scoring"""
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, max_depth=10)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_importance = {}
        self.training_data = deque(maxlen=10000)  # Rolling window of training data
        
    def extract_features(self, match_data: Dict) -> np.ndarray:
        """Extract features for ML scoring"""
        features = []
        
        # String similarity features
        features.append(match_data.get('exact_match', 0))
        features.append(match_data.get('fuzzy_ratio', 0) / 100)
        features.append(match_data.get('token_sort_ratio', 0) / 100)
        features.append(match_data.get('partial_ratio', 0) / 100)
        features.append(match_data.get('phonetic_match', 0))
        
        # Data quality features
        features.append(match_data.get('data_sources_count', 0) / 10)
        features.append(match_data.get('evidence_count', 0) / 10)
        features.append(match_data.get('document_evidence', 0))
        features.append(match_data.get('official_record', 0))
        
        # Temporal features
        days_old = match_data.get('data_age_days', 0)
        features.append(min(1.0, max(0, 1 - (days_old / 365))))  # Decay over 1 year
        
        # Spatial features
        features.append(match_data.get('distance_miles', 0) / 10)
        features.append(match_data.get('same_zip', 0))
        features.append(match_data.get('same_city', 0))
        
        # Network features
        features.append(match_data.get('network_connections', 0) / 10)
        features.append(match_data.get('shared_officers', 0) / 5)
        features.append(match_data.get('property_portfolio_size', 0) / 20)
        
        # Business indicators
        features.append(match_data.get('is_business_entity', 0))
        features.append(match_data.get('has_ein', 0))
        features.append(match_data.get('active_status', 0))
        features.append(match_data.get('verified_listing', 0))
        
        return np.array(features).reshape(1, -1)
    
    def train(self, training_samples: List[Tuple[Dict, bool]]):
        """Train the model with labeled samples"""
        if len(training_samples) < 100:
            return  # Need minimum samples
            
        X = []
        y = []
        
        for features, is_correct in training_samples:
            X.append(self.extract_features(features).flatten())
            y.append(1 if is_correct else 0)
            
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # Calculate feature importance
        self.feature_importance = dict(zip(
            ['exact_match', 'fuzzy_ratio', 'token_sort', 'partial_ratio', 'phonetic',
             'sources', 'evidence', 'document', 'official', 'recency',
             'distance', 'same_zip', 'same_city', 'network', 'officers',
             'portfolio', 'is_business', 'has_ein', 'active', 'verified'],
            self.model.feature_importances_
        ))
        
    def predict_confidence(self, match_data: Dict) -> float:
        """Predict confidence score using ML model"""
        if not self.is_trained:
            # Fallback to rule-based scoring
            return self._rule_based_score(match_data)
            
        features = self.extract_features(match_data)
        features_scaled = self.scaler.transform(features)
        
        # Get probability of being correct
        prob = self.model.predict_proba(features_scaled)[0][1]
        
        # Combine with rule-based for stability
        rule_score = self._rule_based_score(match_data)
        
        # Weighted average (70% ML, 30% rules)
        return prob * 0.7 + rule_score * 0.3
    
    def _rule_based_score(self, match_data: Dict) -> float:
        """Fallback rule-based scoring"""
        score = 0.5  # Base score
        
        # Boost for exact matches
        if match_data.get('exact_match'):
            score += 0.3
        
        # Boost for multiple sources
        sources = match_data.get('data_sources_count', 0)
        score += min(0.2, sources * 0.05)
        
        # Boost for official records
        if match_data.get('official_record'):
            score += 0.15
            
        # Penalty for old data
        days_old = match_data.get('data_age_days', 0)
        if days_old > 730:  # 2 years
            score -= 0.1
            
        return min(0.95, max(0.1, score))
    
    def add_feedback(self, match_data: Dict, was_correct: bool):
        """Add user feedback for continuous learning"""
        self.training_data.append((match_data, was_correct))
        
        # Retrain periodically
        if len(self.training_data) % 100 == 0 and len(self.training_data) >= 100:
            self.train(list(self.training_data))

# =====================================================
# ADVANCED CACHING SYSTEM
# =====================================================

class IntelligentCache:
    """Multi-layer caching with predictive prefetching"""
    
    def __init__(self, redis_host='localhost', redis_port=6379):
        try:
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            self.redis_available = True
        except:
            self.redis_available = False
            
        self.memory_cache = {}
        self.cache_stats = defaultdict(int)
        self.access_patterns = defaultdict(list)
        self.prefetch_queue = asyncio.Queue()
        
    def _generate_key(self, data_type: str, params: Dict) -> str:
        """Generate cache key from parameters"""
        param_str = json.dumps(params, sort_keys=True)
        hash_obj = hashlib.sha256(param_str.encode())
        return f"{data_type}:{hash_obj.hexdigest()[:16]}"
    
    async def get(self, data_type: str, params: Dict, ttl: int = 300) -> Optional[Any]:
        """Get from cache with multi-layer lookup"""
        key = self._generate_key(data_type, params)
        
        # Track access pattern
        self.access_patterns[data_type].append(datetime.now())
        
        # Level 1: Memory cache
        if key in self.memory_cache:
            cache_entry = self.memory_cache[key]
            if datetime.now() < cache_entry['expires']:
                self.cache_stats['memory_hits'] += 1
                return cache_entry['data']
                
        # Level 2: Redis cache
        if self.redis_available:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    self.cache_stats['redis_hits'] += 1
                    data = json.loads(cached)
                    # Promote to memory cache
                    self.memory_cache[key] = {
                        'data': data,
                        'expires': datetime.now() + timedelta(seconds=ttl)
                    }
                    return data
            except:
                pass
                
        self.cache_stats['misses'] += 1
        
        # Trigger predictive prefetching
        await self._predict_and_prefetch(data_type, params)
        
        return None
    
    async def set(self, data_type: str, params: Dict, data: Any, ttl: int = 300):
        """Set in multi-layer cache"""
        key = self._generate_key(data_type, params)
        
        # Memory cache
        self.memory_cache[key] = {
            'data': data,
            'expires': datetime.now() + timedelta(seconds=ttl)
        }
        
        # Redis cache
        if self.redis_available:
            try:
                self.redis_client.setex(key, ttl, json.dumps(data))
            except:
                pass
                
        # Cleanup old memory cache entries
        if len(self.memory_cache) > 1000:
            self._cleanup_memory_cache()
    
    def _cleanup_memory_cache(self):
        """Remove expired entries from memory cache"""
        now = datetime.now()
        expired_keys = [
            k for k, v in self.memory_cache.items()
            if now >= v['expires']
        ]
        for key in expired_keys:
            del self.memory_cache[key]
    
    async def _predict_and_prefetch(self, data_type: str, params: Dict):
        """Predict next likely queries and prefetch"""
        # Analyze access patterns
        recent_accesses = self.access_patterns[data_type][-10:]
        
        if len(recent_accesses) < 3:
            return
            
        # Simple pattern: if accessing sequential IDs, prefetch next
        if 'id' in params:
            current_id = params['id']
            if isinstance(current_id, int):
                # Prefetch next 3 IDs
                for next_id in range(current_id + 1, current_id + 4):
                    prefetch_params = params.copy()
                    prefetch_params['id'] = next_id
                    await self.prefetch_queue.put((data_type, prefetch_params))
    
    def get_stats(self) -> Dict:
        """Get cache performance statistics"""
        total_requests = sum(self.cache_stats.values())
        hit_rate = 0
        if total_requests > 0:
            hits = self.cache_stats['memory_hits'] + self.cache_stats['redis_hits']
            hit_rate = hits / total_requests
            
        return {
            'memory_hits': self.cache_stats['memory_hits'],
            'redis_hits': self.cache_stats['redis_hits'],
            'misses': self.cache_stats['misses'],
            'hit_rate': f"{hit_rate:.2%}",
            'memory_size': len(self.memory_cache)
        }

# =====================================================
# ENSEMBLE VOTING MECHANISM
# =====================================================

class EnsembleVoter:
    """Combine multiple agent results with weighted voting"""
    
    def __init__(self):
        self.agent_weights = {}
        self.agent_performance = defaultdict(lambda: {'correct': 0, 'total': 0})
        
    def calculate_weights(self):
        """Calculate agent weights based on historical performance"""
        for agent_name, performance in self.agent_performance.items():
            if performance['total'] > 0:
                accuracy = performance['correct'] / performance['total']
                # Weight based on accuracy and sample size
                sample_factor = min(1.0, performance['total'] / 100)
                self.agent_weights[agent_name] = accuracy * sample_factor
            else:
                self.agent_weights[agent_name] = 0.5  # Default weight
    
    def vote(self, results: List[Dict]) -> Dict:
        """Perform weighted ensemble voting"""
        if not results:
            return None
            
        # Group results by company
        company_votes = defaultdict(lambda: {
            'votes': [],
            'total_weight': 0,
            'evidence': set(),
            'best_confidence': 0
        })
        
        for result in results:
            company_key = result['company_doc_number']
            agent_name = result['agent_name']
            confidence = result['confidence']
            
            # Get agent weight
            weight = self.agent_weights.get(agent_name, 0.5)
            
            # Weighted vote
            vote_strength = confidence * weight
            
            company_votes[company_key]['votes'].append({
                'agent': agent_name,
                'confidence': confidence,
                'weight': weight,
                'strength': vote_strength
            })
            
            company_votes[company_key]['total_weight'] += vote_strength
            company_votes[company_key]['evidence'].update(result.get('evidence', []))
            company_votes[company_key]['best_confidence'] = max(
                company_votes[company_key]['best_confidence'],
                confidence
            )
            
            # Store company details from first occurrence
            if 'company_name' not in company_votes[company_key]:
                company_votes[company_key]['company_name'] = result['company_name']
                company_votes[company_key]['company_doc_number'] = result['company_doc_number']
        
        # Calculate final scores
        final_results = []
        for company_key, vote_data in company_votes.items():
            # Calculate consensus score
            num_agents = len(vote_data['votes'])
            avg_weight = vote_data['total_weight'] / num_agents if num_agents > 0 else 0
            
            # Boost for consensus
            consensus_boost = min(0.1, (num_agents - 1) * 0.03)
            
            # Calculate vote entropy (lower = more agreement)
            confidences = [v['confidence'] for v in vote_data['votes']]
            if len(confidences) > 1:
                vote_entropy = entropy(confidences)
                agreement_score = 1 - min(1, vote_entropy)
            else:
                agreement_score = 0.5
            
            # Final ensemble score
            ensemble_score = min(0.95, avg_weight + consensus_boost + (agreement_score * 0.1))
            
            final_results.append({
                'company_name': vote_data['company_name'],
                'company_doc_number': vote_data['company_doc_number'],
                'ensemble_confidence': ensemble_score,
                'best_individual_confidence': vote_data['best_confidence'],
                'num_agents_agree': num_agents,
                'evidence': list(vote_data['evidence']),
                'voting_details': vote_data['votes']
            })
        
        # Sort by ensemble confidence
        final_results.sort(key=lambda x: x['ensemble_confidence'], reverse=True)
        
        return final_results[0] if final_results else None
    
    def update_performance(self, agent_name: str, was_correct: bool):
        """Update agent performance metrics"""
        self.agent_performance[agent_name]['total'] += 1
        if was_correct:
            self.agent_performance[agent_name]['correct'] += 1
        
        # Recalculate weights periodically
        if self.agent_performance[agent_name]['total'] % 10 == 0:
            self.calculate_weights()

# =====================================================
# ADVANCED STRING MATCHING
# =====================================================

class AdvancedStringMatcher:
    """Advanced string matching with multiple algorithms"""
    
    @staticmethod
    def comprehensive_match(str1: str, str2: str) -> Dict[str, float]:
        """Perform comprehensive string matching"""
        if not str1 or not str2:
            return {'overall': 0}
            
        str1_clean = str1.upper().strip()
        str2_clean = str2.upper().strip()
        
        scores = {}
        
        # Exact match
        scores['exact'] = 1.0 if str1_clean == str2_clean else 0.0
        
        # Fuzzy matching
        scores['fuzzy_ratio'] = fuzz.ratio(str1_clean, str2_clean) / 100
        scores['token_sort'] = fuzz.token_sort_ratio(str1_clean, str2_clean) / 100
        scores['token_set'] = fuzz.token_set_ratio(str1_clean, str2_clean) / 100
        scores['partial'] = fuzz.partial_ratio(str1_clean, str2_clean) / 100
        
        # Phonetic matching
        try:
            scores['soundex'] = 1.0 if jellyfish.soundex(str1_clean) == jellyfish.soundex(str2_clean) else 0.0
            scores['metaphone'] = 1.0 if jellyfish.metaphone(str1_clean) == jellyfish.metaphone(str2_clean) else 0.0
        except:
            scores['soundex'] = 0
            scores['metaphone'] = 0
        
        # Jaro-Winkler distance
        scores['jaro_winkler'] = jellyfish.jaro_winkler_similarity(str1_clean, str2_clean)
        
        # Levenshtein distance (normalized)
        max_len = max(len(str1_clean), len(str2_clean))
        if max_len > 0:
            lev_dist = jellyfish.levenshtein_distance(str1_clean, str2_clean)
            scores['levenshtein'] = 1 - (lev_dist / max_len)
        else:
            scores['levenshtein'] = 0
        
        # Calculate weighted overall score
        weights = {
            'exact': 1.0,
            'fuzzy_ratio': 0.7,
            'token_sort': 0.8,
            'token_set': 0.6,
            'partial': 0.5,
            'soundex': 0.4,
            'metaphone': 0.4,
            'jaro_winkler': 0.7,
            'levenshtein': 0.6
        }
        
        weighted_sum = sum(scores[k] * weights.get(k, 0.5) for k in scores)
        total_weight = sum(weights.get(k, 0.5) for k in scores)
        
        scores['overall'] = weighted_sum / total_weight if total_weight > 0 else 0
        
        return scores

# =====================================================
# ADDRESS PARSING AND MATCHING
# =====================================================

class AddressIntelligence:
    """Intelligent address parsing and matching"""
    
    @staticmethod
    def parse_address(address_str: str) -> Dict:
        """Parse address into components"""
        try:
            parsed = usaddress.parse(address_str)
            
            # Group components
            components = defaultdict(list)
            for value, label in parsed:
                components[label].append(value)
            
            # Join multiple values
            result = {}
            for label, values in components.items():
                result[label] = ' '.join(values)
                
            return result
        except:
            # Fallback to simple parsing
            parts = address_str.split(',')
            return {
                'AddressNumber': parts[0].strip() if parts else '',
                'StreetName': parts[1].strip() if len(parts) > 1 else '',
                'PlaceName': parts[2].strip() if len(parts) > 2 else ''
            }
    
    @staticmethod
    def match_addresses(addr1: str, addr2: str) -> float:
        """Intelligent address matching"""
        parsed1 = AddressIntelligence.parse_address(addr1)
        parsed2 = AddressIntelligence.parse_address(addr2)
        
        # Key components to match
        key_components = ['AddressNumber', 'StreetName', 'PlaceName', 'ZipCode']
        
        scores = []
        weights = []
        
        for component in key_components:
            val1 = parsed1.get(component, '').upper()
            val2 = parsed2.get(component, '').upper()
            
            if val1 and val2:
                if component == 'AddressNumber':
                    # Exact match for numbers
                    score = 1.0 if val1 == val2 else 0.0
                    weight = 1.0
                elif component == 'ZipCode':
                    # Partial match for zip (5 vs 9 digit)
                    score = 1.0 if val1[:5] == val2[:5] else 0.0
                    weight = 0.8
                else:
                    # Fuzzy match for text
                    score = fuzz.ratio(val1, val2) / 100
                    weight = 0.9 if component == 'StreetName' else 0.7
                    
                scores.append(score)
                weights.append(weight)
        
        if scores:
            return sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        
        # Fallback to simple fuzzy matching
        return fuzz.ratio(addr1.upper(), addr2.upper()) / 100

# =====================================================
# NETWORK GRAPH ANALYSIS
# =====================================================

class NetworkGraphAnalyzer:
    """Advanced network analysis for corporate relationships"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.centrality_cache = {}
        self.community_cache = {}
        
    def add_relationship(self, entity1: str, entity2: str, 
                        relationship_type: str, weight: float = 1.0):
        """Add relationship to graph"""
        self.graph.add_edge(entity1, entity2, 
                           type=relationship_type,
                           weight=weight)
        
        # Invalidate caches
        self.centrality_cache = {}
        self.community_cache = {}
    
    def find_connections(self, entity: str, max_depth: int = 3) -> List[Tuple[str, int, List[str]]]:
        """Find all connected entities up to max_depth"""
        if entity not in self.graph:
            return []
            
        connections = []
        visited = set()
        
        # BFS to find connections
        queue = [(entity, 0, [entity])]
        
        while queue:
            current, depth, path = queue.pop(0)
            
            if depth > max_depth:
                continue
                
            if current in visited and depth > 0:
                continue
                
            visited.add(current)
            
            if depth > 0:
                connections.append((current, depth, path))
                
            # Add neighbors to queue
            for neighbor in self.graph.neighbors(current):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1, path + [neighbor]))
                    
        return connections
    
    def calculate_importance(self, entity: str) -> Dict[str, float]:
        """Calculate various centrality measures"""
        if entity not in self.graph:
            return {'degree': 0, 'betweenness': 0, 'closeness': 0, 'pagerank': 0}
            
        # Use cached values if available
        if entity in self.centrality_cache:
            return self.centrality_cache[entity]
            
        try:
            # Calculate centrality measures
            degree = self.graph.degree(entity)
            
            betweenness_all = nx.betweenness_centrality(self.graph)
            betweenness = betweenness_all.get(entity, 0)
            
            if nx.is_connected(self.graph.to_undirected()):
                closeness_all = nx.closeness_centrality(self.graph)
                closeness = closeness_all.get(entity, 0)
            else:
                closeness = 0
                
            pagerank_all = nx.pagerank(self.graph)
            pagerank = pagerank_all.get(entity, 0)
            
            result = {
                'degree': degree,
                'betweenness': betweenness,
                'closeness': closeness,
                'pagerank': pagerank
            }
            
            self.centrality_cache[entity] = result
            return result
            
        except:
            return {'degree': 0, 'betweenness': 0, 'closeness': 0, 'pagerank': 0}
    
    def find_communities(self) -> Dict[str, int]:
        """Detect communities in the network"""
        if self.community_cache:
            return self.community_cache
            
        try:
            # Convert to undirected for community detection
            undirected = self.graph.to_undirected()
            
            # Use Louvain method for community detection
            import community as community_louvain
            communities = community_louvain.best_partition(undirected)
            
            self.community_cache = communities
            return communities
        except:
            return {}
    
    def get_network_stats(self) -> Dict:
        """Get overall network statistics"""
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'average_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes()
                              if self.graph.number_of_nodes() > 0 else 0,
            'connected_components': nx.number_weakly_connected_components(self.graph)
        }

# =====================================================
# REAL-TIME LEARNING SYSTEM
# =====================================================

class RealTimeLearner:
    """Continuous learning and adaptation system"""
    
    def __init__(self):
        self.match_history = deque(maxlen=10000)
        self.pattern_library = defaultdict(list)
        self.success_patterns = defaultdict(float)
        self.failure_patterns = defaultdict(float)
        
    def record_match(self, property_data: Dict, company_data: Dict, 
                    confidence: float, was_correct: Optional[bool] = None):
        """Record a match for learning"""
        match_record = {
            'timestamp': datetime.now(),
            'property': property_data,
            'company': company_data,
            'confidence': confidence,
            'correct': was_correct,
            'features': self._extract_patterns(property_data, company_data)
        }
        
        self.match_history.append(match_record)
        
        # Update pattern success rates
        if was_correct is not None:
            for pattern in match_record['features']:
                if was_correct:
                    self.success_patterns[pattern] += 1
                else:
                    self.failure_patterns[pattern] += 1
    
    def _extract_patterns(self, property_data: Dict, company_data: Dict) -> List[str]:
        """Extract patterns from a match"""
        patterns = []
        
        # Address patterns
        if property_data.get('address') and company_data.get('address'):
            if property_data['address'] == company_data['address']:
                patterns.append('exact_address_match')
            elif property_data.get('city') == company_data.get('city'):
                patterns.append('same_city')
                
        # Name patterns
        owner = property_data.get('owner_name', '').upper()
        company = company_data.get('company_name', '').upper()
        
        if owner and company:
            if owner == company:
                patterns.append('exact_name_match')
            elif owner in company or company in owner:
                patterns.append('substring_match')
            elif any(word in company for word in owner.split()):
                patterns.append('word_overlap')
                
        # Business entity patterns
        if any(suffix in owner for suffix in ['LLC', 'INC', 'CORP']):
            patterns.append('business_entity_owner')
            
        # Value patterns
        value = property_data.get('value', 0)
        if value > 5000000:
            patterns.append('high_value_property')
        elif value > 1000000:
            patterns.append('commercial_value_range')
            
        return patterns
    
    def get_pattern_confidence(self, patterns: List[str]) -> float:
        """Calculate confidence based on historical pattern success"""
        if not patterns:
            return 0.5
            
        total_weight = 0
        weighted_sum = 0
        
        for pattern in patterns:
            successes = self.success_patterns.get(pattern, 0)
            failures = self.failure_patterns.get(pattern, 0)
            
            if successes + failures > 0:
                success_rate = successes / (successes + failures)
                weight = min(1.0, (successes + failures) / 10)  # Weight by sample size
                
                weighted_sum += success_rate * weight
                total_weight += weight
                
        if total_weight > 0:
            return weighted_sum / total_weight
        
        return 0.5
    
    def suggest_improvements(self) -> List[str]:
        """Suggest improvements based on patterns"""
        suggestions = []
        
        # Analyze failure patterns
        high_failure_patterns = [
            pattern for pattern, count in self.failure_patterns.items()
            if count > self.success_patterns.get(pattern, 0) * 2
        ]
        
        if high_failure_patterns:
            suggestions.append(f"High failure patterns detected: {', '.join(high_failure_patterns[:3])}")
            
        # Analyze success patterns
        high_success_patterns = [
            pattern for pattern, count in self.success_patterns.items()
            if count > 10 and count > self.failure_patterns.get(pattern, 0) * 3
        ]
        
        if high_success_patterns:
            suggestions.append(f"Reliable patterns: {', '.join(high_success_patterns[:3])}")
            
        # Check data quality
        recent_matches = list(self.match_history)[-100:]
        avg_confidence = np.mean([m['confidence'] for m in recent_matches]) if recent_matches else 0
        
        if avg_confidence < 0.6:
            suggestions.append("Low average confidence - consider adding more data sources")
        elif avg_confidence > 0.85:
            suggestions.append("High confidence achieved - system performing well")
            
        return suggestions

# =====================================================
# MASTER OPTIMIZED ORCHESTRATOR
# =====================================================

class OptimizedChainOrchestrator:
    """Ultimate orchestrator with all optimizations"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        
        # Initialize components
        self.ml_scorer = MLConfidenceScorer()
        self.cache = IntelligentCache()
        self.ensemble = EnsembleVoter()
        self.string_matcher = AdvancedStringMatcher()
        self.address_intel = AddressIntelligence()
        self.network_graph = NetworkGraphAnalyzer()
        self.learner = RealTimeLearner()
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Performance metrics
        self.metrics = {
            'total_matches': 0,
            'avg_confidence': 0,
            'avg_processing_time': 0,
            'cache_hit_rate': 0
        }
        
    async def match_property(self, property_data: Dict, config: Dict = None) -> Dict:
        """
        Master matching function with all optimizations
        
        Config options:
        - min_confidence: Minimum confidence threshold (0-1)
        - max_agents: Maximum number of agents to use
        - use_ml: Use ML scoring
        - use_ensemble: Use ensemble voting
        - use_cache: Use caching
        - explain: Generate explanations
        """
        start_time = datetime.now()
        
        # Default config
        config = config or {}
        min_confidence = config.get('min_confidence', 0.6)
        max_agents = config.get('max_agents', 6)
        use_ml = config.get('use_ml', True)
        use_ensemble = config.get('use_ensemble', True)
        use_cache = config.get('use_cache', True)
        
        # Check cache first
        if use_cache:
            cached_result = await self.cache.get('property_match', property_data)
            if cached_result:
                self.metrics['cache_hit_rate'] = self.cache.get_stats()['hit_rate']
                return cached_result
        
        # Extract key features for ML
        ml_features = self._extract_ml_features(property_data)
        
        # Run agents in parallel (this would call your existing agents)
        agent_results = await self._run_agents_parallel(property_data, max_agents)
        
        # Apply ML scoring if enabled
        if use_ml and self.ml_scorer.is_trained:
            for result in agent_results:
                ml_confidence = self.ml_scorer.predict_confidence(ml_features)
                # Blend ML and agent confidence
                result['confidence'] = (result['confidence'] + ml_confidence) / 2
        
        # Apply ensemble voting if enabled
        if use_ensemble and len(agent_results) > 1:
            best_match = self.ensemble.vote(agent_results)
        else:
            # Sort by confidence and take best
            agent_results.sort(key=lambda x: x['confidence'], reverse=True)
            best_match = agent_results[0] if agent_results else None
        
        # Build network relationships
        if best_match:
            self._update_network(property_data, best_match)
            
            # Calculate network importance
            importance = self.network_graph.calculate_importance(
                best_match.get('company_doc_number', '')
            )
            best_match['network_importance'] = importance
        
        # Record for learning
        if best_match:
            self.learner.record_match(
                property_data,
                best_match,
                best_match.get('ensemble_confidence', best_match.get('confidence', 0))
            )
        
        # Calculate final result
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            'match': best_match,
            'alternatives': agent_results[1:6] if len(agent_results) > 1 else [],
            'processing_time': processing_time,
            'ml_features': ml_features if config.get('explain') else None,
            'network_stats': self.network_graph.get_network_stats(),
            'suggestions': self.learner.suggest_improvements(),
            'cache_stats': self.cache.get_stats() if use_cache else None
        }
        
        # Cache the result
        if use_cache and best_match:
            await self.cache.set('property_match', property_data, result, ttl=600)
        
        # Update metrics
        self._update_metrics(result)
        
        return result
    
    def _extract_ml_features(self, property_data: Dict) -> Dict:
        """Extract features for ML scoring"""
        return {
            'has_tax_id': bool(property_data.get('tax_id')),
            'has_address': bool(property_data.get('address')),
            'has_owner': bool(property_data.get('owner_name')),
            'is_commercial': property_data.get('property_use_code', '').startswith('C'),
            'value_range': self._categorize_value(property_data.get('value', 0)),
            'data_completeness': sum([
                bool(property_data.get(field))
                for field in ['address', 'owner_name', 'parcel_id', 'city', 'zip']
            ]) / 5
        }
    
    def _categorize_value(self, value: float) -> str:
        """Categorize property value"""
        if value > 10000000:
            return 'institutional'
        elif value > 5000000:
            return 'high_commercial'
        elif value > 1000000:
            return 'commercial'
        elif value > 500000:
            return 'mid_range'
        else:
            return 'residential'
    
    async def _run_agents_parallel(self, property_data: Dict, max_agents: int) -> List[Dict]:
        """Run agents in parallel (placeholder for actual agent execution)"""
        # This would integrate with your existing agent system
        # For now, returning mock results
        return []
    
    def _update_network(self, property_data: Dict, company_match: Dict):
        """Update network graph with new relationship"""
        property_id = property_data.get('parcel_id', '')
        company_id = company_match.get('company_doc_number', '')
        
        if property_id and company_id:
            self.network_graph.add_relationship(
                property_id,
                company_id,
                'owns',
                weight=company_match.get('confidence', 0.5)
            )
            
            # Add owner relationships if available
            owner = property_data.get('owner_name', '')
            if owner:
                self.network_graph.add_relationship(
                    owner,
                    company_id,
                    'associated_with',
                    weight=0.7
                )
    
    def _update_metrics(self, result: Dict):
        """Update performance metrics"""
        self.metrics['total_matches'] += 1
        
        if result.get('match'):
            confidence = result['match'].get('ensemble_confidence',
                                            result['match'].get('confidence', 0))
            
            # Running average
            n = self.metrics['total_matches']
            self.metrics['avg_confidence'] = (
                (self.metrics['avg_confidence'] * (n - 1) + confidence) / n
            )
            
            self.metrics['avg_processing_time'] = (
                (self.metrics['avg_processing_time'] * (n - 1) + result['processing_time']) / n
            )
    
    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report"""
        return {
            'metrics': self.metrics,
            'cache_performance': self.cache.get_stats(),
            'ensemble_weights': self.ensemble.agent_weights,
            'ml_model': {
                'is_trained': self.ml_scorer.is_trained,
                'feature_importance': self.ml_scorer.feature_importance,
                'training_samples': len(self.ml_scorer.training_data)
            },
            'network_analysis': self.network_graph.get_network_stats(),
            'learning_insights': self.learner.suggest_improvements()
        }
    
    async def train_ml_model(self, training_data: List[Tuple[Dict, bool]]):
        """Train the ML confidence scorer"""
        self.ml_scorer.train(training_data)
        logger.info(f"ML model trained with {len(training_data)} samples")
    
    def provide_feedback(self, match_id: str, was_correct: bool):
        """Provide feedback for continuous learning"""
        # Update ML scorer
        # This would look up the match and update accordingly
        pass
    
    async def shutdown(self):
        """Graceful shutdown"""
        self.executor.shutdown(wait=True)
        logger.info("Optimized orchestrator shutdown complete")