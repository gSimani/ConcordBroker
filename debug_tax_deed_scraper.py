"""
Debug Tax Deed Scraper to see what's being scraped
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json

async def debug_scrape():
    """Debug the auction scraping"""
    BASE_URL = "https://broward.deedauction.net"
    AUCTIONS_URL = f"{BASE_URL}/auctions"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(AUCTIONS_URL) as response:
            html = await response.text()
            
            # Save HTML for inspection
            with open('auction_page.html', 'w', encoding='utf-8') as f:
                f.write(html)
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for the upcoming auctions table
            print("\n=== Looking for upcoming auctions table ===")
            upcoming_table = soup.find('table', {'id': 'upcoming_auctions'})
            if upcoming_table:
                print("Found upcoming_auctions table!")
                tbody = upcoming_table.find('tbody')
                if tbody:
                    rows = tbody.find_all('tr')
                    print(f"Found {len(rows)} rows in tbody")
                    
                    for i, row in enumerate(rows[:3]):  # First 3 rows
                        print(f"\nRow {i+1}:")
                        cells = row.find_all('td')
                        for j, cell in enumerate(cells):
                            print(f"  Cell {j}: {cell.text.strip()[:100]}")
                            # Check for links
                            link = cell.find('a')
                            if link:
                                print(f"    Link: {link.get('href', 'no href')}")
                else:
                    print("No tbody found in upcoming_auctions table")
            else:
                print("No upcoming_auctions table found")
                
            # Look for any tables
            all_tables = soup.find_all('table')
            print(f"\n=== Found {len(all_tables)} total tables ===")
            for i, table in enumerate(all_tables):
                table_id = table.get('id', 'no-id')
                table_class = table.get('class', ['no-class'])
                print(f"Table {i+1}: id='{table_id}', class={table_class}")
                
            # Look for auction data in other formats
            print("\n=== Looking for auction links ===")
            auction_links = soup.find_all('a', href=lambda x: x and '/auction/' in x)
            print(f"Found {len(auction_links)} auction links")
            for link in auction_links[:5]:
                print(f"  - {link.text.strip()}: {link.get('href')}")

asyncio.run(debug_scrape())