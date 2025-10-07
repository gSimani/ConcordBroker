"""
SQLAlchemy Database Integration Layer for ConcordBroker
Complete integration with all Supabase tables and data processing
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey, func, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from typing import List, Dict, Any, Optional, Tuple
import os
import json
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection - localhost configuration
# For localhost development with Supabase local or direct PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:54322/postgres')

# Alternative configurations:
# For direct PostgreSQL: postgresql://postgres:password@localhost:5432/concordbroker
# For Supabase local: postgresql://postgres:postgres@localhost:54322/postgres
# For remote Supabase: postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=0, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========================================
# DATA MODELS - Complete Supabase Schema
# ========================================

class FloridaParcel(Base):
    """Main property table with all Florida parcel data"""
    __tablename__ = 'florida_parcels'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, index=True, nullable=False)
    county = Column(String, index=True)
    year = Column(Integer, default=2025)

    # Address fields
    phy_addr1 = Column(String)
    phy_addr2 = Column(String)
    phy_city = Column(String)
    phy_state = Column(String)
    phy_zipcd = Column(String)

    # Owner information
    owner_name = Column(String, index=True)
    owner_addr1 = Column(String)
    owner_addr2 = Column(String)
    owner_city = Column(String)
    owner_state = Column(String)
    owner_zip = Column(String)

    # Property values
    just_value = Column(Float)
    assessed_value = Column(Float)
    taxable_value = Column(Float)
    land_value = Column(Float)
    building_value = Column(Float)
    market_value = Column(Float)

    # Property characteristics
    year_built = Column(Integer)
    eff_year_built = Column(Integer)
    total_living_area = Column(Float)
    heated_area = Column(Float)
    land_sqft = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    stories = Column(Integer)
    units = Column(Integer)

    # Property classification
    property_use = Column(String)
    property_use_desc = Column(String)
    property_type = Column(String)
    dor_uc = Column(String)

    # Legal description
    legal_desc = Column(Text)
    subdivision = Column(String)
    lot = Column(String)
    block = Column(String)
    zoning = Column(String)

    # Tax information
    tax_amount = Column(Float)
    millage_rate = Column(Float)
    homestead_exemption = Column(Boolean)
    other_exemptions = Column(String)

    # Sale information
    sale_price = Column(Float)
    sale_date = Column(DateTime)
    sale_type = Column(String)
    deed_type = Column(String)
    qual_cd1 = Column(String)
    vi_code = Column(String)

    # Additional fields
    school_district = Column(String)
    neighborhood = Column(String)
    census_tract = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)

    # Relationships
    sales_history = relationship("PropertySalesHistory", back_populates="property")
    tax_deeds = relationship("TaxDeedSale", back_populates="property")
    assessments = relationship("NavAssessment", back_populates="property")
    foreclosures = relationship("Foreclosure", back_populates="property")
    liens = relationship("TaxLien", back_populates="property")
    permits = relationship("Permit", back_populates="property")


class PropertySalesHistory(Base):
    """Historical sales data for properties"""
    __tablename__ = 'property_sales_history'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, ForeignKey('florida_parcels.parcel_id'), index=True)
    sale_date = Column(DateTime, index=True)
    sale_price = Column(Float)
    sale_type = Column(String)
    document_type = Column(String)
    qualified_sale = Column(Boolean)
    grantor_name = Column(String)
    grantee_name = Column(String)
    book = Column(String)
    page = Column(String)
    cin = Column(String)
    vi_code = Column(String)
    is_distressed = Column(Boolean)
    is_bank_sale = Column(Boolean)
    is_cash_sale = Column(Boolean)
    record_link = Column(String)

    # Relationship
    property = relationship("FloridaParcel", back_populates="sales_history")


class TaxDeedSale(Base):
    """Tax deed sales data"""
    __tablename__ = 'tax_deed_sales'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, ForeignKey('florida_parcels.parcel_id'), index=True)
    certificate_number = Column(String, unique=True)
    auction_date = Column(DateTime, index=True)
    auction_status = Column(String)  # upcoming, active, sold, canceled
    opening_bid = Column(Float)
    winning_bid = Column(Float)
    bidder_number = Column(String)
    certificate_year = Column(Integer)
    tax_amount = Column(Float)
    interest_rate = Column(Float)
    redemption_amount = Column(Float)
    redemption_deadline = Column(DateTime)
    property_address = Column(String)
    assessed_value = Column(Float)

    # Relationship
    property = relationship("FloridaParcel", back_populates="tax_deeds")


class NavAssessment(Base):
    """Non-ad valorem assessments"""
    __tablename__ = 'nav_assessments'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, ForeignKey('florida_parcels.parcel_id'), index=True)
    assessment_year = Column(Integer)
    assessment_type = Column(String)
    assessment_name = Column(String)
    amount = Column(Float)
    district_name = Column(String)
    is_cdd = Column(Boolean)
    is_hoa = Column(Boolean)

    # Relationship
    property = relationship("FloridaParcel", back_populates="assessments")


class SunbizCorporate(Base):
    """Sunbiz corporate data"""
    __tablename__ = 'sunbiz_corporate'

    id = Column(Integer, primary_key=True)
    document_number = Column(String, unique=True, index=True)
    corporate_name = Column(String, index=True)
    status = Column(String)
    filing_type = Column(String)
    principal_address = Column(String)
    mailing_address = Column(String)
    registered_agent_name = Column(String)
    registered_agent_address = Column(String)
    date_filed = Column(DateTime)
    state_formed = Column(String)
    last_event = Column(String)
    last_event_date = Column(DateTime)
    officers = Column(JSON)  # List of officer dicts
    annual_reports = Column(JSON)  # List of annual report dicts
    documents = Column(JSON)  # List of document dicts
    ein_number = Column(String)

    # Computed fields for analysis
    years_active = Column(Integer)
    is_active = Column(Boolean)
    officer_count = Column(Integer)
    property_count = Column(Integer)  # Count of properties owned


class Foreclosure(Base):
    """Foreclosure data"""
    __tablename__ = 'foreclosures'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, ForeignKey('florida_parcels.parcel_id'), index=True)
    case_number = Column(String, unique=True)
    filing_date = Column(DateTime)
    auction_date = Column(DateTime)
    status = Column(String)  # pre_foreclosure, active, sold, canceled
    plaintiff = Column(String)
    defendant = Column(String)
    loan_amount = Column(Float)
    judgment_amount = Column(Float)
    property_address = Column(String)

    # Relationship
    property = relationship("FloridaParcel", back_populates="foreclosures")


class TaxLien(Base):
    """Tax lien data"""
    __tablename__ = 'tax_liens'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, ForeignKey('florida_parcels.parcel_id'), index=True)
    lien_number = Column(String, unique=True)
    lien_date = Column(DateTime)
    amount = Column(Float)
    interest_rate = Column(Float)
    redemption_date = Column(DateTime)
    status = Column(String)  # active, redeemed, foreclosed
    certificate_holder = Column(String)

    # Relationship
    property = relationship("FloridaParcel", back_populates="liens")


class Permit(Base):
    """Building permits data"""
    __tablename__ = 'permits'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, ForeignKey('florida_parcels.parcel_id'), index=True)
    permit_number = Column(String, unique=True)
    permit_type = Column(String)
    description = Column(Text)
    issue_date = Column(DateTime)
    finalize_date = Column(DateTime)
    status = Column(String)
    contractor_name = Column(String)
    estimated_value = Column(Float)

    # Relationship
    property = relationship("FloridaParcel", back_populates="permits")


# ========================================
# DATA ACCESS LAYER - Query Functions
# ========================================

class PropertyDataAccess:
    """Complete data access layer for all property-related queries"""

    def __init__(self, session: Session):
        self.session = session

    def get_property_by_parcel_id(self, parcel_id: str) -> Optional[FloridaParcel]:
        """Get property by parcel ID"""
        return self.session.query(FloridaParcel).filter(
            FloridaParcel.parcel_id == parcel_id
        ).first()

    def get_properties_by_address(self, address: str, city: Optional[str] = None) -> List[FloridaParcel]:
        """Search properties by address"""
        query = self.session.query(FloridaParcel)

        # Clean address for search
        search_address = address.replace('-', ' ').upper()
        query = query.filter(FloridaParcel.phy_addr1.ilike(f'%{search_address}%'))

        if city:
            query = query.filter(FloridaParcel.phy_city.ilike(f'%{city}%'))

        return query.limit(10).all()

    def get_properties_by_owner(self, owner_name: str) -> List[FloridaParcel]:
        """Get all properties owned by a person/entity"""
        return self.session.query(FloridaParcel).filter(
            FloridaParcel.owner_name.ilike(f'%{owner_name}%')
        ).all()

    def get_sales_history(self, parcel_id: str, limit: int = 10) -> List[PropertySalesHistory]:
        """Get sales history for a property"""
        return self.session.query(PropertySalesHistory).filter(
            PropertySalesHistory.parcel_id == parcel_id
        ).order_by(PropertySalesHistory.sale_date.desc()).limit(limit).all()

    def get_upcoming_tax_deeds(self, county: Optional[str] = None, days_ahead: int = 30) -> List[TaxDeedSale]:
        """Get upcoming tax deed sales"""
        query = self.session.query(TaxDeedSale).filter(
            TaxDeedSale.auction_status == 'upcoming',
            TaxDeedSale.auction_date >= datetime.now(),
            TaxDeedSale.auction_date <= datetime.now() + timedelta(days=days_ahead)
        )

        if county:
            query = query.join(FloridaParcel).filter(FloridaParcel.county == county.upper())

        return query.order_by(TaxDeedSale.auction_date).all()

    def get_distressed_properties(self, county: Optional[str] = None) -> List[Dict]:
        """Get distressed properties (foreclosures, tax deeds, liens)"""
        results = []

        # Get properties with active foreclosures
        foreclosure_query = self.session.query(FloridaParcel).join(Foreclosure).filter(
            Foreclosure.status.in_(['pre_foreclosure', 'active'])
        )

        if county:
            foreclosure_query = foreclosure_query.filter(FloridaParcel.county == county.upper())

        for prop in foreclosure_query.all():
            results.append({
                'type': 'foreclosure',
                'property': prop,
                'details': prop.foreclosures[0] if prop.foreclosures else None
            })

        # Get properties with tax liens
        lien_query = self.session.query(FloridaParcel).join(TaxLien).filter(
            TaxLien.status == 'active'
        )

        if county:
            lien_query = lien_query.filter(FloridaParcel.county == county.upper())

        for prop in lien_query.all():
            results.append({
                'type': 'tax_lien',
                'property': prop,
                'details': prop.liens[0] if prop.liens else None
            })

        return results

    def get_investment_opportunities(self, max_price: float = 500000, min_roi: float = 0.15) -> List[Dict]:
        """Find investment opportunities based on criteria"""
        opportunities = []

        # Find undervalued properties (sale price < assessed value)
        undervalued = self.session.query(FloridaParcel).filter(
            FloridaParcel.sale_price < FloridaParcel.assessed_value * 0.8,
            FloridaParcel.sale_price < max_price,
            FloridaParcel.sale_date >= datetime.now() - timedelta(days=365)
        ).all()

        for prop in undervalued:
            if prop.sale_price and prop.assessed_value:
                discount_pct = (prop.assessed_value - prop.sale_price) / prop.assessed_value
                if discount_pct >= min_roi:
                    opportunities.append({
                        'type': 'undervalued',
                        'property': prop,
                        'discount_percentage': discount_pct * 100,
                        'potential_profit': prop.assessed_value - prop.sale_price
                    })

        return opportunities

    def get_market_statistics(self, county: str, property_type: Optional[str] = None) -> Dict:
        """Get market statistics for a county"""
        query = self.session.query(FloridaParcel).filter(
            FloridaParcel.county == county.upper()
        )

        if property_type:
            query = query.filter(FloridaParcel.property_type == property_type)

        properties = query.all()

        if not properties:
            return {}

        # Calculate statistics
        prices = [p.sale_price for p in properties if p.sale_price]
        values = [p.assessed_value for p in properties if p.assessed_value]
        sqft_prices = [p.sale_price / p.total_living_area for p in properties
                      if p.sale_price and p.total_living_area and p.total_living_area > 0]

        return {
            'total_properties': len(properties),
            'avg_sale_price': np.mean(prices) if prices else 0,
            'median_sale_price': np.median(prices) if prices else 0,
            'avg_assessed_value': np.mean(values) if values else 0,
            'median_assessed_value': np.median(values) if values else 0,
            'avg_price_per_sqft': np.mean(sqft_prices) if sqft_prices else 0,
            'median_price_per_sqft': np.median(sqft_prices) if sqft_prices else 0,
            'price_range': {
                'min': min(prices) if prices else 0,
                'max': max(prices) if prices else 0
            }
        }

    def get_sunbiz_entities_by_owner(self, owner_name: str) -> List[SunbizCorporate]:
        """Get Sunbiz entities associated with an owner"""
        # Search in corporate name
        name_matches = self.session.query(SunbizCorporate).filter(
            SunbizCorporate.corporate_name.ilike(f'%{owner_name}%')
        ).all()

        # Search in officers
        officer_matches = self.session.query(SunbizCorporate).filter(
            func.cast(SunbizCorporate.officers, String).ilike(f'%{owner_name}%')
        ).all()

        # Combine and deduplicate
        all_matches = list(set(name_matches + officer_matches))
        return all_matches

    def calculate_property_metrics(self, property: FloridaParcel) -> Dict:
        """Calculate comprehensive metrics for a property"""
        metrics = {}

        # Value metrics
        if property.sale_price and property.assessed_value:
            metrics['price_to_assessed_ratio'] = property.sale_price / property.assessed_value

        if property.sale_price and property.total_living_area and property.total_living_area > 0:
            metrics['price_per_sqft'] = property.sale_price / property.total_living_area

        if property.land_value and property.building_value:
            metrics['land_to_building_ratio'] = property.land_value / (property.building_value + 0.01)

        # Tax metrics
        if property.taxable_value:
            metrics['effective_tax_rate'] = (property.tax_amount or 0) / property.taxable_value
            metrics['homestead_savings'] = property.taxable_value * 0.03 if property.homestead_exemption else 0

        # Age and depreciation
        if property.year_built:
            property_age = datetime.now().year - property.year_built
            metrics['property_age'] = property_age
            metrics['depreciation_factor'] = max(0, 1 - (property_age * 0.01))  # 1% per year

        # Investment metrics
        if property.sale_price:
            # Estimate rental income (2% rule)
            estimated_rent = property.sale_price * 0.008  # 0.8% of purchase price per month
            metrics['estimated_monthly_rent'] = estimated_rent
            metrics['gross_rental_yield'] = (estimated_rent * 12) / property.sale_price

            # Cap rate (assuming 30% expenses)
            net_income = estimated_rent * 12 * 0.7
            metrics['cap_rate'] = net_income / property.sale_price

        # Sales velocity
        sales_history = self.get_sales_history(property.parcel_id)
        if len(sales_history) >= 2:
            days_between_sales = []
            for i in range(len(sales_history) - 1):
                if sales_history[i].sale_date and sales_history[i+1].sale_date:
                    days = (sales_history[i].sale_date - sales_history[i+1].sale_date).days
                    days_between_sales.append(days)

            if days_between_sales:
                metrics['avg_holding_period_days'] = np.mean(days_between_sales)
                metrics['sales_frequency'] = len(sales_history)

        # Market position
        if property.sale_price:
            # Get comparable properties
            comparables = self.session.query(FloridaParcel).filter(
                FloridaParcel.county == property.county,
                FloridaParcel.property_type == property.property_type,
                FloridaParcel.sale_price.between(property.sale_price * 0.8, property.sale_price * 1.2),
                FloridaParcel.parcel_id != property.parcel_id
            ).limit(20).all()

            if comparables:
                comp_prices = [c.sale_price for c in comparables if c.sale_price]
                if comp_prices:
                    metrics['price_vs_comps'] = property.sale_price / np.mean(comp_prices)
                    metrics['price_percentile'] = np.percentile(comp_prices + [property.sale_price],
                                                               [property.sale_price]).mean()

        return metrics

    def get_portfolio_analysis(self, owner_name: str) -> Dict:
        """Analyze entire portfolio for an owner"""
        properties = self.get_properties_by_owner(owner_name)

        if not properties:
            return {'error': 'No properties found'}

        total_value = sum(p.assessed_value or 0 for p in properties)
        total_tax = sum(p.tax_amount or 0 for p in properties)

        # Group by county
        by_county = {}
        for prop in properties:
            county = prop.county or 'Unknown'
            if county not in by_county:
                by_county[county] = []
            by_county[county].append(prop)

        # Group by type
        by_type = {}
        for prop in properties:
            ptype = prop.property_type or 'Unknown'
            if ptype not in by_type:
                by_type[ptype] = []
            by_type[ptype].append(prop)

        return {
            'total_properties': len(properties),
            'total_assessed_value': total_value,
            'total_annual_tax': total_tax,
            'average_property_value': total_value / len(properties) if properties else 0,
            'by_county': {k: len(v) for k, v in by_county.items()},
            'by_type': {k: len(v) for k, v in by_type.items()},
            'properties': properties
        }


# ========================================
# CALCULATION ENGINE
# ========================================

class PropertyCalculations:
    """Advanced calculations and analytics for properties"""

    @staticmethod
    def calculate_roi(purchase_price: float, current_value: float,
                     rental_income: float = 0, expenses: float = 0,
                     holding_period_years: float = 1) -> Dict:
        """Calculate comprehensive ROI metrics"""

        # Capital appreciation
        appreciation = current_value - purchase_price
        appreciation_rate = appreciation / purchase_price / holding_period_years

        # Cash flow
        net_income = (rental_income - expenses) * holding_period_years

        # Total return
        total_return = appreciation + net_income
        roi = total_return / purchase_price
        annual_roi = roi / holding_period_years

        # Cash-on-cash return (if rental)
        cash_on_cash = 0
        if rental_income > 0:
            annual_cash_flow = (rental_income - expenses)
            cash_on_cash = annual_cash_flow / purchase_price

        return {
            'total_roi': roi * 100,
            'annual_roi': annual_roi * 100,
            'appreciation': appreciation,
            'appreciation_rate': appreciation_rate * 100,
            'net_income': net_income,
            'cash_on_cash_return': cash_on_cash * 100
        }

    @staticmethod
    def calculate_affordability(income: float, down_payment: float,
                              interest_rate: float = 0.065,
                              loan_term_years: int = 30) -> Dict:
        """Calculate home affordability based on income"""

        # Standard debt-to-income ratio
        max_monthly_payment = income * 0.28 / 12  # 28% of gross income

        # Calculate max loan amount
        monthly_rate = interest_rate / 12
        num_payments = loan_term_years * 12

        # Mortgage formula: P = M * [(1+r)^n - 1] / [r * (1+r)^n]
        if monthly_rate > 0:
            max_loan = max_monthly_payment * ((1 + monthly_rate)**num_payments - 1) / \
                      (monthly_rate * (1 + monthly_rate)**num_payments)
        else:
            max_loan = max_monthly_payment * num_payments

        max_purchase_price = max_loan + down_payment

        return {
            'max_purchase_price': max_purchase_price,
            'max_loan_amount': max_loan,
            'down_payment': down_payment,
            'max_monthly_payment': max_monthly_payment,
            'debt_to_income_ratio': 28,
            'interest_rate': interest_rate * 100,
            'loan_term_years': loan_term_years
        }

    @staticmethod
    def calculate_market_trends(properties: List[FloridaParcel],
                              time_period_days: int = 365) -> Dict:
        """Calculate market trends from property data"""

        cutoff_date = datetime.now() - timedelta(days=time_period_days)

        # Filter recent sales
        recent_sales = [p for p in properties if p.sale_date and p.sale_date >= cutoff_date]

        if not recent_sales:
            return {'error': 'No recent sales data'}

        # Group by month
        monthly_data = {}
        for prop in recent_sales:
            if prop.sale_date and prop.sale_price:
                month_key = prop.sale_date.strftime('%Y-%m')
                if month_key not in monthly_data:
                    monthly_data[month_key] = []
                monthly_data[month_key].append(prop.sale_price)

        # Calculate monthly averages
        monthly_avg = {k: np.mean(v) for k, v in monthly_data.items()}

        # Calculate trend
        if len(monthly_avg) >= 2:
            prices = list(monthly_avg.values())
            months = list(range(len(prices)))

            # Linear regression for trend
            z = np.polyfit(months, prices, 1)
            trend_slope = z[0]

            # Percentage change
            price_change = (prices[-1] - prices[0]) / prices[0] * 100 if prices[0] > 0 else 0

            return {
                'monthly_averages': monthly_avg,
                'trend': 'increasing' if trend_slope > 0 else 'decreasing',
                'monthly_change_rate': trend_slope,
                'total_change_percentage': price_change,
                'sample_size': len(recent_sales),
                'time_period_days': time_period_days
            }

        return {'error': 'Insufficient data for trend analysis'}

    @staticmethod
    def score_investment_opportunity(property: FloridaParcel,
                                    market_stats: Dict) -> Dict:
        """Score a property as an investment opportunity"""

        score = 50  # Base score
        factors = []

        # Price vs market
        if property.sale_price and market_stats.get('median_sale_price'):
            price_ratio = property.sale_price / market_stats['median_sale_price']
            if price_ratio < 0.8:
                score += 20
                factors.append('Priced below market median')
            elif price_ratio > 1.2:
                score -= 10
                factors.append('Priced above market median')

        # Value appreciation potential
        if property.assessed_value and property.sale_price:
            if property.assessed_value > property.sale_price * 1.1:
                score += 15
                factors.append('Assessed value higher than sale price')

        # Property age
        if property.year_built:
            age = datetime.now().year - property.year_built
            if age < 10:
                score += 10
                factors.append('Newer construction')
            elif age > 50:
                score -= 10
                factors.append('Older property - potential maintenance issues')

        # Size and features
        if property.total_living_area:
            if property.total_living_area > 2000:
                score += 5
                factors.append('Large living area')

        if property.bedrooms and property.bedrooms >= 3:
            score += 5
            factors.append('3+ bedrooms')

        # Location factors
        if property.homestead_exemption:
            score += 5
            factors.append('Homestead area - stable neighborhood')

        # Ensure score is within bounds
        score = max(0, min(100, score))

        return {
            'investment_score': score,
            'rating': 'Excellent' if score >= 80 else 'Good' if score >= 60 else 'Fair' if score >= 40 else 'Poor',
            'factors': factors
        }


# ========================================
# GRAPH DATA GENERATOR
# ========================================

class PropertyGraphGenerator:
    """Generate data for graphs and visualizations"""

    def __init__(self, session: Session):
        self.session = session
        self.data_access = PropertyDataAccess(session)

    def generate_price_history_chart(self, parcel_id: str) -> Dict:
        """Generate price history chart data"""
        sales = self.data_access.get_sales_history(parcel_id)

        if not sales:
            return {'error': 'No sales history available'}

        chart_data = {
            'labels': [],
            'datasets': [{
                'label': 'Sale Price',
                'data': [],
                'borderColor': 'rgb(75, 192, 192)',
                'tension': 0.1
            }]
        }

        for sale in reversed(sales):  # Oldest to newest
            if sale.sale_date and sale.sale_price:
                chart_data['labels'].append(sale.sale_date.strftime('%Y-%m'))
                chart_data['datasets'][0]['data'].append(sale.sale_price)

        return chart_data

    def generate_market_comparison_chart(self, property: FloridaParcel) -> Dict:
        """Generate market comparison chart"""

        # Get comparable properties
        comparables = self.session.query(FloridaParcel).filter(
            FloridaParcel.county == property.county,
            FloridaParcel.property_type == property.property_type,
            FloridaParcel.total_living_area.between(
                property.total_living_area * 0.8 if property.total_living_area else 0,
                property.total_living_area * 1.2 if property.total_living_area else 999999
            ),
            FloridaParcel.parcel_id != property.parcel_id
        ).limit(10).all()

        chart_data = {
            'labels': ['Subject Property'] + [f'Comp {i+1}' for i in range(len(comparables))],
            'datasets': [
                {
                    'label': 'Sale Price',
                    'data': [property.sale_price] + [c.sale_price for c in comparables],
                    'backgroundColor': ['rgba(255, 99, 132, 0.2)'] + ['rgba(54, 162, 235, 0.2)'] * len(comparables)
                },
                {
                    'label': 'Assessed Value',
                    'data': [property.assessed_value] + [c.assessed_value for c in comparables],
                    'backgroundColor': ['rgba(255, 159, 64, 0.2)'] + ['rgba(75, 192, 192, 0.2)'] * len(comparables)
                }
            ]
        }

        return chart_data

    def generate_portfolio_distribution_chart(self, owner_name: str) -> Dict:
        """Generate portfolio distribution charts"""
        analysis = self.data_access.get_portfolio_analysis(owner_name)

        # By county pie chart
        county_chart = {
            'labels': list(analysis['by_county'].keys()),
            'datasets': [{
                'data': list(analysis['by_county'].values()),
                'backgroundColor': [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                ]
            }]
        }

        # By type pie chart
        type_chart = {
            'labels': list(analysis['by_type'].keys()),
            'datasets': [{
                'data': list(analysis['by_type'].values()),
                'backgroundColor': [
                    'rgba(255, 159, 64, 0.2)',
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                ]
            }]
        }

        return {
            'county_distribution': county_chart,
            'type_distribution': type_chart,
            'summary': {
                'total_properties': analysis['total_properties'],
                'total_value': analysis['total_assessed_value'],
                'average_value': analysis['average_property_value']
            }
        }

    def generate_tax_deed_timeline(self, county: Optional[str] = None) -> Dict:
        """Generate timeline of upcoming tax deed sales"""
        upcoming_sales = self.data_access.get_upcoming_tax_deeds(county, days_ahead=60)

        timeline_data = {
            'events': []
        }

        for sale in upcoming_sales:
            if sale.auction_date:
                timeline_data['events'].append({
                    'date': sale.auction_date.isoformat(),
                    'title': f'Tax Deed Sale - {sale.certificate_number}',
                    'description': f'Opening Bid: ${sale.opening_bid:,.2f}',
                    'parcel_id': sale.parcel_id,
                    'type': 'tax_deed'
                })

        return timeline_data

    def generate_roi_calculator_chart(self, purchase_price: float,
                                     rental_income: float,
                                     expenses: float) -> Dict:
        """Generate ROI projection charts"""

        years = list(range(1, 11))  # 10 year projection
        roi_data = []
        cumulative_return = []

        for year in years:
            # Assume 3% annual appreciation
            current_value = purchase_price * (1.03 ** year)

            roi = PropertyCalculations.calculate_roi(
                purchase_price, current_value,
                rental_income * 12, expenses * 12, year
            )

            roi_data.append(roi['annual_roi'])
            cumulative_return.append(roi['total_roi'])

        return {
            'labels': [f'Year {y}' for y in years],
            'datasets': [
                {
                    'label': 'Annual ROI %',
                    'data': roi_data,
                    'borderColor': 'rgb(75, 192, 192)',
                    'fill': False
                },
                {
                    'label': 'Cumulative Return %',
                    'data': cumulative_return,
                    'borderColor': 'rgb(255, 99, 132)',
                    'fill': False
                }
            ]
        }


# ========================================
# API INTEGRATION FUNCTIONS
# ========================================

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def fetch_property_complete_data(parcel_id: str) -> Dict:
    """Fetch complete property data with all relationships"""
    with SessionLocal() as session:
        data_access = PropertyDataAccess(session)

        # Get main property
        property = data_access.get_property_by_parcel_id(parcel_id)
        if not property:
            return {'error': 'Property not found'}

        # Get all related data
        sales_history = data_access.get_sales_history(parcel_id)
        metrics = data_access.calculate_property_metrics(property)

        # Get Sunbiz data if owner exists
        sunbiz_data = []
        if property.owner_name:
            sunbiz_data = data_access.get_sunbiz_entities_by_owner(property.owner_name)

        # Generate graph data
        graph_gen = PropertyGraphGenerator(session)
        price_chart = graph_gen.generate_price_history_chart(parcel_id)
        comparison_chart = graph_gen.generate_market_comparison_chart(property)

        return {
            'property': property.__dict__,
            'sales_history': [sale.__dict__ for sale in sales_history],
            'metrics': metrics,
            'sunbiz_entities': [entity.__dict__ for entity in sunbiz_data],
            'charts': {
                'price_history': price_chart,
                'market_comparison': comparison_chart
            }
        }


def search_properties(query: str, filters: Dict = None) -> List[Dict]:
    """Search properties with filters"""
    with SessionLocal() as session:
        base_query = session.query(FloridaParcel)

        # Apply search query
        if query:
            base_query = base_query.filter(
                or_(
                    FloridaParcel.phy_addr1.ilike(f'%{query}%'),
                    FloridaParcel.owner_name.ilike(f'%{query}%'),
                    FloridaParcel.parcel_id == query
                )
            )

        # Apply filters
        if filters:
            if 'min_price' in filters:
                base_query = base_query.filter(FloridaParcel.sale_price >= filters['min_price'])
            if 'max_price' in filters:
                base_query = base_query.filter(FloridaParcel.sale_price <= filters['max_price'])
            if 'property_type' in filters:
                base_query = base_query.filter(FloridaParcel.property_type == filters['property_type'])
            if 'county' in filters:
                base_query = base_query.filter(FloridaParcel.county == filters['county'].upper())
            if 'min_sqft' in filters:
                base_query = base_query.filter(FloridaParcel.total_living_area >= filters['min_sqft'])
            if 'max_sqft' in filters:
                base_query = base_query.filter(FloridaParcel.total_living_area <= filters['max_sqft'])

        results = base_query.limit(100).all()
        return [prop.__dict__ for prop in results]


def get_dashboard_data(user_id: Optional[str] = None) -> Dict:
    """Get comprehensive dashboard data"""
    with SessionLocal() as session:
        data_access = PropertyDataAccess(session)

        # Get market statistics for major counties
        counties = ['BROWARD', 'MIAMI-DADE', 'PALM BEACH']
        market_stats = {}
        for county in counties:
            market_stats[county] = data_access.get_market_statistics(county)

        # Get upcoming tax deeds
        tax_deeds = data_access.get_upcoming_tax_deeds(days_ahead=7)

        # Get recent distressed properties
        distressed = data_access.get_distressed_properties()[:10]

        # Get top investment opportunities
        opportunities = data_access.get_investment_opportunities(max_price=300000)[:10]

        return {
            'market_statistics': market_stats,
            'upcoming_tax_deeds': [td.__dict__ for td in tax_deeds],
            'distressed_properties': distressed,
            'investment_opportunities': opportunities,
            'timestamp': datetime.now().isoformat()
        }


# Create all tables
Base.metadata.create_all(bind=engine)

logger.info("SQLAlchemy integration layer initialized successfully")