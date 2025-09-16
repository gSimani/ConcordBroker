"""
Graph-based recommendation engine for ConcordBroker
Uses Neo4j graph patterns and Graphiti temporal data for intelligent property recommendations
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
from neo4j import AsyncSession
from .property_graph_service import PropertyGraphService
from .enhanced_rag_service import EnhancedRAGService
from ..agents.confidence_agent import ConfidenceAgent

class RecommendationType(Enum):
    INVESTMENT = "investment"
    SIMILAR_PROPERTIES = "similar_properties"
    MARKET_OPPORTUNITIES = "market_opportunities"
    RISK_ANALYSIS = "risk_analysis"
    PORTFOLIO_EXPANSION = "portfolio_expansion"
    FLIP_OPPORTUNITIES = "flip_opportunities"

@dataclass
class PropertyRecommendation:
    parcel_id: str
    recommendation_type: RecommendationType
    title: str
    description: str
    confidence_score: float
    potential_roi: Optional[float] = None
    risk_level: str = "medium"
    reasoning: List[str] = None
    supporting_data: Dict[str, Any] = None
    urgency: str = "normal"  # low, normal, high, urgent
    estimated_value: Optional[float] = None
    comparable_properties: List[str] = None
    action_items: List[str] = None
    
    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = []
        if self.supporting_data is None:
            self.supporting_data = {}
        if self.comparable_properties is None:
            self.comparable_properties = []
        if self.action_items is None:
            self.action_items = []

@dataclass
class RecommendationRequest:
    user_id: str
    recommendation_types: List[RecommendationType]
    filters: Dict[str, Any] = None
    max_results: int = 10
    include_reasoning: bool = True
    confidence_threshold: float = 0.6
    location_preferences: List[str] = None
    budget_range: Tuple[float, float] = None
    investment_strategy: str = "balanced"  # conservative, balanced, aggressive
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}
        if self.location_preferences is None:
            self.location_preferences = []

class GraphRecommendationEngine:
    def __init__(self, graph_service: PropertyGraphService, rag_service: EnhancedRAGService):
        self.graph_service = graph_service
        self.rag_service = rag_service
        self.confidence_agent = ConfidenceAgent()
        
        # Recommendation weights - can be tuned based on user feedback
        self.weights = {
            'price_trend': 0.25,
            'location_score': 0.20,
            'ownership_stability': 0.15,
            'market_activity': 0.15,
            'property_condition': 0.10,
            'historical_performance': 0.15
        }
        
        # Risk thresholds
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        }

    async def generate_recommendations(
        self, 
        request: RecommendationRequest
    ) -> List[PropertyRecommendation]:
        """Generate personalized property recommendations based on graph analysis"""
        
        recommendations = []
        
        for rec_type in request.recommendation_types:
            try:
                if rec_type == RecommendationType.INVESTMENT:
                    recs = await self._find_investment_opportunities(request)
                elif rec_type == RecommendationType.SIMILAR_PROPERTIES:
                    recs = await self._find_similar_properties(request)
                elif rec_type == RecommendationType.MARKET_OPPORTUNITIES:
                    recs = await self._find_market_opportunities(request)
                elif rec_type == RecommendationType.RISK_ANALYSIS:
                    recs = await self._analyze_risk_properties(request)
                elif rec_type == RecommendationType.PORTFOLIO_EXPANSION:
                    recs = await self._suggest_portfolio_expansion(request)
                elif rec_type == RecommendationType.FLIP_OPPORTUNITIES:
                    recs = await self._find_flip_opportunities(request)
                else:
                    continue
                    
                recommendations.extend(recs)
                
            except Exception as e:
                print(f"Error generating {rec_type.value} recommendations: {e}")
                continue
        
        # Sort by confidence and apply filters
        recommendations = [r for r in recommendations if r.confidence_score >= request.confidence_threshold]
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return recommendations[:request.max_results]

    async def _find_investment_opportunities(
        self, 
        request: RecommendationRequest
    ) -> List[PropertyRecommendation]:
        """Find properties with strong investment potential using graph patterns"""
        
        query = """
        MATCH (p:Property)
        OPTIONAL MATCH (p)-[:SOLD_TO]->(t:Transaction)
        OPTIONAL MATCH (p)-[:LOCATED_IN]->(area:Area)
        WITH p, 
             collect(t) as transactions,
             area,
             p.current_value as current_value,
             p.assessed_value as assessed_value
        WHERE size(transactions) >= 2 
          AND current_value IS NOT NULL
          AND assessed_value IS NOT NULL
        
        // Calculate price appreciation
        WITH p, transactions, area, current_value, assessed_value,
             [t IN transactions | t.price] as prices,
             [t IN transactions | t.date] as dates
        WHERE size(prices) >= 2
        
        // Calculate ROI potential
        WITH p, area,
             current_value,
             assessed_value,
             prices[-1] - prices[0] as price_change,
             duration.between(date(dates[0]), date(dates[-1])).months as months_held
        WHERE months_held > 0
        
        WITH p, area,
             current_value,
             assessed_value,
             price_change,
             (price_change / prices[0]) * 100 as appreciation_percent,
             (price_change / months_held) * 12 as annualized_return
        
        // Find undervalued properties with good appreciation
        WHERE current_value < assessed_value * 0.9  // Potentially undervalued
          OR annualized_return > 5.0  // Good historical returns
        
        RETURN p.parcel_id as parcel_id,
               p.address as address,
               p.city as city,
               current_value,
               assessed_value,
               appreciation_percent,
               annualized_return,
               area.market_trend as market_trend
        ORDER BY annualized_return DESC
        LIMIT 50
        """
        
        results = await self.graph_service.execute_query(query)
        recommendations = []
        
        for record in results:
            # Calculate confidence based on multiple factors
            factors = {
                'historical_performance': min(record.get('annualized_return', 0) / 15.0, 1.0),
                'value_gap': min((record.get('assessed_value', 0) - record.get('current_value', 0)) / record.get('current_value', 1), 0.3) / 0.3,
                'market_trend': 0.8 if record.get('market_trend') == 'growing' else 0.5
            }
            
            confidence = await self.confidence_agent.calculate_confidence(
                input_data=record,
                context={'factors': factors}
            )
            
            if confidence >= 0.6:
                roi_estimate = record.get('annualized_return', 0)
                risk_level = self._calculate_risk_level(roi_estimate, record)
                
                recommendation = PropertyRecommendation(
                    parcel_id=record['parcel_id'],
                    recommendation_type=RecommendationType.INVESTMENT,
                    title=f"Investment Opportunity - {record.get('address', 'Unknown Address')}",
                    description=f"Property showing {roi_estimate:.1f}% annualized returns with potential undervaluation",
                    confidence_score=confidence,
                    potential_roi=roi_estimate,
                    risk_level=risk_level,
                    reasoning=[
                        f"Historical annualized return: {roi_estimate:.1f}%",
                        f"Current value ${record.get('current_value', 0):,.0f} vs assessed ${record.get('assessed_value', 0):,.0f}",
                        f"Located in {record.get('city', 'Unknown')} with {record.get('market_trend', 'stable')} market"
                    ],
                    urgency="high" if roi_estimate > 12 else "normal",
                    estimated_value=record.get('current_value'),
                    action_items=[
                        "Schedule property inspection",
                        "Analyze comparable sales",
                        "Review property condition and needed repairs",
                        "Calculate total investment including renovation costs"
                    ]
                )
                
                recommendations.append(recommendation)
        
        return recommendations

    async def _find_similar_properties(
        self, 
        request: RecommendationRequest
    ) -> List[PropertyRecommendation]:
        """Find properties similar to user's existing portfolio or preferences"""
        
        # Get user's property preferences from past activity
        query = """
        MATCH (u:User {user_id: $user_id})-[:INTERESTED_IN|OWNS]->(p:Property)
        WITH collect(p) as user_properties
        
        // Find common characteristics
        UNWIND user_properties as up
        MATCH (similar:Property)
        WHERE similar.city = up.city
          AND abs(similar.bedrooms - up.bedrooms) <= 1
          AND abs(similar.current_value - up.current_value) / up.current_value <= 0.3
          AND similar.parcel_id <> up.parcel_id
        
        WITH similar, count(*) as similarity_score,
             avg([prop in user_properties | prop.current_value]) as avg_user_value
        
        WHERE similarity_score >= 2
        
        RETURN similar.parcel_id as parcel_id,
               similar.address as address,
               similar.city as city,
               similar.current_value as current_value,
               similarity_score,
               abs(similar.current_value - avg_user_value) / avg_user_value as value_similarity
        ORDER BY similarity_score DESC, value_similarity ASC
        LIMIT 20
        """
        
        results = await self.graph_service.execute_query(
            query, 
            parameters={'user_id': request.user_id}
        )
        
        recommendations = []
        
        for record in results:
            confidence = min(record.get('similarity_score', 0) / 5.0, 0.9)
            
            recommendation = PropertyRecommendation(
                parcel_id=record['parcel_id'],
                recommendation_type=RecommendationType.SIMILAR_PROPERTIES,
                title=f"Similar Property - {record.get('address', 'Unknown Address')}",
                description=f"Property matching your portfolio characteristics in {record.get('city')}",
                confidence_score=confidence,
                risk_level="low",
                reasoning=[
                    f"Matches {record.get('similarity_score', 0)} of your property criteria",
                    f"Located in familiar market: {record.get('city')}",
                    f"Similar value range: ${record.get('current_value', 0):,.0f}"
                ],
                estimated_value=record.get('current_value')
            )
            
            recommendations.append(recommendation)
        
        return recommendations

    async def _find_market_opportunities(
        self, 
        request: RecommendationRequest
    ) -> List[PropertyRecommendation]:
        """Identify emerging market opportunities using graph network analysis"""
        
        query = """
        MATCH (p:Property)-[:LOCATED_IN]->(area:Area)
        MATCH (area)-[:HAS_RECENT_SALE]->(recent:Transaction)
        WHERE recent.date > date() - duration('P6M')
        
        WITH area, 
             count(recent) as recent_sales,
             avg(recent.price) as avg_recent_price,
             collect(p) as properties
        WHERE recent_sales >= 5
        
        // Find areas with increasing activity and prices
        MATCH (area)-[:HAS_HISTORICAL_SALE]->(historical:Transaction)
        WHERE historical.date < date() - duration('P12M')
        
        WITH area, recent_sales, avg_recent_price, properties,
             avg(historical.price) as avg_historical_price,
             count(historical) as historical_sales
        WHERE historical_sales >= 5
        
        WITH area, properties, recent_sales, historical_sales,
             (avg_recent_price - avg_historical_price) / avg_historical_price as price_growth,
             (recent_sales - historical_sales) as activity_increase
        WHERE price_growth > 0.1 OR activity_increase > 0.2
        
        UNWIND properties as p
        WHERE p.current_value < avg_recent_price * 0.8  // Below market average
        
        RETURN p.parcel_id as parcel_id,
               p.address as address,
               p.city as city,
               p.current_value as current_value,
               area.name as area_name,
               price_growth * 100 as price_growth_percent,
               activity_increase as market_activity_increase
        ORDER BY price_growth DESC, activity_increase DESC
        LIMIT 20
        """
        
        results = await self.graph_service.execute_query(query)
        recommendations = []
        
        for record in results:
            price_growth = record.get('price_growth_percent', 0)
            activity_increase = record.get('market_activity_increase', 0)
            
            # Higher confidence for areas with both price growth and activity
            confidence = min((price_growth / 20.0) + (activity_increase / 10.0), 0.95)
            
            if confidence >= 0.6:
                recommendation = PropertyRecommendation(
                    parcel_id=record['parcel_id'],
                    recommendation_type=RecommendationType.MARKET_OPPORTUNITIES,
                    title=f"Emerging Market - {record.get('address', 'Unknown Address')}",
                    description=f"Property in rapidly appreciating {record.get('area_name')} area",
                    confidence_score=confidence,
                    risk_level="medium",
                    reasoning=[
                        f"Area showing {price_growth:.1f}% price growth",
                        f"Market activity increased by {activity_increase} transactions",
                        f"Property priced below area average"
                    ],
                    urgency="high" if price_growth > 15 else "normal",
                    estimated_value=record.get('current_value'),
                    action_items=[
                        "Research local development plans",
                        "Analyze area demographic trends",
                        "Compare with similar emerging markets",
                        "Monitor competition and inventory levels"
                    ]
                )
                
                recommendations.append(recommendation)
        
        return recommendations

    async def _analyze_risk_properties(
        self, 
        request: RecommendationRequest
    ) -> List[PropertyRecommendation]:
        """Identify properties with potential risks using graph pattern analysis"""
        
        query = """
        MATCH (p:Property)
        OPTIONAL MATCH (p)-[:HAS_LIEN]->(lien:TaxLien)
        OPTIONAL MATCH (p)-[:IN_FORECLOSURE]->(foreclosure:Foreclosure)
        OPTIONAL MATCH (p)-[:OWNED_BY]->(owner:Owner)
        OPTIONAL MATCH (owner)-[:OWNS]->(other_props:Property)
        
        WITH p, 
             count(lien) as lien_count,
             count(foreclosure) as foreclosure_count,
             count(other_props) as owner_property_count,
             owner
        
        // Calculate risk factors
        WITH p, owner,
             CASE WHEN lien_count > 0 THEN 0.3 ELSE 0 END as lien_risk,
             CASE WHEN foreclosure_count > 0 THEN 0.4 ELSE 0 END as foreclosure_risk,
             CASE WHEN owner_property_count > 10 THEN 0.1 ELSE 0.2 END as concentration_risk
        
        WITH p, owner,
             lien_risk + foreclosure_risk + concentration_risk as total_risk
        WHERE total_risk > 0.3
        
        RETURN p.parcel_id as parcel_id,
               p.address as address,
               p.city as city,
               p.current_value as current_value,
               total_risk,
               lien_risk > 0 as has_liens,
               foreclosure_risk > 0 as in_foreclosure,
               owner.name as owner_name
        ORDER BY total_risk DESC
        LIMIT 15
        """
        
        results = await self.graph_service.execute_query(query)
        recommendations = []
        
        for record in results:
            total_risk = record.get('total_risk', 0)
            confidence = min(total_risk, 0.9)
            
            risk_factors = []
            if record.get('has_liens'):
                risk_factors.append("Property has tax liens")
            if record.get('in_foreclosure'):
                risk_factors.append("Property in foreclosure process")
            
            risk_level = "high" if total_risk > 0.6 else "medium"
            
            recommendation = PropertyRecommendation(
                parcel_id=record['parcel_id'],
                recommendation_type=RecommendationType.RISK_ANALYSIS,
                title=f"Risk Alert - {record.get('address', 'Unknown Address')}",
                description=f"Property with elevated risk factors requiring attention",
                confidence_score=confidence,
                risk_level=risk_level,
                reasoning=risk_factors,
                urgency="high" if risk_level == "high" else "normal",
                estimated_value=record.get('current_value'),
                action_items=[
                    "Review legal status and liens",
                    "Assess owner financial situation",
                    "Consider portfolio diversification",
                    "Monitor market conditions closely"
                ]
            )
            
            recommendations.append(recommendation)
        
        return recommendations

    async def _suggest_portfolio_expansion(
        self, 
        request: RecommendationRequest
    ) -> List[PropertyRecommendation]:
        """Suggest properties for portfolio diversification"""
        
        query = """
        MATCH (u:User {user_id: $user_id})-[:OWNS]->(owned:Property)
        WITH u, collect(distinct owned.city) as owned_cities,
             collect(distinct owned.property_type) as owned_types,
             avg(owned.current_value) as avg_owned_value
        
        MATCH (p:Property)
        WHERE NOT p.city IN owned_cities  // Different geographic area
          AND NOT p.property_type IN owned_types  // Different property type
          AND p.current_value BETWEEN avg_owned_value * 0.5 AND avg_owned_value * 2.0
        
        // Find areas with good fundamentals
        MATCH (p)-[:LOCATED_IN]->(area:Area)
        WHERE area.employment_growth > 0.02  // 2% employment growth
          AND area.population_growth > 0.01  // 1% population growth
        
        RETURN p.parcel_id as parcel_id,
               p.address as address,
               p.city as city,
               p.property_type as property_type,
               p.current_value as current_value,
               area.employment_growth * 100 as employment_growth_percent,
               area.population_growth * 100 as population_growth_percent
        ORDER BY area.employment_growth + area.population_growth DESC
        LIMIT 15
        """
        
        results = await self.graph_service.execute_query(
            query, 
            parameters={'user_id': request.user_id}
        )
        
        recommendations = []
        
        for record in results:
            emp_growth = record.get('employment_growth_percent', 0)
            pop_growth = record.get('population_growth_percent', 0)
            
            confidence = min((emp_growth + pop_growth) / 10.0, 0.85)
            
            if confidence >= 0.5:
                recommendation = PropertyRecommendation(
                    parcel_id=record['parcel_id'],
                    recommendation_type=RecommendationType.PORTFOLIO_EXPANSION,
                    title=f"Diversification Opportunity - {record.get('address')}",
                    description=f"Expand into {record.get('city')} {record.get('property_type')} market",
                    confidence_score=confidence,
                    risk_level="medium",
                    reasoning=[
                        f"Geographic diversification to {record.get('city')}",
                        f"Property type diversification: {record.get('property_type')}",
                        f"Area has {emp_growth:.1f}% employment growth",
                        f"Population growing at {pop_growth:.1f}%"
                    ],
                    estimated_value=record.get('current_value'),
                    action_items=[
                        "Research local market dynamics",
                        "Connect with local property managers",
                        "Understand local regulations and taxes",
                        "Assess property management complexity"
                    ]
                )
                
                recommendations.append(recommendation)
        
        return recommendations

    async def _find_flip_opportunities(
        self, 
        request: RecommendationRequest
    ) -> List[PropertyRecommendation]:
        """Find properties suitable for fix-and-flip investments"""
        
        query = """
        MATCH (p:Property)
        WHERE p.condition_score < 6  // Properties needing work
          AND p.current_value IS NOT NULL
        
        // Find comparable sales in the area
        MATCH (p)-[:LOCATED_IN]->(area:Area)
        MATCH (area)<-[:LOCATED_IN]-(comparable:Property)
        WHERE comparable.condition_score >= 8  // Good condition properties
          AND abs(comparable.bedrooms - p.bedrooms) <= 1
          AND abs(comparable.bathrooms - p.bathrooms) <= 1
          AND comparable.square_footage BETWEEN p.square_footage * 0.8 AND p.square_footage * 1.2
        
        // Calculate potential after-repair value (ARV)
        WITH p, avg(comparable.current_value) as estimated_arv,
             p.current_value as current_value,
             p.condition_score as condition_score
        WHERE estimated_arv > current_value * 1.2  // At least 20% upside potential
        
        // Estimate renovation costs based on condition
        WITH p, estimated_arv, current_value, condition_score,
             (10 - condition_score) * p.square_footage * 15 as estimated_renovation_cost
        
        WITH p, estimated_arv, current_value, estimated_renovation_cost,
             estimated_arv - current_value - estimated_renovation_cost as potential_profit
        WHERE potential_profit > current_value * 0.15  // At least 15% profit margin
        
        RETURN p.parcel_id as parcel_id,
               p.address as address,
               p.city as city,
               current_value,
               estimated_arv,
               estimated_renovation_cost,
               potential_profit,
               (potential_profit / (current_value + estimated_renovation_cost)) * 100 as roi_percent
        ORDER BY roi_percent DESC
        LIMIT 10
        """
        
        results = await self.graph_service.execute_query(query)
        recommendations = []
        
        for record in results:
            roi = record.get('roi_percent', 0)
            confidence = min(roi / 30.0, 0.9)  # Scale confidence based on ROI
            
            if confidence >= 0.5:
                recommendation = PropertyRecommendation(
                    parcel_id=record['parcel_id'],
                    recommendation_type=RecommendationType.FLIP_OPPORTUNITIES,
                    title=f"Flip Opportunity - {record.get('address')}",
                    description=f"Property with {roi:.1f}% estimated ROI potential",
                    confidence_score=confidence,
                    potential_roi=roi,
                    risk_level="high",  # Flips are inherently higher risk
                    reasoning=[
                        f"Current value: ${record.get('current_value', 0):,.0f}",
                        f"Estimated ARV: ${record.get('estimated_arv', 0):,.0f}",
                        f"Renovation estimate: ${record.get('estimated_renovation_cost', 0):,.0f}",
                        f"Potential profit: ${record.get('potential_profit', 0):,.0f}"
                    ],
                    urgency="normal",
                    estimated_value=record.get('estimated_arv'),
                    action_items=[
                        "Get professional contractor estimates",
                        "Inspect for structural issues",
                        "Research permit requirements",
                        "Analyze comparable sales trends",
                        "Calculate holding costs and timeline"
                    ]
                )
                
                recommendations.append(recommendation)
        
        return recommendations

    def _calculate_risk_level(self, roi: float, property_data: Dict[str, Any]) -> str:
        """Calculate risk level based on ROI and property characteristics"""
        
        base_risk = 0.5
        
        # Adjust risk based on ROI (higher ROI often means higher risk)
        if roi > 15:
            base_risk += 0.2
        elif roi < 5:
            base_risk += 0.1
        
        # Adjust based on property characteristics
        if property_data.get('market_trend') == 'declining':
            base_risk += 0.1
        elif property_data.get('market_trend') == 'growing':
            base_risk -= 0.1
        
        if base_risk <= self.risk_thresholds['low']:
            return "low"
        elif base_risk <= self.risk_thresholds['medium']:
            return "medium"
        else:
            return "high"

    async def get_recommendation_explanation(
        self, 
        parcel_id: str, 
        recommendation_type: RecommendationType
    ) -> Dict[str, Any]:
        """Get detailed explanation for why a property was recommended"""
        
        query = """
        MATCH (p:Property {parcel_id: $parcel_id})
        OPTIONAL MATCH (p)-[:LOCATED_IN]->(area:Area)
        OPTIONAL MATCH (p)-[:OWNED_BY]->(owner:Owner)
        OPTIONAL MATCH (p)-[:HAS_TRANSACTION]->(t:Transaction)
        
        RETURN p, area, owner, collect(t) as transactions
        """
        
        results = await self.graph_service.execute_query(
            query, 
            parameters={'parcel_id': parcel_id}
        )
        
        if not results:
            return {"error": "Property not found"}
        
        property_data = results[0]
        
        # Use RAG service to generate natural language explanation
        context = f"""
        Property: {property_data.get('p', {}).get('address', 'Unknown')}
        Area: {property_data.get('area', {}).get('name', 'Unknown')}
        Owner: {property_data.get('owner', {}).get('name', 'Unknown')}
        Recent transactions: {len(property_data.get('transactions', []))}
        """
        
        explanation = await self.rag_service.hybrid_search(
            query=f"Explain why this property is recommended for {recommendation_type.value}",
            context=context
        )
        
        return {
            "property_data": property_data,
            "explanation": explanation,
            "recommendation_type": recommendation_type.value
        }

    async def update_recommendation_feedback(
        self, 
        user_id: str, 
        parcel_id: str, 
        feedback: str, 
        rating: int
    ) -> bool:
        """Update recommendation engine based on user feedback"""
        
        try:
            # Store feedback in graph
            query = """
            MATCH (u:User {user_id: $user_id})
            MATCH (p:Property {parcel_id: $parcel_id})
            CREATE (u)-[:RATED {
                rating: $rating,
                feedback: $feedback,
                timestamp: datetime()
            }]->(p)
            """
            
            await self.graph_service.execute_query(
                query,
                parameters={
                    'user_id': user_id,
                    'parcel_id': parcel_id,
                    'rating': rating,
                    'feedback': feedback
                }
            )
            
            # TODO: Use feedback to retrain recommendation weights
            await self._adjust_recommendation_weights(user_id, feedback, rating)
            
            return True
            
        except Exception as e:
            print(f"Error updating recommendation feedback: {e}")
            return False

    async def _adjust_recommendation_weights(
        self, 
        user_id: str, 
        feedback: str, 
        rating: int
    ) -> None:
        """Adjust recommendation weights based on user feedback (simplified version)"""
        
        # Simple feedback learning - in production, use more sophisticated ML
        adjustment_factor = (rating - 3) * 0.02  # -0.04 to +0.04
        
        if 'price' in feedback.lower():
            self.weights['price_trend'] += adjustment_factor
        elif 'location' in feedback.lower():
            self.weights['location_score'] += adjustment_factor
        elif 'risk' in feedback.lower():
            self.weights['ownership_stability'] += adjustment_factor
        
        # Normalize weights to sum to 1.0
        total_weight = sum(self.weights.values())
        for key in self.weights:
            self.weights[key] /= total_weight