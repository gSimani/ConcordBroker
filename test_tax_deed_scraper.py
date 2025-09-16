"""
Test script for Tax Deed Auction Scraper
=========================================
Tests the scraper without database integration
"""

import asyncio
import json
from apps.workers.tax_deed_auction_scraper import TaxDeedAuctionScraper

async def test_scraper():
    """Test the tax deed auction scraper"""
    print("Starting Tax Deed Auction Scraper Test...")
    print("=" * 60)
    
    async with TaxDeedAuctionScraper() as scraper:
        # Test fetching the main auctions page
        print("\n1. Fetching auctions page...")
        html = await scraper.fetch_page(scraper.AUCTIONS_URL)
        
        if html:
            print("   ✓ Successfully fetched auctions page")
            
            # Test parsing upcoming auctions
            print("\n2. Parsing upcoming auctions...")
            auctions_list = scraper.parse_upcoming_auctions(html)
            print(f"   ✓ Found {len(auctions_list)} upcoming auctions")
            
            for auction in auctions_list:
                print(f"\n   Auction: {auction.get('description', 'Unknown')}")
                print(f"   - ID: {auction.get('auction_id', 'N/A')}")
                print(f"   - Items: {auction.get('total_items', 0)}")
                print(f"   - Status: {auction.get('status', 'Unknown')}")
                print(f"   - URL: {auction.get('url', 'N/A')}")
                
            # Test fetching details for first auction if available
            if auctions_list:
                first_auction = auctions_list[0]
                print(f"\n3. Fetching details for: {first_auction['description']}")
                print("   This may take a moment...")
                
                auction_details = await scraper.fetch_auction_details(first_auction['url'])
                
                if auction_details:
                    print(f"   ✓ Successfully fetched auction details")
                    print(f"   - Available properties: {auction_details.get('available_count', 'Unknown')}")
                    print(f"   - Total properties: {len(auction_details.get('properties', []))}")
                    
                    # Show sample properties
                    properties = auction_details.get('properties', [])
                    if properties:
                        print(f"\n4. Sample Properties (showing first 3):")
                        for i, prop in enumerate(properties[:3], 1):
                            print(f"\n   Property {i}:")
                            print(f"   - Tax Deed #: {prop.get('tax_deed_number', 'N/A')}")
                            print(f"   - Status: {prop.get('status', 'Unknown')}")
                            print(f"   - Opening Bid: ${prop.get('opening_bid', 0):,.2f}")
                            print(f"   - Best Bid: ${prop.get('best_bid', 0):,.2f}" if prop.get('best_bid') else "   - Best Bid: None")
                            print(f"   - Close Time: {prop.get('close_time', 'N/A')}")
                            
                            # Show expanded details if available
                            if prop.get('parcel_number'):
                                print(f"   - Parcel: {prop.get('parcel_number')}")
                            if prop.get('situs_address'):
                                print(f"   - Address: {prop.get('situs_address')}")
                            if prop.get('homestead') is not None:
                                print(f"   - Homestead: {'Yes' if prop.get('homestead') else 'No'}")
                            if prop.get('assessed_value'):
                                print(f"   - Assessed Value: ${prop.get('assessed_value'):,.2f}")
                            if prop.get('applicant'):
                                print(f"   - Applicant: {prop.get('applicant')}")
                            if prop.get('legal_description'):
                                print(f"   - Legal: {prop.get('legal_description')[:50]}...")
                                
                    # Save sample data
                    print("\n5. Saving sample data to JSON...")
                    sample_data = {
                        'auction': first_auction,
                        'details': {
                            'available_count': auction_details.get('available_count'),
                            'statistics': auction_details.get('statistics', {}),
                            'sample_properties': properties[:5] if properties else []
                        }
                    }
                    
                    with open('tax_deed_scraper_test_results.json', 'w') as f:
                        json.dump(sample_data, f, indent=2, default=str)
                    print("   ✓ Saved to tax_deed_scraper_test_results.json")
                    
                else:
                    print("   ✗ Failed to fetch auction details")
            else:
                print("\n✗ No auctions found to test")
                
        else:
            print("   ✗ Failed to fetch auctions page")
            print("   Check internet connection and URL accessibility")
            
    print("\n" + "=" * 60)
    print("Test completed!")
    
async def test_full_scrape():
    """Test full scraping of all auctions"""
    print("\nRunning FULL SCRAPE TEST...")
    print("This will scrape ALL auctions and may take several minutes.")
    print("=" * 60)
    
    async with TaxDeedAuctionScraper() as scraper:
        auctions = await scraper.scrape_all_auctions()
        
        if auctions:
            print(f"\n✓ Successfully scraped {len(auctions)} auctions")
            
            total_properties = sum(len(a.properties) for a in auctions)
            print(f"✓ Total properties scraped: {total_properties}")
            
            # Statistics
            upcoming_count = sum(
                len([p for p in a.properties if p.status.value == 'Upcoming']) 
                for a in auctions
            )
            canceled_count = sum(
                len([p for p in a.properties if p.status.value == 'Canceled']) 
                for a in auctions
            )
            
            print(f"\nStatistics:")
            print(f"- Upcoming properties: {upcoming_count}")
            print(f"- Canceled properties: {canceled_count}")
            
            # Find high-value properties
            high_value = []
            homestead = []
            
            for auction in auctions:
                for prop in auction.properties:
                    if prop.opening_bid > 100000:
                        high_value.append(prop)
                    if prop.homestead:
                        homestead.append(prop)
                        
            print(f"- High-value properties (>$100k): {len(high_value)}")
            print(f"- Homestead properties: {len(homestead)}")
            
            # Save full results
            scraper.save_to_json(auctions, 'tax_deed_full_scrape_test.json')
            print(f"\n✓ Full results saved to tax_deed_full_scrape_test.json")
            
            # Show sample high-value property
            if high_value:
                print(f"\nSample High-Value Property:")
                hv = high_value[0]
                print(f"- Tax Deed: {hv.tax_deed_number}")
                print(f"- Address: {hv.situs_address}")
                print(f"- Opening Bid: ${hv.opening_bid:,.2f}")
                print(f"- Parcel: {hv.parcel_number}")
                
        else:
            print("\n✗ No auctions scraped")
            
if __name__ == "__main__":
    print("Tax Deed Auction Scraper Test Suite")
    print("====================================\n")
    
    # Run basic test first
    asyncio.run(test_scraper())
    
    # Ask if user wants to run full scrape
    response = input("\nDo you want to run the FULL SCRAPE test? (y/n): ")
    if response.lower() == 'y':
        asyncio.run(test_full_scrape())