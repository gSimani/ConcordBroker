import psycopg2
from .config import Settings


def verify_no_dups(settings: Settings):
    print('[VERIFY] Checking duplicate keys for parcels and sales')
    conn = psycopg2.connect(
        host=settings.pg_host,
        port=settings.pg_port,
        database=settings.pg_db,
        user=settings.pg_user,
        password=settings.pg_password,
        sslmode=settings.pg_sslmode,
        options=f"-c statement_timeout={settings.pg_statement_timeout_ms}"
    )
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM (
                  SELECT parcel_id, county, year, COUNT(*)
                  FROM public.florida_parcels
                  GROUP BY parcel_id, county, year HAVING COUNT(*)>1
                ) t;
            """)
            dup_parcels = cur.fetchone()[0]
            cur.execute("""
                SELECT COUNT(*) FROM (
                  SELECT parcel_id, county, sale_date, sale_price, or_book, or_page, clerk_no, COUNT(*)
                  FROM public.property_sales_history
                  GROUP BY parcel_id, county, sale_date, sale_price, or_book, or_page, clerk_no HAVING COUNT(*)>1
                ) t;
            """)
            dup_sales = cur.fetchone()[0]
            print(f"[VERIFY] dup_parcels={dup_parcels}, dup_sales={dup_sales}")
    finally:
        conn.close()

