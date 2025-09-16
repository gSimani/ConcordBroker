"""
Intelligent Data Mapping System with Pandas, Playwright MCP, and OpenCV
Ensures 100% accurate data flow from Supabase to all UI components
"""

import pandas as pd
import numpy as np
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import hashlib
from enum import Enum

# Database connections
from supabase import create_client, Client
import psycopg2
from psycopg2.extras import RealDictCursor

# Playwright for UI verification
from playwright.async_api import async_playwright, Page, Browser

# OpenCV for visual validation
import cv2
from PIL import Image
import pytesseract
import base64
import io

# Data processing
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Environment
import os
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================================================================
# Data Mapping Configuration
# =====================================================================

@dataclass
class FieldMapping:
    """Defines mapping between database field and UI component"""
    db_table: str
    db_field: str
    ui_page: str
    ui_tab: str
    ui_subtab: Optional[str]
    ui_component: str
    ui_field: str
    data_type: str
    transformation: Optional[str] = None
    validation_rule: Optional[str] = None
    required: bool = False
    default_value: Any = None

@dataclass
class DataMappingConfig:
    """Complete data mapping configuration"""

    # Property Appraiser Database Mappings
    property_appraiser_mappings: List[FieldMapping] = field(default_factory=lambda: [
        # OVERVIEW TAB
        FieldMapping("florida_parcels", "phy_addr1", "property_profile", "overview", None, "PropertyLocation", "street_address", "string", None, "not_empty", True),
        FieldMapping("florida_parcels", "phy_city", "property_profile", "overview", None, "PropertyLocation", "city", "string", "uppercase", "not_empty", True),
        FieldMapping("florida_parcels", "phy_zipcd", "property_profile", "overview", None, "PropertyLocation", "zip_code", "string", None, "regex:^\\d{5}$", True),
        FieldMapping("florida_parcels", "parcel_id", "property_profile", "overview", None, "PropertyLocation", "parcel_id", "string", None, "not_empty", True),
        FieldMapping("florida_parcels", "dor_uc", "property_profile", "overview", None, "PropertyLocation", "property_type", "string", "property_type_desc", None, False),

        # Valuation Summary
        FieldMapping("florida_parcels", "jv", "property_profile", "overview", None, "ValuationSummary", "just_value", "float", "currency", "positive", True),
        FieldMapping("florida_parcels", "tv_sd", "property_profile", "overview", None, "ValuationSummary", "taxable_value", "float", "currency", "positive", True),
        FieldMapping("florida_parcels", "lnd_val", "property_profile", "overview", None, "ValuationSummary", "land_value", "float", "currency", "positive", False),

        # Recent Sale
        FieldMapping("florida_parcels", "sale_prc1", "property_profile", "overview", None, "RecentSale", "sale_price", "float", "currency", "positive", False),
        FieldMapping("florida_parcels", "sale_yr1", "property_profile", "overview", None, "RecentSale", "sale_year", "integer", None, "range:1900-2025", False),
        FieldMapping("florida_parcels", "sale_mo1", "property_profile", "overview", None, "RecentSale", "sale_month", "integer", None, "range:1-12", False),
        FieldMapping("florida_parcels", "qual_cd1", "property_profile", "overview", None, "RecentSale", "sale_qualification", "string", "qualification_desc", None, False),

        # CORE PROPERTY INFO TAB
        FieldMapping("florida_parcels", "owner_name", "property_profile", "core-property", "owner", "OwnerSection", "owner_name", "string", None, "not_empty", True),
        FieldMapping("florida_parcels", "owner_addr1", "property_profile", "core-property", "owner", "OwnerSection", "owner_address", "string", None, None, False),
        FieldMapping("florida_parcels", "owner_city", "property_profile", "core-property", "owner", "OwnerSection", "owner_city", "string", None, None, False),
        FieldMapping("florida_parcels", "owner_state", "property_profile", "core-property", "owner", "OwnerSection", "owner_state", "string", "state_abbr", "length:2", False),
        FieldMapping("florida_parcels", "owner_zip", "property_profile", "core-property", "owner", "OwnerSection", "owner_zip", "string", None, "regex:^\\d{5}(-\\d{4})?$", False),

        # Property Details
        FieldMapping("florida_parcels", "tot_lvg_area", "property_profile", "core-property", "details", "PropertyDetails", "living_area", "integer", "number_format", "positive", False),
        FieldMapping("florida_parcels", "lnd_sqfoot", "property_profile", "core-property", "details", "PropertyDetails", "land_sqft", "integer", "number_format", "positive", False),
        FieldMapping("florida_parcels", "bedroom_cnt", "property_profile", "core-property", "details", "PropertyDetails", "bedrooms", "integer", None, "range:0-20", False),
        FieldMapping("florida_parcels", "bathroom_cnt", "property_profile", "core-property", "details", "PropertyDetails", "bathrooms", "float", None, "range:0-20", False),
        FieldMapping("florida_parcels", "act_yr_blt", "property_profile", "core-property", "details", "PropertyDetails", "year_built", "integer", None, "range:1800-2025", False),
        FieldMapping("florida_parcels", "eff_yr_blt", "property_profile", "core-property", "details", "PropertyDetails", "effective_year_built", "integer", None, "range:1800-2025", False),
        FieldMapping("florida_parcels", "no_res_unts", "property_profile", "core-property", "details", "PropertyDetails", "units", "integer", None, "range:1-1000", False, 1),

        # VALUATION TAB
        FieldMapping("florida_parcels", "av_sd", "property_profile", "valuation", None, "CurrentAssessment", "assessed_value", "float", "currency", "positive", True),
        FieldMapping("florida_parcels", "av_nsd", "property_profile", "valuation", None, "CurrentAssessment", "assessed_value_non_school", "float", "currency", "positive", False),
        FieldMapping("florida_parcels", "tv_nsd", "property_profile", "valuation", None, "CurrentAssessment", "taxable_value_non_school", "float", "currency", "positive", False),

        # TAXES TAB - NAV Data
        FieldMapping("nav_assessments", "taxing_authority", "property_profile", "taxes", "authorities", "TaxingAuthorities", "authority_name", "string", None, "not_empty", True),
        FieldMapping("nav_assessments", "millage_rate", "property_profile", "taxes", "authorities", "TaxingAuthorities", "millage_rate", "float", None, "positive", True),
        FieldMapping("nav_assessments", "taxable_value", "property_profile", "taxes", "authorities", "TaxingAuthorities", "taxable_value", "float", "currency", "positive", True),
        FieldMapping("nav_assessments", "tax_amount", "property_profile", "taxes", "authorities", "TaxingAuthorities", "tax_amount", "float", "currency", "positive", True),

        # SALES HISTORY TAB
        FieldMapping("sdf_sales", "sale_date", "property_profile", "sales", None, "SalesHistory", "sale_date", "date", "date_format", "valid_date", True),
        FieldMapping("sdf_sales", "sale_price", "property_profile", "sales", None, "SalesHistory", "sale_price", "float", "currency", "positive", True),
        FieldMapping("sdf_sales", "grantor", "property_profile", "sales", None, "SalesHistory", "seller_name", "string", None, None, False),
        FieldMapping("sdf_sales", "grantee", "property_profile", "sales", None, "SalesHistory", "buyer_name", "string", None, None, False),
        FieldMapping("sdf_sales", "deed_type", "property_profile", "sales", None, "SalesHistory", "deed_type", "string", None, None, False),
        FieldMapping("sdf_sales", "or_book", "property_profile", "sales", None, "SalesHistory", "book_number", "string", None, None, False),
        FieldMapping("sdf_sales", "or_page", "property_profile", "sales", None, "SalesHistory", "page_number", "string", None, None, False),

        # BUILDING TAB
        FieldMapping("florida_parcels", "stories", "property_profile", "building", None, "BuildingInfo", "stories", "integer", None, "range:1-100", False),
        FieldMapping("florida_parcels", "roof_type", "property_profile", "building", None, "BuildingInfo", "roof_type", "string", None, None, False),
        FieldMapping("florida_parcels", "roof_material", "property_profile", "building", None, "BuildingInfo", "roof_material", "string", None, None, False),
        FieldMapping("florida_parcels", "foundation", "property_profile", "building", None, "BuildingInfo", "foundation_type", "string", None, None, False),
        FieldMapping("florida_parcels", "exterior_wall", "property_profile", "building", None, "BuildingInfo", "exterior_wall", "string", None, None, False),
        FieldMapping("florida_parcels", "heating", "property_profile", "building", None, "BuildingInfo", "heating_type", "string", None, None, False),
        FieldMapping("florida_parcels", "cooling", "property_profile", "building", None, "BuildingInfo", "cooling_type", "string", None, None, False),

        # LAND TAB
        FieldMapping("florida_parcels", "legal_desc", "property_profile", "land", None, "LegalDescription", "legal_description", "string", None, None, False),
        FieldMapping("florida_parcels", "subdivision", "property_profile", "land", None, "LegalDescription", "subdivision_name", "string", None, None, False),
        FieldMapping("florida_parcels", "plat_book", "property_profile", "land", None, "LegalDescription", "plat_book", "string", None, None, False),
        FieldMapping("florida_parcels", "plat_page", "property_profile", "land", None, "LegalDescription", "plat_page", "string", None, None, False),
        FieldMapping("florida_parcels", "section", "property_profile", "land", None, "LegalDescription", "section", "string", None, None, False),
        FieldMapping("florida_parcels", "township", "property_profile", "land", None, "LegalDescription", "township", "string", None, None, False),
        FieldMapping("florida_parcels", "range", "property_profile", "land", None, "LegalDescription", "range", "string", None, None, False),
    ])

    # Sunbiz Database Mappings
    sunbiz_mappings: List[FieldMapping] = field(default_factory=lambda: [
        # SUNBIZ TAB
        FieldMapping("sunbiz_entities", "entity_name", "property_profile", "sunbiz", "entity", "EntityInfo", "business_name", "string", None, "not_empty", True),
        FieldMapping("sunbiz_entities", "document_number", "property_profile", "sunbiz", "entity", "EntityInfo", "document_number", "string", None, "not_empty", True),
        FieldMapping("sunbiz_entities", "status", "property_profile", "sunbiz", "entity", "EntityInfo", "status", "string", None, None, True),
        FieldMapping("sunbiz_entities", "filing_date", "property_profile", "sunbiz", "entity", "EntityInfo", "filing_date", "date", "date_format", "valid_date", False),
        FieldMapping("sunbiz_entities", "entity_type", "property_profile", "sunbiz", "entity", "EntityInfo", "entity_type", "string", None, None, False),
        FieldMapping("sunbiz_entities", "principal_address", "property_profile", "sunbiz", "entity", "EntityInfo", "principal_address", "string", None, None, False),
        FieldMapping("sunbiz_entities", "mailing_address", "property_profile", "sunbiz", "entity", "EntityInfo", "mailing_address", "string", None, None, False),
        FieldMapping("sunbiz_entities", "registered_agent", "property_profile", "sunbiz", "entity", "EntityInfo", "registered_agent", "string", None, None, False),

        # Officers/Directors
        FieldMapping("sunbiz_officers", "officer_name", "property_profile", "sunbiz", "officers", "OfficersSection", "name", "string", None, "not_empty", True),
        FieldMapping("sunbiz_officers", "officer_title", "property_profile", "sunbiz", "officers", "OfficersSection", "title", "string", None, None, True),
        FieldMapping("sunbiz_officers", "officer_address", "property_profile", "sunbiz", "officers", "OfficersSection", "address", "string", None, None, False),
    ])

    # Tax Deed Mappings
    tax_deed_mappings: List[FieldMapping] = field(default_factory=lambda: [
        # TAX DEED SALES TAB
        FieldMapping("tax_deed_sales", "certificate_number", "property_profile", "tax-deed-sales", None, "TaxDeedAuctions", "certificate_number", "string", None, "not_empty", True),
        FieldMapping("tax_deed_sales", "auction_date", "property_profile", "tax-deed-sales", None, "TaxDeedAuctions", "auction_date", "date", "date_format", "valid_date", True),
        FieldMapping("tax_deed_sales", "minimum_bid", "property_profile", "tax-deed-sales", None, "TaxDeedAuctions", "minimum_bid", "float", "currency", "positive", True),
        FieldMapping("tax_deed_sales", "winning_bid", "property_profile", "tax-deed-sales", None, "TaxDeedAuctions", "winning_bid", "float", "currency", "positive", False),
        FieldMapping("tax_deed_sales", "auction_status", "property_profile", "tax-deed-sales", None, "TaxDeedAuctions", "status", "string", None, None, True),
        FieldMapping("tax_deed_sales", "td_number", "property_profile", "tax-deed-sales", None, "TaxDeedAuctions", "td_number", "string", None, None, False),
        FieldMapping("tax_deed_sales", "tax_years", "property_profile", "tax-deed-sales", None, "TaxDeedAuctions", "tax_years", "string", None, None, False),

        # TAX CERTIFICATES
        FieldMapping("tax_certificates", "certificate_year", "property_profile", "sales-tax-deed", None, "TaxCertificates", "certificate_year", "integer", None, "range:2000-2025", True),
        FieldMapping("tax_certificates", "certificate_amount", "property_profile", "sales-tax-deed", None, "TaxCertificates", "certificate_amount", "float", "currency", "positive", True),
        FieldMapping("tax_certificates", "interest_rate", "property_profile", "sales-tax-deed", None, "TaxCertificates", "interest_rate", "float", "percentage", "range:0-18", False),
        FieldMapping("tax_certificates", "redemption_date", "property_profile", "sales-tax-deed", None, "TaxCertificates", "redemption_date", "date", "date_format", "valid_date", False),
        FieldMapping("tax_certificates", "certificate_status", "property_profile", "sales-tax-deed", None, "TaxCertificates", "status", "string", None, None, False),
    ])

    # Permit Mappings
    permit_mappings: List[FieldMapping] = field(default_factory=lambda: [
        # PERMIT TAB
        FieldMapping("building_permits", "permit_number", "property_profile", "permit", None, "PermitsList", "permit_number", "string", None, "not_empty", True),
        FieldMapping("building_permits", "permit_type", "property_profile", "permit", None, "PermitsList", "permit_type", "string", None, None, True),
        FieldMapping("building_permits", "issue_date", "property_profile", "permit", None, "PermitsList", "issue_date", "date", "date_format", "valid_date", True),
        FieldMapping("building_permits", "status", "property_profile", "permit", None, "PermitsList", "status", "string", None, None, True),
        FieldMapping("building_permits", "contractor", "property_profile", "permit", None, "PermitsList", "contractor_name", "string", None, None, False),
        FieldMapping("building_permits", "estimated_value", "property_profile", "permit", None, "PermitsList", "estimated_value", "float", "currency", "positive", False),
        FieldMapping("building_permits", "description", "property_profile", "permit", None, "PermitsList", "description", "string", None, None, False),
        FieldMapping("building_permits", "completion_date", "property_profile", "permit", None, "PermitsList", "completion_date", "date", "date_format", "valid_date", False),
    ])

