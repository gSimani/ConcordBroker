"""
Quick verification script to check upload completion status
"""

import psycopg2
from urllib.parse import urlparse
from pathlib import Path
import os

def get_connection():
    """Get database connection"""
    db_url = "postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
    parsed = urlparse(db_url)
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip('/'),
        user=parsed.username,
        password=parsed.password.replace('%40', '@') if parsed.password else None,
        sslmode='require'
    )
    return conn

def verify_completion():
    """Verify upload completion"""
    print("\n" + "="*70)
    print("FLORIDA DATABASE UPLOAD VERIFICATION")
    print("="*70)
    
    # Get filesystem count
    data_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
    all_files = []
    for root, dirs, files in os.walk(data_path):
        for file in files:
            if file.endswith('.txt') and 'README' not in file.upper():
                all_files.append(file)
    
    print(f"\n📁 FILESYSTEM:")
    print(f"   Total .txt files: {len(all_files)}")
    
    # Get database stats
    conn = get_connection()
    with conn.cursor() as cur:
        # Total entities
        cur.execute("SELECT COUNT(*) FROM florida_entities")
        total_entities = cur.fetchone()[0]
        
        # Unique source files
        cur.execute("SELECT COUNT(DISTINCT source_file) FROM florida_entities WHERE source_file IS NOT NULL")
        unique_files = cur.fetchone()[0]
        
        # Get list of processed files
        cur.execute("SELECT DISTINCT source_file FROM florida_entities WHERE source_file IS NOT NULL")
        processed_files = {row[0] for row in cur.fetchall()}
        
        # Entity breakdown by prefix
        cur.execute("""
            SELECT 
                CASE 
                    WHEN entity_id LIKE 'B_%' THEN 'Backward Agent'
                    WHEN entity_id LIKE 'GAP_%' THEN 'Gap Filler'
                    ELSE 'Forward Agent'
                END as agent,
                COUNT(*) as count
            FROM florida_entities
            GROUP BY 1
        """)
        agent_stats = cur.fetchall()
        
        # Recent activity
        cur.execute("""
            SELECT COUNT(*) as recent 
            FROM florida_entities 
            WHERE created_at >= NOW() - INTERVAL '10 minutes'
        """)
        recent = cur.fetchone()[0]
    
    conn.close()
    
    # Find missing files
    missing_files = []
    for file in all_files:
        if file not in processed_files:
            missing_files.append(file)
    
    # Print results
    print(f"\n💾 DATABASE:")
    print(f"   Total entities: {total_entities:,}")
    print(f"   Unique source files: {unique_files}")
    print(f"   Recent inserts (10 min): {recent:,}")
    
    print(f"\n🤖 BY AGENT:")
    for agent, count in agent_stats:
        print(f"   {agent}: {count:,}")
    
    print(f"\n📊 COMPLETION STATUS:")
    print(f"   Files in filesystem: {len(all_files)}")
    print(f"   Files in database: {unique_files}")
    print(f"   Missing files: {len(missing_files)}")
    
    if missing_files:
        print(f"\n⚠️  MISSING FILES ({len(missing_files)}):")
        for i, file in enumerate(missing_files[:20], 1):
            print(f"   {i}. {file}")
        if len(missing_files) > 20:
            print(f"   ... and {len(missing_files) - 20} more")
    else:
        print(f"\n✅ ALL FILES UPLOADED SUCCESSFULLY!")
    
    completion_rate = (unique_files / len(all_files) * 100) if all_files else 0
    print(f"\n📈 COMPLETION RATE: {completion_rate:.1f}%")
    
    if completion_rate >= 99.5:
        print("\n🎉 DATABASE IS COMPLETE! (99.5%+ coverage)")
    elif completion_rate >= 99:
        print("\n✅ DATABASE IS NEARLY COMPLETE! (99%+ coverage)")
    else:
        print(f"\n⏳ Upload in progress... {100 - completion_rate:.1f}% remaining")
    
    print("="*70)
    
    return missing_files

if __name__ == "__main__":
    missing = verify_completion()
    if not missing:
        print("\n🏆 PERFECT! No files missing - database is 100% complete!")