#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Local Orchestrator with Agent Communication
Manages agents and coordinates their work through message passing
"""

import os
import sys
import time
import platform
import json
import subprocess
from datetime import datetime
from pathlib import Path
from threading import Thread

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env.mcp')

import psycopg2
import psycopg2.extras
import psutil

class EnhancedOrchestrator:
    """
    Enhanced orchestrator with agent communication
    """

    def __init__(self):
        self.agent_id = f"local-orchestrator-{platform.node()}"
        self.agent_name = f"Local PC Orchestrator ({platform.node()})"
        self.environment = "pc"
        self.conn = None
        self.running = False
        self.heartbeat_interval = 30
        self.message_check_interval = 10
        self.registered = False
        self.managed_agents = {}  # Track agents we're managing

    def connect(self):
        """Connect to Supabase"""
        try:
            conn_string = os.getenv('POSTGRES_URL_NON_POOLING')
            if not conn_string:
                raise Exception("POSTGRES_URL_NON_POOLING not found")

            self.conn = psycopg2.connect(conn_string)
            self.conn.autocommit = True
            return True
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            return False

    def register(self):
        """Register orchestrator"""
        if not self.conn:
            if not self.connect():
                return False

        try:
            cursor = self.conn.cursor()

            cpu_count = psutil.cpu_count()
            ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)

            cursor.execute("""
                INSERT INTO agent_registry (
                    agent_id, agent_name, agent_type, environment,
                    status, last_heartbeat, capabilities, metadata
                ) VALUES (
                    %s, %s, %s, %s, %s, NOW(),
                    %s::jsonb, %s::jsonb
                )
                ON CONFLICT (agent_id) DO UPDATE
                SET status = 'online',
                    last_heartbeat = NOW(),
                    capabilities = EXCLUDED.capabilities,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW();
            """, (
                self.agent_id,
                self.agent_name,
                'orchestrator',
                self.environment,
                'online',
                json.dumps({
                    'can_run_python': True,
                    'can_run_node': True,
                    'can_manage_agents': True,
                    'can_coordinate': True,
                    'system': {
                        'platform': platform.system(),
                        'machine': platform.machine(),
                        'cpu_count': cpu_count,
                        'ram_gb': ram_gb
                    }
                }),
                json.dumps({
                    'hostname': platform.node(),
                    'python_version': platform.python_version(),
                    'started_at': datetime.now().isoformat(),
                    'version': '2.0-enhanced'
                })
            ))

            cursor.close()
            self.registered = True
            return True

        except Exception as e:
            print(f"[ERROR] Registration failed: {e}")
            return False

    def check_messages(self):
        """Check for pending messages"""
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Get pending messages for this orchestrator
            cursor.execute("""
                SELECT message_id, from_agent_id, message_type, payload, priority, created_at
                FROM agent_messages
                WHERE to_agent_id = %s
                  AND status = 'pending'
                ORDER BY priority ASC, created_at ASC
                LIMIT 10;
            """, (self.agent_id,))

            messages = cursor.fetchall()

            # Mark as delivered
            if messages:
                message_ids = [m['message_id'] for m in messages]
                cursor.execute("""
                    UPDATE agent_messages
                    SET status = 'delivered',
                        delivered_at = NOW()
                    WHERE message_id = ANY(%s);
                """, (message_ids,))

            cursor.close()
            return messages

        except Exception as e:
            print(f"[ERROR] Message check failed: {e}")
            return []

    def handle_message(self, message):
        """Handle incoming message with Chain-of-Thought"""
        print(f"\n  📨 MESSAGE RECEIVED:")
        print(f"     From: {message['from_agent_id']}")
        print(f"     Type: {message['message_type']}")
        print(f"     Priority: {message['priority']}")

        # Chain-of-Thought reasoning
        print(f"\n  💭 Reasoning about message...")

        payload = message['payload']
        message_type = message['message_type']

        if message_type == 'alert':
            print(f"     → This is an alert, needs attention")

            alert_type = payload.get('alert_type')
            print(f"     → Alert type: {alert_type}")

            if alert_type == 'data_quality_issues':
                issues = payload.get('issues', [])
                print(f"     → Data quality issues detected: {issues}")
                print(f"     → Decision: Log as high-priority alert")

                # Store alert
                self.store_orchestrator_alert(
                    'data_quality',
                    'high',
                    f"Agent reported data quality issues: {', '.join(issues)}",
                    payload
                )

                # Could trigger remediation agent here
                print(f"     → Action: Would trigger remediation (Phase 4)")

        elif message_type == 'query':
            print(f"     → Agent is requesting information")
            # Handle queries
            pass

        elif message_type == 'response':
            print(f"     → Response to previous query")
            # Handle responses
            pass

        # Mark as processed
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE agent_messages
                SET status = 'processed',
                    processed_at = NOW()
                WHERE message_id = %s;
            """, (message['message_id'],))
            cursor.close()
            print(f"     ✅ Message processed")
        except Exception as e:
            print(f"     ❌ Failed to mark as processed: {e}")

    def store_orchestrator_alert(self, alert_type, severity, message, details):
        """Store alert from orchestrator's perspective"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO agent_alerts (
                    agent_id, alert_type, severity, message, details, status
                ) VALUES (%s, %s, %s, %s, %s::jsonb, 'active');
            """, (self.agent_id, alert_type, severity, message, json.dumps(details)))
            cursor.close()
            print(f"  🚨 Orchestrator logged alert: [{severity}] {message}")
        except Exception as e:
            print(f"  [ERROR] Failed to store alert: {e}")

    def send_heartbeat(self):
        """Send heartbeat with managed agents info"""
        if not self.conn:
            if not self.connect():
                return False

        try:
            cursor = self.conn.cursor()

            cpu_percent = psutil.cpu_percent(interval=1)
            ram_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:\\').percent

            cursor.execute("""
                UPDATE agent_registry
                SET last_heartbeat = NOW(),
                    status = 'online',
                    metadata = jsonb_set(
                        metadata,
                        '{resources}',
                        %s::jsonb
                    ),
                    updated_at = NOW()
                WHERE agent_id = %s;
            """, (
                json.dumps({
                    'cpu_percent': cpu_percent,
                    'ram_percent': ram_percent,
                    'disk_percent': disk_percent,
                    'managed_agents': len(self.managed_agents),
                    'timestamp': datetime.now().isoformat()
                }),
                self.agent_id
            ))

            cursor.close()
            return True

        except Exception as e:
            print(f"[ERROR] Heartbeat failed: {e}")
            self.conn = None
            return False

    def get_all_agents(self):
        """Get all agents in system"""
        if not self.conn:
            if not self.connect():
                return []

        try:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cursor.execute("""
                SELECT agent_id, agent_name, agent_type, environment, status, last_heartbeat
                FROM agent_registry
                ORDER BY
                    CASE WHEN status = 'online' THEN 0 ELSE 1 END,
                    last_heartbeat DESC;
            """)

            results = cursor.fetchall()
            cursor.close()
            return results

        except Exception as e:
            print(f"[ERROR] Failed to get agents: {e}")
            return []

    def get_pending_alerts(self):
        """Get unresolved alerts"""
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cursor.execute("""
                SELECT agent_id, alert_type, severity, message, created_at
                FROM agent_alerts
                WHERE status = 'active'
                ORDER BY
                    CASE severity
                        WHEN 'critical' THEN 0
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        ELSE 3
                    END,
                    created_at DESC
                LIMIT 5;
            """)

            results = cursor.fetchall()
            cursor.close()
            return results

        except Exception as e:
            print(f"[ERROR] Failed to get alerts: {e}")
            return []

    def display_status(self):
        """Enhanced status display"""
        print("\n" + "="*70)
        print(f"  ORCHESTRATOR STATUS - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)

        # Agents
        print(f"\n  🤖 AGENT MESH:")
        agents = self.get_all_agents()
        if agents:
            for agent in agents:
                status_icon = "✅" if agent['status'] == 'online' else "❌"
                env_icon = {
                    "pc": "💻",
                    "railway": "🚂",
                    "github": "🐙",
                    "deployment": "🧪"
                }.get(agent['environment'], "📦")

                type_label = {
                    'orchestrator': '[ORCH]',
                    'monitoring': '[MON]',
                    'processing': '[PROC]',
                    'test': '[TEST]'
                }.get(agent['agent_type'], '[AGENT]')

                print(f"    {status_icon} {env_icon} {type_label:<8} {agent['agent_name']:<35}")

        # Alerts
        alerts = self.get_pending_alerts()
        if alerts:
            print(f"\n  🚨 ACTIVE ALERTS ({len(alerts)}):")
            for alert in alerts:
                severity_icon = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(alert['severity'], '⚪')

                print(f"    {severity_icon} [{alert['severity'].upper()}] {alert['message'][:50]}")
                print(f"       Agent: {alert['agent_id']}")

        print("\n" + "="*70)

    def run(self):
        """Enhanced run loop with message handling"""
        print("\n" + "="*70)
        print("  🚀 ENHANCED LOCAL ORCHESTRATOR v2.0")
        print("="*70)
        print(f"\n  Features:")
        print(f"    ✓ Agent communication")
        print(f"    ✓ Chain-of-thought reasoning")
        print(f"    ✓ Alert management")
        print(f"    ✓ Agent coordination")

        # Connect
        print(f"\n  [1/3] Connecting...")
        if not self.connect():
            print("  ❌ Connection failed")
            return

        print("  ✅ Connected")

        # Register
        print(f"  [2/3] Registering...")
        if not self.register():
            print("  ❌ Registration failed")
            return

        print("  ✅ Registered")

        # Start
        print(f"  [3/3] Starting orchestration loop...")
        print("  ✅ Running")
        print("\n  Press Ctrl+C to stop\n")

        self.running = True
        heartbeat_count = 0
        message_check_count = 0

        try:
            while self.running:
                # Check messages more frequently than heartbeat
                message_check_count += 1
                if message_check_count >= self.message_check_interval:
                    messages = self.check_messages()
                    if messages:
                        print(f"\n  📬 {len(messages)} new message(s)")
                        for msg in messages:
                            self.handle_message(msg)
                    message_check_count = 0

                # Heartbeat
                time.sleep(1)
                heartbeat_count += 1

                if heartbeat_count >= self.heartbeat_interval:
                    if self.send_heartbeat():
                        heartbeat_count = 0

                        # Display status every 5 heartbeats
                        if heartbeat_count % 5 == 0:
                            self.display_status()
                        else:
                            print(f"  💓 Heartbeat sent at {datetime.now().strftime('%H:%M:%S')}")
                    else:
                        print(f"  ⚠️  Heartbeat failed, will retry...")

        except KeyboardInterrupt:
            print("\n\n  🛑 Stopping orchestrator...")
            self.stop()

    def stop(self):
        """Stop orchestrator"""
        self.running = False

        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    UPDATE agent_registry
                    SET status = 'offline',
                        updated_at = NOW()
                    WHERE agent_id = %s;
                """, (self.agent_id,))
                cursor.close()
                print("  ✅ Marked as offline")
            except:
                pass

            self.conn.close()

        print("  ✅ Stopped\n")


if __name__ == "__main__":
    orchestrator = EnhancedOrchestrator()
    orchestrator.run()
