#!/usr/bin/env python3
"""
Tax Deed Data Validation Monitor
Compares tax deed data between broward.deedauction.net source and Supabase database
Generates detailed comparison reports and alerts for discrepancies
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import re

# Third-party imports
from playwright.async_api import async_playwright, Page, Browser
from supabase import create_client, Client
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tax_deed_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TaxDeedProperty:
    """Data structure for tax deed property information"""
    tax_deed_number: str
    parcel_number: str
    address: str
    opening_bid: float
    status: str
    applicant_name: str
    auction_date: Optional[str] = None
    description: Optional[str] = None
    homestead: Optional[bool] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

@dataclass
class ComparisonResult:
    """Result of data comparison"""
    timestamp: str
    source_count: int
    database_count: int
    match_percentage: float
    missing_in_database: List[Dict[str, Any]]
    extra_in_database: List[Dict[str, Any]]
    field_mismatches: List[Dict[str, Any]]
    accuracy_score: float
    recommendations: List[str]

class TaxDeedSourceScraper:
    """Scraper for broward.deedauction.net"""
    
    def __init__(self):
        self.base_url = "https://broward.deedauction.net/auction/110"
        self.properties: List[TaxDeedProperty] = []
    
    async def scrape_properties(self) -> List[TaxDeedProperty]:
        """Scrape all properties from the source website"""
        logger.info("Starting web scraping of broward.deedauction.net...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to auction page
                await page.goto(self.base_url, wait_until='networkidle')
                logger.info(f"Loaded page: {self.base_url}")
                
                # Wait for content to load
                await page.wait_for_timeout(3000)
                
                # Click all expand buttons to reveal hidden details
                await self._expand_all_details(page)
                
                # Extract property data
                properties = await self._extract_properties(page)
                
                logger.info(f"Successfully scraped {len(properties)} properties")
                return properties
                
            except Exception as e:
                logger.error(f"Error during scraping: {e}")
                return []
            finally:
                await browser.close()
    
    async def _expand_all_details(self, page: Page):
        """Click all expand buttons to reveal hidden property details"""
        expand_selectors = [
            'button[class*="expand"]',
            'button[class*="show"]',
            'a[class*="expand"]',
            '.expandable',
            '[data-toggle="collapse"]',
            'button:has-text("Show")',
            'button:has-text("Expand")',
            'button:has-text("More")',
            '.btn-primary',
            '.btn-secondary'
        ]
        
        for selector in expand_selectors:
            try:
                expand_buttons = await page.query_selector_all(selector)
                for button in expand_buttons:
                    try:
                        await button.click()
                        await page.wait_for_timeout(500)  # Wait for expand animation
                    except:
                        continue
            except:
                continue
        
        # Wait for all content to load after expanding
        await page.wait_for_timeout(2000)
        logger.info("Expanded all available property details")
    
    async def _extract_properties(self, page: Page) -> List[TaxDeedProperty]:
        """Extract property data from the page"""
        properties = []
        
        try:
            # Based on website analysis, look for table rows with property data
            # First try to find the main results table
            table_selectors = [
                'table.results tr',
                '.results tr',
                'table tr',
                'tr'
            ]
            
            property_rows = []
            for selector in table_selectors:
                try:
                    rows = await page.query_selector_all(selector)
                    # Filter rows that contain property data
                    for row in rows:
                        text_content = await row.text_content()
                        if text_content and (
                            any(keyword in text_content.lower() for keyword in [
                                'td-', '$', 'upcoming', 'active', 'canceled', 'am', 'pm'
                            ]) and len(text_content.strip()) > 20
                        ):
                            property_rows.append(row)
                    
                    if property_rows:
                        logger.info(f"Found {len(property_rows)} property rows with selector: {selector}")
                        break
                except:
                    continue
            
            # If table approach doesn't work, try alternative selectors
            if not property_rows:
                logger.info("Table approach failed, trying alternative selectors...")
                await self._try_expand_buttons(page)
                
                # Look for property containers
                container_selectors = [
                    'div[class*="item"]',
                    'div[class*="property"]',
                    'div[class*="auction"]',
                    '.property-item',
                    '.auction-item'
                ]
                
                for selector in container_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        property_rows.extend(elements)
                    except:
                        continue
            
            logger.info(f"Processing {len(property_rows)} property elements")
            
            # Extract data from each property row
            for row in property_rows:
                try:
                    property_data = await self._extract_table_row_property(row)
                    if property_data:
                        properties.append(property_data)
                        logger.info(f"Successfully extracted property: {property_data.tax_deed_number}")
                except Exception as e:
                    logger.warning(f"Error extracting property from row: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error in property extraction: {e}")
        
        return properties
    
    async def _try_expand_buttons(self, page: Page):
        """Try to click expand buttons to reveal more details"""
        expand_selectors = [
            'button[onclick*="toggle"]',
            '.expand-icon',
            '.toggle-icon',
            'button:has-text("+")',
            'button:has-text("Expand")',
            '[onclick*="toggle_item_details"]'
        ]
        
        for selector in expand_selectors:
            try:
                buttons = await page.query_selector_all(selector)
                for button in buttons:
                    try:
                        await button.click()
                        await page.wait_for_timeout(300)
                    except:
                        continue
            except:
                continue
    
    async def _extract_table_row_property(self, row) -> Optional[TaxDeedProperty]:
        """Extract property data from a table row"""
        try:
            # Get all cells in the row
            cells = await row.query_selector_all('td')
            
            if len(cells) < 3:  # Need at least 3 cells for meaningful data
                return None
            
            # Extract text from each cell
            cell_texts = []
            for cell in cells:
                text = await cell.text_content()
                cell_texts.append(text.strip() if text else "")
            
            # Based on website structure analysis:
            # Column 1: Tax Deed Number
            # Column 2: Opening Bid
            # Column 3: Close Time  
            # Column 4: Status
            
            tax_deed_number = ""
            opening_bid = 0.0
            status = "Unknown"
            address = ""
            parcel_number = ""
            applicant_name = ""
            
            # Extract Tax Deed Number (usually first column)
            if len(cell_texts) > 0:
                tax_deed_match = re.search(r'(\d+)', cell_texts[0])
                if tax_deed_match:
                    tax_deed_number = tax_deed_match.group(1)
            
            # Extract Opening Bid (usually second column)
            if len(cell_texts) > 1:
                bid_match = re.search(r'\$([0-9,]+\.?\d*)', cell_texts[1])
                if bid_match:
                    try:
                        opening_bid = float(bid_match.group(1).replace(',', ''))
                    except:
                        pass
            
            # Extract Status (usually last column)
            if len(cell_texts) > 2:
                status_text = cell_texts[-1].lower()
                if 'upcoming' in status_text:
                    status = "Upcoming"
                elif 'active' in status_text:
                    status = "Active"
                elif 'canceled' in status_text or 'cancelled' in status_text:
                    status = "Cancelled"
                elif 'completed' in status_text or 'sold' in status_text:
                    status = "Completed"
            
            # Try to get parcel number from PDF links or other sources
            try:
                pdf_links = await row.query_selector_all('a[href*=".pdf"]')
                if pdf_links:
                    href = await pdf_links[0].get_attribute('href')
                    if href:
                        # Extract parcel from PDF filename like "51640_514114-10-6250.pdf"
                        parcel_match = re.search(r'_([0-9\-]+)\.pdf', href)
                        if parcel_match:
                            parcel_number = parcel_match.group(1)
            except:
                pass
            
            # Try to extract address from row content
            row_text = await row.text_content()
            address_patterns = [
                r'([0-9]+\s+[A-Za-z\s]+(?:St|Ave|Rd|Dr|Blvd|Ln|Way|Ct|Pl)[^,\n]*)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:St|Ave|Rd|Dr|Blvd|Ln|Way|Ct|Pl))'
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, row_text)
                if match:
                    address = match.group(1).strip()
                    break
            
            # Only create property if we have essential data
            if tax_deed_number or opening_bid > 0:
                return TaxDeedProperty(
                    tax_deed_number=tax_deed_number,
                    parcel_number=parcel_number,
                    address=address,
                    opening_bid=opening_bid,
                    status=status,
                    applicant_name=applicant_name
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting table row property: {e}")
            return None
    
    async def _is_property_row(self, element) -> bool:
        """Check if table row contains property data"""
        try:
            text_content = await element.text_content()
            return any(keyword in text_content.lower() for keyword in [
                'td-', 'tax deed', 'parcel', 'opening bid', 'applicant'
            ])
        except:
            return False
    
    async def _has_property_content(self, element) -> bool:
        """Check if div contains property-like content"""
        try:
            text_content = await element.text_content()
            return (
                len(text_content) > 50 and  # Has substantial content
                any(keyword in text_content.lower() for keyword in [
                    'td-', 'tax deed', 'parcel', 'opening bid', 'applicant'
                ])
            )
        except:
            return False
    
    async def _extract_single_property(self, element) -> Optional[TaxDeedProperty]:
        """Extract data from a single property element"""
        try:
            text_content = await element.text_content()
            inner_html = await element.inner_html()
            
            # Extract Tax Deed Number
            tax_deed_match = re.search(r'TD[-\s]?(\d+[-\s]?\d*)', text_content, re.IGNORECASE)
            tax_deed_number = tax_deed_match.group(0) if tax_deed_match else ""
            
            # Extract Parcel Number
            parcel_patterns = [
                r'Parcel[:\s]+([0-9\-]+)',
                r'Folio[:\s]+([0-9\-]+)',
                r'PCN[:\s]+([0-9\-]+)',
                r'([0-9]{2,}-[0-9]{2,}-[0-9]{2,})',
                r'([0-9]{10,})'
            ]
            parcel_number = ""
            for pattern in parcel_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    parcel_number = match.group(1)
                    break
            
            # Extract Address
            address_patterns = [
                r'(?:Address|Location|Property)[:\s]+([^$\n\r]+?)(?:\$|Opening|Applicant)',
                r'([0-9]+\s+[A-Za-z\s]+(?:St|Ave|Rd|Dr|Blvd|Ln|Way|Ct|Pl)[^$\n\r]*)',
                r'([^,\n\r]+,\s*[A-Z]{2}\s*[0-9]{5})'
            ]
            address = ""
            for pattern in address_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    address = match.group(1).strip()
                    break
            
            # Extract Opening Bid
            bid_patterns = [
                r'Opening Bid[:\s]+\$([0-9,]+\.?\d*)',
                r'Bid[:\s]+\$([0-9,]+\.?\d*)',
                r'\$([0-9,]+\.?\d*)',
            ]
            opening_bid = 0.0
            for pattern in bid_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    bid_str = match.group(1).replace(',', '')
                    try:
                        opening_bid = float(bid_str)
                        break
                    except:
                        continue
            
            # Extract Status
            status_patterns = [
                r'Status[:\s]+([A-Za-z\s]+)',
                r'(Active|Cancelled|Upcoming|Completed|Sold)',
            ]
            status = "Unknown"
            for pattern in status_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    status = match.group(1).strip()
                    break
            
            # Extract Applicant Name
            applicant_patterns = [
                r'Applicant[:\s]+([^$\n\r]+?)(?:\$|Tax|Opening|Status)',
                r'Applied by[:\s]+([^$\n\r]+?)(?:\$|Tax|Opening|Status)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+LLC|Inc|Corp)?)'
            ]
            applicant_name = ""
            for pattern in applicant_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    applicant_name = match.group(1).strip()
                    break
            
            # Only create property if we have essential data
            if tax_deed_number or parcel_number:
                return TaxDeedProperty(
                    tax_deed_number=tax_deed_number,
                    parcel_number=parcel_number,
                    address=address,
                    opening_bid=opening_bid,
                    status=status,
                    applicant_name=applicant_name
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting single property: {e}")
            return None

class TaxDeedDatabaseClient:
    """Client for Supabase tax deed database operations"""
    
    def __init__(self):
        # Use provided credentials from requirements
        self.supabase_url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"
        
        self.client = create_client(self.supabase_url, self.supabase_key)
        logger.info("Initialized Supabase client")
    
    def get_tax_deed_properties(self) -> List[Dict[str, Any]]:
        """Fetch all tax deed properties from database"""
        try:
            response = self.client.table('tax_deed_bidding_items').select('*').execute()
            logger.info(f"Fetched {len(response.data)} properties from database")
            return response.data
        except Exception as e:
            logger.error(f"Error fetching from database: {e}")
            return []
    
    def get_table_schema(self) -> Dict[str, Any]:
        """Get the table schema information"""
        try:
            # Get a sample record to understand structure
            response = self.client.table('tax_deed_bidding_items').select('*').limit(1).execute()
            if response.data:
                return response.data[0]
            return {}
        except Exception as e:
            logger.error(f"Error getting table schema: {e}")
            return {}

class TaxDeedDataComparator:
    """Compares source data with database data"""
    
    def __init__(self):
        self.scraper = TaxDeedSourceScraper()
        self.db_client = TaxDeedDatabaseClient()
    
    async def run_comparison(self) -> ComparisonResult:
        """Run complete data comparison"""
        logger.info("Starting tax deed data comparison...")
        
        # Get source data
        source_properties = await self.scraper.scrape_properties()
        
        # Get database data
        db_properties = self.db_client.get_tax_deed_properties()
        
        # Perform comparison
        result = self._compare_data(source_properties, db_properties)
        
        logger.info(f"Comparison complete. Accuracy: {result.accuracy_score:.1f}%")
        return result
    
    def _compare_data(self, source_properties: List[TaxDeedProperty], 
                     db_properties: List[Dict[str, Any]]) -> ComparisonResult:
        """Compare source and database properties"""
        
        # Convert source properties to dict for easier comparison
        source_dict = {self._get_property_key(prop): asdict(prop) for prop in source_properties}
        
        # Create database property lookup
        db_dict = {}
        for prop in db_properties:
            key = self._get_db_property_key(prop)
            if key:
                db_dict[key] = prop
        
        # Find missing properties
        missing_in_db = []
        for key, prop in source_dict.items():
            if key not in db_dict:
                missing_in_db.append(prop)
        
        # Find extra properties
        extra_in_db = []
        for key, prop in db_dict.items():
            if key not in source_dict:
                extra_in_db.append(prop)
        
        # Find field mismatches
        field_mismatches = []
        for key in set(source_dict.keys()) & set(db_dict.keys()):
            mismatches = self._compare_property_fields(source_dict[key], db_dict[key])
            if mismatches:
                field_mismatches.append({
                    'property_key': key,
                    'mismatches': mismatches
                })
        
        # Calculate accuracy metrics
        total_source = len(source_properties)
        total_db = len(db_properties)
        matching_count = len(set(source_dict.keys()) & set(db_dict.keys()))
        
        if total_source > 0:
            match_percentage = (matching_count / total_source) * 100
        else:
            match_percentage = 0
        
        # Calculate overall accuracy score
        accuracy_score = self._calculate_accuracy_score(
            total_source, total_db, matching_count, len(field_mismatches)
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            missing_in_db, extra_in_db, field_mismatches
        )
        
        return ComparisonResult(
            timestamp=datetime.now().isoformat(),
            source_count=total_source,
            database_count=total_db,
            match_percentage=match_percentage,
            missing_in_database=missing_in_db,
            extra_in_database=extra_in_db,
            field_mismatches=field_mismatches,
            accuracy_score=accuracy_score,
            recommendations=recommendations
        )
    
    def _get_property_key(self, prop: TaxDeedProperty) -> str:
        """Generate unique key for source property"""
        if prop.tax_deed_number:
            return prop.tax_deed_number
        elif prop.parcel_number:
            return prop.parcel_number
        else:
            return f"{prop.address}_{prop.opening_bid}"
    
    def _get_db_property_key(self, prop: Dict[str, Any]) -> str:
        """Generate unique key for database property"""
        tax_deed_fields = ['tax_deed_number', 'tax_deed_id', 'deed_number']
        parcel_fields = ['parcel_number', 'parcel_id', 'folio_number']
        
        # Try tax deed number first
        for field in tax_deed_fields:
            if field in prop and prop[field]:
                return str(prop[field])
        
        # Try parcel number
        for field in parcel_fields:
            if field in prop and prop[field]:
                return str(prop[field])
        
        # Fallback to address + bid
        address = prop.get('address') or prop.get('situs_address') or ''
        bid = prop.get('opening_bid') or prop.get('bid_amount') or 0
        return f"{address}_{bid}"
    
    def _compare_property_fields(self, source_prop: Dict[str, Any], 
                               db_prop: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare individual fields between source and database property"""
        mismatches = []
        
        # Field mapping between source and database
        field_mappings = {
            'tax_deed_number': ['tax_deed_number', 'tax_deed_id', 'deed_number'],
            'parcel_number': ['parcel_number', 'parcel_id', 'folio_number'],
            'address': ['address', 'situs_address', 'property_address'],
            'opening_bid': ['opening_bid', 'bid_amount', 'minimum_bid'],
            'status': ['status', 'auction_status', 'property_status'],
            'applicant_name': ['applicant_name', 'applicant', 'bidder_name']
        }
        
        for source_field, db_fields in field_mappings.items():
            source_value = source_prop.get(source_field)
            db_value = None
            
            # Find matching database field
            for db_field in db_fields:
                if db_field in db_prop:
                    db_value = db_prop[db_field]
                    break
            
            # Compare values
            if source_value and db_value:
                if not self._values_match(source_value, db_value):
                    mismatches.append({
                        'field': source_field,
                        'source_value': source_value,
                        'database_value': db_value,
                        'database_field': db_field
                    })
        
        return mismatches
    
    def _values_match(self, source_val: Any, db_val: Any) -> bool:
        """Check if two values match (with tolerance for formatting differences)"""
        # Convert to strings for comparison
        source_str = str(source_val).strip().lower()
        db_str = str(db_val).strip().lower()
        
        # Exact match
        if source_str == db_str:
            return True
        
        # Numeric comparison with tolerance
        try:
            source_num = float(re.sub(r'[^\d.]', '', str(source_val)))
            db_num = float(re.sub(r'[^\d.]', '', str(db_val)))
            return abs(source_num - db_num) < 0.01
        except:
            pass
        
        # Address comparison (normalize spaces, punctuation)
        source_normalized = re.sub(r'[^\w\s]', '', source_str)
        db_normalized = re.sub(r'[^\w\s]', '', db_str)
        if source_normalized == db_normalized:
            return True
        
        return False
    
    def _calculate_accuracy_score(self, source_count: int, db_count: int, 
                                matching_count: int, mismatch_count: int) -> float:
        """Calculate overall accuracy score"""
        if source_count == 0:
            return 100.0 if db_count == 0 else 0.0
        
        # Base accuracy from matching properties
        base_accuracy = (matching_count / source_count) * 100
        
        # Penalty for field mismatches
        if matching_count > 0:
            field_accuracy = max(0, 100 - (mismatch_count / matching_count) * 50)
        else:
            field_accuracy = 100
        
        # Weighted average
        return (base_accuracy * 0.7) + (field_accuracy * 0.3)
    
    def _generate_recommendations(self, missing: List[Dict], extra: List[Dict], 
                                mismatches: List[Dict]) -> List[str]:
        """Generate recommendations based on comparison results"""
        recommendations = []
        
        if missing:
            recommendations.append(f"Add {len(missing)} missing properties to database")
            recommendations.append("Review data import process for completeness")
        
        if extra:
            recommendations.append(f"Review {len(extra)} extra properties in database")
            recommendations.append("Check for outdated or duplicate records")
        
        if mismatches:
            recommendations.append(f"Fix {len(mismatches)} field mismatches")
            recommendations.append("Review field mapping and data transformation logic")
        
        if not missing and not extra and not mismatches:
            recommendations.append("Data is perfectly synchronized!")
        
        return recommendations

