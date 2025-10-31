#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deploy Agent Registry Schema to Supabase
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment
load_dotenv('.env.mcp')

try:
    import psycopg2
except ImportError:
    print("[!] psycopg2 not installed. Installing...")
    os.system("pip install psycopg2-binary")
    import psycopg2

# Connection details
from urllib.parse import quote_plus

# Use direct connection string from env (already has pooler)
conn_string = os.getenv('POSTGRES_URL_NON_POOLING')

if not conn_string:
    # Fallback to building it manually
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE', 'postgres')
    encoded_password = quote_plus(POSTGRES_PASSWORD)
    conn_string = f"postgresql://{POSTGRES_USER}:{encoded_password}@{POSTGRES_HOST}:5432/{POSTGRES_DATABASE}"

print("🚀 Deploying Agent Registry Schema to Supabase...")
print(f"📍 Using connection string from environment")

try:
    # Read schema file
    schema_path = Path('setup/agent_registry_schema.sql')
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        sys.exit(1)

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    print(f"📄 Loaded schema file: {len(schema_sql)} characters")

    # Connect to database
    print("🔌 Connecting to Supabase...")
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True
    cursor = conn.cursor()

    print("✅ Connected successfully")

    # Execute schema
    print("📊 Creating tables and functions...")
    cursor.execute(schema_sql)

    print("✅ Schema deployed successfully!")

    # Verify tables exist
    print("\n🔍 Verifying tables...")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE 'agent_%'
        ORDER BY table_name;
    """)

    tables = cursor.fetchall()
    print(f"\n📋 Agent tables created ({len(tables)}):")
    for table in tables:
        print(f"   ✅ {table[0]}")

    # Check functions
    print("\n🔍 Verifying functions...")
    cursor.execute("""
        SELECT routine_name
        FROM information_schema.routines
        WHERE routine_schema = 'public'
        AND routine_name LIKE '%agent%'
        ORDER BY routine_name;
    """)

    functions = cursor.fetchall()
    print(f"\n⚙️  Agent functions created ({len(functions)}):")
    for func in functions:
        print(f"   ✅ {func[0]}")

    # Insert test orchestrator
    print("\n🧪 Inserting test agent...")
    cursor.execute("""
        INSERT INTO agent_registry (
            agent_id,
            agent_name,
            agent_type,
            environment,
            status,
            last_heartbeat,
            capabilities
        ) VALUES (
            'deployment-test-agent',
            'Deployment Test Agent',
            'test',
            'deployment',
            'offline',
            NOW(),
            jsonb_build_object('deployed', true, 'timestamp', NOW()::text)
        )
        ON CONFLICT (agent_id) DO UPDATE
        SET last_heartbeat = NOW(),
            capabilities = EXCLUDED.capabilities;
    """)

    print("✅ Test agent inserted")

    # Query test agent
    cursor.execute("""
        SELECT agent_id, agent_name, status, last_heartbeat, environment
        FROM agent_registry
        WHERE agent_id = 'deployment-test-agent';
    """)

    test_agent = cursor.fetchone()
    if test_agent:
        print(f"\n🎯 Test Agent Retrieved:")
        print(f"   ID: {test_agent[0]}")
        print(f"   Name: {test_agent[1]}")
        print(f"   Status: {test_agent[2]}")
        print(f"   Last Heartbeat: {test_agent[3]}")
        print(f"   Environment: {test_agent[4]}")

    # Get health summary
    print("\n📊 Agent Health Summary:")
    cursor.execute("SELECT * FROM get_agent_health_summary();")
    health = cursor.fetchall()

    if health:
        for row in health:
            print(f"   Environment: {row[0]}")
            print(f"     Total Agents: {row[1]}")
            print(f"     Online: {row[2]}, Offline: {row[3]}, Error: {row[4]}")
    else:
        print("   No agents yet (this is normal)")

    cursor.close()
    conn.close()

    print("\n" + "="*60)
    print("🎉 PHASE 1 COMPLETE: Database Foundation Ready!")
    print("="*60)
    print("\n✅ All tables created")
    print("✅ All functions deployed")
    print("✅ Test agent registered")
    print("✅ Connection verified")
    print("\n📍 Next: Phase 2 - Local Orchestrator")
    print("   Run: python local-agent-orchestrator/orchestrator.py")

except psycopg2.Error as e:
    print(f"\n❌ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
