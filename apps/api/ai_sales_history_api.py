"""
AI-Enhanced Sales History API with Agent Integration
Provides sales history data with AI-powered analysis and insights
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from supabase import create_client
import uvicorn
import json
import statistics
import httpx

app = FastAPI(title="AI Sales History API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase connection
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class SalesAnalysisAgent:
    """AI Agent for analyzing property sales history"""

    @staticmethod
    def analyze_price_trend(sales_history: List[Dict]) -> Dict:
        """Analyze price trends over time"""
        if not sales_history or len(sales_history) < 2:
            return {
                "trend": "insufficient_data",
                "message": "Need at least 2 sales to analyze trends"
            }

        # Sort by date
        sorted_sales = sorted(sales_history, key=lambda x: x.get('sale_date', ''))

        prices = [s['sale_price'] for s in sorted_sales if s.get('sale_price', 0) > 0]

        if len(prices) < 2:
            return {
                "trend": "insufficient_data",
                "message": "Need at least 2 valid sales prices"
            }

        # Calculate appreciation
        first_sale = sorted_sales[0]
        last_sale = sorted_sales[-1]

        appreciation = ((last_sale['sale_price'] - first_sale['sale_price']) / first_sale['sale_price']) * 100

        # Calculate years between sales
        try:
            first_date = datetime.fromisoformat(first_sale['sale_date'].replace('Z', '+00:00'))
            last_date = datetime.fromisoformat(last_sale['sale_date'].replace('Z', '+00:00'))
            years = (last_date - first_date).days / 365.25
            annual_appreciation = appreciation / years if years > 0 else 0
        except:
            years = 0
            annual_appreciation = 0

        # Determine trend
        if appreciation > 20:
            trend = "strong_growth"
            trend_emoji = "📈"
        elif appreciation > 5:
            trend = "moderate_growth"
            trend_emoji = "📊"
        elif appreciation > -5:
            trend = "stable"
            trend_emoji = "➡️"
        else:
            trend = "declining"
            trend_emoji = "📉"

        return {
            "trend": trend,
            "trend_emoji": trend_emoji,
            "total_appreciation": round(appreciation, 2),
            "annual_appreciation": round(annual_appreciation, 2),
            "years_analyzed": round(years, 1),
            "price_range": {
                "min": min(prices),
                "max": max(prices),
                "average": round(statistics.mean(prices), 2),
                "median": round(statistics.median(prices), 2)
            }
        }

    @staticmethod
    def analyze_market_activity(sales_history: List[Dict]) -> Dict:
        """Analyze market activity patterns"""
        if not sales_history:
            return {"activity_level": "no_data"}

        # Count sales by year
        sales_by_year = {}
        for sale in sales_history:
            try:
                year = sale['sale_date'][:4]
                sales_by_year[year] = sales_by_year.get(year, 0) + 1
            except:
                continue

        # Analyze frequency
        total_sales = len(sales_history)
        if total_sales >= 10:
            activity_level = "very_high"
            activity_emoji = "🔥"
        elif total_sales >= 5:
            activity_level = "high"
            activity_emoji = "🎯"
        elif total_sales >= 3:
            activity_level = "moderate"
            activity_emoji = "✅"
        else:
            activity_level = "low"
            activity_emoji = "🔍"

        # Find most active period
        if sales_by_year:
            most_active_year = max(sales_by_year, key=sales_by_year.get)
            most_sales = sales_by_year[most_active_year]
        else:
            most_active_year = None
            most_sales = 0

        return {
            "activity_level": activity_level,
            "activity_emoji": activity_emoji,
            "total_transactions": total_sales,
            "sales_by_year": sales_by_year,
            "most_active_year": most_active_year,
            "peak_activity_count": most_sales
        }

    @staticmethod
    def generate_investment_insights(property_data: Dict, sales_analysis: Dict) -> Dict:
        """Generate AI-powered investment insights"""
        insights = []
        recommendations = []
        risk_factors = []

        # Price trend insights
        if sales_analysis.get('price_trend', {}).get('trend') == 'strong_growth':
            insights.append("🚀 Property shows strong appreciation history")
            recommendations.append("Consider for long-term investment")
        elif sales_analysis.get('price_trend', {}).get('trend') == 'declining':
            insights.append("⚠️ Property values have been declining")
            risk_factors.append("Historical price depreciation")

        # Market activity insights
        if sales_analysis.get('market_activity', {}).get('activity_level') == 'very_high':
            insights.append("🔄 High transaction frequency indicates liquid market")
            recommendations.append("Good for quick resale opportunities")
        elif sales_analysis.get('market_activity', {}).get('activity_level') == 'low':
            insights.append("🐌 Low transaction history")
            risk_factors.append("May be harder to resell")

        # Calculate ROI potential
        current_value = property_data.get('just_value', 0)
        if current_value > 0 and sales_analysis.get('price_trend', {}).get('annual_appreciation'):
            annual_rate = sales_analysis['price_trend']['annual_appreciation']
            five_year_projection = current_value * (1 + annual_rate/100) ** 5
            insights.append(f"📊 5-year value projection: ${five_year_projection:,.0f}")

        # Investment score (0-100)
        score = 50  # Base score

        # Adjust based on appreciation
        if sales_analysis.get('price_trend', {}).get('annual_appreciation', 0) > 5:
            score += 20
        elif sales_analysis.get('price_trend', {}).get('annual_appreciation', 0) > 2:
            score += 10
        elif sales_analysis.get('price_trend', {}).get('annual_appreciation', 0) < 0:
            score -= 20

        # Adjust based on market activity
        if sales_analysis.get('market_activity', {}).get('activity_level') == 'very_high':
            score += 15
        elif sales_analysis.get('market_activity', {}).get('activity_level') == 'high':
            score += 10
        elif sales_analysis.get('market_activity', {}).get('activity_level') == 'low':
            score -= 10

        # Cap score between 0 and 100
        score = max(0, min(100, score))

        # Determine investment grade
        if score >= 80:
            grade = "A"
            grade_emoji = "🌟"
        elif score >= 70:
            grade = "B"
            grade_emoji = "✨"
        elif score >= 60:
            grade = "C"
            grade_emoji = "👍"
        elif score >= 50:
            grade = "D"
            grade_emoji = "🤔"
        else:
            grade = "F"
            grade_emoji = "⚠️"

        return {
            "investment_score": score,
            "investment_grade": f"{grade} {grade_emoji}",
            "insights": insights,
            "recommendations": recommendations,
            "risk_factors": risk_factors,
            "ai_summary": f"This property scores {score}/100 as an investment opportunity based on historical sales data and market trends."
        }

@app.get("/")
async def root():
    return {
        "service": "AI Sales History API",
        "status": "running",
        "endpoints": [
            "/api/sales-history/{parcel_id}",
            "/api/sales-analysis/{parcel_id}",
            "/api/mini-card-data/{parcel_id}"
        ]
    }

@app.get("/api/sales-history/{parcel_id}")
async def get_sales_history(parcel_id: str):
    """Get complete sales history for a property"""
    try:
        # Query property_sales_history table
        result = supabase.table('property_sales_history') \
            .select('*') \
            .eq('parcel_id', parcel_id) \
            .gte('sale_price', 1000) \
            .order('sale_date', desc=True) \
            .execute()

        sales_records = []

        if result.data:
            for record in result.data:
                sales_records.append({
                    "sale_date": record.get('sale_date'),
                    "sale_price": record.get('sale_price', 0),
                    "seller_name": record.get('seller_name', 'N/A'),
                    "buyer_name": record.get('buyer_name', 'N/A'),
                    "instrument_type": record.get('instrument_type', 'N/A'),
                    "book_page": record.get('book_page', 'N/A'),
                    "qualification": record.get('qualification', 'N/A'),
                    "vacant_at_sale": record.get('vacant_at_sale', False),
                    "year": record.get('year', 0)
                })

        # If no records in property_sales_history, try florida_parcels as fallback
        if not sales_records:
            parcel_result = supabase.table('florida_parcels') \
                .select('sale_date,sale_price,seller_name,buyer_name,sale_yr1,sale_mo1') \
                .eq('parcel_id', parcel_id) \
                .execute()

            if parcel_result.data and parcel_result.data[0]:
                record = parcel_result.data[0]
                if record.get('sale_price', 0) > 1000:
                    sales_records.append({
                        "sale_date": record.get('sale_date'),
                        "sale_price": record.get('sale_price', 0),
                        "seller_name": record.get('seller_name', 'N/A'),
                        "buyer_name": record.get('buyer_name', 'N/A'),
                        "instrument_type": "Deed",
                        "book_page": "N/A",
                        "qualification": "Q",
                        "vacant_at_sale": False,
                        "year": record.get('sale_yr1', 0)
                    })

        return {
            "success": True,
            "parcel_id": parcel_id,
            "total_sales": len(sales_records),
            "sales_history": sales_records
        }

    except Exception as e:
        print(f"Error fetching sales history: {e}")
        return {
            "success": False,
            "error": str(e),
            "sales_history": []
        }

@app.get("/api/sales-analysis/{parcel_id}")
async def get_sales_analysis(parcel_id: str):
    """Get AI-powered sales analysis for a property"""
    try:
        # Get sales history
        sales_response = await get_sales_history(parcel_id)
        sales_history = sales_response.get('sales_history', [])

        # Get property data
        property_result = supabase.table('florida_parcels') \
            .select('*') \
            .eq('parcel_id', parcel_id) \
            .limit(1) \
            .execute()

        property_data = property_result.data[0] if property_result.data else {}

        # Initialize AI agent
        agent = SalesAnalysisAgent()

        # Perform analyses
        price_trend = agent.analyze_price_trend(sales_history)
        market_activity = agent.analyze_market_activity(sales_history)

        # Generate investment insights
        investment_insights = agent.generate_investment_insights(
            property_data,
            {
                "price_trend": price_trend,
                "market_activity": market_activity
            }
        )

        return {
            "success": True,
            "parcel_id": parcel_id,
            "property_address": f"{property_data.get('phy_addr1', 'N/A')}, {property_data.get('phy_city', 'N/A')}",
            "current_value": property_data.get('just_value', 0),
            "sales_count": len(sales_history),
            "analysis": {
                "price_trend": price_trend,
                "market_activity": market_activity,
                "investment_insights": investment_insights
            },
            "last_sale": sales_history[0] if sales_history else None,
            "ai_generated": True,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"Error in sales analysis: {e}")
        return {
            "success": False,
            "error": str(e),
            "analysis": {}
        }

@app.get("/api/mini-card-data/{parcel_id}")
async def get_mini_card_sales_data(parcel_id: str):
    """Get condensed sales data for mini property cards"""
    try:
        # Get sales history
        sales_response = await get_sales_history(parcel_id)
        sales_history = sales_response.get('sales_history', [])

        # Get last sale
        last_sale = sales_history[0] if sales_history else None

        # Quick AI analysis
        agent = SalesAnalysisAgent()
        price_trend = agent.analyze_price_trend(sales_history) if len(sales_history) >= 2 else {}

        # Format for mini card display
        mini_card_data = {
            "has_sales": len(sales_history) > 0,
            "last_sale_price": last_sale['sale_price'] if last_sale else None,
            "last_sale_date": last_sale['sale_date'] if last_sale else None,
            "total_sales": len(sales_history),
            "price_trend": price_trend.get('trend_emoji', ''),
            "appreciation": price_trend.get('total_appreciation', 0) if price_trend else 0,
            "quick_insight": None
        }

        # Generate quick insight
        if mini_card_data['has_sales']:
            if price_trend.get('trend') == 'strong_growth':
                mini_card_data['quick_insight'] = "📈 Strong appreciation"
            elif price_trend.get('trend') == 'moderate_growth':
                mini_card_data['quick_insight'] = "📊 Steady growth"
            elif len(sales_history) >= 5:
                mini_card_data['quick_insight'] = "🔄 Active market"
            elif last_sale:
                mini_card_data['quick_insight'] = f"Last sale: ${last_sale['sale_price']:,.0f}"

        return {
            "success": True,
            "parcel_id": parcel_id,
            "mini_card_data": mini_card_data
        }

    except Exception as e:
        print(f"Error getting mini card data: {e}")
        return {
            "success": False,
            "error": str(e),
            "mini_card_data": {
                "has_sales": False,
                "last_sale_price": None,
                "last_sale_date": None,
                "total_sales": 0,
                "price_trend": "",
                "appreciation": 0,
                "quick_insight": None
            }
        }

@app.get("/api/batch-mini-cards")
async def get_batch_mini_card_data(parcel_ids: str = Query(..., description="Comma-separated parcel IDs")):
    """Get sales data for multiple properties at once (for performance)"""
    try:
        ids = parcel_ids.split(',')[:20]  # Limit to 20 properties

        # Fetch all data in parallel
        tasks = [get_mini_card_sales_data(pid.strip()) for pid in ids]
        results = await asyncio.gather(*tasks)

        # Format response
        batch_data = {}
        for result in results:
            if result['success']:
                batch_data[result['parcel_id']] = result['mini_card_data']

        return {
            "success": True,
            "count": len(batch_data),
            "data": batch_data
        }

    except Exception as e:
        print(f"Error in batch processing: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {}
        }

if __name__ == "__main__":
    print("Starting AI Sales History API on port 8004...")
    print("This API provides AI-powered sales analysis and insights")
    uvicorn.run(app, host="0.0.0.0", port=8004)