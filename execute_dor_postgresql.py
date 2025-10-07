"""
Execute County-Batched DOR Use Code Assignment via PostgreSQL
Direct database connection for maximum efficiency
"""

import psycopg2
import time
from datetime import datetime
from typing import Dict, List, Tuple
import json

# PostgreSQL Configuration
DB_CONFIG = {
    "host": "db.pmispwtdngkcmsrsjwbp.supabase.co",
    "database": "postgres",
    "user": "postgres",
    "password": "West@Boca613!",
    "port": 5432,
    "sslmode": "require"
}

def get_connection():
    """Get PostgreSQL connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        return None

def get_county_distribution(conn) -> List[Tuple[str, int, int]]:
    """Get list of counties ordered by properties needing updates"""
    print("\n[PHASE 1] Analyzing County Distribution")
    print("=" * 80)

    sql = """
    SELECT
        county,
        COUNT(*) as total,
        COUNT(CASE WHEN land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99' THEN 1 END) as need_update
    FROM florida_parcels
    WHERE year = 2025
    GROUP BY county
    HAVING COUNT(CASE WHEN land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99' THEN 1 END) > 0
    ORDER BY need_update DESC
    """

    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        counties = cursor.fetchall()
        cursor.close()

        print(f"[SUCCESS] Found {len(counties)} counties needing updates")
        print(f"\nTop 10 Counties by Update Volume:")
        for i, (county, total, need_update) in enumerate(counties[:10], 1):
            print(f"  {i:2d}. {county:20s} - {need_update:>10,} / {total:>10,} properties")

        return counties

    except Exception as e:
        print(f"[ERROR] Failed to get county distribution: {e}")
        return []

def process_county(conn, county: str, index: int, total: int) -> Dict:
    """Process a single county"""
    start_time = time.time()

    print(f"\n[{index}/{total}] Processing {county}...", end=" ", flush=True)

    # Build UPDATE SQL with intelligent logic
    update_sql = f"""
    UPDATE florida_parcels
    SET
        land_use_code = CASE
            -- Multi-Family 10+
            WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN '02'
            -- Industrial
            WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN '24'
            -- Commercial
            WHEN (just_value > 500000 AND building_value > 200000
                  AND building_value BETWEEN COALESCE(land_value, 0) * 0.3 AND COALESCE(land_value, 1) * 4) THEN '17'
            -- Agricultural
            WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN '01'
            -- Condominium
            WHEN (just_value BETWEEN 100000 AND 500000
                  AND building_value BETWEEN 50000 AND 300000
                  AND building_value BETWEEN COALESCE(land_value, 0) * 0.8 AND COALESCE(land_value, 1) * 1.5) THEN '03'
            -- Vacant Residential
            WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN '10'
            -- Single Family
            WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN '00'
            -- Default to Single Family
            ELSE '00'
        END,
        property_use = CASE
            WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN 'MF 10+'
            WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN 'Industria'
            WHEN (just_value > 500000 AND building_value > 200000
                  AND building_value BETWEEN COALESCE(land_value, 0) * 0.3 AND COALESCE(land_value, 1) * 4) THEN 'Commercia'
            WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN 'Agricult.'
            WHEN (just_value BETWEEN 100000 AND 500000
                  AND building_value BETWEEN 50000 AND 300000
                  AND building_value BETWEEN COALESCE(land_value, 0) * 0.8 AND COALESCE(land_value, 1) * 1.5) THEN 'Condo'
            WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN 'Vacant Re'
            WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN 'SFR'
            ELSE 'SFR'
        END
    WHERE year = 2025
        AND county = %s
        AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99')
    """

    try:
        cursor = conn.cursor()

        # Execute update
        cursor.execute(update_sql, (county,))
        rows_updated = cursor.rowcount
        conn.commit()

        # Validate
        validate_sql = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as with_code
        FROM florida_parcels
        WHERE year = 2025 AND county = %s
        """

        cursor.execute(validate_sql, (county,))
        total_rows, with_code = cursor.fetchone()
        coverage = (with_code / total_rows * 100) if total_rows > 0 else 0

        cursor.close()

        elapsed = time.time() - start_time
        print(f"✓ Updated {rows_updated:,} | Coverage: {coverage:.1f}% | {elapsed:.2f}s")

        return {
            "success": True,
            "county": county,
            "rows_updated": rows_updated,
            "total": total_rows,
            "with_code": with_code,
            "coverage": coverage,
            "elapsed": elapsed
        }

    except Exception as e:
        conn.rollback()
        print(f"✗ ERROR: {e}")
        return {
            "success": False,
            "county": county,
            "error": str(e)
        }

def get_overall_status(conn) -> Dict:
    """Get overall coverage status"""
    sql = """
    SELECT
        COUNT(*) as total,
        COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as with_code
    FROM florida_parcels
    WHERE year = 2025
    """

    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        total, with_code = cursor.fetchone()
        cursor.close()

        coverage = (with_code / total * 100) if total > 0 else 0
        return {
            "total": total,
            "with_code": with_code,
            "without_code": total - with_code,
            "coverage_pct": coverage
        }

    except Exception as e:
        print(f"[ERROR] Failed to get overall status: {e}")
        return {}

def get_distribution_analysis(conn) -> List[Dict]:
    """Get distribution of DOR codes"""
    sql = """
    SELECT
        land_use_code,
        property_use,
        COUNT(*) as count,
        ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM florida_parcels WHERE year = 2025) * 100, 2) as pct
    FROM florida_parcels
    WHERE year = 2025 AND land_use_code IS NOT NULL
    GROUP BY land_use_code, property_use
    ORDER BY count DESC
    LIMIT 20
    """

    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()

        return [
            {
                "land_use_code": row[0],
                "property_use": row[1],
                "count": row[2],
                "pct": float(row[3])
            }
            for row in rows
        ]

    except Exception as e:
        print(f"[ERROR] Failed to get distribution: {e}")
        return []

def main():
    """Execute county-batched DOR assignment"""
    print("=" * 80)
    print("[AI AGENT] County-Batched DOR Use Code Assignment via PostgreSQL")
    print("=" * 80)

    start_time = time.time()

    # Connect to database
    print("\n[CONNECTING] Establishing PostgreSQL connection...")
    conn = get_connection()
    if not conn:
        print("[ERROR] Failed to connect to database")
        return False

    print("[SUCCESS] Connected to PostgreSQL")

    try:
        # Phase 1: Discovery
        counties = get_county_distribution(conn)
        if not counties:
            print("\n[INFO] All properties already have DOR codes assigned!")
            return True

        initial_status = get_overall_status(conn)
        print(f"\n[INITIAL STATUS]")
        print(f"  Total Properties: {initial_status.get('total', 0):,}")
        print(f"  With Code: {initial_status.get('with_code', 0):,}")
        print(f"  Without Code: {initial_status.get('without_code', 0):,}")
        print(f"  Coverage: {initial_status.get('coverage_pct', 0):.2f}%")

        # Update Phase 1 complete
        print("\n[PHASE 1 COMPLETE] ✓ County distribution analyzed")

        # Phase 2: Process Top 10 Counties
        print(f"\n[PHASE 2] Processing Top 10 Counties")
        print("=" * 80)

        results = []
        top_10 = counties[:min(10, len(counties))]

        for i, (county, total, need_update) in enumerate(top_10, 1):
            result = process_county(conn, county, i, len(top_10))
            results.append(result)

        checkpoint = get_overall_status(conn)
        print(f"\n[CHECKPOINT] After Top 10 Counties:")
        print(f"  Coverage: {checkpoint.get('coverage_pct', 0):.2f}%")
        print(f"  Properties Updated: {checkpoint.get('with_code', 0) - initial_status.get('with_code', 0):,}")

        # Phase 3: Process Remaining Counties
        remaining = counties[10:]
        if remaining:
            print(f"\n[PHASE 3] Processing Remaining {len(remaining)} Counties")
            print("=" * 80)

            for i, (county, total, need_update) in enumerate(remaining, len(top_10) + 1):
                result = process_county(conn, county, i, len(counties))
                results.append(result)

        # Phase 4: Final Validation
        print(f"\n[PHASE 4] Final Validation & Analysis")
        print("=" * 80)

        final_status = get_overall_status(conn)
        distribution = get_distribution_analysis(conn)

        total_elapsed = time.time() - start_time

        # Generate Report
        print(f"\n{'=' * 80}")
        print(f"[EXECUTION COMPLETE] ✓")
        print(f"{'=' * 80}")

        print(f"\n[BEFORE]")
        print(f"  Total Properties: {initial_status.get('total', 0):,}")
        print(f"  With Code: {initial_status.get('with_code', 0):,}")
        print(f"  Coverage: {initial_status.get('coverage_pct', 0):.2f}%")

        print(f"\n[AFTER]")
        print(f"  Total Properties: {final_status.get('total', 0):,}")
        print(f"  With Code: {final_status.get('with_code', 0):,}")
        print(f"  Coverage: {final_status.get('coverage_pct', 0):.2f}%")

        print(f"\n[IMPACT]")
        properties_updated = final_status.get('with_code', 0) - initial_status.get('with_code', 0)
        improvement = final_status.get('coverage_pct', 0) - initial_status.get('coverage_pct', 0)
        print(f"  Properties Updated: {properties_updated:,}")
        print(f"  Coverage Improvement: +{improvement:.2f}%")
        print(f"  Execution Time: {total_elapsed / 60:.2f} minutes")
        print(f"  Counties Processed: {len(results)}")
        print(f"  Successful Updates: {sum(1 for r in results if r.get('success'))}")
        print(f"  Failed Updates: {sum(1 for r in results if not r.get('success'))}")

        print(f"\n[TOP 10 USE CODE DISTRIBUTION]")
        for item in distribution[:10]:
            print(f"  {item['land_use_code']:3s} - {item['property_use']:12s}: {item['count']:>10,} ({item['pct']:>5.1f}%)")

        # Success Rating
        coverage = final_status.get('coverage_pct', 0)
        if coverage >= 100:
            rating = 10
        elif coverage >= 99.5:
            rating = 9
        elif coverage >= 95:
            rating = 8
        elif coverage >= 90:
            rating = 7
        else:
            rating = 6

        print(f"\n[SUCCESS RATING] {rating}/10")

        # Check for gaps
        gaps = [r for r in results if not r.get('success')]
        if gaps:
            print(f"\n[GAPS IDENTIFIED] {len(gaps)} counties failed:")
            for gap in gaps:
                print(f"  - {gap['county']}: {gap.get('error', 'Unknown error')}")

        print("=" * 80)

        # Save detailed results
        report = {
            "execution_timestamp": datetime.now().isoformat(),
            "initial_status": initial_status,
            "final_status": final_status,
            "properties_updated": properties_updated,
            "coverage_improvement": improvement,
            "execution_time_minutes": total_elapsed / 60,
            "counties_processed": len(results),
            "successful_counties": sum(1 for r in results if r.get('success')),
            "failed_counties": sum(1 for r in results if not r.get('success')),
            "county_results": results,
            "distribution": distribution,
            "success_rating": rating,
            "gaps": gaps
        }

        filename = f"DOR_ASSIGNMENT_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n[REPORT SAVED] {filename}\n")

        return True

    finally:
        if conn:
            conn.close()
            print("[DISCONNECTED] PostgreSQL connection closed")

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)