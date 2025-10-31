#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Watch Agent Activity in Real-Time
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv('.env.mcp')

import psycopg2
import psycopg2.extras

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    conn_string = os.getenv('POSTGRES_URL_NON_POOLING')

    print("=" * 80)
    print("  🎬 REAL-TIME AGENT ACTIVITY MONITOR")
    print("  Watching for agent communication and activity...")
    print("  Press Ctrl+C to stop")
    print("=" * 80)
    print()

    last_message_count = 0
    last_alert_count = 0
    last_metric_count = 0
    iteration = 0

    try:
        while True:
            iteration += 1
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Check for new messages
            cursor.execute("SELECT COUNT(*) as count FROM agent_messages;")
            message_count = cursor.fetchone()['count']

            # Check for new alerts
            cursor.execute("SELECT COUNT(*) as count FROM agent_alerts;")
            alert_count = cursor.fetchone()['count']

            # Check for new metrics
            cursor.execute("SELECT COUNT(*) as count FROM agent_metrics;")
            metric_count = cursor.fetchone()['count']

            # Check agent heartbeats
            cursor.execute("""
                SELECT agent_id, agent_name, status, last_heartbeat
                FROM agent_registry
                WHERE environment = 'pc' AND status = 'online'
                ORDER BY last_heartbeat DESC;
            """)
            online_agents = cursor.fetchall()

            # Display current status
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iteration #{iteration}")
            print(f"  Online Agents: {len(online_agents)}")
            print(f"  Messages: {message_count} {'🆕' if message_count > last_message_count else ''}")
            print(f"  Alerts: {alert_count} {'🆕' if alert_count > last_alert_count else ''}")
            print(f"  Metrics: {metric_count} {'🆕' if metric_count > last_metric_count else ''}")

            # Show agent heartbeats
            for agent in online_agents:
                age = (datetime.now(agent['last_heartbeat'].tzinfo) - agent['last_heartbeat']).seconds
                print(f"    💓 {agent['agent_name']}: {age}s ago")

            # Show new messages if any
            if message_count > last_message_count:
                print("\n  🆕 NEW MESSAGES:")
                cursor.execute("""
                    SELECT from_agent_id, to_agent_id, message_type, status, created_at
                    FROM agent_messages
                    ORDER BY created_at DESC
                    LIMIT 5;
                """)
                messages = cursor.fetchall()
                for msg in messages:
                    print(f"    📨 {msg['from_agent_id'][:30]} → {msg['to_agent_id'][:30]}")
                    print(f"       Type: {msg['message_type']} | Status: {msg['status']}")

            # Show new alerts if any
            if alert_count > last_alert_count:
                print("\n  🆕 NEW ALERTS:")
                cursor.execute("""
                    SELECT agent_id, alert_type, severity, message, created_at
                    FROM agent_alerts
                    ORDER BY created_at DESC
                    LIMIT 5;
                """)
                alerts = cursor.fetchall()
                for alert in alerts:
                    print(f"    🚨 {alert['alert_type']} [{alert['severity']}]")
                    print(f"       From: {alert['agent_id'][:40]}")
                    print(f"       {alert['message'][:60]}")

            # Show new metrics if any
            if metric_count > last_metric_count:
                print("\n  🆕 NEW METRICS:")
                cursor.execute("""
                    SELECT agent_id, metric_name, metric_value, recorded_at
                    FROM agent_metrics
                    ORDER BY recorded_at DESC
                    LIMIT 5;
                """)
                metrics = cursor.fetchall()
                for metric in metrics:
                    print(f"    📊 {metric['metric_name']}: {metric['metric_value']}")
                    print(f"       From: {metric['agent_id'][:40]}")

            last_message_count = message_count
            last_alert_count = alert_count
            last_metric_count = metric_count

            cursor.close()
            conn.close()

            time.sleep(10)  # Check every 10 seconds

    except KeyboardInterrupt:
        print("\n\n  🛑 Monitoring stopped\n")

if __name__ == "__main__":
    main()
