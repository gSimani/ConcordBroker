#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Agent Activity - See what agents are doing
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv('.env.mcp')

import psycopg2
import psycopg2.extras

def main():
    print("=" * 80)
    print("  🔍 AGENT ACTIVITY MONITOR")
    print("=" * 80)

    conn_string = os.getenv('POSTGRES_URL_NON_POOLING')
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Check agents
    print("\n📊 REGISTERED AGENTS:")
    cursor.execute("""
        SELECT agent_id, agent_name, agent_type, status,
               last_heartbeat, environment
        FROM agent_registry
        ORDER BY last_heartbeat DESC;
    """)
    agents = cursor.fetchall()

    for agent in agents:
        status_icon = "✅" if agent['status'] == 'online' else "❌"
        print(f"  {status_icon} {agent['agent_name']}")
        print(f"     ID: {agent['agent_id']}")
        print(f"     Type: {agent['agent_type']} | Env: {agent['environment']}")
        print(f"     Status: {agent['status']}")
        print(f"     Last Heartbeat: {agent['last_heartbeat']}")
        print()

    # Check messages
    print("\n📬 AGENT MESSAGES:")
    cursor.execute("""
        SELECT message_id, from_agent_id, to_agent_id, message_type,
               status, priority, created_at
        FROM agent_messages
        ORDER BY created_at DESC
        LIMIT 10;
    """)
    messages = cursor.fetchall()

    if messages:
        for msg in messages:
            print(f"  📨 {msg['from_agent_id']}")
            print(f"     → {msg['to_agent_id']}")
            print(f"     Type: {msg['message_type']} | Priority: {msg['priority']}")
            print(f"     Status: {msg['status']} | Time: {msg['created_at']}")
            print()
    else:
        print("  No messages yet")

    # Check alerts
    print("\n🚨 AGENT ALERTS:")
    cursor.execute("""
        SELECT alert_id, agent_id, alert_type, severity,
               message, status, created_at
        FROM agent_alerts
        ORDER BY created_at DESC
        LIMIT 10;
    """)
    alerts = cursor.fetchall()

    if alerts:
        for alert in alerts:
            severity_icon = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }.get(alert['severity'], '⚪')

            print(f"  {severity_icon} {alert['alert_type']}")
            print(f"     Agent: {alert['agent_id']}")
            print(f"     Severity: {alert['severity']}")
            print(f"     Message: {alert['message']}")
            print(f"     Status: {alert['status']} | Time: {alert['created_at']}")
            print()
    else:
        print("  No alerts yet")

    # Check metrics
    print("\n📈 AGENT METRICS (Recent):")
    cursor.execute("""
        SELECT agent_id, metric_type, metric_name, metric_value,
               recorded_at
        FROM agent_metrics
        ORDER BY recorded_at DESC
        LIMIT 10;
    """)
    metrics = cursor.fetchall()

    if metrics:
        for metric in metrics:
            print(f"  📊 {metric['agent_id']}")
            print(f"     Type: {metric['metric_type']} | Name: {metric['metric_name']}")
            print(f"     Value: {metric['metric_value']}")
            print(f"     Time: {metric['recorded_at']}")
            print()
    else:
        print("  No metrics yet")

    cursor.close()
    conn.close()

    print("=" * 80)

if __name__ == "__main__":
    main()
