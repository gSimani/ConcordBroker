import asyncio
import sys
from pathlib import Path
from florida_comprehensive_downloader import FloridaRevenueDownloader

class TestFloridaDownloader(FloridaRevenueDownloader):
    """Test version with limited scope"""
    
    def __init__(self):
        super().__init__()
        # Limit to just one data type for testing
        self.data_types = {
            'NAL': 'https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P'
        }
        # Limit counties for testing
        self.florida_counties = ['BROWARD', 'ALACHUA', 'BAY']  # Just 3 counties for test
        
    async def test_link_extraction(self):
        """Test the link extraction functionality"""
        print("Testing link extraction...")
        
        browser = await self.setup_browser()
        page = await browser.new_page()
        
        try:
            for data_type, url in self.data_types.items():
                print(f"\nTesting {data_type} at {url}")
                links = await self.extract_download_links(page, url, data_type)
                
                print(f"Found {len(links)} links:")
                for i, (download_url, filename) in enumerate(links[:5]):  # Show first 5
                    county = self.get_county_from_filename(filename)
                    print(f"  {i+1}. {filename} -> County: {county}")
                    print(f"      URL: {download_url[:80]}...")
                    
                if len(links) > 5:
                    print(f"  ... and {len(links) - 5} more")
                    
        except Exception as e:
            print(f"Error during test: {e}")
        finally:
            await page.close()
            await browser.close()

async def main():
    """Run the test"""
    tester = TestFloridaDownloader()
    await tester.test_link_extraction()

if __name__ == "__main__":
    asyncio.run(main())