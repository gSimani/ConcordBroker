"""
Create Sunbiz tables/indexes idempotently, enable RLS, and verify status.
"""
import os, json
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGS = os.path.join(ROOT, "logs")
os.makedirs(LOGS, exist_ok=True)
# load .env
env = {}
try:
    with open(os.path.join(ROOT, '.env'), 'r', encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if line and not line.startswith('#') and '=' in line:
                k,v = line.split('=',1)
                env[k.strip()] = v.strip()
except Exception:
    pass
os.environ.update(env)
DB = os.getenv('POSTGRES_URL_NON_POOLING') or os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
if not DB:
    print('ERROR: no database URL found in .env')
    raise SystemExit(2)
report = {'ts': datetime.now().isoformat(), 'steps': []}
stmts = [
    ("create_sunbiz_corporate", """
    CREATE TABLE IF NOT EXISTS sunbiz_corporate (
      id BIGSERIAL PRIMARY KEY,
      corporate_name TEXT NOT NULL,
      fein TEXT,
      principal_address TEXT,
      mailing_address TEXT,
      status TEXT,
      officers JSONB,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """),
    ("idx_sunbiz_name", "CREATE INDEX IF NOT EXISTS idx_sunbiz_name ON sunbiz_corporate(corporate_name);"),
    ("idx_sunbiz_name_gin", "CREATE INDEX IF NOT EXISTS idx_sunbiz_name_gin ON sunbiz_corporate USING GIN (to_tsvector('english', corporate_name));"),
    ("rls_sunbiz_corporate", "ALTER TABLE sunbiz_corporate ENABLE ROW LEVEL SECURITY;"),
    ("create_owner_entity_links", """
    CREATE TABLE IF NOT EXISTS owner_entity_links (
      id BIGSERIAL PRIMARY KEY,
      county TEXT,
      owner_name TEXT,
      norm_owner TEXT,
      sunbiz_id BIGINT,
      corporate_name TEXT,
      norm_corp TEXT,
      match_type TEXT,
      confidence NUMERIC,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """),
    ("idx_oel_owner", "CREATE INDEX IF NOT EXISTS idx_oel_owner ON owner_entity_links(norm_owner);"),
    ("idx_oel_sunbiz", "CREATE INDEX IF NOT EXISTS idx_oel_sunbiz ON owner_entity_links(sunbiz_id);"),
    ("rls_owner_entity_links", "ALTER TABLE owner_entity_links ENABLE ROW LEVEL SECURITY;")
]
with psycopg2.connect(DB) as conn:
    with conn.cursor() as cur:
        for name, sql in stmts:
            try:
                cur.execute(sql)
                conn.commit()
                report['steps'].append({'name': name, 'status': 'ok'})
            except Exception as e:
                conn.rollback()
                report['steps'].append({'name': name, 'status': 'error', 'error': str(e)})
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        checks = {}
        cur.execute("SELECT to_regclass('public.sunbiz_corporate') AS regclass;")
        checks['sunbiz_corporate_exists'] = cur.fetchall()
        cur.execute("SELECT to_regclass('public.owner_entity_links') AS regclass;")
        checks['owner_entity_links_exists'] = cur.fetchall()
        cur.execute("SELECT COUNT(*) AS rows FROM sunbiz_corporate;")
        checks['sunbiz_corporate_count'] = cur.fetchall()
        cur.execute("SELECT COUNT(*) AS rows FROM owner_entity_links;")
        checks['owner_entity_links_count'] = cur.fetchall()
        cur.execute("""
            SELECT tablename, indexname, indexdef
            FROM pg_indexes
            WHERE tablename IN ('sunbiz_corporate','owner_entity_links')
            ORDER BY tablename, indexname;
        """)
        checks['index_defs'] = cur.fetchall()
        cur.execute("""
            SELECT c.relname AS index_name, i.indisvalid
            FROM pg_index i
            JOIN pg_class c ON c.oid = i.indexrelid
            WHERE c.relname IN ('idx_sunbiz_name','idx_sunbiz_name_gin','idx_oel_owner','idx_oel_sunbiz');
        """)
        checks['index_validity'] = cur.fetchall()
        cur.execute("""
            SELECT table_name, row_security
            FROM information_schema.tables
            WHERE table_schema='public' AND table_name IN ('sunbiz_corporate','owner_entity_links');
        """)
        checks['rls_status'] = cur.fetchall()
        cur.execute("""
            SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
            FROM pg_policies
            WHERE tablename IN ('sunbiz_corporate','owner_entity_links');
        """)
        checks['policies'] = cur.fetchall()
report['checks'] = checks
out = os.path.join(LOGS, 'sunbiz_schema_setup.json')
with open(out, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, default=str)
print(json.dumps(report, indent=2, default=str))
