"""
Property Scoring Algorithm
Calculates investment potential score based on multiple factors
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import statistics

import numpy as np
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PropertyScore(BaseModel):
    """Property score with detailed breakdown"""
    folio: str
    total_score: float
    breakdown: Dict[str, float]
    factors: Dict[str, Any]
    calculated_at: datetime
    confidence: float


class ScoringService:
    """Service for calculating property investment scores"""
    
    # Use code weights (higher = better investment potential)
    USE_CODE_WEIGHTS = {
        '48': 30,  # Industrial warehouses - highest potential
        '43': 28,  # Lumber yards
        '39': 25,  # Hotels/motels
        '17': 25,  # Office buildings
        '11': 22,  # Retail stores
        '03': 22,  # Multi-family 10+ units
        '04': 20,  # Condominiums
        '00': 18,  # Vacant land - development potential
        '10': 16,  # Vacant commercial
        '40': 16,  # Vacant industrial
        '01': 15,  # Single family
        '02': 12,  # Mobile homes
        '08': 12,  # Multi-family <10 units
    }
    
    def calculate_score(self, 
                       parcel: Dict[str, Any],
                       comparables: List[Dict[str, Any]] = None,
                       market_data: Dict[str, Any] = None) -> PropertyScore:
        """
        Calculate comprehensive property score
        
        Args:
            parcel: Property data dictionary
            comparables: List of comparable properties in same area
            market_data: Market trends and statistics
            
        Returns:
            PropertyScore with detailed breakdown
        """
        
        folio = parcel.get('folio', 'unknown')
        logger.info(f"Calculating score for {folio}")
        
        # Initialize scores
        total_score = 50.0  # Base score
        breakdown = {}
        factors = {}
        
        # 1. Use Code Score (0-30 points)
        use_score = self._calculate_use_code_score(parcel)
        breakdown['use_code'] = use_score
        total_score += use_score
        
        # 2. Value Assessment Gap (0-20 points)
        value_gap_score = self._calculate_value_gap_score(parcel)
        breakdown['value_gap'] = value_gap_score
        total_score += value_gap_score
        
        # 3. Recent Sales Activity (0-15 points)
        sales_score = self._calculate_sales_activity_score(parcel)
        breakdown['sales_activity'] = sales_score
        total_score += sales_score
        
        # 4. Price vs Comparables (0-15 points)
        if comparables:
            comp_score = self._calculate_comparable_score(parcel, comparables)
            breakdown['price_comparison'] = comp_score
            total_score += comp_score
        else:
            breakdown['price_comparison'] = 0
        
        # 5. Age Factor (0-10 points)
        age_score = self._calculate_age_score(parcel)
        breakdown['age_factor'] = age_score
        total_score += age_score
        
        # 6. Entity Ownership (0-10 points)
        entity_score = self._calculate_entity_score(parcel)
        breakdown['entity_ownership'] = entity_score
        total_score += entity_score
        
        # 7. Location Score (0-10 points)
        location_score = self._calculate_location_score(parcel)
        breakdown['location_quality'] = location_score
        total_score += location_score
        
        # 8. Size/Scale Score (0-10 points)
        size_score = self._calculate_size_score(parcel)
        breakdown['property_size'] = size_score
        total_score += size_score
        
        # Ensure score is 0-100
        total_score = max(0, min(100, total_score))
        
        # Calculate confidence based on data completeness
        confidence = self._calculate_confidence(parcel, breakdown)
        
        # Store detailed factors for transparency
        factors = {
            'use_code': parcel.get('main_use'),
            'sub_use': parcel.get('sub_use'),
            'just_value': parcel.get('just_value'),
            'assessed_value': parcel.get('assessed_value'),
            'taxable_value': parcel.get('taxable'),
            'year_built': parcel.get('eff_year'),
            'land_sf': parcel.get('land_sf'),
            'building_sf': parcel.get('bldg_sf'),
            'city': parcel.get('city'),
            'owner_type': 'entity' if parcel.get('owner_entity_id') else 'individual',
            'last_sale_date': parcel.get('last_sale_date'),
            'comparable_count': len(comparables) if comparables else 0,
        }
        
        return PropertyScore(
            folio=folio,
            total_score=round(total_score, 2),
            breakdown=breakdown,
            factors=factors,
            calculated_at=datetime.now(),
            confidence=round(confidence, 2)
        )
    
    def _calculate_use_code_score(self, parcel: Dict) -> float:
        """Calculate score based on property use code"""
        use_code = parcel.get('main_use', '')
        base_score = self.USE_CODE_WEIGHTS.get(use_code, 5)
        
        # Adjust for sub-use if available
        sub_use = parcel.get('sub_use', '')
        if sub_use:
            # Bonus for specific high-value sub-uses
            if use_code == '48' and sub_use in ['01', '02']:  # Distribution warehouses
                base_score += 2
            elif use_code == '17' and sub_use in ['01', '02']:  # Medical offices
                base_score += 3
        
        return min(30, base_score)
    
    def _calculate_value_gap_score(self, parcel: Dict) -> float:
        """Calculate score based on assessment vs market value gap"""
        just_value = parcel.get('just_value', 0)
        assessed_value = parcel.get('assessed_soh', parcel.get('assessed_value', 0))
        
        if not just_value or not assessed_value or just_value <= 0:
            return 0
        
        # Calculate gap ratio
        gap_ratio = (just_value - assessed_value) / just_value
        
        # Higher gap = higher opportunity
        if gap_ratio > 0.3:  # 30%+ gap
            return 20
        elif gap_ratio > 0.2:  # 20-30% gap
            return 15
        elif gap_ratio > 0.1:  # 10-20% gap
            return 10
        elif gap_ratio > 0.05:  # 5-10% gap
            return 5
        else:
            return 0
    
    def _calculate_sales_activity_score(self, parcel: Dict) -> float:
        """Calculate score based on recent sales activity"""
        sales = parcel.get('sales', [])
        
        if not sales:
            # No recent sales might indicate opportunity
            return 5
        
        # Count recent sales (last 2 years)
        two_years_ago = datetime.now() - timedelta(days=730)
        recent_sales = [
            s for s in sales 
            if isinstance(s.get('sale_date'), (str, datetime))
        ]
        
        recent_count = len(recent_sales)
        
        if recent_count == 0:
            return 5  # No recent sales
        elif recent_count == 1:
            return 10  # One recent sale - moderate activity
        elif recent_count == 2:
            return 15  # Two sales - high activity
        else:
            return 12  # Multiple sales - very active (might be flipping)
    
    def _calculate_comparable_score(self, parcel: Dict, 
                                   comparables: List[Dict]) -> float:
        """Calculate score based on price vs comparables"""
        if not comparables or len(comparables) < 3:
            return 0
        
        parcel_value = parcel.get('just_value', 0)
        parcel_land_sf = parcel.get('land_sf', 1)
        
        if not parcel_value or not parcel_land_sf:
            return 0
        
        parcel_ppsf = parcel_value / parcel_land_sf
        
        # Calculate comparable median price per sq ft
        comp_ppsf_values = []
        for comp in comparables:
            comp_value = comp.get('just_value', 0)
            comp_land_sf = comp.get('land_sf', 0)
            if comp_value and comp_land_sf:
                comp_ppsf_values.append(comp_value / comp_land_sf)
        
        if not comp_ppsf_values:
            return 0
        
        median_ppsf = statistics.median(comp_ppsf_values)
        
        # Calculate discount ratio
        if median_ppsf > 0:
            discount_ratio = (median_ppsf - parcel_ppsf) / median_ppsf
        else:
            return 0
        
        # Score based on discount
        if discount_ratio > 0.3:  # 30%+ below median
            return 15
        elif discount_ratio > 0.15:  # 15-30% below
            return 12
        elif discount_ratio > 0:  # 0-15% below
            return 8
        else:  # At or above median
            return 3
    
    def _calculate_age_score(self, parcel: Dict) -> float:
        """Calculate score based on property age"""
        eff_year = parcel.get('eff_year') or parcel.get('act_year')
        
        if not eff_year:
            return 0
        
        current_year = datetime.now().year
        age = current_year - eff_year
        
        if age > 50:
            # Very old - redevelopment opportunity
            return 10
        elif age > 30:
            # Old - renovation opportunity
            return 8
        elif age > 20:
            # Mature property
            return 5
        elif age < 5:
            # Very new - less opportunity
            return 3
        else:
            # Middle age
            return 4
    
    def _calculate_entity_score(self, parcel: Dict) -> float:
        """Calculate score based on ownership type"""
        if parcel.get('owner_entity_id'):
            # Corporate ownership often indicates investment property
            return 10
        
        owner_name = parcel.get('owner_raw', '').upper()
        
        # Check for corporate indicators in name
        corporate_indicators = ['LLC', 'INC', 'CORP', 'LP', 'TRUST', 'INVESTMENT']
        if any(indicator in owner_name for indicator in corporate_indicators):
            return 8
        
        return 0
    
    def _calculate_location_score(self, parcel: Dict) -> float:
        """Calculate score based on location quality"""
        city = parcel.get('city', '').upper()
        
        # Premium cities
        premium_cities = ['FORT LAUDERDALE', 'HOLLYWOOD', 'POMPANO BEACH', 
                         'DEERFIELD BEACH', 'CORAL SPRINGS']
        
        # Growing cities
        growing_cities = ['MIRAMAR', 'PEMBROKE PINES', 'DAVIE', 
                         'SUNRISE', 'PLANTATION']
        
        if city in premium_cities:
            return 10
        elif city in growing_cities:
            return 8
        elif city:
            return 5
        else:
            return 0
    
    def _calculate_size_score(self, parcel: Dict) -> float:
        """Calculate score based on property size"""
        land_sf = parcel.get('land_sf', 0)
        
        if land_sf > 100000:  # 2+ acres
            return 10
        elif land_sf > 43560:  # 1+ acre
            return 8
        elif land_sf > 20000:  # ~0.5 acre
            return 6
        elif land_sf > 10000:
            return 4
        else:
            return 2
    
    def _calculate_confidence(self, parcel: Dict, breakdown: Dict) -> float:
        """Calculate confidence score based on data completeness"""
        required_fields = [
            'just_value', 'assessed_soh', 'land_sf', 'main_use',
            'city', 'owner_raw'
        ]
        
        # Count available fields
        available = sum(1 for field in required_fields if parcel.get(field))
        field_completeness = available / len(required_fields)
        
        # Check breakdown components
        scoring_components = len([v for v in breakdown.values() if v > 0])
        component_completeness = scoring_components / len(breakdown)
        
        # Average completeness
        confidence = (field_completeness + component_completeness) / 2 * 100
        
        return confidence
    
    def batch_score(self, parcels: List[Dict], 
                   get_comparables_func=None) -> List[PropertyScore]:
        """Score multiple properties in batch"""
        scores = []
        
        for parcel in parcels:
            comparables = []
            if get_comparables_func:
                comparables = get_comparables_func(parcel)
            
            score = self.calculate_score(parcel, comparables)
            scores.append(score)
        
        return scores
    
    def get_score_interpretation(self, score: float) -> str:
        """Get human-readable interpretation of score"""
        if score >= 80:
            return "Excellent investment opportunity"
        elif score >= 70:
            return "Strong investment potential"
        elif score >= 60:
            return "Good investment candidate"
        elif score >= 50:
            return "Moderate investment potential"
        elif score >= 40:
            return "Below average opportunity"
        else:
            return "Poor investment candidate"