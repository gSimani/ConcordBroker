import json
import os
from datetime import datetime
from psycopg2 import connect
from psycopg2.extras import RealDictCursor

ROOT = r"C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker"
ENV_PATH = os.path.join(ROOT, '.env')
if os.path.exists(ENV_PATH):
    for line in open(ENV_PATH, 'r', encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip())

db_url = os.getenv('POSTGRES_URL_NON_POOLING') or os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
# Sanitize DSN for psycopg2 (remove unsupported query params like supa=...)
import re
if db_url and 'supa=' in db_url:
    db_url = re.sub(r'([&?])supa=[^&]+', r'$1', db_url)
    db_url = db_url.replace('?&','?').rstrip('&').rstrip('?')
if not db_url:
    print(json.dumps({'ok': False, 'error': 'DATABASE_URL not found'}, indent=2))
    raise SystemExit(2)

queries = {
  'index_validity': """
    SELECT c.relname AS index_name, i.indisvalid
    FROM pg_index i
    JOIN pg_class c ON c.oid = i.indexrelid
    WHERE c.relname IN ('ux_florida_parcels_parcel_county_year','idx_parcels_county_year');
  """,
  'index_list': """
    SELECT indexname, indexdef
    FROM pg_indexes
    WHERE tablename = 'florida_parcels'
    ORDER BY indexname;
  """,
  'remaining_dups': """
    SELECT COUNT(*) AS remaining_dups FROM (
      SELECT parcel_id, county, year, COUNT(*) AS c
      FROM public.florida_parcels
      GROUP BY parcel_id, county, year
      HAVING COUNT(*) > 1
    ) t;
  """,
  'activity': """
    SELECT now() AS ts, pid, wait_event_type, wait_event, state,
           left(regexp_replace(query, '\\s+', ' ', 'g'), 200) AS query
    FROM pg_stat_activity
    WHERE query ILIKE '%florida_parcels%'
    ORDER BY ts DESC
    LIMIT 20;
  """,
  'role_timeouts': """
    SELECT rolname, rolconfig
    FROM pg_roles
    WHERE rolname IN ('anon','authenticated','service_role','authenticator','postgres');
  """,
  'statement_timeout': "show statement_timeout;",
}

out = {'ok': True, 'ts': datetime.utcnow().isoformat()+'Z', 'queries': {}}
with connect(db_url) as conn:
  with conn.cursor(cursor_factory=RealDictCursor) as cur:
    for k, q in queries.items():
      try:
        cur.execute(q)
        data = cur.fetchall() if cur.description else []
        out['queries'][k] = data
      except Exception as e:
        out['queries'][k] = {'error': str(e)}

log_path = os.path.join(ROOT, 'logs', 'verify_db_enforcement.json')
os.makedirs(os.path.dirname(log_path), exist_ok=True)
open(log_path, 'w', encoding='utf-8').write(json.dumps(out, indent=2, default=str))
pass



