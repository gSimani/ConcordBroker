#!/usr/bin/env python3
"""
Apply a SQL file against Supabase Postgres using psycopg2, then optionally run verification queries.
"""
import sys
from pathlib import Path
import psycopg2

# Match connection used by other scripts
PG_CONFIG = {
    'host': 'aws-1-us-east-1.pooler.supabase.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres.pmispwtdngkcmsrsjwbp',
    'password': 'West@Boca613!',
    'sslmode': 'require',
    'connect_timeout': 30,
    'options': '-c statement_timeout=300000'
}


def exec_sql(conn, sql: str):
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/apply_sql_file.py <path-to-sql-file>")
        sys.exit(1)

    sql_path = Path(sys.argv[1])
    if not sql_path.exists():
        print(f"File not found: {sql_path}")
        sys.exit(1)

    sql_text = sql_path.read_text(encoding='utf-8')

    print(f"[CONNECT] Connecting to Postgres at {PG_CONFIG['host']} ...")
    conn = psycopg2.connect(**PG_CONFIG)
    try:
        print(f"[APPLY] Executing SQL from {sql_path}")
        # Execute as a single script
        exec_sql(conn, sql_text)
        print("[SUCCESS] SQL applied")

        # Optional refresh and verification
        print("[REFRESH] Refreshing sales summary materialized view (concurrently)")
        exec_sql(conn, "SELECT public.refresh_parcel_sales_summary();")
        print("[SUCCESS] Refresh complete")

        # Verifications
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.florida_parcels_latest')")
            latest_view = cur.fetchone()[0]
            print(f"[VERIFY] florida_parcels_latest: {latest_view}")

            cur.execute("SELECT to_regclass('public.parcel_sales_summary')")
            mv = cur.fetchone()[0]
            print(f"[VERIFY] parcel_sales_summary: {mv}")

            cur.execute("SELECT indexname FROM pg_indexes WHERE schemaname='public' AND tablename IN ('florida_parcels','parcel_sales_summary') AND indexname IN ('idx_fp_latest_year','uk_parcel_sales_summary','idx_parcel_sales_summary_last_date') ORDER BY indexname;")
            idx = cur.fetchall()
            print(f"[VERIFY] indexes: {[r[0] for r in idx]}")

            cur.execute("SELECT parcel_id, county, total_sales, last_sale_date, last_sale_price FROM public.parcel_sales_summary ORDER BY last_sale_date DESC NULLS LAST LIMIT 5;")
            rows = cur.fetchall()
            print(f"[SAMPLE] parcel_sales_summary (top 5): {rows}")

    finally:
        conn.close()
        print("[DISCONNECT] Connection closed")


if __name__ == '__main__':
    main()

