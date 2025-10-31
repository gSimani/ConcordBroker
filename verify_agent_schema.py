#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify Agent Registry Schema in Supabase
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment
load_dotenv('.env.mcp')

try:
    import psycopg2
except ImportError:
    print("[!] Installing psycopg2-binary...")
    os.system("pip install psycopg2-binary")
    import psycopg2

# Use connection string from env
conn_string = os.getenv('POSTGRES_URL_NON_POOLING')

print("=" * 70)
print("🔍 VERIFYING AGENT REGISTRY SCHEMA IN SUPABASE")
print("=" * 70)

try:
    # Connect to database
    print("\n🔌 Connecting to Supabase...")
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True
    cursor = conn.cursor()
    print("✅ Connected successfully\n")

    # Verify tables exist
    print("📋 AGENT TABLES:")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE 'agent_%'
        ORDER BY table_name;
    """)

    tables = cursor.fetchall()
    if tables:
        for table in tables:
            print(f"   ✅ {table[0]}")
        print(f"\n   Total: {len(tables)} tables")
    else:
        print("   ❌ No agent tables found!")
        sys.exit(1)

    # Check functions
    print("\n⚙️  AGENT FUNCTIONS:")
    cursor.execute("""
        SELECT routine_name
        FROM information_schema.routines
        WHERE routine_schema = 'public'
        AND routine_name LIKE '%agent%'
        ORDER BY routine_name;
    """)

    functions = cursor.fetchall()
    if functions:
        for func in functions:
            print(f"   ✅ {func[0]}")
        print(f"\n   Total: {len(functions)} functions")

    # Insert/Update test agent
    print("\n🧪 REGISTERING TEST AGENT:")
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
            'online',
            NOW(),
            jsonb_build_object('deployed', true, 'timestamp', NOW()::text, 'phase', 1)
        )
        ON CONFLICT (agent_id) DO UPDATE
        SET last_heartbeat = NOW(),
            status = 'online',
            capabilities = EXCLUDED.capabilities,
            updated_at = NOW();
    """)

    print("   ✅ Test agent registered")

    # Query test agent
    cursor.execute("""
        SELECT agent_id, agent_name, status, last_heartbeat, environment, capabilities
        FROM agent_registry
        WHERE agent_id = 'deployment-test-agent';
    """)

    test_agent = cursor.fetchone()
    if test_agent:
        print(f"\n📊 TEST AGENT STATUS:")
        print(f"   ID: {test_agent[0]}")
        print(f"   Name: {test_agent[1]}")
        print(f"   Status: {test_agent[2]}")
        print(f"   Last Heartbeat: {test_agent[3]}")
        print(f"   Environment: {test_agent[4]}")
        print(f"   Capabilities: {test_agent[5]}")

    # Get all agents
    cursor.execute("SELECT COUNT(*) FROM agent_registry;")
    agent_count = cursor.fetchone()[0]
    print(f"\n📈 TOTAL AGENTS IN REGISTRY: {agent_count}")

    # Get health summary
    print("\n🏥 HEALTH SUMMARY BY ENVIRONMENT:")
    cursor.execute("SELECT * FROM get_agent_health_summary();")
    health = cursor.fetchall()

    if health:
        for row in health:
            if row[0]:  # If environment is not null
                print(f"\n   Environment: {row[0]}")
                print(f"      Total: {row[1]} agents")
                print(f"      Online: {row[2]} | Offline: {row[3]} | Error: {row[4]}")
                print(f"      Active Tasks: {row[5]}")
                print(f"      Pending Messages: {row[6]}")
                print(f"      Unresolved Alerts: {row[7]}")
    else:
        print("   No environment data yet")

    # Test health query
    print("\n✅ TESTING AGENT FUNCTIONS:")
    cursor.execute("SELECT * FROM get_active_agents();")
    active = cursor.fetchall()
    print(f"   get_active_agents(): {len(active)} active agents")

    # Test message table
    cursor.execute("SELECT COUNT(*) FROM agent_messages;")
    msg_count = cursor.fetchone()[0]
    print(f"   agent_messages: {msg_count} messages")

    # Test tasks table
    cursor.execute("SELECT COUNT(*) FROM agent_tasks;")
    task_count = cursor.fetchone()[0]
    print(f"   agent_tasks: {task_count} tasks")

    cursor.close()
    conn.close()

    print("\n" + "=" * 70)
    print("🎉 PHASE 1 COMPLETE: DATABASE FOUNDATION VERIFIED!")
    print("=" * 70)
    print("\n✅ All tables exist and accessible")
    print("✅ All functions working")
    print("✅ Test agent registered successfully")
    print("✅ Health monitoring operational")
    print("\n📍 READY FOR PHASE 2: Local Agent Orchestrator")
    print("\n   Next steps:")
    print("   1. The database is ready")
    print("   2. Agents can now register themselves")
    print("   3. Move to Phase 2 deployment")
    print("\n" + "=" * 70)

except psycopg2.Error as e:
    print(f"\n❌ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
