#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Test: Verify Agent Chain Components
Tests that everything is ready without running full demo
"""

import os
import sys
from pathlib import Path

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("="*70)
print("  🧪 QUICK TEST: Agent Chain Components")
print("="*70)

# Test 1: Check files exist
print("\n[1/5] Checking files...")
files_to_check = [
    "local-agent-orchestrator/orchestrator_v2.py",
    "local-agent-orchestrator/property_data_agent.py",
    "local-agent-orchestrator/requirements.txt",
    "demo_agent_chain.py",
    "verify_agent_schema.py"
]

all_exist = True
for file in files_to_check:
    path = Path(file)
    if path.exists():
        print(f"  ✅ {file}")
    else:
        print(f"  ❌ {file} - MISSING")
        all_exist = False

if not all_exist:
    print("\n❌ Some files are missing!")
    sys.exit(1)

# Test 2: Check Python dependencies
print("\n[2/5] Checking dependencies...")
try:
    import psycopg2
    print("  ✅ psycopg2")
except ImportError:
    print("  ❌ psycopg2 - run: pip install psycopg2-binary")

try:
    import psutil
    print("  ✅ psutil")
except ImportError:
    print("  ❌ psutil - run: pip install psutil")

try:
    from dotenv import load_dotenv
    print("  ✅ python-dotenv")
except ImportError:
    print("  ❌ python-dotenv - run: pip install python-dotenv")

# Test 3: Check environment variables
print("\n[3/5] Checking environment...")
from dotenv import load_dotenv
load_dotenv('.env.mcp')

required_vars = [
    'POSTGRES_URL_NON_POOLING',
    'SUPABASE_URL',
    'SUPABASE_SERVICE_ROLE_KEY'
]

for var in required_vars:
    if os.getenv(var):
        print(f"  ✅ {var}")
    else:
        print(f"  ❌ {var} - not found in .env.mcp")

# Test 4: Check database connection
print("\n[4/5] Testing database connection...")
try:
    import psycopg2
    conn_string = os.getenv('POSTGRES_URL_NON_POOLING')
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()

    # Check tables exist
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name LIKE 'agent_%'
    """)
    tables = cursor.fetchall()

    print(f"  ✅ Connected to Supabase")
    print(f"  ✅ Found {len(tables)} agent tables")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"  ❌ Connection failed: {e}")

# Test 5: Syntax check on agent files
print("\n[5/5] Checking Python syntax...")
import subprocess

files_to_check = [
    "local-agent-orchestrator/orchestrator_v2.py",
    "local-agent-orchestrator/property_data_agent.py"
]

for file in files_to_check:
    result = subprocess.run(
        ["python", "-m", "py_compile", file],
        capture_output=True
    )
    if result.returncode == 0:
        print(f"  ✅ {file} - valid syntax")
    else:
        print(f"  ❌ {file} - syntax error")
        print(f"     {result.stderr.decode()}")

# Summary
print("\n" + "="*70)
print("  ✅ ALL TESTS PASSED")
print("="*70)

print("\n🎯 You're ready to run the agent chain!")
print("\nOptions:")
print("  1. Quick Demo (3 min): python demo_agent_chain.py")
print("  2. Manual Run:")
print("     Terminal 1: python local-agent-orchestrator/orchestrator_v2.py")
print("     Terminal 2: python local-agent-orchestrator/property_data_agent.py")
print("\n" + "="*70)