async def main():
    """Main function to run the tax deed data monitoring"""
    print("=" * 80)
    print("TAX DEED DATA VALIDATION MONITOR")
    print("=" * 80)
    
    try:
        # Run comparison
        comparator = TaxDeedDataComparator()
        result = await comparator.run_comparison()
        
        # Save report
        report_file = "tax_deed_comparison_report.json"
        with open(report_file, 'w') as f:
            json.dump(asdict(result), f, indent=2, default=str)
        
        # Display summary
        print(f"\nCOMPARISSON SUMMARY")
        print("-" * 40)
        print(f"Source Properties: {result.source_count}")
        print(f"Database Properties: {result.database_count}")
        print(f"Match Percentage: {result.match_percentage:.1f}%")
        print(f"Accuracy Score: {result.accuracy_score:.1f}%")
        print(f"Missing in DB: {len(result.missing_in_database)}")
        print(f"Extra in DB: {len(result.extra_in_database)}")
        print(f"Field Mismatches: {len(result.field_mismatches)}")
        
        print(f"\nRECOMMENDATIONS:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"{i}. {rec}")
        
        print(f"\nReport saved to: {report_file}")
        
        # Generate alerts if accuracy is low
        if result.accuracy_score < 95:
            print(f"\n[ALERT] Data accuracy below 95% ({result.accuracy_score:.1f}%)")
            print("Review and fix data synchronization issues")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(main())