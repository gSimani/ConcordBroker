#!/usr/bin/env python3
"""
Quick setup for tax deed tables in the existing database
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def create_tax_deed_tables():
    """Create tax deed tables"""
    
    # Use the same database connection as our property data
    DATABASE_URL = "postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
    
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Drop existing tables
        print("Dropping existing tax deed tables...")
        cur.execute("DROP TABLE IF EXISTS public.auction_bidding_history CASCADE")
        cur.execute("DROP TABLE IF EXISTS public.tax_deed_bidding_items CASCADE") 
        cur.execute("DROP TABLE IF EXISTS public.tax_deed_auctions CASCADE")
        conn.commit()
        
        # Create tax deed auctions table
        print("Creating tax_deed_auctions table...")
        cur.execute("""
            CREATE TABLE public.tax_deed_auctions (
                id SERIAL PRIMARY KEY,
                auction_date DATE NOT NULL,
                auction_time TIME,
                description TEXT,
                auction_type VARCHAR(50),
                status VARCHAR(50),
                total_items INTEGER DEFAULT 0,
                items_sold INTEGER DEFAULT 0,
                total_revenue DECIMAL(12,2),
                location VARCHAR(255),
                auctioneer VARCHAR(255),
                online_platform VARCHAR(100),
                platform_url TEXT,
                registration_deadline DATE,
                deposit_required DECIMAL(10,2),
                bid_increment DECIMAL(8,2) DEFAULT 25.00,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                data_source VARCHAR(50) DEFAULT 'County Records'
            )
        """)
        conn.commit()
        
        # Create tax deed bidding items table
        print("Creating tax_deed_bidding_items table...")
        cur.execute("""
            CREATE TABLE public.tax_deed_bidding_items (
                id SERIAL PRIMARY KEY,
                auction_id INTEGER REFERENCES tax_deed_auctions(id) ON DELETE CASCADE,
                parcel_id VARCHAR(50) NOT NULL,
                tax_deed_number VARCHAR(50) UNIQUE,
                tax_certificate_number VARCHAR(50),
                legal_situs_address TEXT,
                homestead_exemption BOOLEAN DEFAULT FALSE,
                assessed_value DECIMAL(12,2),
                soh_value DECIMAL(12,2),
                opening_bid DECIMAL(10,2),
                current_bid DECIMAL(10,2),
                reserve_met BOOLEAN DEFAULT FALSE,
                close_time TIMESTAMP,
                item_status VARCHAR(50),
                total_bids INTEGER DEFAULT 0,
                unique_bidders INTEGER DEFAULT 0,
                applicant_name VARCHAR(255),
                tax_years_included VARCHAR(50),
                total_taxes_owed DECIMAL(10,2),
                winning_bid DECIMAL(10,2),
                winning_bidder VARCHAR(100),
                gis_parcel_map_url TEXT,
                property_appraisal_url TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
        
        # Create view for easy queries
        print("Creating tax_deed_items_view...")
        cur.execute("""
            CREATE OR REPLACE VIEW public.tax_deed_items_view AS
            SELECT 
                tdi.*,
                ta.auction_date,
                ta.auction_time,
                ta.description as auction_description,
                ta.online_platform,
                ta.platform_url,
                EXTRACT(EPOCH FROM (tdi.close_time - NOW())) as seconds_remaining
            FROM tax_deed_bidding_items tdi
            LEFT JOIN tax_deed_auctions ta ON tdi.auction_id = ta.id
            ORDER BY ta.auction_date DESC, tdi.close_time DESC
        """)
        conn.commit()
        
        # Insert sample data
        print("Inserting sample auction data...")
        cur.execute("""
            INSERT INTO tax_deed_auctions 
            (auction_date, auction_time, description, auction_type, status, total_items, online_platform, platform_url, deposit_required)
            VALUES 
            ('2025-01-15', '10:00:00', 'Broward County Tax Deed Sale - January 2025', 'Online', 'Upcoming', 245, 'DeedAuction.net', 'https://broward.deedauction.net/', 5000),
            ('2025-03-20', '10:00:00', 'Broward County Tax Deed Sale - March 2025', 'Online', 'Upcoming', 198, 'DeedAuction.net', 'https://broward.deedauction.net/', 5000),
            ('2024-11-20', '10:00:00', 'Broward County Tax Deed Sale - November 2024', 'Online', 'Completed', 187, 'DeedAuction.net', 'https://broward.deedauction.net/', 5000)
            RETURNING id
        """)
        auction_ids = cur.fetchall()
        conn.commit()
        
        # Insert sample bidding items
        print("Inserting sample bidding items...")
        cur.execute("""
            INSERT INTO tax_deed_bidding_items 
            (auction_id, parcel_id, tax_deed_number, tax_certificate_number, legal_situs_address, 
             homestead_exemption, assessed_value, soh_value, opening_bid, current_bid, 
             close_time, item_status, total_bids, unique_bidders, applicant_name, 
             tax_years_included, total_taxes_owed, property_appraisal_url)
            VALUES 
            (%s, '474131031040', 'TD-2025-00123', 'TC-2022-05847', '12681 NW 78 MNR, PARKLAND, FL 33076', 
             FALSE, 580000.00, 551000.00, 8500.00, 12750.00, 
             '2025-01-15 17:00:00', 'Active', 8, 5, 'Investment Holdings LLC', 
             '2020-2022', 8234.50, 'https://bcpa.broward.org/property/474131031040'),
            (%s, '064210015020', 'TD-2024-00987', 'TC-2021-08934', '5678 EXAMPLE AVE, PEMBROKE PINES, FL 33028', 
             FALSE, 425000.00, 405000.00, 12500.00, 67500.00, 
             '2024-11-20 17:00:00', 'Sold', 24, 12, 'Sunshine Investments Corp', 
             '2019-2021', 12234.80, 'https://bcpa.broward.org/property/064210015020')
        """, (auction_ids[0][0], auction_ids[2][0]))
        conn.commit()
        
        # Verify tables
        cur.execute("SELECT count(*) FROM tax_deed_auctions")
        auction_count = cur.fetchone()[0]
        
        cur.execute("SELECT count(*) FROM tax_deed_bidding_items")
        item_count = cur.fetchone()[0]
        
        print(f"SUCCESS! Created tables with {auction_count} auctions and {item_count} bidding items")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    create_tax_deed_tables()