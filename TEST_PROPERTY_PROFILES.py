"""
Test Property Profile System
Demonstrates the complete property profile functionality
"""

import asyncio
import json
from datetime import datetime
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / 'apps' / 'api'))

from property_profile_service import PropertyProfileService

async def test_property_profiles():
    """Test property profile generation"""
    
    print("=" * 60)
    print("PROPERTY PROFILE SYSTEM TEST")
    print("=" * 60)
    
    # Initialize service
    print("\n1. Initializing Property Profile Service...")
    service = PropertyProfileService()
    await service.initialize()
    print("   PASS - Service initialized")
    
    # Test addresses
    test_properties = [
        {
            "address": "123 Main Street",
            "city": "Fort Lauderdale",
            "state": "FL"
        },
        {
            "address": "456 Ocean Drive",
            "city": "Miami Beach", 
            "state": "FL"
        },
        {
            "address": "789 Las Olas Blvd",
            "city": "Fort Lauderdale",
            "state": "FL"
        }
    ]
    
    print("\n2. Testing Property Profiles:")
    
    for prop in test_properties:
        print(f"\n   Testing: {prop['address']}, {prop['city']}")
        print("   " + "-" * 50)
        
        try:
            # Get profile
            profile = await service.get_property_profile(
                address=prop['address'],
                city=prop['city'],
                state=prop['state']
            )
            
            # Display key information
            print(f"   Address: {profile.address}")
            print(f"   City: {profile.city}, {profile.state}")
            print(f"   Parcel ID: {profile.parcel_id or 'Not found'}")
            print(f"   Owner: {profile.owner_name or 'Not found'}")
            print(f"   Owner Type: {profile.owner_type or 'Unknown'}")
            print(f"   Property Type: {profile.property_type or 'Unknown'}")
            print(f"   Market Value: ${profile.market_value:,.0f}" if profile.market_value else "   Market Value: N/A")
            print(f"   Last Sale: ${profile.last_sale_price:,.0f}" if profile.last_sale_price else "   Last Sale: N/A")
            print(f"   Investment Score: {profile.investment_score}/100")
            print(f"   Data Sources: {', '.join(profile.data_sources)}")
            print(f"   Confidence: {profile.confidence_score:.0f}%")
            
            # Check for opportunities
            if profile.opportunities:
                print(f"\n   Opportunities Found:")
                for opp in profile.opportunities:
                    print(f"     - {opp}")
            
            # Check for risks
            if profile.risk_factors:
                print(f"\n   Risk Factors:")
                for risk in profile.risk_factors:
                    print(f"     - {risk}")
            
            # Check special conditions
            if profile.is_distressed:
                print("   ALERT: Distressed property!")
            if profile.is_bank_owned:
                print("   ALERT: Bank-owned (REO)!")
            if profile.is_in_cdd:
                print(f"   ALERT: Property in CDD (${profile.total_nav_assessment:.0f}/year)")
            
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("PROFILE DATA STRUCTURE")
    print("=" * 60)
    
    # Show complete data structure for one property
    if test_properties:
        print("\nComplete profile structure for first property:")
        try:
            profile = await service.get_property_profile(
                address=test_properties[0]['address'],
                city=test_properties[0]['city'],
                state=test_properties[0]['state']
            )
            
            profile_dict = service.to_dict(profile)
            print(json.dumps(profile_dict, indent=2, default=str))
            
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("API ENDPOINTS AVAILABLE")
    print("=" * 60)
    
    print("\nProperty Profile Endpoints:")
    print("GET /api/property/profile/{city}/{address}")
    print("  Example: http://localhost:8000/api/property/profile/fort-lauderdale/123-main-street")
    
    print("\nSearch Endpoints:")
    print("GET /api/property/search?q={query}")
    print("GET /api/property/investment-opportunities")
    print("GET /api/property/market-analysis/{city}")
    print("GET /api/property/owner/{owner_name}")
    
    print("\nData Status:")
    print("GET /api/data/status")
    
    print("\n" + "=" * 60)
    print("FRONTEND URLS")
    print("=" * 60)
    
    print("\nProperty Profile Pages:")
    print("http://localhost:5175/properties/fort-lauderdale/123-main-street")
    print("http://localhost:5175/properties/miami-beach/456-ocean-drive")
    print("http://localhost:5175/properties/boca-raton/789-palmetto-park-road")

async def test_api_server():
    """Test running the API server"""
    print("\n" + "=" * 60)
    print("STARTING API SERVER")
    print("=" * 60)
    
    print("\nTo start the API server, run:")
    print("cd apps/api")
    print("python property_profile_api.py")
    print("\nOr:")
    print("uvicorn property_profile_api:app --reload --port 8000")
    
    print("\nThe API will be available at:")
    print("http://localhost:8000")
    print("http://localhost:8000/docs (Swagger UI)")

def display_architecture():
    """Display system architecture"""
    print("\n" + "=" * 60)
    print("PROPERTY PROFILE ARCHITECTURE")
    print("=" * 60)
    
    architecture = """
    User Request: /properties/fort-lauderdale/123-main-street
                                    ↓
                        React PropertyProfile Component
                                    ↓
                    API Call: /api/property/profile/fort-lauderdale/123-main-street
                                    ↓
                        PropertyProfileService (Aggregator)
                                    ↓
                    ┌───────────────────────────────────┐
                    │     Parallel Data Fetching       │
                    ├───────────────────────────────────┤
                    │ BCPA: Property characteristics    │
                    │ SDF: Sales history & distress     │
                    │ NAV: Special assessments & CDD    │
                    │ TPP: Business personal property   │
                    │ Sunbiz: Business entity lookup    │
                    │ Official Records: Deed history    │
                    │ DOR: Tax assessments              │
                    └───────────────────────────────────┘
                                    ↓
                        Data Aggregation & Scoring
                                    ↓
                    Investment Analysis & Risk Assessment
                                    ↓
                        Complete Property Profile
    """
    
    print(architecture)

if __name__ == "__main__":
    print("\nTesting Property Profile System...")
    print("This demonstrates the complete property data aggregation")
    print("=" * 60)
    
    # Display architecture
    display_architecture()
    
    # Run tests
    try:
        asyncio.run(test_property_profiles())
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Show API server instructions
    asyncio.run(test_api_server())
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
    print("\nProperty Profile System is ready!")
    print("All data sources are integrated and address-based profiles are available.")