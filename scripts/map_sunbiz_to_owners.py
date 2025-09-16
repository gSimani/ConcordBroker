"""
Map florida_parcels owners to Sunbiz corporate entities and emit links.
"""

import os
import re
import csv
from datetime import datetime
from typing import Dict, List, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGS = os.path.join(ROOT, "logs")


def load_env():
    env_path = os.path.join(ROOT, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


SUFFIX_RE = re.compile(r"\b(LLC|L\.L\.C\.|INC|INC\.|CORP|CORPORATION|CO\.|COMPANY|LP|LLP|L\.P\.|TRUST|HOLDINGS|INVESTMENTS|PROPERTIES|GROUP|PARTNERS|CAPITAL)\b", re.I)
NON_WORD = re.compile(r"[^A-Z0-9\s]")
WS = re.compile(r"\s+")


def norm_name(s: str) -> str:
    s = s.upper().strip()
    s = SUFFIX_RE.sub("", s)
    s = NON_WORD.sub(" ", s)
    s = WS.sub(" ", s)
    return s.strip()


def main():
    os.makedirs(LOGS, exist_ok=True)
    load_env()
    db_url = os.getenv("POSTGRES_URL_NON_POOLING") or os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not db_url:
        print("ERROR: No database URL in .env")
        return

    counties = os.environ.get("OWNER_LINK_COUNTIES", "BROWARD,ALACHUA").split(",")
    counties = [c.strip() for c in counties if c.strip()]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_csv = os.path.join(LOGS, f"owner_entity_links_{ts}.csv")

    with psycopg2.connect(db_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Load corporate names from either sunbiz_corporate or sunbiz_entities
            try:
                cur.execute("SELECT id, corporate_name FROM sunbiz_corporate WHERE corporate_name IS NOT NULL")
                corp_rows = cur.fetchall()
                name_field = 'corporate_name'
            except Exception:
                try:
                    cur.execute("SELECT id, entity_name AS corporate_name FROM sunbiz_entities WHERE entity_name IS NOT NULL")
                    corp_rows = cur.fetchall()
                    name_field = 'corporate_name'
                except Exception:
                    print("No Sunbiz corporate/entities tables found; aborting.")
                    return

            corp_map: Dict[str, List[Tuple[str, str]]] = {}
            for r in corp_rows:
                cname = r.get(name_field) or ""
                nid = str(r.get("id"))
                n = norm_name(cname)
                if not n:
                    continue
                corp_map.setdefault(n, []).append((nid, cname))
            print(f"Sunbiz entities loaded: {len(corp_rows)}")

            with open(out_csv, "w", newline="", encoding="utf-8") as fw:
                wr = csv.writer(fw)
                wr.writerow(["county","owner_name","norm_owner","sunbiz_id","corporate_name","norm_corp","match_type","confidence"])

                for county in counties:
                    print(f"[{county}] loading distinct owners...")
                    cur.execute(
                        """
                        SELECT DISTINCT owner_name
                        FROM florida_parcels
                        WHERE county = %s AND owner_name IS NOT NULL AND owner_name <> ''
                        """,
                        (county,)
                    )
                    owners = [row["owner_name"] for row in cur.fetchall()]
                    print(f"[{county}] owners: {len(owners)}")
                    matches = 0
                    for oname in owners:
                        o_norm = norm_name(oname)
                        if not o_norm:
                            continue
                        if o_norm in corp_map:
                            for nid, cname in corp_map[o_norm]:
                                wr.writerow([county, oname, o_norm, nid, cname, o_norm, "equal_norm", 1.0])
                                matches += 1
                        else:
                            # conservative contains rule
                            for ckey, vals in corp_map.items():
                                if len(ckey) < 6:
                                    continue
                                if ckey in o_norm and len(ckey.split()) >= 2:
                                    nid, cname = vals[0]
                                    wr.writerow([county, oname, o_norm, nid, cname, ckey, "contains", 0.8])
                                    matches += 1
                                    break
                    print(f"[{county}] matches: {matches}")

    print(f"Wrote: {out_csv}")


if __name__ == "__main__":
    main()
