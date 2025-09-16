"""
Property Profile Service
Aggregates data from all sources to create comprehensive property profiles
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

@dataclass
class PropertyProfile:
    """Complete property profile data structure"""
    
    # Core Property Info
    address: str
    city: str
    state: str = "FL"
    zip_code: str = None
    parcel_id: str = None
    folio_number: str = None
    
    # Property Characteristics (from BCPA)
    property_type: str = None
    year_built: int = None
    living_area: int = None
    lot_size: int = None
    bedrooms: int = None
    bathrooms: float = None
    pool: bool = False
    
    # Valuation (from BCPA/DOR)
    market_value: float = None
    assessed_value: float = None
    taxable_value: float = None
    last_sale_price: float = None
    last_sale_date: str = None
    
    # Ownership (from BCPA/Sunbiz)
    owner_name: str = None
    owner_type: str = None  # Individual, LLC, Corporation, Trust
    owner_address: str = None
    business_entity: Dict = None  # Sunbiz data if owner is business
    
    # Sales History (from SDF)
    sales_history: List[Dict] = None
    total_sales: int = 0
    is_distressed: bool = False
    is_bank_owned: bool = False
    qualification_code: str = None
    days_on_market: int = None
    
    # Tax Information (from NAV/TPP)
    property_taxes: float = None
    nav_assessments: List[Dict] = None
    total_nav_assessment: float = 0
    is_in_cdd: bool = False
    special_districts: List[str] = None
    tangible_property_value: float = None
    
    # Market Analysis
    price_per_sqft: float = None
    neighborhood_avg_price: float = None
    price_trend: str = None  # increasing, stable, declining
    comp_properties: List[Dict] = None
    
    # Investment Metrics
    rental_estimate: float = None
    cap_rate: float = None
    roi_potential: float = None
    flip_potential: bool = False
    investment_score: int = None  # 1-100
    
    # Alerts & Opportunities
    alerts: List[Dict] = None
    opportunities: List[str] = None
    risk_factors: List[str] = None
    
    # Metadata
    last_updated: str = None
    data_sources: List[str] = None
    confidence_score: float = None  # Data completeness score

class PropertyProfileService:
    """Service to aggregate property data from all sources"""
    
    def __init__(self):
        self.data_sources = {
            'bcpa': None,  # Property characteristics
            'sdf': None,   # Sales history
            'nav': None,   # Non-ad valorem assessments
            'tpp': None,   # Tangible property
            'sunbiz': None,  # Business ownership
            'official_records': None,  # Deed records
            'dor': None   # Tax assessments
        }
        
    async def initialize(self):
        """Initialize connections to all data sources"""
        # Import all database modules
        try:
            from apps.workers.bcpa.database import BCPADB
            self.data_sources['bcpa'] = BCPADB()
            await self.data_sources['bcpa'].connect()
        except:
            logger.warning("BCPA database not available")
            
        try:
            from apps.workers.sdf_sales.database_supabase import SDFSupabaseDB
            self.data_sources['sdf'] = SDFSupabaseDB()
            await self.data_sources['sdf'].connect()
        except:
            logger.warning("SDF database not available")
            
        try:
            from apps.workers.nav_assessments.database_supabase import NAVSupabaseDB
            self.data_sources['nav'] = NAVSupabaseDB()
            await self.data_sources['nav'].connect()
        except:
            logger.warning("NAV database not available")
            
        try:
            from apps.workers.tpp.database_supabase import TPPSupabaseDB
            self.data_sources['tpp'] = TPPSupabaseDB()
            await self.data_sources['tpp'].connect()
        except:
            logger.warning("TPP database not available")
            
        try:
            from apps.workers.sunbiz_sftp.database import SunbizSFTPDB
            self.data_sources['sunbiz'] = SunbizSFTPDB()
            await self.data_sources['sunbiz'].connect()
        except:
            logger.warning("Sunbiz database not available")
    
    async def get_property_profile(self, address: str, city: str, 
                                  state: str = "FL") -> PropertyProfile:
        """Get complete property profile for an address"""
        
        # Create base profile
        profile = PropertyProfile(
            address=address,
            city=city,
            state=state,
            last_updated=datetime.now().isoformat(),
            data_sources=[],
            alerts=[],
            opportunities=[],
            risk_factors=[]
        )
        
        # Normalize address for searching
        normalized_address = self.normalize_address(address, city)
        
        # Fetch data from all sources in parallel
        tasks = []
        
        if self.data_sources['bcpa']:
            tasks.append(self.fetch_bcpa_data(normalized_address, profile))
            
        if self.data_sources['sdf']:
            tasks.append(self.fetch_sdf_data(normalized_address, profile))
            
        if self.data_sources['nav']:
            tasks.append(self.fetch_nav_data(normalized_address, profile))
            
        if self.data_sources['tpp']:
            tasks.append(self.fetch_tpp_data(normalized_address, profile))
            
        if self.data_sources['sunbiz']:
            tasks.append(self.fetch_sunbiz_data(profile))
        
        # Wait for all data fetches
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate derived metrics
        self.calculate_investment_metrics(profile)
        self.identify_opportunities(profile)
        self.assess_risk_factors(profile)
        self.calculate_confidence_score(profile)
        
        return profile
    
    def normalize_address(self, address: str, city: str) -> str:
        """Normalize address for database searches"""
        # Remove common variations
        address = address.upper()
        address = address.replace("STREET", "ST")
        address = address.replace("AVENUE", "AVE")
        address = address.replace("ROAD", "RD")
        address = address.replace("BOULEVARD", "BLVD")
        address = address.replace("DRIVE", "DR")
        address = address.replace("LANE", "LN")
        address = address.replace("COURT", "CT")
        address = address.replace("PLACE", "PL")
        
        # Combine with city
        return f"{address}, {city.upper()}"
    
    async def fetch_bcpa_data(self, address: str, profile: PropertyProfile):
        """Fetch property characteristics from BCPA"""
        try:
            # Search for property by address
            results = await self.data_sources['bcpa'].search_by_address(address)
            
            if results:
                prop = results[0]  # Take first match
                
                # Update profile with BCPA data
                profile.parcel_id = prop.get('parcel_id')
                profile.folio_number = prop.get('folio_number')
                profile.property_type = prop.get('property_use')
                profile.year_built = prop.get('year_built')
                profile.living_area = prop.get('living_area')
                profile.lot_size = prop.get('lot_size')
                profile.bedrooms = prop.get('bedrooms')
                profile.bathrooms = prop.get('bathrooms')
                profile.pool = prop.get('pool', False)
                
                profile.market_value = prop.get('market_value')
                profile.assessed_value = prop.get('assessed_value')
                profile.taxable_value = prop.get('taxable_value')
                
                profile.owner_name = prop.get('owner_name')
                profile.owner_address = prop.get('owner_address')
                
                profile.data_sources.append('BCPA')
                
        except Exception as e:
            logger.error(f"Error fetching BCPA data: {e}")
    
    async def fetch_sdf_data(self, address: str, profile: PropertyProfile):
        """Fetch sales history from SDF"""
        try:
            if not profile.parcel_id:
                return
                
            # Get sales history
            sales = await self.data_sources['sdf'].get_sales_by_parcel(
                profile.parcel_id
            )
            
            if sales:
                profile.sales_history = []
                
                for sale in sales:
                    sale_record = {
                        'date': sale.get('sale_date'),
                        'price': sale.get('sale_price'),
                        'qualification_code': sale.get('qualification_code'),
                        'qualification': sale.get('qualification_description'),
                        'is_distressed': sale.get('is_distressed_sale'),
                        'is_bank_sale': sale.get('is_bank_sale')
                    }
                    profile.sales_history.append(sale_record)
                    
                    # Check latest sale
                    if len(profile.sales_history) == 1:
                        profile.last_sale_price = sale.get('sale_price')
                        profile.last_sale_date = str(sale.get('sale_date'))
                        profile.qualification_code = sale.get('qualification_code')
                        profile.is_distressed = sale.get('is_distressed_sale', False)
                        profile.is_bank_owned = sale.get('is_bank_sale', False)
                
                profile.total_sales = len(profile.sales_history)
                profile.data_sources.append('SDF')
                
                # Check for flip potential
                if len(sales) >= 2:
                    recent_sales = sales[:2]
                    price_change = recent_sales[0]['sale_price'] - recent_sales[1]['sale_price']
                    if price_change > recent_sales[1]['sale_price'] * 0.3:
                        profile.flip_potential = True
                        
        except Exception as e:
            logger.error(f"Error fetching SDF data: {e}")
    
    async def fetch_nav_data(self, address: str, profile: PropertyProfile):
        """Fetch NAV assessments"""
        try:
            if not profile.parcel_id:
                return
                
            # Get NAV summary
            summary = await self.data_sources['nav'].get_parcel_summary(
                profile.parcel_id
            )
            
            if summary:
                profile.total_nav_assessment = summary.get('total_nav_assessment', 0)
                
                # Get detailed assessments
                details = await self.data_sources['nav'].get_parcel_details(
                    profile.parcel_id
                )
                
                if details:
                    profile.nav_assessments = []
                    profile.special_districts = []
                    
                    for assessment in details:
                        profile.nav_assessments.append({
                            'authority': assessment.get('authority_name'),
                            'type': assessment.get('authority_type'),
                            'amount': assessment.get('nav_assessment')
                        })
                        
                        if assessment.get('is_cdd'):
                            profile.is_in_cdd = True
                            
                        district = assessment.get('district_name')
                        if district and district not in profile.special_districts:
                            profile.special_districts.append(district)
                    
                    profile.data_sources.append('NAV')
                    
        except Exception as e:
            logger.error(f"Error fetching NAV data: {e}")
    
    async def fetch_tpp_data(self, address: str, profile: PropertyProfile):
        """Fetch tangible personal property data"""
        try:
            if not profile.owner_name:
                return
                
            # Search by owner name
            tpp_accounts = await self.data_sources['tpp'].search_by_owner(
                profile.owner_name
            )
            
            if tpp_accounts:
                total_tpp_value = sum(
                    acc.get('taxable_value', 0) for acc in tpp_accounts
                )
                profile.tangible_property_value = total_tpp_value
                profile.data_sources.append('TPP')
                
        except Exception as e:
            logger.error(f"Error fetching TPP data: {e}")
    
    async def fetch_sunbiz_data(self, profile: PropertyProfile):
        """Fetch business entity data if owner is a business"""
        try:
            if not profile.owner_name:
                return
                
            # Check if owner appears to be a business
            business_indicators = ['LLC', 'INC', 'CORP', 'LP', 'TRUST', 'PARTNERSHIP']
            is_business = any(ind in profile.owner_name.upper() for ind in business_indicators)
            
            if is_business:
                # Search for business entity
                entities = await self.data_sources['sunbiz'].search_by_entity_name(
                    profile.owner_name
                )
                
                if entities:
                    entity = entities[0]  # Take best match
                    
                    profile.owner_type = self.classify_owner_type(entity.get('entity_type'))
                    profile.business_entity = {
                        'doc_number': entity.get('doc_number'),
                        'entity_type': entity.get('entity_type'),
                        'status': entity.get('status'),
                        'filing_date': str(entity.get('filing_date')),
                        'registered_agent': entity.get('registered_agent_name'),
                        'principal_city': entity.get('principal_city'),
                        'principal_state': entity.get('principal_state')
                    }
                    
                    profile.data_sources.append('Sunbiz')
                    
                    # Check if entity is active
                    if entity.get('status') != 'ACTIVE':
                        profile.risk_factors.append('Owner entity is inactive')
            else:
                profile.owner_type = 'Individual'
                
        except Exception as e:
            logger.error(f"Error fetching Sunbiz data: {e}")
    
    def classify_owner_type(self, entity_type: str) -> str:
        """Classify owner type from entity type"""
        if not entity_type:
            return 'Unknown'
            
        entity_upper = entity_type.upper()
        
        if 'LLC' in entity_upper or 'L.L.C' in entity_upper:
            return 'LLC'
        elif 'CORP' in entity_upper or 'INC' in entity_upper:
            return 'Corporation'
        elif 'TRUST' in entity_upper:
            return 'Trust'
        elif 'PARTNERSHIP' in entity_upper or ' LP' in entity_upper:
            return 'Partnership'
        else:
            return 'Business Entity'
    
    def calculate_investment_metrics(self, profile: PropertyProfile):
        """Calculate investment metrics"""
        
        # Price per square foot
        if profile.living_area and profile.last_sale_price:
            profile.price_per_sqft = profile.last_sale_price / profile.living_area
        
        # Rental estimate (simple model - needs refinement)
        if profile.market_value:
            # Rough estimate: 0.8-1.2% of market value per month
            profile.rental_estimate = profile.market_value * 0.01
            
            # Cap rate calculation
            annual_rent = profile.rental_estimate * 12
            expenses = annual_rent * 0.4  # Assume 40% expenses
            noi = annual_rent - expenses
            
            if profile.market_value > 0:
                profile.cap_rate = (noi / profile.market_value) * 100
        
        # Investment score (0-100)
        score = 50  # Base score
        
        # Positive factors
        if profile.is_distressed:
            score += 15
        if profile.is_bank_owned:
            score += 10
        if profile.flip_potential:
            score += 10
        if profile.cap_rate and profile.cap_rate > 7:
            score += 10
        if profile.price_per_sqft and profile.price_per_sqft < 200:
            score += 5
            
        # Negative factors
        if profile.is_in_cdd:
            score -= 5
        if profile.total_nav_assessment > 5000:
            score -= 10
        if profile.owner_type == 'Trust':
            score -= 5  # Harder to negotiate
            
        profile.investment_score = min(100, max(0, score))
    
    def identify_opportunities(self, profile: PropertyProfile):
        """Identify investment opportunities"""
        
        if profile.is_distressed:
            profile.opportunities.append("Distressed property - potential below-market purchase")
            
        if profile.is_bank_owned:
            profile.opportunities.append("Bank-owned (REO) - motivated seller")
            
        if profile.flip_potential:
            profile.opportunities.append("Flip opportunity detected - significant price appreciation potential")
            
        if profile.cap_rate and profile.cap_rate > 8:
            profile.opportunities.append(f"High cap rate ({profile.cap_rate:.1f}%) - strong rental potential")
            
        if profile.owner_type in ['LLC', 'Corporation'] and profile.business_entity:
            if profile.business_entity.get('status') != 'ACTIVE':
                profile.opportunities.append("Owner entity inactive - potential motivated seller")
                
        if profile.total_sales >= 3:
            profile.opportunities.append("High transaction frequency - possible wholesale opportunity")
            
        if profile.year_built and profile.year_built < 1980:
            profile.opportunities.append("Older property - renovation/redevelopment potential")
    
    def assess_risk_factors(self, profile: PropertyProfile):
        """Assess risk factors"""
        
        if profile.is_in_cdd:
            profile.risk_factors.append(f"Property in CDD - additional assessments ${profile.total_nav_assessment:.0f}/year")
            
        if profile.total_nav_assessment > 5000:
            profile.risk_factors.append(f"High special assessments - ${profile.total_nav_assessment:.0f}/year")
            
        if profile.qualification_code == '37':
            profile.risk_factors.append("Tax deed sale - potential title issues")
            
        if profile.year_built and profile.year_built < 1970:
            profile.risk_factors.append("Built before 1970 - potential structural/code issues")
            
        if profile.owner_type == 'Trust':
            profile.risk_factors.append("Trust ownership - complex negotiation possible")
            
        if not profile.sales_history or len(profile.sales_history) == 0:
            profile.risk_factors.append("No recent sales history - difficult to value")
    
    def calculate_confidence_score(self, profile: PropertyProfile):
        """Calculate data confidence score based on completeness"""
        
        total_fields = 0
        filled_fields = 0
        
        # Check key fields
        key_fields = [
            'parcel_id', 'property_type', 'year_built', 'living_area',
            'market_value', 'owner_name', 'sales_history', 'nav_assessments'
        ]
        
        for field in key_fields:
            total_fields += 1
            if getattr(profile, field, None):
                filled_fields += 1
        
        # Check data sources
        expected_sources = ['BCPA', 'SDF', 'NAV', 'TPP', 'Sunbiz']
        source_coverage = len(profile.data_sources) / len(expected_sources)
        
        # Calculate confidence
        field_coverage = filled_fields / total_fields if total_fields > 0 else 0
        profile.confidence_score = (field_coverage * 0.7 + source_coverage * 0.3) * 100
    
    def to_dict(self, profile: PropertyProfile) -> Dict:
        """Convert profile to dictionary"""
        return asdict(profile)
    
    def to_json(self, profile: PropertyProfile) -> str:
        """Convert profile to JSON"""
        return json.dumps(self.to_dict(profile), default=str)