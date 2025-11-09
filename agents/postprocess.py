import psycopg2
from .config import Settings


def refresh_sales_summary(settings: Settings):
    print('[POST] Refreshing parcel_sales_summary (concurrently)')
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
            cur.execute("SELECT public.refresh_parcel_sales_summary();")
        conn.commit()
    finally:
        conn.close()
    print('[POST] Refresh complete')

