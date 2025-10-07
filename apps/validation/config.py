"""
Configuration for UI Field Validation System
"""
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional
import os

class ValidationConfig(BaseSettings):
    """Validation configuration"""

    # Supabase configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Firecrawl configuration
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")

    # Target website configuration
    TARGET_SITE_URL: str = os.getenv("VALIDATION_TARGET_URL", "https://www.concordbroker.com")
    STAGING_URL: str = os.getenv("VALIDATION_STAGING_URL", "https://concord-broker.vercel.app")
    CRAWL_MAX_PAGES: int = int(os.getenv("VALIDATION_MAX_PAGES", "500"))
    CRAWL_DEPTH: int = int(os.getenv("VALIDATION_CRAWL_DEPTH", "3"))

    # Output configuration
    OUTPUT_DIR: str = os.getenv("VALIDATION_OUTPUT_DIR", "./validation_reports")
    REPORT_FORMAT: str = "excel"  # excel, csv, json

    # Validation rules
    NORMALIZE_CASE: bool = True
    NORMALIZE_WHITESPACE: bool = True
    FUZZY_MATCH_THRESHOLD: int = int(os.getenv("VALIDATION_FUZZY_THRESHOLD", "85"))  # 0-100, higher = stricter

    # Label to database field mappings
    LABEL_MAPPINGS: Dict[str, str] = {
        # Property Information
        "property owner": "owner_name",
        "owner name": "owner_name",
        "owner": "owner_name",
        "property address": "phy_addr1",
        "address": "phy_addr1",
        "street address": "phy_addr1",
        "city": "phy_city",
        "zip code": "phy_zipcd",
        "zip": "phy_zipcd",
        "parcel id": "parcel_id",
        "parcel number": "parcel_id",
        "parcel #": "parcel_id",

        # Values
        "market value": "jv",
        "just value": "jv",
        "assessed value": "av_sd",
        "taxable value": "tv_sd",
        "land value": "lnd_val",
        "building value": "bldg_val",
        "sale price": "sale_prc1",
        "last sale price": "sale_prc1",
        "tax amount": "tax_amount",
        "annual taxes": "tax_amount",

        # Property details
        "year built": "act_yr_blt",
        "actual year built": "act_yr_blt",
        "effective year built": "eff_yr_blt",
        "bedrooms": "bedroom_cnt",
        "bathrooms": "bathroom_cnt",
        "living area": "tot_lvg_area",
        "square feet": "tot_lvg_area",
        "lot size": "lnd_sqfoot",
        "units": "no_res_unts",
        "number of units": "no_res_unts",

        # DOR codes
        "property use": "property_use",
        "property type": "property_use",
        "use code": "dor_uc",
        "dor code": "dor_uc",
        "land use code": "land_use_code",

        # Dates
        "sale date": "sale_date",
        "last sale date": "sale_date",

        # Exemptions
        "homestead": "homestead_exemption",
        "homestead exemption": "homestead_exemption",
        "exemptions": "other_exemptions",
        "other exemptions": "other_exemptions",

        # Additional fields
        "subdivision": "subdivision",
        "county": "county",
        "folio": "parcel_id",
        "book/page": "book_page",
        "or book": "or_book",
        "or page": "or_page",
        "cin": "cin",
        "clerk number": "cin",
    }

    # HTML patterns to extract label-field pairs
    EXTRACTION_PATTERNS: List[Dict] = [
        # Pattern 1: <label>Text</label><input value="..." />
        {
            "type": "label_input",
            "label_selector": "label",
            "field_selector": "input, select, textarea",
            "proximity": "adjacent"
        },
        # Pattern 2: <div class="field-label">Text</div><div class="field-value">Value</div>
        {
            "type": "class_based",
            "label_classes": ["label", "field-label", "property-label"],
            "value_classes": ["value", "field-value", "property-value"],
            "proximity": "sibling"
        },
        # Pattern 3: <span>Label:</span> <strong>Value</strong>
        {
            "type": "inline_text",
            "label_pattern": r"([^:]+):\s*",
            "value_tags": ["strong", "span", "div", "p"],
            "proximity": "inline"
        },
        # Pattern 4: React component data attributes
        {
            "type": "data_attributes",
            "label_attr": "data-label",
            "value_attr": "data-value"
        }
    ]

    # Tables to validate
    VALIDATION_TABLES: List[str] = [
        "florida_parcels",
        "florida_entities",
        "sunbiz_corporate"
    ]

    # Property page URL patterns
    PROPERTY_URL_PATTERNS: List[str] = [
        r"/property/(\d+)",
        r"/properties/(\d+)",
        r"/parcel/([A-Z0-9-]+)",
        r"parcel_id=([A-Z0-9-]+)"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env

# Singleton config instance
config = ValidationConfig()
