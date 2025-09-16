#!/usr/bin/env python3
"""
Simple Database Analysis Script
Direct check of Supabase database tables and data
"""

import os
import psycopg2
from psycopg2 import sql
import sys
from datetime import datetime
from dotenv import load_dotenv

def main():
    # Load environment
    load_dotenv('../../.env')
    
    # Get database URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not found in environment")
        return 1
    
    print("SUPABASE DATABASE ANALYSIS")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        print("SUCCESS: Database connection successful")
        print()
        
        # Check core Florida parcel tables
        print("FLORIDA PARCEL DATA")
        print("-" * 30)
        
        try:
            cur.execute("SELECT COUNT(*) FROM florida_parcels;")
            parcel_count = cur.fetchone()[0]
            print(f"Florida Parcels: {parcel_count:,} records")
            
            if parcel_count > 0:
                # Get sample data
                cur.execute("""
                    SELECT county, COUNT(*) as count 
                    FROM florida_parcels 
                    GROUP BY county 
                    ORDER BY count DESC 
                    LIMIT 5;
                """)
                counties = cur.fetchall()
                print("Top counties:")
                for county, count in counties:
                    print(f"  - {county}: {count:,} parcels")
                
                # Check recent data
                cur.execute("""
                    SELECT MAX(import_date), MIN(import_date), COUNT(*)
                    FROM florida_parcels 
                    WHERE import_date IS NOT NULL;
                """)
                max_date, min_date, dated_count = cur.fetchone()
                if max_date:
                    print(f"Data range: {min_date} to {max_date}")
                    print(f"Records with import dates: {dated_count:,}")
            else:
                print("WARNING: No Florida parcel data found")
                
        except Exception as e:
            print(f"⚠️  Florida parcels table not accessible: {e}")
        
        print()
        
        # Check Sunbiz data
        print("🏢 SUNBIZ BUSINESS ENTITY DATA")
        print("-" * 30)
        
        sunbiz_tables = ['sunbiz_corporate', 'sunbiz_corporate_events', 'sunbiz_fictitious']
        for table in sunbiz_tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count = cur.fetchone()[0]
                print(f"{table}: {count:,} records")
            except Exception as e:
                print(f"⚠️  {table} not found or accessible")
        
        print()
        
        # Check entity matching system
        print("🔗 ENTITY MATCHING SYSTEM")
        print("-" * 30)
        
        matching_tables = [
            'property_entity_matches',
            'entity_portfolio_summary', 
            'entity_relationships'
        ]
        
        for table in matching_tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count = cur.fetchone()[0]
                print(f"{table}: {count:,} records")
            except Exception as e:
                print(f"⚠️  {table} not found or accessible")
        
        print()
        
        # Check monitoring agents
        print("🤖 MONITORING AGENTS")
        print("-" * 30)
        
        try:
            cur.execute("SELECT COUNT(*) FROM monitoring_agents;")
            agent_count = cur.fetchone()[0]
            print(f"Monitoring agents: {agent_count} configured")
            
            if agent_count > 0:
                cur.execute("""
                    SELECT agent_name, enabled, last_run 
                    FROM monitoring_agents 
                    ORDER BY agent_name;
                """)
                agents = cur.fetchall()
                for name, enabled, last_run in agents:
                    status = "✅ Enabled" if enabled else "❌ Disabled"
                    last = last_run.strftime('%Y-%m-%d') if last_run else "Never"
                    print(f"  - {name}: {status}, Last run: {last}")
        except Exception as e:
            print(f"⚠️  Monitoring agents table not accessible: {e}")
        
        print()
        
        # Overall assessment
        print("📋 DEPLOYMENT SUMMARY")
        print("-" * 30)
        
        # Check if schemas exist
        cur.execute("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN (
                'florida_parcels', 
                'sunbiz_corporate', 
                'property_entity_matches',
                'monitoring_agents'
            );
        """)
        
        existing_tables = [row[1] for row in cur.fetchall()]
        required_tables = ['florida_parcels', 'sunbiz_corporate', 'property_entity_matches', 'monitoring_agents']
        
        print(f"Core tables present: {len(existing_tables)}/{len(required_tables)}")
        
        missing_tables = set(required_tables) - set(existing_tables)
        if missing_tables:
            print("Missing tables:")
            for table in missing_tables:
                print(f"  - {table}")
        
        # Overall health
        if len(existing_tables) == len(required_tables):
            if parcel_count > 0:
                print("\n🎉 DATABASE STATUS: EXCELLENT")
                print("All core systems are deployed with data")
            else:
                print("\n⚠️  DATABASE STATUS: GOOD") 
                print("All tables exist but some need data loading")
        else:
            print("\n❌ DATABASE STATUS: NEEDS ATTENTION")
            print("Missing core database tables")
        
        print()
        
        # Next steps
        print("📝 RECOMMENDED ACTIONS")
        print("-" * 30)
        
        if parcel_count == 0:
            print("1. Load Florida parcel data: python run_parcel_sync.py")
        
        if 'sunbiz_corporate' not in existing_tables or parcel_count == 0:
            print("2. Load Sunbiz data: python sunbiz_pipeline.py")
        
        if 'property_entity_matches' not in existing_tables:
            print("3. Run entity matching: python entity_matching_service.py")
            
        if 'monitoring_agents' not in existing_tables:
            print("4. Set up monitoring: python setup_monitoring.py")
        
        print("5. For complete deployment: python supabase_deployment_script.py")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return 1
    
    finally:
        if 'conn' in locals():
            conn.close()
    
    return 0

if __name__ == "__main__":
    exit(main())