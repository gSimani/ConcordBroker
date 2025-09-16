#!/usr/bin/env python3
"""
Database Analysis Script - Clean version without Unicode
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
    
    # Get database URL - try different formats
    db_url = os.getenv('DATABASE_URL')
    
    # If DATABASE_URL has issues, construct from components
    if not db_url or 'supa=base-pooler.x' in db_url:
        # Construct clean URL
        db_url = "postgresql://postgres.pmispwtdngkcmsrsjwbp:tCgELRm4m2paFokA@aws-1-us-east-1.pooler.supabase.com:6543/postgres"
    
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
        
        parcel_count = 0
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
                result = cur.fetchone()
                if result[0]:
                    max_date, min_date, dated_count = result
                    print(f"Data range: {min_date} to {max_date}")
                    print(f"Records with import dates: {dated_count:,}")
            else:
                print("WARNING: No Florida parcel data found")
                
        except Exception as e:
            print(f"WARNING: Florida parcels table not accessible: {e}")
        
        print()
        
        # Check Sunbiz data
        print("SUNBIZ BUSINESS ENTITY DATA")
        print("-" * 30)
        
        sunbiz_tables = ['sunbiz_corporate', 'sunbiz_corporate_events', 'sunbiz_fictitious']
        sunbiz_total = 0
        for table in sunbiz_tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count = cur.fetchone()[0]
                sunbiz_total += count
                print(f"{table}: {count:,} records")
            except Exception as e:
                print(f"WARNING: {table} not found or accessible")
        
        print()
        
        # Check entity matching system
        print("ENTITY MATCHING SYSTEM")
        print("-" * 30)
        
        matching_tables = [
            'property_entity_matches',
            'entity_portfolio_summary', 
            'entity_relationships'
        ]
        
        matching_total = 0
        for table in matching_tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count = cur.fetchone()[0]
                matching_total += count
                print(f"{table}: {count:,} records")
            except Exception as e:
                print(f"WARNING: {table} not found or accessible")
        
        print()
        
        # Check monitoring agents
        print("MONITORING AGENTS")
        print("-" * 30)
        
        agent_count = 0
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
                    status = "ENABLED" if enabled else "DISABLED"
                    last = last_run.strftime('%Y-%m-%d') if last_run else "Never"
                    print(f"  - {name}: {status}, Last run: {last}")
        except Exception as e:
            print(f"WARNING: Monitoring agents table not accessible: {e}")
        
        print()
        
        # Overall assessment
        print("DEPLOYMENT SUMMARY")
        print("-" * 30)
        
        # Check if schemas exist
        cur.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN (
                'florida_parcels', 
                'sunbiz_corporate', 
                'property_entity_matches',
                'monitoring_agents'
            )
            ORDER BY tablename;
        """)
        
        existing_tables = [row[0] for row in cur.fetchall()]
        required_tables = ['florida_parcels', 'sunbiz_corporate', 'property_entity_matches', 'monitoring_agents']
        
        print(f"Core tables present: {len(existing_tables)}/{len(required_tables)}")
        if existing_tables:
            print("Existing tables:")
            for table in existing_tables:
                print(f"  + {table}")
        
        missing_tables = set(required_tables) - set(existing_tables)
        if missing_tables:
            print("Missing tables:")
            for table in missing_tables:
                print(f"  - {table}")
        
        # Data summary
        print(f"\nData Summary:")
        print(f"  Florida Parcels: {parcel_count:,}")
        print(f"  Sunbiz Records: {sunbiz_total:,}")  
        print(f"  Entity Matches: {matching_total:,}")
        print(f"  Monitoring Agents: {agent_count}")
        
        # Overall health
        tables_score = len(existing_tables) / len(required_tables) * 100
        data_score = 0
        if parcel_count > 0:
            data_score += 25
        if sunbiz_total > 0:
            data_score += 25
        if matching_total > 0:
            data_score += 25
        if agent_count > 0:
            data_score += 25
            
        overall_score = (tables_score + data_score) / 2
        
        print(f"\nOverall Health Score: {overall_score:.1f}%")
        
        if overall_score >= 90:
            print("DATABASE STATUS: EXCELLENT")
            print("All core systems are deployed with data")
        elif overall_score >= 70:
            print("DATABASE STATUS: GOOD") 
            print("Most systems deployed, some optimization needed")
        elif overall_score >= 50:
            print("DATABASE STATUS: NEEDS ATTENTION")
            print("Core systems partially deployed")
        else:
            print("DATABASE STATUS: CRITICAL")
            print("Major deployment issues detected")
        
        print()
        
        # Next steps
        print("RECOMMENDED ACTIONS")
        print("-" * 30)
        
        actions = []
        if parcel_count == 0:
            actions.append("1. Load Florida parcel data: python run_parcel_sync.py")
        
        if sunbiz_total == 0:
            actions.append("2. Load Sunbiz data: python sunbiz_pipeline.py")
        
        if matching_total == 0:
            actions.append("3. Run entity matching: python entity_matching_service.py")
            
        if agent_count == 0:
            actions.append("4. Set up monitoring: python setup_monitoring.py")
        
        if not actions:
            actions.append("Database appears fully deployed!")
            actions.append("Consider running periodic maintenance and updates")
        else:
            actions.append("For complete automated deployment: python supabase_deployment_script.py")
        
        for action in actions:
            print(action)
        
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        return 1
    
    finally:
        if 'conn' in locals():
            conn.close()
    
    return 0

if __name__ == "__main__":
    exit(main())