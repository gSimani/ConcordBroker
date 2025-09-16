"""
Bulk NAL loader wrapper for florida_parcels using direct Postgres.

- Reads counties from the local data directory or via --counties
- Streams CSV in chunks and upserts into public.florida_parcels
- Uses psycopg2 execute_values with ON CONFLICT (parcel_id, county, year)
- Sets safe session timeouts for bulk ingestion
"""

import os
import sys
import argparse
import glob
from datetime import datetime
from typing import List, Tuple, Optional

import pandas as pd
from psycopg2 import connect
from psycopg2.extras import execute_values


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "TEMP", "DATABASE PROPERTY APP")


def load_env(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def get_db_url() -> str:
    # Prefer non-pooling for bulk
    db = (
        os.getenv("POSTGRES_URL_NON_POOLING")
        or os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
    )
    if not db:
        print("ERROR: No database URL found in environment (.env)", file=sys.stderr)
        sys.exit(2)
    return db


def safe_int(v):
    try:
        return int(float(str(v).replace(",", ""))) if (v is not None and str(v) not in ("", "nan", "None")) else None
    except Exception:
        return None


def safe_float(v):
    try:
        return float(str(v).replace(",", "")) if (v is not None and str(v) not in ("", "nan", "None")) else None
    except Exception:
        return None


def build_sale_date(yr, mo) -> Optional[str]:
    y = safe_int(yr)
    m = safe_int(mo)
    if not y or not m:
        return None
    return f"{y}-{str(m).zfill(2)}-01"


def county_csv(county: str) -> Optional[str]:
    nal = os.path.join(DATA_DIR, county, "NAL")
    files = glob.glob(os.path.join(nal, "*.csv"))
    return files[0] if files else None


def discover_counties() -> List[str]:
    if not os.path.isdir(DATA_DIR):
        return []
    out = []
    for name in os.listdir(DATA_DIR):
        if name in ("NAL_2025", "NAL_2025P"):
            continue
        p = os.path.join(DATA_DIR, name)
        if os.path.isdir(p):
            out.append(name)
    out.sort()
    return out


def upsert_chunk(cur, records: List[Tuple]):
    # order of columns must match template
    sql = (
        "INSERT INTO public.florida_parcels ("
        "parcel_id, county, year, owner_name, owner_addr1, owner_city, owner_state, owner_zip, "
        "phy_addr1, phy_addr2, phy_city, phy_state, phy_zipcd, property_use, year_built, total_living_area, "
        "just_value, assessed_value, taxable_value, land_value, building_value, sale_price, sale_date"
        ") VALUES %s "
        "ON CONFLICT (parcel_id, county, year) DO UPDATE SET "
        "owner_name = EXCLUDED.owner_name, owner_addr1 = EXCLUDED.owner_addr1, owner_city = EXCLUDED.owner_city, owner_state = EXCLUDED.owner_state, owner_zip = EXCLUDED.owner_zip, "
        "phy_addr1 = EXCLUDED.phy_addr1, phy_addr2 = EXCLUDED.phy_addr2, phy_city = EXCLUDED.phy_city, phy_state = EXCLUDED.phy_state, phy_zipcd = EXCLUDED.phy_zipcd, "
        "property_use = EXCLUDED.property_use, year_built = EXCLUDED.year_built, total_living_area = EXCLUDED.total_living_area, "
        "just_value = EXCLUDED.just_value, assessed_value = EXCLUDED.assessed_value, taxable_value = EXCLUDED.taxable_value, "
        "land_value = EXCLUDED.land_value, building_value = EXCLUDED.building_value, sale_price = EXCLUDED.sale_price, sale_date = EXCLUDED.sale_date"
    )
    template = (
        "(%s,%s,%s,%s,%s,%s,%s,%s,"
        "%s,%s,%s,%s,%s,%s,%s,%s,"
        "%s,%s,%s,%s,%s,%s,%s)"
    )
    execute_values(cur, sql, records, template=template, page_size=1000)


def process_county(conn, county: str, year: int, chunk_rows: int) -> int:
    path = county_csv(county)
    if not path:
        print(f"[{county}] No NAL CSV found; skipping")
        return 0
    total = 0
    for chunk in pd.read_csv(path, chunksize=chunk_rows, low_memory=False, encoding="utf-8", on_bad_lines="skip"):
        records: List[Tuple] = []
        for _, row in chunk.iterrows():
            parcel_id = str(row.get("PARCEL_ID", "")).strip()
            if not parcel_id:
                continue
            jv = safe_float(row.get("JV"))
            land_val = safe_float(row.get("LND_VAL"))
            building_val = (jv - land_val) if (jv is not None and land_val is not None) else None
            rec = (
                parcel_id,
                county,
                year,
                (str(row.get("OWN_NAME"))[:255] if pd.notna(row.get("OWN_NAME")) else None),
                (str(row.get("OWN_ADDR1"))[:255] if pd.notna(row.get("OWN_ADDR1")) else None),
                (str(row.get("OWN_CITY"))[:100] if pd.notna(row.get("OWN_CITY")) else None),
                (str(row.get("OWN_STATE"))[:2] if pd.notna(row.get("OWN_STATE")) else None),
                (str(row.get("OWN_ZIPCD"))[:10] if pd.notna(row.get("OWN_ZIPCD")) else None),
                (str(row.get("PHY_ADDR1"))[:255] if pd.notna(row.get("PHY_ADDR1")) else None),
                (str(row.get("PHY_ADDR2"))[:255] if pd.notna(row.get("PHY_ADDR2")) else None),
                (str(row.get("PHY_CITY"))[:100] if pd.notna(row.get("PHY_CITY")) else None),
                "FL",
                (str(row.get("PHY_ZIPCD"))[:10] if pd.notna(row.get("PHY_ZIPCD")) else None),
                (str(row.get("DOR_UC"))[:10] if pd.notna(row.get("DOR_UC")) else None),
                safe_int(row.get("ACT_YR_BLT")),
                safe_int(row.get("TOT_LVG_AREA")),
                jv,
                safe_float(row.get("AV_SD")),
                safe_float(row.get("TV_SD")),
                land_val,
                building_val,
                safe_float(row.get("SALE_PRC1")),
                build_sale_date(row.get("SALE_YR1"), row.get("SALE_MO1")),
            )
            records.append(rec)
        if not records:
            continue
        with conn.cursor() as cur:
            upsert_chunk(cur, records)
        conn.commit()
        total += len(records)
        if total % 25000 < len(records):
            print(f"[{county}] Progress: {total} rows upserted")
    print(f"[{county}] Done: {total} rows upserted")
    return total


def main():
    parser = argparse.ArgumentParser(description="Bulk NAL loader to florida_parcels (direct Postgres)")
    parser.add_argument("--counties", type=str, default="", help="Comma-separated list of counties to process (default: all detected)")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--chunk-rows", type=int, default=10000, help="Rows per chunk read from CSV")
    parser.add_argument("--analyze-every", type=str, default="county", choices=["none", "county"], help="Run ANALYZE after each county")
    args = parser.parse_args()

    load_env(os.path.join(ROOT, ".env"))
    db_url = get_db_url()

    # Discover counties
    if args.counties:
        requested = [c.strip() for c in args.counties.split(",") if c.strip()]
        counties = [c for c in requested if os.path.isdir(os.path.join(DATA_DIR, c))]
    else:
        counties = discover_counties()
    if not counties:
        print("No counties found to process.")
        return

    print(f"Processing counties: {', '.join(counties[:10])}{'...' if len(counties) > 10 else ''}")

    with connect(db_url) as conn:
        with conn.cursor() as cur:
            # Session tuning
            cur.execute("SET statement_timeout = '30min'")
            cur.execute("SET lock_timeout = '30s'")
            cur.execute("SET idle_in_transaction_session_timeout = '2min'")
        conn.commit()

        grand_total = 0
        for c in counties:
            try:
                cnt = process_county(conn, c, args.year, args.chunk_rows)
                grand_total += cnt
                if args.analyze_every == "county":
                    with conn.cursor() as cur:
                        cur.execute("ANALYZE public.florida_parcels")
                    conn.commit()
            except Exception as e:
                print(f"[{c}] ERROR: {e}")
                conn.rollback()

    print(f"All done. Total rows upserted: {grand_total}")


if __name__ == "__main__":
    main()