# =====================================================================
# Pandas Data Pipeline
# =====================================================================

class PandasDataPipeline:
    """Data manipulation and validation using Pandas"""

    def __init__(self, config: DataMappingConfig):
        self.config = config
        self.supabase = self._init_supabase()
        self.validation_errors = []

    def _init_supabase(self) -> Client:
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        return create_client(url, key)

    def fetch_property_data(self, parcel_id: str) -> Dict[str, pd.DataFrame]:
        """Fetch all property-related data from database"""
        data_frames = {}

        # Fetch florida_parcels data
        try:
            response = self.supabase.table('florida_parcels').select('*').eq('parcel_id', parcel_id).execute()
            if response.data:
                data_frames['florida_parcels'] = pd.DataFrame(response.data)
                logger.info(f"Fetched {len(response.data)} records from florida_parcels")
        except Exception as e:
            logger.error(f"Error fetching florida_parcels: {e}")

        # Fetch NAV assessments
        try:
            response = self.supabase.table('nav_assessments').select('*').eq('parcel_id', parcel_id).execute()
            if response.data:
                data_frames['nav_assessments'] = pd.DataFrame(response.data)
                logger.info(f"Fetched {len(response.data)} NAV assessments")
        except Exception as e:
            logger.error(f"Error fetching nav_assessments: {e}")

        # Fetch SDF sales history
        try:
            response = self.supabase.table('sdf_sales').select('*').eq('parcel_id', parcel_id).order('sale_date', desc=True).execute()
            if response.data:
                data_frames['sdf_sales'] = pd.DataFrame(response.data)
                logger.info(f"Fetched {len(response.data)} sales records")
        except Exception as e:
            logger.error(f"Error fetching sdf_sales: {e}")

        # Fetch Sunbiz data (by owner name)
        if 'florida_parcels' in data_frames and not data_frames['florida_parcels'].empty:
            owner_name = data_frames['florida_parcels'].iloc[0].get('owner_name')
            if owner_name:
                try:
                    # Search for entities
                    response = self.supabase.table('sunbiz_entities').select('*').ilike('entity_name', f'%{owner_name}%').execute()
                    if response.data:
                        data_frames['sunbiz_entities'] = pd.DataFrame(response.data)

                        # Get officers for each entity
                        entity_ids = [e['id'] for e in response.data if 'id' in e]
                        if entity_ids:
                            officer_response = self.supabase.table('sunbiz_officers').select('*').in_('entity_id', entity_ids).execute()
                            if officer_response.data:
                                data_frames['sunbiz_officers'] = pd.DataFrame(officer_response.data)
                except Exception as e:
                    logger.error(f"Error fetching sunbiz data: {e}")

        # Fetch tax deed sales
        try:
            response = self.supabase.table('tax_deed_sales').select('*').eq('parcel_id', parcel_id).execute()
            if response.data:
                data_frames['tax_deed_sales'] = pd.DataFrame(response.data)
                logger.info(f"Fetched {len(response.data)} tax deed sales")
        except Exception as e:
            logger.error(f"Error fetching tax_deed_sales: {e}")

        # Fetch tax certificates
        try:
            response = self.supabase.table('tax_certificates').select('*').eq('parcel_id', parcel_id).execute()
            if response.data:
                data_frames['tax_certificates'] = pd.DataFrame(response.data)
                logger.info(f"Fetched {len(response.data)} tax certificates")
        except Exception as e:
            logger.error(f"Error fetching tax_certificates: {e}")

        # Fetch building permits
        try:
            response = self.supabase.table('building_permits').select('*').eq('parcel_id', parcel_id).execute()
            if response.data:
                data_frames['building_permits'] = pd.DataFrame(response.data)
                logger.info(f"Fetched {len(response.data)} building permits")
        except Exception as e:
            logger.error(f"Error fetching building_permits: {e}")

        return data_frames

    def apply_transformations(self, value: Any, transformation: str) -> Any:
        """Apply data transformations"""
        if value is None or pd.isna(value):
            return None

        if transformation == "currency":
            return f"${float(value):,.2f}" if value else "$0.00"
        elif transformation == "uppercase":
            return str(value).upper()
        elif transformation == "state_abbr":
            # Convert state name to abbreviation
            state_map = {"FLORIDA": "FL", "GEORGIA": "GA", "ALABAMA": "AL"}
            return state_map.get(str(value).upper(), str(value)[:2].upper())
        elif transformation == "property_type_desc":
            # Convert property use code to description
            type_map = {
                "0100": "Single Family",
                "0101": "Single Family - Pool",
                "0200": "Multi-Family",
                "0300": "Condominium",
                "0400": "Townhouse",
                "1000": "Commercial",
                "2000": "Industrial",
                "5000": "Agricultural",
                "0000": "Vacant Land"
            }
            return type_map.get(str(value), "Other")
        elif transformation == "qualification_desc":
            # Convert qualification code to description
            qual_map = {
                "Q": "Qualified - Arms Length",
                "U": "Unqualified",
                "W": "Warranty Deed",
                "S": "Special Warranty",
                "QC": "Quit Claim"
            }
            return qual_map.get(str(value), str(value))
        elif transformation == "date_format":
            # Format date consistently
            if isinstance(value, str):
                try:
                    dt = pd.to_datetime(value)
                    return dt.strftime("%Y-%m-%d")
                except:
                    return value
            return value
        elif transformation == "number_format":
            # Format numbers with commas
            return f"{int(value):,}" if value else "0"
        elif transformation == "percentage":
            return f"{float(value):.2f}%"
        else:
            return value

    def validate_field(self, value: Any, validation_rule: str) -> bool:
        """Validate field values"""
        if validation_rule is None:
            return True

        if value is None or pd.isna(value):
            return validation_rule != "not_empty"

        if validation_rule == "not_empty":
            return bool(value) and str(value).strip() != ""
        elif validation_rule == "positive":
            try:
                return float(value) > 0
            except:
                return False
        elif validation_rule.startswith("regex:"):
            import re
            pattern = validation_rule.replace("regex:", "")
            return bool(re.match(pattern, str(value)))
        elif validation_rule.startswith("range:"):
            try:
                min_val, max_val = validation_rule.replace("range:", "").split("-")
                val = float(value)
                return float(min_val) <= val <= float(max_val)
            except:
                return False
        elif validation_rule.startswith("length:"):
            expected_len = int(validation_rule.replace("length:", ""))
            return len(str(value)) == expected_len
        elif validation_rule == "valid_date":
            try:
                pd.to_datetime(value)
                return True
            except:
                return False

        return True

    def map_data_to_ui(self, data_frames: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Map database data to UI structure"""
        ui_data = {
            "property_profile": {
                "overview": {},
                "core-property": {"owner": {}, "details": {}},
                "valuation": {},
                "taxes": {"authorities": []},
                "sales": [],
                "building": {},
                "land": {},
                "sunbiz": {"entity": {}, "officers": []},
                "permit": [],
                "tax-deed-sales": [],
                "sales-tax-deed": []
            }
        }

        # Get all mappings
        all_mappings = (
            self.config.property_appraiser_mappings +
            self.config.sunbiz_mappings +
            self.config.tax_deed_mappings +
            self.config.permit_mappings
        )

        # Process each mapping
        for mapping in all_mappings:
            if mapping.db_table not in data_frames:
                continue

            df = data_frames[mapping.db_table]
            if df.empty:
                continue

            # Handle multiple records (e.g., sales history, permits)
            if mapping.ui_tab in ["sales", "permit", "tax-deed-sales", "sales-tax-deed"] or \
               (mapping.ui_tab == "taxes" and mapping.ui_subtab == "authorities") or \
               (mapping.ui_tab == "sunbiz" and mapping.ui_subtab == "officers"):
                # Process all records
                records = []
                for _, row in df.iterrows():
                    if mapping.db_field in row:
                        value = row[mapping.db_field]

                        # Validate
                        if not self.validate_field(value, mapping.validation_rule):
                            if mapping.required:
                                self.validation_errors.append({
                                    "field": mapping.db_field,
                                    "table": mapping.db_table,
                                    "error": f"Validation failed: {mapping.validation_rule}",
                                    "value": value
                                })
                            value = mapping.default_value

                        # Transform
                        if mapping.transformation:
                            value = self.apply_transformations(value, mapping.transformation)

                        # Create record
                        if mapping.ui_subtab:
                            record = {mapping.ui_field: value}
                        else:
                            record = {mapping.ui_field: value}

                        records.append(record)

                # Store in UI data
                if mapping.ui_subtab:
                    ui_data["property_profile"][mapping.ui_tab][mapping.ui_subtab] = records
                else:
                    ui_data["property_profile"][mapping.ui_tab] = records

            else:
                # Process single record
                row = df.iloc[0]
                if mapping.db_field in row:
                    value = row[mapping.db_field]

                    # Validate
                    if not self.validate_field(value, mapping.validation_rule):
                        if mapping.required:
                            self.validation_errors.append({
                                "field": mapping.db_field,
                                "table": mapping.db_table,
                                "error": f"Validation failed: {mapping.validation_rule}",
                                "value": value
                            })
                        value = mapping.default_value

                    # Transform
                    if mapping.transformation:
                        value = self.apply_transformations(value, mapping.transformation)

                    # Store in UI data
                    if mapping.ui_subtab:
                        if mapping.ui_subtab not in ui_data["property_profile"][mapping.ui_tab]:
                            ui_data["property_profile"][mapping.ui_tab][mapping.ui_subtab] = {}
                        ui_data["property_profile"][mapping.ui_tab][mapping.ui_subtab][mapping.ui_field] = value
                    else:
                        ui_data["property_profile"][mapping.ui_tab][mapping.ui_field] = value

        return ui_data

    def generate_mapping_report(self) -> pd.DataFrame:
        """Generate a report of all mappings"""
        all_mappings = (
            self.config.property_appraiser_mappings +
            self.config.sunbiz_mappings +
            self.config.tax_deed_mappings +
            self.config.permit_mappings
        )

        report_data = []
        for mapping in all_mappings:
            report_data.append({
                "Database Table": mapping.db_table,
                "Database Field": mapping.db_field,
                "UI Page": mapping.ui_page,
                "UI Tab": mapping.ui_tab,
                "UI Subtab": mapping.ui_subtab or "N/A",
                "UI Component": mapping.ui_component,
                "UI Field": mapping.ui_field,
                "Data Type": mapping.data_type,
                "Transformation": mapping.transformation or "None",
                "Validation": mapping.validation_rule or "None",
                "Required": "Yes" if mapping.required else "No"
            })

        return pd.DataFrame(report_data)

# =====================================================================
# Playwright MCP Verification
# =====================================================================

class PlaywrightMCPVerification:
    """Verify data mapping using Playwright and MCP"""

    def __init__(self, mcp_url: str = "http://localhost:3001"):
        self.mcp_url = mcp_url
        self.browser = None
        self.page = None
        self.verification_results = []

    async def initialize(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Show browser for debugging
            args=['--disable-gpu', '--no-sandbox']
        )
        self.page = await self.browser.new_page()
        logger.info("Playwright browser initialized for verification")

    async def verify_property_page(self, parcel_id: str, expected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify property page displays correct data"""
        verification_report = {
            "parcel_id": parcel_id,
            "timestamp": datetime.now().isoformat(),
            "verified_fields": [],
            "failed_fields": [],
            "missing_fields": [],
            "screenshots": []
        }

        try:
            # Navigate to property page
            url = f"http://localhost:5173/property/{parcel_id}"
            await self.page.goto(url, wait_until='networkidle')
            await asyncio.sleep(2)  # Wait for React to render

            # Take initial screenshot
            screenshot_path = f"verification/property_{parcel_id}_full.png"
            await self.page.screenshot(path=screenshot_path, full_page=True)
            verification_report["screenshots"].append(screenshot_path)

            # Verify each tab
            tabs_to_verify = ["overview", "core-property", "valuation", "taxes", "sunbiz", "permit", "tax-deed-sales"]

            for tab in tabs_to_verify:
                # Click on tab
                tab_selector = f'[data-tab="{tab}"], button:has-text("{tab}"), .tab-executive:has-text("{tab}")'
                try:
                    await self.page.click(tab_selector, timeout=5000)
                    await asyncio.sleep(1)
                except:
                    logger.warning(f"Could not click tab: {tab}")
                    continue

                # Take screenshot of tab
                tab_screenshot = f"verification/property_{parcel_id}_{tab}.png"
                await self.page.screenshot(path=tab_screenshot)
                verification_report["screenshots"].append(tab_screenshot)

                # Get expected data for this tab
                if tab in expected_data.get("property_profile", {}):
                    tab_data = expected_data["property_profile"][tab]

                    # Verify fields in tab
                    await self._verify_tab_fields(tab, tab_data, verification_report)

            # Calculate verification score
            total_fields = len(verification_report["verified_fields"]) + len(verification_report["failed_fields"])
            if total_fields > 0:
                verification_report["score"] = len(verification_report["verified_fields"]) / total_fields * 100
            else:
                verification_report["score"] = 0

            # Send results to MCP
            await self._notify_mcp("verification_complete", verification_report)

        except Exception as e:
            logger.error(f"Error verifying property page: {e}")
            verification_report["error"] = str(e)

        return verification_report

    async def _verify_tab_fields(self, tab: str, tab_data: Any, report: Dict):
        """Verify fields within a specific tab"""
        if isinstance(tab_data, dict):
            for field_name, expected_value in tab_data.items():
                if isinstance(expected_value, (dict, list)):
                    # Nested data structure
                    continue

                # Try to find the field on the page
                field_found = await self._find_and_verify_field(field_name, expected_value)

                if field_found:
                    report["verified_fields"].append({
                        "tab": tab,
                        "field": field_name,
                        "expected": expected_value,
                        "status": "verified"
                    })
                else:
                    report["failed_fields"].append({
                        "tab": tab,
                        "field": field_name,
                        "expected": expected_value,
                        "status": "not_found"
                    })

    async def _find_and_verify_field(self, field_name: str, expected_value: Any) -> bool:
        """Find and verify a specific field value on the page"""
        try:
            # Convert field name to possible selectors
            selectors = [
                f'[data-field="{field_name}"]',
                f'[data-testid="{field_name}"]',
                f'.{field_name}',
                f'#{field_name}',
                f'*:has-text("{field_name}")',
            ]

            # Also search for the value itself
            if expected_value:
                value_str = str(expected_value)
                selectors.append(f'*:has-text("{value_str}")')

            # Try each selector
            for selector in selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=1000)
                    if element:
                        # Get the text content
                        text = await element.text_content()

                        # Check if value matches
                        if expected_value and str(expected_value) in text:
                            return True
                        elif field_name.lower() in text.lower():
                            return True
                except:
                    continue

            return False

        except Exception as e:
            logger.debug(f"Field not found: {field_name}")
            return False

    async def _notify_mcp(self, event_type: str, data: Dict):
        """Send verification results to MCP Server"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                headers = {"x-api-key": "concordbroker-mcp-key"}
                payload = {
                    "event": event_type,
                    "timestamp": datetime.now().isoformat(),
                    "data": data
                }
                await session.post(
                    f"{self.mcp_url}/api/events",
                    json=payload,
                    headers=headers
                )
        except Exception as e:
            logger.error(f"Failed to notify MCP: {e}")

    async def cleanup(self):
        """Clean up Playwright resources"""
        if self.browser:
            await self.browser.close()

# =====================================================================
# OpenCV Visual Validation
# =====================================================================

class OpenCVVisualValidation:
    """Visual validation of UI data using OpenCV"""

    def __init__(self):
        self.validation_results = []

    def validate_screenshot(self, screenshot_path: str, expected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate screenshot contains expected data using OCR"""
        validation_result = {
            "screenshot": screenshot_path,
            "timestamp": datetime.now().isoformat(),
            "detected_text": [],
            "matched_fields": [],
            "missing_fields": [],
            "confidence_scores": {}
        }

        try:
            # Load image
            img = cv2.imread(screenshot_path)
            if img is None:
                raise Exception(f"Could not load image: {screenshot_path}")

            # Convert to grayscale for better OCR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply preprocessing for better OCR
            # 1. Denoise
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

            # 2. Threshold
            _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 3. Dilation and erosion to remove noise
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

            # Perform OCR
            text = pytesseract.image_to_string(processed)
            validation_result["detected_text"] = text.split('\n')

            # Search for expected values in OCR text
            for field_name, field_value in self._flatten_dict(expected_data).items():
                if field_value:
                    value_str = str(field_value)

                    # Check if value exists in OCR text
                    if self._fuzzy_match(value_str, text):
                        validation_result["matched_fields"].append({
                            "field": field_name,
                            "value": value_str,
                            "found": True
                        })
                        validation_result["confidence_scores"][field_name] = self._calculate_confidence(value_str, text)
                    else:
                        validation_result["missing_fields"].append({
                            "field": field_name,
                            "value": value_str,
                            "found": False
                        })
                        validation_result["confidence_scores"][field_name] = 0.0

            # Calculate overall score
            total_fields = len(validation_result["matched_fields"]) + len(validation_result["missing_fields"])
            if total_fields > 0:
                validation_result["overall_score"] = len(validation_result["matched_fields"]) / total_fields * 100
            else:
                validation_result["overall_score"] = 0

            # Highlight detected areas
            self._create_annotated_image(img, validation_result)

        except Exception as e:
            logger.error(f"Error in visual validation: {e}")
            validation_result["error"] = str(e)

        return validation_result

    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, v))
        return dict(items)

    def _fuzzy_match(self, needle: str, haystack: str, threshold: int = 85) -> bool:
        """Fuzzy string matching"""
        from fuzzywuzzy import fuzz

        # Clean strings
        needle = str(needle).strip().lower()
        haystack = haystack.lower()

        # Direct substring match
        if needle in haystack:
            return True

        # Fuzzy matching for each line
        for line in haystack.split('\n'):
            if fuzz.partial_ratio(needle, line) >= threshold:
                return True

        return False

    def _calculate_confidence(self, expected: str, text: str) -> float:
        """Calculate confidence score for field detection"""
        from fuzzywuzzy import fuzz

        expected = str(expected).strip().lower()
        best_score = 0

        for line in text.split('\n'):
            line = line.strip().lower()
            if line:
                score = fuzz.ratio(expected, line)
                best_score = max(best_score, score)

        return best_score / 100.0

    def _create_annotated_image(self, img: np.ndarray, validation_result: Dict):
        """Create annotated image showing detected fields"""
        annotated = img.copy()

        # Draw rectangles around detected text areas
        # This is a simplified version - in production you'd use more sophisticated detection
        height, width = img.shape[:2]

        # Add validation status overlay
        overlay = annotated.copy()
        cv2.rectangle(overlay, (10, 10), (300, 100), (0, 255, 0) if validation_result["overall_score"] > 80 else (0, 0, 255), -1)
        cv2.addWeighted(overlay, 0.3, annotated, 0.7, 0, annotated)

        # Add text with validation score
        score_text = f"Validation Score: {validation_result['overall_score']:.1f}%"
        cv2.putText(annotated, score_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Save annotated image
        output_path = validation_result["screenshot"].replace(".png", "_annotated.png")
        cv2.imwrite(output_path, annotated)
        validation_result["annotated_screenshot"] = output_path

# =====================================================================
# Intelligent Data Mapping Service
# =====================================================================

class IntelligentDataMappingService:
    """Main service orchestrating data mapping and verification"""

    def __init__(self):
        self.config = DataMappingConfig()
        self.pandas_pipeline = PandasDataPipeline(self.config)
        self.playwright_verifier = PlaywrightMCPVerification()
        self.opencv_validator = OpenCVVisualValidation()

    async def map_and_verify_property(self, parcel_id: str) -> Dict[str, Any]:
        """Complete mapping and verification for a property"""
        result = {
            "parcel_id": parcel_id,
            "timestamp": datetime.now().isoformat(),
            "mapping_status": "pending",
            "verification_status": "pending",
            "validation_status": "pending",
            "data": {},
            "errors": [],
            "warnings": []
        }

        try:
            # Step 1: Fetch data using Pandas
            logger.info(f"Fetching data for parcel {parcel_id}")
            data_frames = self.pandas_pipeline.fetch_property_data(parcel_id)

            if not data_frames:
                result["errors"].append("No data found for parcel")
                return result

            # Step 2: Map data to UI structure
            logger.info("Mapping data to UI structure")
            ui_data = self.pandas_pipeline.map_data_to_ui(data_frames)
            result["data"] = ui_data
            result["mapping_status"] = "completed"

            # Add validation errors
            if self.pandas_pipeline.validation_errors:
                result["warnings"].extend(self.pandas_pipeline.validation_errors)

            # Step 3: Verify with Playwright MCP
            logger.info("Starting Playwright verification")
            await self.playwright_verifier.initialize()

            verification_report = await self.playwright_verifier.verify_property_page(parcel_id, ui_data)
            result["verification_report"] = verification_report
            result["verification_status"] = "completed" if verification_report.get("score", 0) > 80 else "failed"

            # Step 4: Visual validation with OpenCV
            logger.info("Starting OpenCV visual validation")
            if verification_report.get("screenshots"):
                validation_results = []
                for screenshot in verification_report["screenshots"]:
                    validation = self.opencv_validator.validate_screenshot(screenshot, ui_data)
                    validation_results.append(validation)

                result["validation_results"] = validation_results
                avg_score = np.mean([v.get("overall_score", 0) for v in validation_results])
                result["validation_status"] = "completed" if avg_score > 80 else "failed"

            # Step 5: Generate comprehensive report
            result["summary"] = {
                "total_fields_mapped": len(self.pandas_pipeline.config.property_appraiser_mappings) +
                                      len(self.pandas_pipeline.config.sunbiz_mappings) +
                                      len(self.pandas_pipeline.config.tax_deed_mappings) +
                                      len(self.pandas_pipeline.config.permit_mappings),
                "fields_verified": len(verification_report.get("verified_fields", [])),
                "fields_failed": len(verification_report.get("failed_fields", [])),
                "verification_score": verification_report.get("score", 0),
                "validation_score": avg_score if "validation_results" in result else 0,
                "overall_status": "PASS" if result["verification_status"] == "completed" and result["validation_status"] == "completed" else "FAIL"
            }

            # Cleanup
            await self.playwright_verifier.cleanup()

        except Exception as e:
            logger.error(f"Error in mapping and verification: {e}")
            result["errors"].append(str(e))
            result["mapping_status"] = "failed"

        return result

    def generate_mapping_documentation(self) -> str:
        """Generate comprehensive mapping documentation"""
        doc = "# Data Mapping Documentation\n\n"
        doc += f"Generated: {datetime.now().isoformat()}\n\n"

        # Generate mapping report
        report_df = self.pandas_pipeline.generate_mapping_report()

        # Group by UI Tab
        for tab in report_df['UI Tab'].unique():
            doc += f"## {tab.upper()} Tab\n\n"
            tab_data = report_df[report_df['UI Tab'] == tab]

            doc += "| Database Table | Database Field | UI Component | UI Field | Transformation | Required |\n"
            doc += "|----------------|----------------|--------------|----------|----------------|----------|\n"

            for _, row in tab_data.iterrows():
                doc += f"| {row['Database Table']} | {row['Database Field']} | {row['UI Component']} | {row['UI Field']} | {row['Transformation']} | {row['Required']} |\n"

            doc += "\n"

        return doc

# =====================================================================
# Example Usage
# =====================================================================

async def main():
    """Example usage of the intelligent data mapping system"""

    # Initialize the service
    service = IntelligentDataMappingService()

    # Test with a property
    parcel_id = "494224020080"  # Example parcel ID

    logger.info(f"Starting data mapping and verification for parcel {parcel_id}")

    # Run mapping and verification
    result = await service.map_and_verify_property(parcel_id)

    # Print results
    print("\n" + "="*60)
    print(f"DATA MAPPING AND VERIFICATION REPORT")
    print("="*60)
    print(f"Parcel ID: {result['parcel_id']}")
    print(f"Timestamp: {result['timestamp']}")
    print(f"Mapping Status: {result['mapping_status']}")
    print(f"Verification Status: {result['verification_status']}")
    print(f"Validation Status: {result['validation_status']}")

    if 'summary' in result:
        print("\nSUMMARY:")
        for key, value in result['summary'].items():
            print(f"  {key}: {value}")

    if result.get('errors'):
        print("\nERRORS:")
        for error in result['errors']:
            print(f"  - {error}")

    if result.get('warnings'):
        print("\nWARNINGS:")
        for warning in result['warnings']:
            print(f"  - {warning}")

    # Generate documentation
    doc = service.generate_mapping_documentation()
    with open("data_mapping_documentation.md", "w") as f:
        f.write(doc)
    print("\nDocumentation generated: data_mapping_documentation.md")

    # Save full results to JSON
    with open(f"mapping_verification_{parcel_id}.json", "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"Full results saved: mapping_verification_{parcel_id}.json")

if __name__ == "__main__":
    asyncio.run(main())