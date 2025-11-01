#!/usr/bin/env python3
"""
Health Check Script for Docker HEALTHCHECK
Returns exit code 0 if healthy, 1 if unhealthy
"""

import os
import sys
import psycopg2
from datetime import datetime, timedelta

def check_health():
    """Check if orchestrator is healthy"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv('SUPABASE_HOST'),
            database=os.getenv('SUPABASE_DB', 'postgres'),
            user=os.getenv('SUPABASE_USER', 'postgres'),
            password=os.getenv('SUPABASE_PASSWORD'),
            port=int(os.getenv('SUPABASE_PORT', '5432')),
            connect_timeout=5
        )
        cursor = conn.cursor()

        # Check if orchestrator has sent heartbeat recently (< 2 minutes)
        cursor.execute("""
            SELECT last_heartbeat
            FROM agent_registry
            WHERE agent_type = 'orchestrator'
            AND status = 'online'
            ORDER BY last_heartbeat DESC
            LIMIT 1;
        """)

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            print("ERROR: No orchestrator heartbeat found")
            return False

        last_heartbeat = result[0]
        age = (datetime.now() - last_heartbeat).total_seconds()

        if age > 120:  # 2 minutes
            print(f"ERROR: Last heartbeat {age:.0f}s ago (stale)")
            return False

        print(f"OK: Last heartbeat {age:.0f}s ago")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False


if __name__ == "__main__":
    if check_health():
        sys.exit(0)  # Healthy
    else:
        sys.exit(1)  # Unhealthy
