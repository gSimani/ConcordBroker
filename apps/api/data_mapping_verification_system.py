"""
Comprehensive Data Mapping and Verification System
Uses SQLAlchemy, Playwright MCP, and OpenCV to ensure 100% accurate data placement
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import QueuePool
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import aiohttp
from playwright.async_api import async_playwright, Page, Browser
import cv2
import numpy as np
from PIL import Image
import io
import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL",
    "postgresql://postgres.pmispwtdngkcmsrsjwbp:vM4g2024$$Florida1@aws-0-us-east-1.pooler.supabase.com:6543/postgres")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=False
)

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==================== SQLAlchemy Models ====================

class FloridaParcel(Base):
    """Property Appraiser main data model"""
    __tablename__ = 'florida_parcels'

    # Primary Keys
    parcel_id = Column(String, primary_key=True)
    county = Column(String, primary_key=True)
    year = Column(Integer, primary_key=True, default=2025)

    # Property Address Fields (NAL)
    phy_addr1 = Column(String)  # Physical address line 1
    phy_addr2 = Column(String)  # Physical address line 2
    phy_city = Column(String)
    phy_zipcode = Column(String)

    # Owner Information (NAL)
    owner_name = Column(String)
    owner_addr1 = Column(String)
    owner_addr2 = Column(String)
    owner_city = Column(String)
    owner_state = Column(String)
    owner_zipcode = Column(String)

    # Property Values (NAV)
    just_value = Column(Float)  # Market value
    assessed_value = Column(Float)
    taxable_value = Column(Float)
    land_value = Column(Float)
    building_value = Column(Float)

    # Property Characteristics (NAP)
    year_built = Column(Integer)
    total_living_area = Column(Integer)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    land_sqft = Column(Integer)  # From LND_SQFOOT
    use_code = Column(String)
    property_type = Column(String)

    # Sales Information (SDF)
    sale_date = Column(DateTime)
    sale_price = Column(Float)
    or_book = Column(String)
    or_page = Column(String)

    # Tax Information
    millage_rate = Column(Float)
    tax_amount = Column(Float)
    exemptions = Column(String)

    # Relationships
    tax_deeds = relationship("TaxDeedSale", back_populates="property")
    sunbiz_entities = relationship("SunbizEntity", back_populates="property")
    permits = relationship("BuildingPermit", back_populates="property")
    sales_history = relationship("SalesHistory", back_populates="property")

class TaxDeedSale(Base):
    """Tax Deed Sales data model"""
    __tablename__ = 'tax_deed_sales'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, ForeignKey('florida_parcels.parcel_id'))
    td_number = Column(String, unique=True)
    certificate_number = Column(String)

    # Auction Information
    auction_date = Column(DateTime)
    auction_status = Column(String)  # upcoming, completed, cancelled

    # Financial Information
    minimum_bid = Column(Float)
    winning_bid = Column(Float)
    assessed_value = Column(Float)

    # Property Details
    property_address = Column(String)
    property_use = Column(String)

    # Relationships
    property = relationship("FloridaParcel", back_populates="tax_deeds")

class SunbizEntity(Base):
    """Sunbiz business entity data model"""
    __tablename__ = 'sunbiz_entities'

    id = Column(Integer, primary_key=True)
    entity_name = Column(String)
    document_number = Column(String, unique=True)

    # Entity Information
    status = Column(String)
    entity_type = Column(String)
    filing_date = Column(DateTime)

    # Address Information
    principal_address = Column(String)
    mailing_address = Column(String)

    # Agent Information
    registered_agent = Column(String)
    agent_address = Column(String)

    # Property Association
    parcel_id = Column(String, ForeignKey('florida_parcels.parcel_id'))
    owner_name = Column(String)

    # Officers/Directors
    officers = Column(Text)  # JSON string of officers

    # Relationships
    property = relationship("FloridaParcel", back_populates="sunbiz_entities")

class BuildingPermit(Base):
    """Building permits data model"""
    __tablename__ = 'building_permits'

    id = Column(Integer, primary_key=True)
    permit_number = Column(String, unique=True)
    parcel_id = Column(String, ForeignKey('florida_parcels.parcel_id'))

    # Permit Information
    permit_type = Column(String)
    description = Column(Text)
    issue_date = Column(DateTime)
    finalize_date = Column(DateTime)
    status = Column(String)

    # Construction Details
    contractor = Column(String)
    estimated_value = Column(Float)
    actual_value = Column(Float)

    # Relationships
    property = relationship("FloridaParcel", back_populates="permits")

class SalesHistory(Base):
    """Sales history data model"""
    __tablename__ = 'sales_history'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, ForeignKey('florida_parcels.parcel_id'))

    # Sale Information
    sale_date = Column(DateTime)
    sale_price = Column(Float)
    seller_name = Column(String)
    buyer_name = Column(String)

    # Recording Information
    or_book = Column(String)
    or_page = Column(String)
    instrument_number = Column(String)

    # Sale Type
    sale_type = Column(String)  # arms-length, foreclosure, quitclaim
    qualified = Column(Boolean)

    # Relationships
    property = relationship("FloridaParcel", back_populates="sales_history")

# ==================== UI Field Mapping Configuration ====================

@dataclass
class UIFieldMapping:
    """Maps database fields to UI components"""
    ui_component: str  # Component path (e.g., "OverviewTab.PropertyLocation")
    db_table: str
    db_field: str
    transform: Optional[str] = None  # Optional transformation function
    validation: Optional[str] = None  # Validation rule
    required: bool = True

class DataMappingSystem:
    """Comprehensive data mapping configuration"""

    def __init__(self):
        self.mappings = self._initialize_mappings()

    def _initialize_mappings(self) -> Dict[str, List[UIFieldMapping]]:
        """Define all UI to database field mappings"""
        return {
            # Overview Tab
            "OverviewTab": [
                # Property Location Section
                UIFieldMapping("PropertyLocation.address", "florida_parcels", "phy_addr1", required=True),
                UIFieldMapping("PropertyLocation.city", "florida_parcels", "phy_city"),
                UIFieldMapping("PropertyLocation.zipcode", "florida_parcels", "phy_zipcode"),
                UIFieldMapping("PropertyLocation.propertyType", "florida_parcels", "use_code",
                             transform="decode_use_code"),
                UIFieldMapping("PropertyLocation.yearBuilt", "florida_parcels", "year_built"),

                # Property Values Section
                UIFieldMapping("PropertyValues.marketValue", "florida_parcels", "just_value",
                             transform="format_currency"),
                UIFieldMapping("PropertyValues.assessedValue", "florida_parcels", "assessed_value",
                             transform="format_currency"),
                UIFieldMapping("PropertyValues.taxableValue", "florida_parcels", "taxable_value",
                             transform="format_currency"),
                UIFieldMapping("PropertyValues.landValue", "florida_parcels", "land_value",
                             transform="format_currency"),
                UIFieldMapping("PropertyValues.buildingValue", "florida_parcels", "building_value",
                             transform="format_currency"),

                # Property Details Section
                UIFieldMapping("PropertyDetails.livingArea", "florida_parcels", "total_living_area",
                             transform="format_sqft"),
                UIFieldMapping("PropertyDetails.bedrooms", "florida_parcels", "bedrooms"),
                UIFieldMapping("PropertyDetails.bathrooms", "florida_parcels", "bathrooms"),
                UIFieldMapping("PropertyDetails.lotSize", "florida_parcels", "land_sqft",
                             transform="format_sqft"),

                # Last Sale Section
                UIFieldMapping("LastSale.date", "florida_parcels", "sale_date",
                             transform="format_date"),
                UIFieldMapping("LastSale.price", "florida_parcels", "sale_price",
                             transform="format_currency"),
                UIFieldMapping("LastSale.book", "florida_parcels", "or_book"),
                UIFieldMapping("LastSale.page", "florida_parcels", "or_page"),
            ],

            # Ownership Tab
            "OwnershipTab": [
                UIFieldMapping("CurrentOwner.name", "florida_parcels", "owner_name", required=True),
                UIFieldMapping("CurrentOwner.mailingAddress", "florida_parcels", "owner_addr1"),
                UIFieldMapping("CurrentOwner.mailingCity", "florida_parcels", "owner_city"),
                UIFieldMapping("CurrentOwner.mailingState", "florida_parcels", "owner_state"),
                UIFieldMapping("CurrentOwner.mailingZip", "florida_parcels", "owner_zipcode"),

                # Sunbiz Information
                UIFieldMapping("BusinessEntity.name", "sunbiz_entities", "entity_name"),
                UIFieldMapping("BusinessEntity.status", "sunbiz_entities", "status"),
                UIFieldMapping("BusinessEntity.type", "sunbiz_entities", "entity_type"),
                UIFieldMapping("BusinessEntity.filingDate", "sunbiz_entities", "filing_date",
                             transform="format_date"),
                UIFieldMapping("BusinessEntity.principalAddress", "sunbiz_entities", "principal_address"),
                UIFieldMapping("BusinessEntity.registeredAgent", "sunbiz_entities", "registered_agent"),
                UIFieldMapping("BusinessEntity.officers", "sunbiz_entities", "officers",
                             transform="parse_json"),
            ],

            # Tax Deed Sales Tab
            "TaxDeedSalesTab": [
                UIFieldMapping("AuctionInfo.tdNumber", "tax_deed_sales", "td_number", required=True),
                UIFieldMapping("AuctionInfo.certificateNumber", "tax_deed_sales", "certificate_number"),
                UIFieldMapping("AuctionInfo.auctionDate", "tax_deed_sales", "auction_date",
                             transform="format_date"),
                UIFieldMapping("AuctionInfo.status", "tax_deed_sales", "auction_status"),

                UIFieldMapping("BidInfo.minimumBid", "tax_deed_sales", "minimum_bid",
                             transform="format_currency"),
                UIFieldMapping("BidInfo.winningBid", "tax_deed_sales", "winning_bid",
                             transform="format_currency"),
                UIFieldMapping("BidInfo.assessedValue", "tax_deed_sales", "assessed_value",
                             transform="format_currency"),

                UIFieldMapping("PropertyInfo.address", "tax_deed_sales", "property_address"),
                UIFieldMapping("PropertyInfo.use", "tax_deed_sales", "property_use"),
            ],

            # Sales History Tab
            "SalesHistoryTab": [
                UIFieldMapping("SalesList.date", "sales_history", "sale_date",
                             transform="format_date"),
                UIFieldMapping("SalesList.price", "sales_history", "sale_price",
                             transform="format_currency"),
                UIFieldMapping("SalesList.seller", "sales_history", "seller_name"),
                UIFieldMapping("SalesList.buyer", "sales_history", "buyer_name"),
                UIFieldMapping("SalesList.type", "sales_history", "sale_type"),
                UIFieldMapping("SalesList.qualified", "sales_history", "qualified",
                             transform="format_boolean"),
                UIFieldMapping("SalesList.book", "sales_history", "or_book"),
                UIFieldMapping("SalesList.page", "sales_history", "or_page"),
            ],

            # Permits Tab
            "PermitTab": [
                UIFieldMapping("PermitList.number", "building_permits", "permit_number"),
                UIFieldMapping("PermitList.type", "building_permits", "permit_type"),
                UIFieldMapping("PermitList.description", "building_permits", "description"),
                UIFieldMapping("PermitList.issueDate", "building_permits", "issue_date",
                             transform="format_date"),
                UIFieldMapping("PermitList.status", "building_permits", "status"),
                UIFieldMapping("PermitList.contractor", "building_permits", "contractor"),
                UIFieldMapping("PermitList.estimatedValue", "building_permits", "estimated_value",
                             transform="format_currency"),
            ],

            # Taxes Tab
            "TaxesTab": [
                UIFieldMapping("TaxInfo.millageRate", "florida_parcels", "millage_rate",
                             transform="format_millage"),
                UIFieldMapping("TaxInfo.taxAmount", "florida_parcels", "tax_amount",
                             transform="format_currency"),
                UIFieldMapping("TaxInfo.exemptions", "florida_parcels", "exemptions",
                             transform="parse_exemptions"),
                UIFieldMapping("TaxInfo.taxableValue", "florida_parcels", "taxable_value",
                             transform="format_currency"),
            ],
        }

    def get_mapping(self, ui_component: str) -> List[UIFieldMapping]:
        """Get mappings for a specific UI component"""
        return self.mappings.get(ui_component, [])

    def validate_mapping(self, mapping: UIFieldMapping, value: Any) -> bool:
        """Validate a value against mapping rules"""
        if mapping.required and value is None:
            return False

        if mapping.validation:
            # Apply validation rules
            if mapping.validation == "positive_number":
                return value is None or value > 0
            elif mapping.validation == "valid_date":
                return value is None or isinstance(value, datetime)
            elif mapping.validation == "non_empty_string":
                return value is None or (isinstance(value, str) and len(value) > 0)

        return True

# ==================== Playwright MCP Verification ====================

class PlaywrightUIVerifier:
    """Verify UI data placement using Playwright"""

    def __init__(self):
        self.browser = None
        self.page = None
        self.verification_results = []

    async def initialize(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Set to False to see the browser
            slow_mo=100  # Slow down for visibility
        )
        self.page = await self.browser.new_page()
        logger.info("Playwright browser initialized")

    async def navigate_to_property(self, parcel_id: str):
        """Navigate to property page"""
        url = f"http://localhost:5173/property/{parcel_id}"
        await self.page.goto(url, wait_until="networkidle")
        logger.info(f"Navigated to property: {parcel_id}")

    async def verify_field(self, selector: str, expected_value: Any) -> bool:
        """Verify a field contains expected value"""
        try:
            element = await self.page.wait_for_selector(selector, timeout=5000)
            actual_value = await element.text_content()

            # Clean and compare values
            actual_clean = str(actual_value).strip() if actual_value else ""
            expected_clean = str(expected_value).strip() if expected_value else ""

            match = actual_clean == expected_clean

            self.verification_results.append({
                "selector": selector,
                "expected": expected_clean,
                "actual": actual_clean,
                "match": match,
                "timestamp": datetime.now()
            })

            if not match:
                logger.warning(f"Mismatch at {selector}: Expected '{expected_clean}', Got '{actual_clean}'")

            return match

        except Exception as e:
            logger.error(f"Error verifying {selector}: {e}")
            self.verification_results.append({
                "selector": selector,
                "expected": str(expected_value),
                "actual": "ERROR",
                "match": False,
                "error": str(e),
                "timestamp": datetime.now()
            })
            return False

    async def verify_tab_data(self, tab_name: str, mappings: List[UIFieldMapping], data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify all fields in a tab"""
        # Click on tab
        tab_selector = f"[data-tab='{tab_name}']"
        await self.page.click(tab_selector)
        await self.page.wait_for_timeout(500)  # Wait for tab to load

        results = {
            "tab": tab_name,
            "total_fields": len(mappings),
            "verified": 0,
            "failed": 0,
            "errors": []
        }

        for mapping in mappings:
            # Construct selector based on UI component path
            selector = self._build_selector(mapping.ui_component)

            # Get expected value from data
            expected = self._get_expected_value(mapping, data)

            # Verify field
            if await self.verify_field(selector, expected):
                results["verified"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "field": mapping.ui_component,
                    "selector": selector
                })

        return results

    def _build_selector(self, ui_component: str) -> str:
        """Build CSS selector from UI component path"""
        parts = ui_component.split(".")
        if len(parts) == 2:
            section, field = parts
            return f"[data-section='{section}'] [data-field='{field}']"
        return f"[data-field='{ui_component}']"

    def _get_expected_value(self, mapping: UIFieldMapping, data: Dict[str, Any]) -> Any:
        """Get expected value from data based on mapping"""
        table_data = data.get(mapping.db_table, {})
        value = table_data.get(mapping.db_field)

        # Apply transformation if needed
        if mapping.transform and value is not None:
            value = self._apply_transform(value, mapping.transform)

        return value

    def _apply_transform(self, value: Any, transform: str) -> Any:
        """Apply transformation to value"""
        if transform == "format_currency":
            return f"${value:,.0f}" if value else "N/A"
        elif transform == "format_date":
            return value.strftime("%m/%d/%Y") if isinstance(value, datetime) else str(value)
        elif transform == "format_sqft":
            return f"{value:,} sq ft" if value else "N/A"
        elif transform == "format_boolean":
            return "Yes" if value else "No"
        elif transform == "format_millage":
            return f"{value:.3f}" if value else "N/A"
        return value

    async def take_screenshot(self, name: str):
        """Take screenshot for visual verification"""
        path = f"verification_screenshots/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=path, full_page=True)
        logger.info(f"Screenshot saved: {path}")
        return path

    async def cleanup(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()

# ==================== OpenCV Visual Verification ====================

class OpenCVVisualVerifier:
    """Visual verification using OpenCV"""

    def __init__(self):
        self.template_cache = {}

    async def verify_screenshot(self, screenshot_path: str) -> Dict[str, Any]:
        """Analyze screenshot for data presence and layout"""
        image = cv2.imread(screenshot_path)

        results = {
            "image_path": screenshot_path,
            "data_fields_detected": 0,
            "empty_fields": 0,
            "layout_score": 0,
            "anomalies": []
        }

        # Convert to grayscale for text detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect text regions
        text_regions = self._detect_text_regions(gray)
        results["data_fields_detected"] = len(text_regions)

        # Check for empty fields (areas that should have text but don't)
        empty_regions = self._detect_empty_fields(gray)
        results["empty_fields"] = len(empty_regions)

        # Analyze layout consistency
        results["layout_score"] = self._analyze_layout(image)

        # Detect visual anomalies
        anomalies = self._detect_anomalies(image)
        results["anomalies"] = anomalies

        # Generate annotated image
        annotated = self._annotate_image(image, text_regions, empty_regions)
        annotated_path = screenshot_path.replace(".png", "_annotated.png")
        cv2.imwrite(annotated_path, annotated)
        results["annotated_image"] = annotated_path

        return results

    def _detect_text_regions(self, gray_image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect regions containing text"""
        # Apply threshold to get binary image
        _, binary = cv2.threshold(gray_image, 200, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # Filter small regions
            if w > 20 and h > 10 and w < 1000 and h < 100:
                text_regions.append((x, y, w, h))

        return text_regions

    def _detect_empty_fields(self, gray_image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect fields that appear to be empty"""
        # Look for label-like text followed by empty space
        empty_regions = []

        # Use edge detection to find field boundaries
        edges = cv2.Canny(gray_image, 50, 150)

        # Find horizontal lines (field separators)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                # Check area below line for emptiness
                roi = gray_image[y1:y1+30, x1:x2]
                if roi.size > 0:
                    mean_val = np.mean(roi)
                    # If mostly white (empty), mark as empty field
                    if mean_val > 240:
                        empty_regions.append((x1, y1, x2-x1, 30))

        return empty_regions

    def _analyze_layout(self, image: np.ndarray) -> float:
        """Analyze layout consistency and alignment"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect edges
        edges = cv2.Canny(gray, 50, 150)

        # Find lines
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=50, maxLineGap=10)

        if lines is None:
            return 0

        # Analyze alignment
        horizontal_lines = []
        vertical_lines = []

        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)

            if angle < 10 or angle > 170:
                horizontal_lines.append(y1)
            elif 80 < angle < 100:
                vertical_lines.append(x1)

        # Calculate alignment score based on consistency
        h_score = self._calculate_alignment_score(horizontal_lines)
        v_score = self._calculate_alignment_score(vertical_lines)

        return (h_score + v_score) / 2

    def _calculate_alignment_score(self, positions: List[int]) -> float:
        """Calculate alignment score for a set of positions"""
        if len(positions) < 2:
            return 0

        positions = sorted(positions)
        gaps = [positions[i+1] - positions[i] for i in range(len(positions)-1)]

        if not gaps:
            return 0

        # Calculate consistency of gaps
        mean_gap = np.mean(gaps)
        std_gap = np.std(gaps)

        # Score based on consistency (lower std is better)
        consistency = 1 - (std_gap / mean_gap if mean_gap > 0 else 1)
        return max(0, min(1, consistency))

    def _detect_anomalies(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect visual anomalies in the image"""
        anomalies = []

        # Check for overlapping text
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Dilate to connect nearby text
        kernel = np.ones((3,3), np.uint8)
        dilated = cv2.dilate(binary, kernel, iterations=2)

        # Find large connected components (potential overlaps)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 10000:  # Large area might indicate overlap
                x, y, w, h = cv2.boundingRect(contour)
                anomalies.append({
                    "type": "potential_overlap",
                    "location": (x, y, w, h),
                    "severity": "medium"
                })

        # Check for truncated text (text at image edges)
        height, width = image.shape[:2]
        edge_threshold = 10

        if np.mean(binary[0:edge_threshold, :]) > 10:
            anomalies.append({
                "type": "truncated_top",
                "severity": "high"
            })

        if np.mean(binary[-edge_threshold:, :]) > 10:
            anomalies.append({
                "type": "truncated_bottom",
                "severity": "high"
            })

        return anomalies

    def _annotate_image(self, image: np.ndarray, text_regions: List, empty_regions: List) -> np.ndarray:
        """Annotate image with verification results"""
        annotated = image.copy()

        # Draw text regions in green
        for x, y, w, h in text_regions:
            cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(annotated, "DATA", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Draw empty regions in red
        for x, y, w, h in empty_regions:
            cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(annotated, "EMPTY", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        return annotated

# ==================== Main Verification System ====================

class DataVerificationSystem:
    """Main system for comprehensive data verification"""

    def __init__(self):
        self.session = SessionLocal()
        self.mapping_system = DataMappingSystem()
        self.playwright_verifier = PlaywrightUIVerifier()
        self.opencv_verifier = OpenCVVisualVerifier()
        self.verification_report = []

    async def verify_property(self, parcel_id: str) -> Dict[str, Any]:
        """Perform complete verification for a property"""
        logger.info(f"Starting verification for property: {parcel_id}")

        # 1. Fetch all data from database
        data = self._fetch_property_data(parcel_id)

        if not data:
            return {"error": f"Property {parcel_id} not found in database"}

        # 2. Initialize Playwright
        await self.playwright_verifier.initialize()

        # 3. Navigate to property page
        await self.playwright_verifier.navigate_to_property(parcel_id)

        # 4. Verify each tab
        verification_results = {
            "parcel_id": parcel_id,
            "timestamp": datetime.now(),
            "tabs": {},
            "overall_score": 0
        }

        for tab_name, mappings in self.mapping_system.mappings.items():
            logger.info(f"Verifying tab: {tab_name}")

            # Verify with Playwright
            tab_results = await self.playwright_verifier.verify_tab_data(
                tab_name, mappings, data
            )

            # Take screenshot
            screenshot_path = await self.playwright_verifier.take_screenshot(f"{parcel_id}_{tab_name}")

            # Verify with OpenCV
            visual_results = await self.opencv_verifier.verify_screenshot(screenshot_path)

            # Combine results
            tab_results["visual_verification"] = visual_results
            verification_results["tabs"][tab_name] = tab_results

        # 5. Calculate overall score
        total_fields = sum(tab["total_fields"] for tab in verification_results["tabs"].values())
        verified_fields = sum(tab["verified"] for tab in verification_results["tabs"].values())
        verification_results["overall_score"] = (verified_fields / total_fields * 100) if total_fields > 0 else 0

        # 6. Clean up
        await self.playwright_verifier.cleanup()

        # 7. Save report
        self._save_verification_report(verification_results)

        return verification_results

    def _fetch_property_data(self, parcel_id: str) -> Dict[str, Any]:
        """Fetch all property data from database"""
        data = {}

        # Fetch main property data
        property_data = self.session.query(FloridaParcel).filter_by(parcel_id=parcel_id).first()
        if property_data:
            data["florida_parcels"] = {
                key: getattr(property_data, key)
                for key in property_data.__table__.columns.keys()
            }

        # Fetch tax deed data
        tax_deeds = self.session.query(TaxDeedSale).filter_by(parcel_id=parcel_id).all()
        if tax_deeds:
            data["tax_deed_sales"] = {
                key: getattr(tax_deeds[0], key)
                for key in tax_deeds[0].__table__.columns.keys()
            } if tax_deeds else {}

        # Fetch Sunbiz data
        sunbiz = self.session.query(SunbizEntity).filter_by(parcel_id=parcel_id).first()
        if sunbiz:
            data["sunbiz_entities"] = {
                key: getattr(sunbiz, key)
                for key in sunbiz.__table__.columns.keys()
            }

        # Fetch permits
        permits = self.session.query(BuildingPermit).filter_by(parcel_id=parcel_id).all()
        if permits:
            data["building_permits"] = [
                {key: getattr(permit, key) for key in permit.__table__.columns.keys()}
                for permit in permits
            ]

        # Fetch sales history
        sales = self.session.query(SalesHistory).filter_by(parcel_id=parcel_id).all()
        if sales:
            data["sales_history"] = [
                {key: getattr(sale, key) for key in sale.__table__.columns.keys()}
                for sale in sales
            ]

        return data

    def _save_verification_report(self, results: Dict[str, Any]):
        """Save verification report to file"""
        report_path = f"verification_reports/report_{results['parcel_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("verification_reports", exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Verification report saved: {report_path}")

        # Also save summary
        summary = {
            "parcel_id": results["parcel_id"],
            "timestamp": results["timestamp"],
            "overall_score": results["overall_score"],
            "tab_scores": {
                tab: {
                    "score": (data["verified"] / data["total_fields"] * 100) if data["total_fields"] > 0 else 0,
                    "errors": len(data.get("errors", []))
                }
                for tab, data in results["tabs"].items()
            }
        }

        self.verification_report.append(summary)

    async def verify_multiple_properties(self, parcel_ids: List[str]) -> Dict[str, Any]:
        """Verify multiple properties"""
        results = {
            "total": len(parcel_ids),
            "verified": 0,
            "failed": 0,
            "properties": []
        }

        for parcel_id in parcel_ids:
            try:
                property_result = await self.verify_property(parcel_id)
                results["properties"].append(property_result)

                if property_result.get("overall_score", 0) >= 90:
                    results["verified"] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                logger.error(f"Error verifying {parcel_id}: {e}")
                results["failed"] += 1

        # Generate final report
        self._generate_final_report(results)

        return results

    def _generate_final_report(self, results: Dict[str, Any]):
        """Generate comprehensive final report"""
        report = {
            "summary": {
                "total_properties": results["total"],
                "fully_verified": results["verified"],
                "verification_issues": results["failed"],
                "success_rate": (results["verified"] / results["total"] * 100) if results["total"] > 0 else 0
            },
            "timestamp": datetime.now(),
            "details": self.verification_report
        }

        report_path = f"verification_reports/final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Final report generated: {report_path}")

        # Print summary
        print("\n" + "="*60)
        print("DATA VERIFICATION COMPLETE")
        print("="*60)
        print(f"Total Properties: {report['summary']['total_properties']}")
        print(f"Fully Verified: {report['summary']['fully_verified']}")
        print(f"Issues Found: {report['summary']['verification_issues']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print("="*60)

# ==================== Example Usage ====================

async def main():
    """Example usage of the verification system"""

    # Initialize system
    verifier = DataVerificationSystem()

    # Test properties
    test_properties = [
        "494224020080",  # Example parcel ID
        "494224020090",
        "494224020100"
    ]

    # Run verification
    results = await verifier.verify_multiple_properties(test_properties)

    return results

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("verification_screenshots", exist_ok=True)
    os.makedirs("verification_reports", exist_ok=True)

    # Run verification
    asyncio.run(main())