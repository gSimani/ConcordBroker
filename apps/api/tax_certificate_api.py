"""
Tax Certificate API Endpoint
Provides real tax certificate data from Supabase
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime
from decimal import Decimal

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection parameters
def get_db_connection():
    return psycopg2.connect(
        host='aws-1-us-east-1.pooler.supabase.com',
        database='postgres',
        user='postgres.pmispwtdngkcmsrsjwbp',
        password='West@Boca613!',
        port=6543,
        cursor_factory=RealDictCursor
    )

@app.get("/api/tax-certificates/{parcel_id}")
async def get_tax_certificates_by_parcel(parcel_id: str):
    """Get all tax certificates for a specific parcel"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Query for tax certificates
        cur.execute("""
            SELECT 
                *,
                redemption_amount - face_amount AS interest_due,
                (expiration_date - CURRENT_DATE) AS days_until_expiration
            FROM tax_certificates
            WHERE parcel_id = %s OR real_estate_account = %s
            ORDER BY tax_year DESC, certificate_number
        """, (parcel_id, parcel_id))
        
        certificates = cur.fetchall()
        
        # Convert Decimal to float for JSON serialization
        for cert in certificates:
            for key, value in cert.items():
                if isinstance(value, Decimal):
                    cert[key] = float(value)
                elif isinstance(value, datetime):
                    cert[key] = value.isoformat()
        
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "parcel_id": parcel_id,
            "certificate_count": len(certificates),
            "certificates": certificates,
            "total_active_amount": sum(c['face_amount'] for c in certificates if c['status'] == 'active'),
            "total_redemption_amount": sum(c['redemption_amount'] for c in certificates if c['status'] == 'active')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tax-certificates")
async def get_all_tax_certificates(status: Optional[str] = None, limit: int = 100):
    """Get all tax certificates with optional filtering"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if status:
            cur.execute("""
                SELECT 
                    *,
                    redemption_amount - face_amount AS interest_due,
                    (expiration_date - CURRENT_DATE) AS days_until_expiration
                FROM tax_certificates
                WHERE status = %s
                ORDER BY tax_year DESC, certificate_number
                LIMIT %s
            """, (status, limit))
        else:
            cur.execute("""
                SELECT 
                    *,
                    redemption_amount - face_amount AS interest_due,
                    (expiration_date - CURRENT_DATE) AS days_until_expiration
                FROM tax_certificates
                ORDER BY tax_year DESC, certificate_number
                LIMIT %s
            """, (limit,))
        
        certificates = cur.fetchall()
        
        # Convert Decimal to float for JSON serialization
        for cert in certificates:
            for key, value in cert.items():
                if isinstance(value, Decimal):
                    cert[key] = float(value)
                elif isinstance(value, datetime):
                    cert[key] = value.isoformat()
        
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "count": len(certificates),
            "certificates": certificates
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tax-certificates/summary/{parcel_id}")
async def get_tax_certificate_summary(parcel_id: str):
    """Get summary of tax certificates for a property"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get summary data
        cur.execute("""
            SELECT 
                COUNT(*) as certificate_count,
                SUM(CASE WHEN status = 'active' THEN face_amount ELSE 0 END) as total_active_amount,
                SUM(CASE WHEN status = 'active' THEN redemption_amount ELSE 0 END) as total_redemption_amount,
                MAX(tax_year) as latest_tax_year,
                STRING_AGG(DISTINCT buyer_name, ', ') as certificate_holders
            FROM tax_certificates
            WHERE parcel_id = %s OR real_estate_account = %s
        """, (parcel_id, parcel_id))
        
        summary = cur.fetchone()
        
        # Convert Decimal to float
        if summary:
            for key, value in summary.items():
                if isinstance(value, Decimal):
                    summary[key] = float(value)
        
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "parcel_id": parcel_id,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tax-certificates/buyers")
async def get_certificate_buyers():
    """Get list of all certificate buyers with their holdings"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                buyer_name,
                COUNT(*) as certificate_count,
                SUM(face_amount) as total_face_amount,
                SUM(redemption_amount) as total_redemption_amount,
                COUNT(DISTINCT parcel_id) as property_count,
                STRING_AGG(DISTINCT status, ', ') as statuses
            FROM tax_certificates
            GROUP BY buyer_name
            ORDER BY total_face_amount DESC
        """)
        
        buyers = cur.fetchall()
        
        # Convert Decimal to float
        for buyer in buyers:
            for key, value in buyer.items():
                if isinstance(value, Decimal):
                    buyer[key] = float(value)
        
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "buyer_count": len(buyers),
            "buyers": buyers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting Tax Certificate API Server...")
    print("Endpoints available:")
    print("  - GET /api/tax-certificates/{parcel_id}")
    print("  - GET /api/tax-certificates")
    print("  - GET /api/tax-certificates/summary/{parcel_id}")
    print("  - GET /api/tax-certificates/buyers")
    uvicorn.run(app, host="0.0.0.0", port=8001)