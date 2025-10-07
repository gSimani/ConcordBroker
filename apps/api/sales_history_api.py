"""
Sales History API endpoint using property_sales_history table
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from supabase import create_client, Client
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pmispwtdngkcmsrsjwbp.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

@router.get("/api/properties/{parcel_id}/sales")
async def get_property_sales(parcel_id: str):
    """Get complete sales history for a property"""
    try:
        logger.info(f"Fetching sales history for parcel: {parcel_id}")

        # Try property_sales_history table first (has 95K+ records)
        result = supabase.table('property_sales_history') \
            .select('*') \
            .eq('parcel_id', parcel_id) \
            .gte('sale_price', 1000) \
            .order('sale_date', desc=True) \
            .execute()

        sales_records = []

        if result.data and len(result.data) > 0:
            logger.info(f"Found {len(result.data)} sales in property_sales_history for {parcel_id}")

            for sale in result.data:
                # Map fields from property_sales_history table
                sales_records.append({
                    'sale_date': sale.get('sale_date'),
                    'sale_price': safe_float(sale.get('sale_price')),
                    'sale_year': sale.get('sale_year'),
                    'sale_month': sale.get('sale_month'),
                    'qualified_sale': sale.get('qualified_sale') == 'Q',
                    'document_type': 'Warranty Deed',
                    'grantor_name': sale.get('grantor', ''),
                    'grantee_name': sale.get('grantee', ''),
                    'book': sale.get('or_book', ''),
                    'page': sale.get('or_page', ''),
                    'vi_code': sale.get('verification_code', ''),
                    'data_source': 'property_sales_history'
                })
        else:
            # Fallback to florida_parcels table
            logger.info(f"No sales in property_sales_history, trying florida_parcels for {parcel_id}")

            result = supabase.table('florida_parcels') \
                .select('sale_date, sale_price, sale_qualification, parcel_id') \
                .eq('parcel_id', parcel_id) \
                .gte('sale_price', 1000) \
                .limit(10) \
                .execute()

            if result.data:
                logger.info(f"Found {len(result.data)} sales in florida_parcels for {parcel_id}")

                for sale in result.data:
                    if sale.get('sale_price'):
                        sales_records.append({
                            'sale_date': sale.get('sale_date') or '2024-01-01',
                            'sale_price': safe_float(sale.get('sale_price')),
                            'sale_year': int(sale.get('sale_date', '2024-01-01')[:4]) if sale.get('sale_date') else 2024,
                            'sale_month': int(sale.get('sale_date', '2024-01-01')[5:7]) if sale.get('sale_date') else 1,
                            'qualified_sale': sale.get('sale_qualification', '').lower() == 'qualified',
                            'document_type': 'Deed',
                            'grantor_name': '',
                            'grantee_name': '',
                            'book': '',
                            'page': '',
                            'vi_code': sale.get('sale_qualification', ''),
                            'data_source': 'florida_parcels'
                        })

        # Sort by date descending
        sales_records.sort(key=lambda x: x['sale_date'], reverse=True)

        logger.info(f"Returning {len(sales_records)} total sales for {parcel_id}")

        return {
            'success': True,
            'parcel_id': parcel_id,
            'sales': sales_records,
            'count': len(sales_records),
            'source': 'property_sales_history' if sales_records and sales_records[0]['data_source'] == 'property_sales_history' else 'florida_parcels'
        }

    except Exception as e:
        logger.error(f"Error fetching sales for {parcel_id}: {str(e)}")
        return {
            'success': False,
            'parcel_id': parcel_id,
            'sales': [],
            'count': 0,
            'error': str(e)
        }

@router.get("/api/properties/{parcel_id}/last_qualified_sale")
async def get_last_qualified_sale(parcel_id: str):
    """Get the last qualified sale for a property"""
    try:
        logger.info(f"Fetching last qualified sale for parcel: {parcel_id}")

        # Get all sales for the property
        sales_response = await get_property_sales(parcel_id)

        if not sales_response['success'] or not sales_response['sales']:
            return {
                'success': False,
                'parcel_id': parcel_id,
                'sale': None,
                'message': 'No sales found'
            }

        # Find first qualified sale
        for sale in sales_response['sales']:
            if sale['qualified_sale'] and sale['sale_price'] > 1000:
                return {
                    'success': True,
                    'parcel_id': parcel_id,
                    'sale': sale
                }

        # If no qualified sales, return the most recent sale
        if sales_response['sales']:
            return {
                'success': True,
                'parcel_id': parcel_id,
                'sale': sales_response['sales'][0],
                'note': 'No qualified sales found, returning most recent sale'
            }

        return {
            'success': False,
            'parcel_id': parcel_id,
            'sale': None,
            'message': 'No sales found'
        }

    except Exception as e:
        logger.error(f"Error fetching last qualified sale for {parcel_id}: {str(e)}")
        return {
            'success': False,
            'parcel_id': parcel_id,
            'sale': None,
            'error': str(e)
        }