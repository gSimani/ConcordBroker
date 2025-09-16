"""
Playwright MCP Integration for Web Scraping Automation
Integrates with MCP Server for coordinated property data collection
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
from playwright.async_api import async_playwright, Browser, Page
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaywrightMCPClient:
    """Client for integrating Playwright with MCP Server"""

    def __init__(self, mcp_url: str = "http://localhost:3001", api_key: str = "concordbroker-mcp-key"):
        self.mcp_url = mcp_url
        self.api_key = api_key
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    async def connect(self):
        """Initialize Playwright and connect to MCP Server"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']
        )
        logger.info("Playwright browser initialized")

        # Verify MCP Server connection
        async with aiohttp.ClientSession() as session:
            headers = {"x-api-key": self.api_key}
            try:
                async with session.get(f"{self.mcp_url}/health", headers=headers) as resp:
                    if resp.status == 200:
                        logger.info("Connected to MCP Server")
                    else:
                        logger.warning(f"MCP Server returned status {resp.status}")
            except Exception as e:
                logger.error(f"Failed to connect to MCP Server: {e}")

    async def disconnect(self):
        """Clean up Playwright resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright resources cleaned up")

    async def notify_mcp(self, event_type: str, data: Dict[str, Any]):
        """Send events to MCP Server"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "event": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            try:
                async with session.post(
                    f"{self.mcp_url}/api/events",
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        logger.debug(f"Event {event_type} sent to MCP")
                    else:
                        logger.warning(f"MCP event failed: {resp.status}")
            except Exception as e:
                logger.error(f"Failed to notify MCP: {e}")

class PropertyScraperMCP:
    """Property scraper with MCP integration"""

    def __init__(self, mcp_client: PlaywrightMCPClient):
        self.mcp_client = mcp_client
        self.scraped_data = []

    async def scrape_property_appraiser(self, county: str, parcel_id: str) -> Dict[str, Any]:
        """Scrape property appraiser website"""
        page = await self.mcp_client.browser.new_page()

        try:
            # Notify MCP of scraping start
            await self.mcp_client.notify_mcp("scrape_start", {
                "county": county,
                "parcel_id": parcel_id,
                "source": "property_appraiser"
            })

            # Navigate to property appraiser site
            url = f"https://{county.lower()}.propertyappraiser.com/property/{parcel_id}"
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Extract property details
            property_data = {}

            # Owner information
            try:
                owner_elem = await page.query_selector('.owner-name')
                if owner_elem:
                    property_data['owner_name'] = await owner_elem.text_content()
            except:
                pass

            # Property values
            value_selectors = {
                'just_value': '.just-value',
                'assessed_value': '.assessed-value',
                'taxable_value': '.taxable-value',
                'land_value': '.land-value',
                'building_value': '.building-value'
            }

            for key, selector in value_selectors.items():
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.text_content()
                        # Clean and convert value
                        value = text.replace('$', '').replace(',', '')
                        property_data[key] = float(value)
                except:
                    continue

            # Property characteristics
            try:
                year_built = await page.query_selector('.year-built')
                if year_built:
                    property_data['year_built'] = int(await year_built.text_content())

                bedrooms = await page.query_selector('.bedrooms')
                if bedrooms:
                    property_data['bedrooms'] = int(await bedrooms.text_content())

                bathrooms = await page.query_selector('.bathrooms')
                if bathrooms:
                    property_data['bathrooms'] = float(await bathrooms.text_content())

                sqft = await page.query_selector('.total-sqft')
                if sqft:
                    property_data['total_sqft'] = int(await sqft.text_content())
            except:
                pass

            # Take screenshot for validation
            screenshot_path = f"screenshots/{county}_{parcel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path)
            property_data['screenshot'] = screenshot_path

            # Notify MCP of successful scrape
            await self.mcp_client.notify_mcp("scrape_complete", {
                "county": county,
                "parcel_id": parcel_id,
                "data_points": len(property_data),
                "success": True
            })

            return property_data

        except Exception as e:
            logger.error(f"Error scraping {parcel_id}: {e}")

            # Notify MCP of error
            await self.mcp_client.notify_mcp("scrape_error", {
                "county": county,
                "parcel_id": parcel_id,
                "error": str(e)
            })

            return {"error": str(e)}

        finally:
            await page.close()

    async def scrape_tax_deed_auction(self, county: str) -> List[Dict[str, Any]]:
        """Scrape tax deed auction listings"""
        page = await self.mcp_client.browser.new_page()
        auctions = []

        try:
            # Notify MCP
            await self.mcp_client.notify_mcp("tax_deed_scrape_start", {"county": county})

            # Navigate to tax deed auction site
            url = f"https://{county.lower()}.realauction.com"
            await page.goto(url, wait_until="networkidle")

            # Wait for auction listings to load
            await page.wait_for_selector('.auction-item', timeout=10000)

            # Extract all auction items
            auction_elements = await page.query_selector_all('.auction-item')

            for element in auction_elements:
                try:
                    auction_data = {}

                    # Parcel ID
                    parcel_elem = await element.query_selector('.parcel-id')
                    if parcel_elem:
                        auction_data['parcel_id'] = await parcel_elem.text_content()

                    # Certificate number
                    cert_elem = await element.query_selector('.certificate-number')
                    if cert_elem:
                        auction_data['certificate_number'] = await cert_elem.text_content()

                    # Auction date
                    date_elem = await element.query_selector('.auction-date')
                    if date_elem:
                        auction_data['auction_date'] = await date_elem.text_content()

                    # Minimum bid
                    bid_elem = await element.query_selector('.minimum-bid')
                    if bid_elem:
                        bid_text = await bid_elem.text_content()
                        bid_value = bid_text.replace('$', '').replace(',', '')
                        auction_data['minimum_bid'] = float(bid_value)

                    # Property address
                    addr_elem = await element.query_selector('.property-address')
                    if addr_elem:
                        auction_data['address'] = await addr_elem.text_content()

                    auctions.append(auction_data)

                except Exception as e:
                    logger.warning(f"Error extracting auction item: {e}")
                    continue

            # Notify MCP of completion
            await self.mcp_client.notify_mcp("tax_deed_scrape_complete", {
                "county": county,
                "auctions_found": len(auctions),
                "success": True
            })

            return auctions

        except Exception as e:
            logger.error(f"Error scraping tax deed auctions: {e}")

            await self.mcp_client.notify_mcp("tax_deed_scrape_error", {
                "county": county,
                "error": str(e)
            })

            return []

        finally:
            await page.close()

    async def scrape_sunbiz(self, entity_name: str) -> Dict[str, Any]:
        """Scrape Florida Sunbiz for business entity information"""
        page = await self.mcp_client.browser.new_page()

        try:
            # Notify MCP
            await self.mcp_client.notify_mcp("sunbiz_scrape_start", {"entity_name": entity_name})

            # Navigate to Sunbiz search
            await page.goto("https://search.sunbiz.org/Inquiry/CorporationSearch/ByName")

            # Perform search
            await page.fill('input[name="SearchTerm"]', entity_name)
            await page.click('button[type="submit"]')

            # Wait for results
            await page.wait_for_selector('.result-item', timeout=10000)

            # Click first result
            first_result = await page.query_selector('.result-item a')
            if first_result:
                await first_result.click()
                await page.wait_for_load_state('networkidle')

                # Extract entity details
                entity_data = {}

                # Entity name
                name_elem = await page.query_selector('.entity-name')
                if name_elem:
                    entity_data['entity_name'] = await name_elem.text_content()

                # Filing information
                filing_elem = await page.query_selector('.filing-info')
                if filing_elem:
                    entity_data['filing_info'] = await filing_elem.text_content()

                # Status
                status_elem = await page.query_selector('.status')
                if status_elem:
                    entity_data['status'] = await status_elem.text_content()

                # Principal address
                addr_elem = await page.query_selector('.principal-address')
                if addr_elem:
                    entity_data['principal_address'] = await addr_elem.text_content()

                # Registered agent
                agent_elem = await page.query_selector('.registered-agent')
                if agent_elem:
                    entity_data['registered_agent'] = await agent_elem.text_content()

                # Officers
                officers = []
                officer_elems = await page.query_selector_all('.officer-row')
                for officer_elem in officer_elems:
                    name = await officer_elem.query_selector('.officer-name')
                    title = await officer_elem.query_selector('.officer-title')
                    if name and title:
                        officers.append({
                            'name': await name.text_content(),
                            'title': await title.text_content()
                        })
                entity_data['officers'] = officers

                # Notify MCP
                await self.mcp_client.notify_mcp("sunbiz_scrape_complete", {
                    "entity_name": entity_name,
                    "data_points": len(entity_data),
                    "success": True
                })

                return entity_data

        except Exception as e:
            logger.error(f"Error scraping Sunbiz: {e}")

            await self.mcp_client.notify_mcp("sunbiz_scrape_error", {
                "entity_name": entity_name,
                "error": str(e)
            })

            return {"error": str(e)}

        finally:
            await page.close()

class BatchScraperMCP:
    """Batch scraping with MCP coordination"""

    def __init__(self, mcp_client: PlaywrightMCPClient):
        self.mcp_client = mcp_client
        self.scraper = PropertyScraperMCP(mcp_client)

    async def scrape_batch(self, tasks: List[Dict[str, Any]], max_concurrent: int = 3):
        """Execute batch scraping with concurrency control"""

        # Notify MCP of batch start
        await self.mcp_client.notify_mcp("batch_scrape_start", {
            "total_tasks": len(tasks),
            "max_concurrent": max_concurrent
        })

        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def scrape_with_limit(task):
            async with semaphore:
                task_type = task.get('type')

                if task_type == 'property':
                    result = await self.scraper.scrape_property_appraiser(
                        task['county'],
                        task['parcel_id']
                    )
                elif task_type == 'tax_deed':
                    result = await self.scraper.scrape_tax_deed_auction(task['county'])
                elif task_type == 'sunbiz':
                    result = await self.scraper.scrape_sunbiz(task['entity_name'])
                else:
                    result = {"error": f"Unknown task type: {task_type}"}

                return {"task": task, "result": result}

        # Execute all tasks concurrently
        results = await asyncio.gather(
            *[scrape_with_limit(task) for task in tasks],
            return_exceptions=True
        )

        # Process results
        successful = sum(1 for r in results if isinstance(r, dict) and 'error' not in r.get('result', {}))
        failed = len(results) - successful

        # Notify MCP of batch completion
        await self.mcp_client.notify_mcp("batch_scrape_complete", {
            "total_tasks": len(tasks),
            "successful": successful,
            "failed": failed
        })

        return results

# Example usage
async def main():
    """Example usage of Playwright MCP integration"""

    async with PlaywrightMCPClient() as mcp_client:
        # Single property scrape
        scraper = PropertyScraperMCP(mcp_client)
        property_data = await scraper.scrape_property_appraiser("BROWARD", "494224020080")
        print("Property data:", property_data)

        # Tax deed auction scrape
        auctions = await scraper.scrape_tax_deed_auction("BROWARD")
        print(f"Found {len(auctions)} auctions")

        # Batch scraping
        batch_scraper = BatchScraperMCP(mcp_client)
        tasks = [
            {"type": "property", "county": "BROWARD", "parcel_id": "494224020080"},
            {"type": "tax_deed", "county": "BROWARD"},
            {"type": "sunbiz", "entity_name": "CONCORD BROKER LLC"}
        ]

        results = await batch_scraper.scrape_batch(tasks)
        print(f"Batch results: {len(results)} tasks completed")

if __name__ == "__main__":
    asyncio.run(main())