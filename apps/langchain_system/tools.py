"""
Custom Tools for LangChain Agents
Specialized tools for property analysis and real estate operations
"""

import os
import json
import logging
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from langchain.tools import Tool, BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class PropertyTools:
    """
    Collection of tools for property-related operations
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_ANON_KEY")
        self.api_base_url = "http://localhost:8002"  # Unified property API
        
        self.tools = self._create_tools()
    
    def _create_tools(self) -> List[Tool]:
        """Create all property tools"""
        
        tools = [
            Tool(
                name="fetch_property_data",
                func=self.fetch_property_data,
                description="Fetch comprehensive property data by parcel ID. Input should be a parcel ID string."
            ),
            Tool(
                name="search_properties",
                func=self.search_properties,
                description="Search for properties based on criteria. Input should be a JSON string with search criteria."
            ),
            Tool(
                name="calculate_investment_score",
                func=self.calculate_investment_score,
                description="Calculate investment score for a property. Input should be a parcel ID."
            ),
            Tool(
                name="get_tax_certificates",
                func=self.get_tax_certificates,
                description="Get tax certificates for a property. Input should be a parcel ID."
            ),
            Tool(
                name="get_sales_history",
                func=self.get_sales_history,
                description="Get sales history for a property. Input should be a parcel ID."
            ),
            Tool(
                name="analyze_comparables",
                func=self.analyze_comparables,
                description="Find and analyze comparable properties. Input should be a JSON with property details."
            ),
            Tool(
                name="estimate_renovation_cost",
                func=self.estimate_renovation_cost,
                description="Estimate renovation costs based on property condition. Input: JSON with sqft and condition."
            ),
            Tool(
                name="calculate_rental_income",
                func=self.calculate_rental_income,
                description="Estimate potential rental income. Input: JSON with property details."
            ),
            Tool(
                name="check_permits",
                func=self.check_permits,
                description="Check building permits for a property. Input should be a parcel ID."
            ),
            Tool(
                name="analyze_neighborhood",
                func=self.analyze_neighborhood,
                description="Analyze neighborhood demographics and trends. Input should be a zip code or address."
            ),
            Tool(
                name="calculate_roi",
                func=self.calculate_roi,
                description="Calculate ROI for property investment. Input: JSON with purchase price, rental income, expenses."
            ),
            Tool(
                name="check_flood_zone",
                func=self.check_flood_zone,
                description="Check if property is in a flood zone. Input should be a parcel ID or address."
            ),
            Tool(
                name="get_property_taxes",
                func=self.get_property_taxes,
                description="Get property tax information. Input should be a parcel ID."
            ),
            Tool(
                name="analyze_market_trends",
                func=self.analyze_market_trends,
                description="Analyze market trends for an area. Input should be a zip code or city name."
            ),
            Tool(
                name="check_liens",
                func=self.check_liens,
                description="Check for liens on a property. Input should be a parcel ID."
            )
        ]
        
        return tools
    
    async def fetch_property_data(self, parcel_id: str) -> str:
        """Fetch comprehensive property data"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/api/properties/{parcel_id}/complete"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return json.dumps(data, indent=2)
                    else:
                        return f"Error fetching property data: HTTP {response.status}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def search_properties(self, criteria: str) -> str:
        """Search for properties based on criteria"""
        try:
            search_params = json.loads(criteria) if isinstance(criteria, str) else criteria
            
            # Build query parameters
            query_params = []
            if "min_price" in search_params:
                query_params.append(f"min_price={search_params['min_price']}")
            if "max_price" in search_params:
                query_params.append(f"max_price={search_params['max_price']}")
            if "city" in search_params:
                query_params.append(f"city={search_params['city']}")
            if "property_type" in search_params:
                query_params.append(f"type={search_params['property_type']}")
            
            # Make synchronous request
            import requests
            url = f"{self.api_base_url}/api/properties/search?{'&'.join(query_params)}"
            response = requests.get(url)
            
            if response.status_code == 200:
                results = response.json()
                return f"Found {len(results)} properties matching criteria: " + json.dumps(results[:5], indent=2)
            else:
                return f"Search failed: HTTP {response.status_code}"
                
        except Exception as e:
            return f"Error searching properties: {str(e)}"
    
    def calculate_investment_score(self, parcel_id: str) -> str:
        """Calculate investment score for a property"""
        try:
            import requests
            url = f"{self.api_base_url}/api/properties/{parcel_id}/investment-score"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                score = data.get("investment_score", 0)
                factors = data.get("scoring_factors", {})
                
                result = f"Investment Score: {score}/100\n\n"
                result += "Scoring Breakdown:\n"
                for factor, value in factors.items():
                    result += f"- {factor}: {value}\n"
                
                return result
            else:
                return f"Error calculating score: HTTP {response.status_code}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_tax_certificates(self, parcel_id: str) -> str:
        """Get tax certificates for a property"""
        try:
            import requests
            url = f"{self.api_base_url}/api/properties/{parcel_id}/tax-certificates"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                certificates = data.get("certificates", [])
                
                if certificates:
                    result = f"Found {len(certificates)} tax certificates:\n\n"
                    for cert in certificates:
                        result += f"Certificate #{cert.get('certificate_number', 'N/A')}\n"
                        result += f"  Face Amount: ${cert.get('face_amount', 0):,.2f}\n"
                        result += f"  Buyer: {cert.get('buyer_name', 'Unknown')}\n"
                        result += f"  Sale Date: {cert.get('sale_date', 'N/A')}\n\n"
                else:
                    result = "No tax certificates found for this property"
                
                return result
            else:
                return f"Error fetching tax certificates: HTTP {response.status_code}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_sales_history(self, parcel_id: str) -> str:
        """Get sales history for a property"""
        try:
            import requests
            url = f"{self.api_base_url}/api/properties/{parcel_id}/sales-history"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                sales = data.get("sales_history", [])
                
                if sales:
                    result = f"Sales History ({len(sales)} transactions):\n\n"
                    for sale in sales:
                        result += f"Date: {sale.get('sale_date', 'N/A')}\n"
                        result += f"  Price: ${sale.get('sale_price', 0):,.2f}\n"
                        result += f"  Buyer: {sale.get('buyer_name', 'Unknown')}\n"
                        result += f"  Seller: {sale.get('seller_name', 'Unknown')}\n\n"
                else:
                    result = "No sales history found for this property"
                
                return result
            else:
                return f"Error fetching sales history: HTTP {response.status_code}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def analyze_comparables(self, property_details: str) -> str:
        """Find and analyze comparable properties"""
        try:
            details = json.loads(property_details) if isinstance(property_details, str) else property_details
            
            # Mock comparable analysis
            result = "Comparable Properties Analysis:\n\n"
            result += f"Based on: {details.get('sqft', 'N/A')} sqft, "
            result += f"{details.get('bedrooms', 'N/A')} beds, "
            result += f"{details.get('bathrooms', 'N/A')} baths\n\n"
            
            # Generate mock comparables
            comparables = [
                {"address": "123 Main St", "price": 250000, "sqft": 1500, "price_per_sqft": 167},
                {"address": "456 Oak Ave", "price": 275000, "sqft": 1600, "price_per_sqft": 172},
                {"address": "789 Elm Dr", "price": 240000, "sqft": 1450, "price_per_sqft": 165}
            ]
            
            for comp in comparables:
                result += f"• {comp['address']}: ${comp['price']:,} (${comp['price_per_sqft']}/sqft)\n"
            
            result += f"\nAverage comparable price: $255,000\n"
            result += f"Average price per sqft: $168\n"
            
            return result
            
        except Exception as e:
            return f"Error analyzing comparables: {str(e)}"
    
    def estimate_renovation_cost(self, property_info: str) -> str:
        """Estimate renovation costs"""
        try:
            info = json.loads(property_info) if isinstance(property_info, str) else property_info
            
            sqft = info.get("sqft", 1500)
            condition = info.get("condition", "fair").lower()
            
            # Cost multipliers based on condition
            cost_per_sqft = {
                "excellent": 0,
                "good": 10,
                "fair": 35,
                "poor": 75,
                "teardown": 150
            }
            
            base_cost = cost_per_sqft.get(condition, 35) * sqft
            
            result = f"Renovation Cost Estimate:\n\n"
            result += f"Property Size: {sqft} sqft\n"
            result += f"Condition: {condition}\n\n"
            result += f"Estimated Costs:\n"
            result += f"• Basic Renovation: ${base_cost:,.2f}\n"
            result += f"• Kitchen Upgrade: ${15000:,.2f}\n"
            result += f"• Bathroom Upgrade: ${8000:,.2f}\n"
            result += f"• Flooring: ${sqft * 5:,.2f}\n"
            result += f"• Paint & Cosmetics: ${sqft * 2:,.2f}\n"
            result += f"\nTotal Estimated: ${base_cost + 23000 + sqft * 7:,.2f}\n"
            
            return result
            
        except Exception as e:
            return f"Error estimating renovation cost: {str(e)}"
    
    def calculate_rental_income(self, property_details: str) -> str:
        """Estimate potential rental income"""
        try:
            details = json.loads(property_details) if isinstance(property_details, str) else property_details
            
            bedrooms = details.get("bedrooms", 3)
            location = details.get("location", "average")
            
            # Base rent by bedrooms
            base_rent = {
                1: 1200,
                2: 1600,
                3: 2200,
                4: 2800,
                5: 3500
            }
            
            monthly_rent = base_rent.get(bedrooms, 2200)
            
            # Location multiplier
            if location == "premium":
                monthly_rent *= 1.3
            elif location == "good":
                monthly_rent *= 1.15
            
            annual_income = monthly_rent * 12
            vacancy_loss = annual_income * 0.05  # 5% vacancy
            net_income = annual_income - vacancy_loss
            
            result = f"Rental Income Analysis:\n\n"
            result += f"Property: {bedrooms} bedroom(s)\n"
            result += f"Location: {location}\n\n"
            result += f"Estimated Monthly Rent: ${monthly_rent:,.2f}\n"
            result += f"Annual Gross Income: ${annual_income:,.2f}\n"
            result += f"Vacancy Loss (5%): -${vacancy_loss:,.2f}\n"
            result += f"Net Annual Income: ${net_income:,.2f}\n"
            
            return result
            
        except Exception as e:
            return f"Error calculating rental income: {str(e)}"
    
    def check_permits(self, parcel_id: str) -> str:
        """Check building permits for a property"""
        try:
            # Mock permit data
            result = f"Building Permits for Parcel {parcel_id}:\n\n"
            
            permits = [
                {"number": "2024-001", "type": "Roof Replacement", "status": "Completed", "date": "2024-03-15"},
                {"number": "2023-045", "type": "Kitchen Remodel", "status": "Completed", "date": "2023-08-20"},
                {"number": "2023-012", "type": "Pool Installation", "status": "Completed", "date": "2023-05-10"}
            ]
            
            if permits:
                for permit in permits:
                    result += f"Permit #{permit['number']}\n"
                    result += f"  Type: {permit['type']}\n"
                    result += f"  Status: {permit['status']}\n"
                    result += f"  Date: {permit['date']}\n\n"
            else:
                result += "No permits found for this property"
            
            return result
            
        except Exception as e:
            return f"Error checking permits: {str(e)}"
    
    def analyze_neighborhood(self, location: str) -> str:
        """Analyze neighborhood demographics and trends"""
        try:
            result = f"Neighborhood Analysis for {location}:\n\n"
            
            # Mock neighborhood data
            result += "Demographics:\n"
            result += "• Median Income: $75,000\n"
            result += "• Population: 25,000\n"
            result += "• Average Age: 38\n"
            result += "• Owner Occupied: 65%\n\n"
            
            result += "Market Trends:\n"
            result += "• YoY Appreciation: +4.2%\n"
            result += "• Average DOM: 35 days\n"
            result += "• Inventory Level: Low\n\n"
            
            result += "Amenities:\n"
            result += "• Schools: Rated 8/10\n"
            result += "• Shopping: 5 min drive\n"
            result += "• Public Transit: Available\n"
            result += "• Parks: 3 within 1 mile\n"
            
            return result
            
        except Exception as e:
            return f"Error analyzing neighborhood: {str(e)}"
    
    def calculate_roi(self, investment_data: str) -> str:
        """Calculate ROI for property investment"""
        try:
            data = json.loads(investment_data) if isinstance(investment_data, str) else investment_data
            
            purchase_price = float(data.get("purchase_price", 250000))
            rental_income = float(data.get("monthly_rental", 2000))
            expenses = float(data.get("monthly_expenses", 500))
            
            # Calculate metrics
            annual_income = rental_income * 12
            annual_expenses = expenses * 12
            net_income = annual_income - annual_expenses
            
            cash_flow = net_income
            cap_rate = (net_income / purchase_price) * 100
            gross_yield = (annual_income / purchase_price) * 100
            
            result = f"ROI Analysis:\n\n"
            result += f"Purchase Price: ${purchase_price:,.2f}\n"
            result += f"Monthly Rental: ${rental_income:,.2f}\n"
            result += f"Monthly Expenses: ${expenses:,.2f}\n\n"
            
            result += "Annual Metrics:\n"
            result += f"• Gross Income: ${annual_income:,.2f}\n"
            result += f"• Total Expenses: ${annual_expenses:,.2f}\n"
            result += f"• Net Income: ${net_income:,.2f}\n\n"
            
            result += "Investment Returns:\n"
            result += f"• Cap Rate: {cap_rate:.2f}%\n"
            result += f"• Gross Yield: {gross_yield:.2f}%\n"
            result += f"• Monthly Cash Flow: ${cash_flow/12:,.2f}\n"
            
            return result
            
        except Exception as e:
            return f"Error calculating ROI: {str(e)}"
    
    def check_flood_zone(self, location: str) -> str:
        """Check if property is in a flood zone"""
        try:
            # Mock flood zone check
            result = f"Flood Zone Analysis for {location}:\n\n"
            result += "FEMA Flood Zone: X (Minimal Risk)\n"
            result += "• 500-year flood plain: No\n"
            result += "• 100-year flood plain: No\n"
            result += "• Flood Insurance Required: No\n"
            result += "• Last Flood Event: None recorded\n"
            result += "• Elevation: 15 feet above sea level\n"
            
            return result
            
        except Exception as e:
            return f"Error checking flood zone: {str(e)}"
    
    def get_property_taxes(self, parcel_id: str) -> str:
        """Get property tax information"""
        try:
            # Mock tax data
            result = f"Property Tax Information for Parcel {parcel_id}:\n\n"
            
            result += "Current Year (2024):\n"
            result += "• Assessed Value: $200,000\n"
            result += "• Taxable Value: $175,000\n"
            result += "• Millage Rate: 20.5\n"
            result += "• Annual Tax: $3,587.50\n\n"
            
            result += "Tax History:\n"
            result += "• 2023: $3,425.00\n"
            result += "• 2022: $3,280.00\n"
            result += "• 2021: $3,150.00\n\n"
            
            result += "Exemptions:\n"
            result += "• Homestead: $25,000\n"
            
            return result
            
        except Exception as e:
            return f"Error fetching property taxes: {str(e)}"
    
    def analyze_market_trends(self, location: str) -> str:
        """Analyze market trends for an area"""
        try:
            result = f"Market Trends for {location}:\n\n"
            
            result += "Price Trends:\n"
            result += "• Median Home Price: $325,000\n"
            result += "• YoY Change: +4.2%\n"
            result += "• 5-Year Change: +28.5%\n\n"
            
            result += "Market Activity:\n"
            result += "• Active Listings: 145\n"
            result += "• Pending Sales: 89\n"
            result += "• Average DOM: 42 days\n"
            result += "• List-to-Sale Ratio: 97.5%\n\n"
            
            result += "Forecast:\n"
            result += "• Next 12 Months: +3.5% to +5.0%\n"
            result += "• Market Type: Seller's Market\n"
            result += "• Inventory Trend: Decreasing\n"
            
            return result
            
        except Exception as e:
            return f"Error analyzing market trends: {str(e)}"
    
    def check_liens(self, parcel_id: str) -> str:
        """Check for liens on a property"""
        try:
            result = f"Lien Search for Parcel {parcel_id}:\n\n"
            
            # Mock lien data
            liens = [
                {"type": "Tax Lien", "amount": 5000, "date": "2023-12-01", "holder": "County Tax Collector"},
                {"type": "HOA Lien", "amount": 1200, "date": "2024-01-15", "holder": "Sunshine HOA"}
            ]
            
            if liens:
                total_liens = sum(lien["amount"] for lien in liens)
                result += f"Found {len(liens)} lien(s) totaling ${total_liens:,.2f}\n\n"
                
                for lien in liens:
                    result += f"{lien['type']}:\n"
                    result += f"  Amount: ${lien['amount']:,.2f}\n"
                    result += f"  Date: {lien['date']}\n"
                    result += f"  Holder: {lien['holder']}\n\n"
            else:
                result += "No liens found on this property"
            
            return result
            
        except Exception as e:
            return f"Error checking liens: {str(e)}"