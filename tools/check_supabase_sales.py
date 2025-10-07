import os
import sys
import json


def load_dotenv_if_available():
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    # Load root and API .env if present
    for path in [".env", os.path.join("apps", "api", ".env")]:
        if os.path.exists(path):
            load_dotenv(path, override=False)


def create_supabase_client():
    try:
        from supabase import create_client
    except Exception as e:
        print("ERROR: supabase python client not installed (pip install supabase)", file=sys.stderr)
        raise
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY")
    if not url or not key:
        print("MISSING_ENV: SUPABASE_URL and/or SUPABASE_ANON_KEY not set.")
        sys.exit(3)
    return create_client(url, key)


TABLES = [
    "property_sales_history",
    "fl_sdf_sales",
    "property_sales",
    "florida_parcels",
    "fl_sales",
    "sales_data",
    "property_transactions",
    "deed_records",
    "florida_sales",
    "broward_sales",
    "miami_dade_sales",
    "palm_beach_sales",
]


def main():
    load_dotenv_if_available()
    try:
        supabase = create_supabase_client()
    except Exception as e:
        print(f"ERROR: cannot create Supabase client: {e}")
        sys.exit(2)

    summary = {
        "tables": [],
        "samples": {},
    }

    for table in TABLES:
        info = {"name": table, "exists": False, "count": None, "sales_columns": []}
        try:
            # HEAD count
            res = supabase.table(table).select("*", count="exact", head=True).execute()
            count = getattr(res, "count", None)
            info["exists"] = True
            info["count"] = count

            # Sample to get columns
            sample = supabase.table(table).select("*", count=None).limit(1).execute()
            cols = list(sample.data[0].keys()) if sample.data else []
            sales_cols = [c for c in cols if any(k in c for k in ["sale", "price", "deed", "book", "page", "transaction", "date"])]
            info["sales_columns"] = sales_cols
            
        except Exception as e:
            # Missing table or permission; mark and continue
            info["error"] = str(e)

        summary["tables"].append(info)

    # Targeted samples
    def try_query(label, table, select, filters=None, order=None, limit=5):
        try:
            q = supabase.table(table).select(select)
            if filters:
                for f in filters:
                    op = f.get("op")
                    if op == "gt":
                        q = q.gt(f["col"], f["val"]) 
                    elif op == "not.is":
                        # supabase-py uses .is_(col, value); value None means IS NULL
                        # We want NOT IS NULL -> negate by filtering gt on empty string when date? Simpler: neq None
                        q = q.neq(f["col"], None)
                    elif op == "eq":
                        q = q.eq(f["col"], f["val"]) 
            if order:
                q = q.order(order, desc=True)
            data = q.limit(limit).execute().data
            summary["samples"][label] = data
        except Exception as e:
            summary["samples"][label] = {"error": str(e)}

    try_query(
        "florida_parcels_recent_sales",
        "florida_parcels",
        "parcel_id, county, sale_price, sale_date",
        filters=[{"col": "sale_price", "op": "gt", "val": 0}, {"col": "sale_date", "op": "not.is", "val": None}],
        order="sale_date",
        limit=5,
    )

    for t in ["property_sales_history", "fl_sdf_sales", "property_sales"]:
        try_query(
            f"{t}_recent",
            t,
            "*",
            order="sale_date",
            limit=5,
        )

    print(json.dumps(summary, default=str))


if __name__ == "__main__":
    main()

