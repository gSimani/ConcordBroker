#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway Cloud Orchestrator - Distributed Agent Mesh
Runs in Railway and coordinates with PC agents via Supabase
"""

import os
import sys
import time
import json
import platform
from datetime import datetime
from pathlib import Path

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv('.env.mcp')

import psycopg2
import psycopg2.extras
import psutil

class RailwayOrchestrator:
    """
    Cloud orchestrator running on Railway
    Coordinates distributed agent mesh across PC, Railway, and GitHub
    """

    def __init__(self):
        # Railway-specific agent ID
        self.agent_id = "railway-orchestrator-cloud"
        self.agent_name = "Railway Cloud Orchestrator"
        self.environment = "railway"
        self.conn = None
        self.running = False
        self.heartbeat_interval = 30  # seconds
        self.message_check_interval = 10  # seconds
        self.registered = False

        print(f"\n{'='*70}")
        print(f"  🚂 RAILWAY CLOUD ORCHESTRATOR")
        print(f"{'='*70}")
        print(f"  Agent ID: {self.agent_id}")
        print(f"  Environment: {self.environment}")
        print(f"  Platform: {platform.system()}")

    def connect(self):
        """Connect to Supabase"""
        try:
            conn_string = os.getenv('POSTGRES_URL_NON_POOLING')
            if not conn_string:
                raise Exception("POSTGRES_URL_NON_POOLING not found")

            self.conn = psycopg2.connect(conn_string)
            self.conn.autocommit = True
            print(f"  ✅ Connected to Supabase")
            return True
        except Exception as e:
            print(f"  ❌ Connection failed: {e}")
            return False

    def register(self):
        """Register cloud orchestrator"""
        if not self.conn:
            if not self.connect():
                return False

        try:
            cursor = self.conn.cursor()

            # Get system info (Railway container)
            cpu_count = psutil.cpu_count() if hasattr(psutil, 'cpu_count') else 1
            ram_gb = round(psutil.virtual_memory().total / (1024**3), 2) if hasattr(psutil, 'virtual_memory') else 1

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
                    'can_coordinate': True,
                    'can_manage_cloud_agents': True,
                    'cross_environment': True,
                    'distributed': True,
                    'system': {
                        'platform': platform.system(),
                        'python_version': platform.python_version(),
                        'cpu_count': cpu_count,
                        'ram_gb': ram_gb
                    }
                }),
                json.dumps({
                    'deployment': 'railway',
                    'started_at': datetime.now().isoformat(),
                    'version': '2.0-railway',
                    'coordinating_environments': ['pc', 'railway', 'github']
                })
            ))

            cursor.close()
            self.registered = True
            print(f"  ✅ Registered as cloud orchestrator")
            return True

        except Exception as e:
            print(f"  ❌ Registration failed: {e}")
            return False

    def check_messages(self):
        """Check for messages from all environments"""
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Get pending messages for this orchestrator
            cursor.execute("""
                SELECT message_id, from_agent_id, message_type, payload,
                       priority, created_at
                FROM agent_messages
                WHERE to_agent_id = %s
                  AND status = 'pending'
                ORDER BY priority ASC, created_at ASC
                LIMIT 20;
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
            print(f"  ⚠️  Message check failed: {e}")
            return []

    def handle_message(self, message):
        """Handle incoming message with Chain-of-Thought"""
        print(f"\n  📨 MESSAGE FROM {message['from_agent_id'][:30]}")
        print(f"     Type: {message['message_type']} | Priority: {message['priority']}")

        # Chain-of-Thought reasoning
        print(f"  💭 Reasoning...")

        payload = message['payload']
        message_type = message['message_type']

        if message_type == 'alert':
            alert_type = payload.get('alert_type')
            print(f"     → Alert type: {alert_type}")

            if alert_type == 'data_quality_issues':
                issues = payload.get('issues', [])
                print(f"     → Issues detected: {', '.join(issues)}")
                print(f"     → Decision: Log and coordinate response")

                # Store alert
                self.store_alert(
                    'data_quality',
                    'high',
                    f"Cross-environment alert: {', '.join(issues)}",
                    payload
                )

                # Could trigger cloud remediation here
                print(f"     → Action: Cloud remediation available")

        elif message_type == 'heartbeat':
            print(f"     → Agent status update")

        elif message_type == 'query':
            print(f"     → Information request")

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
            print(f"     ✅ Processed")
        except Exception as e:
            print(f"     ⚠️  Failed to mark processed: {e}")

    def store_alert(self, alert_type, severity, message, details):
        """Store alert from cloud orchestrator"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO agent_alerts (
                    agent_id, alert_type, severity, message, details, status
                ) VALUES (%s, %s, %s, %s, %s::jsonb, 'active');
            """, (self.agent_id, alert_type, severity, message, json.dumps(details)))
            cursor.close()
            print(f"  🚨 Alert logged: [{severity}] {message}")
        except Exception as e:
            print(f"  ⚠️  Failed to store alert: {e}")

    def send_heartbeat(self):
        """Send heartbeat with system stats"""
        if not self.conn:
            if not self.connect():
                return False

        try:
            cursor = self.conn.cursor()

            # Railway container stats
            cpu_percent = psutil.cpu_percent(interval=0.5) if hasattr(psutil, 'cpu_percent') else 0
            ram_percent = psutil.virtual_memory().percent if hasattr(psutil, 'virtual_memory') else 0

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
                    'timestamp': datetime.now().isoformat(),
                    'uptime_seconds': int(time.time() - self.start_time) if hasattr(self, 'start_time') else 0
                }),
                self.agent_id
            ))

            cursor.close()
            return True

        except Exception as e:
            print(f"  ⚠️  Heartbeat failed: {e}")
            self.conn = None
            return False

    def get_distributed_status(self):
        """Get status of distributed agent mesh"""
        if not self.conn:
            if not self.connect():
                return None

        try:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Count agents by environment
            cursor.execute("""
                SELECT
                    environment,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'online') as online,
                    COUNT(*) FILTER (WHERE status = 'offline') as offline,
                    MAX(last_heartbeat) as latest_heartbeat
                FROM agent_registry
                GROUP BY environment
                ORDER BY environment;
            """)

            env_stats = cursor.fetchall()

            # Get recent alerts
            cursor.execute("""
                SELECT COUNT(*) as alert_count
                FROM agent_alerts
                WHERE status = 'active'
                  AND created_at > NOW() - INTERVAL '1 hour';
            """)

            alert_count = cursor.fetchone()['alert_count']

            # Get pending messages
            cursor.execute("""
                SELECT COUNT(*) as message_count
                FROM agent_messages
                WHERE status = 'pending';
            """)

            message_count = cursor.fetchone()['message_count']

            cursor.close()

            return {
                'environments': env_stats,
                'active_alerts': alert_count,
                'pending_messages': message_count
            }

        except Exception as e:
            print(f"  ⚠️  Status check failed: {e}")
            return None

    def display_status(self):
        """Display distributed mesh status"""
        status = self.get_distributed_status()

        if not status:
            return

        print(f"\n{'='*70}")
        print(f"  DISTRIBUTED MESH STATUS - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")

        print(f"\n  🌐 AGENT ENVIRONMENTS:")
        for env in status['environments']:
            env_icon = {
                'pc': '💻',
                'railway': '🚂',
                'github': '🐙',
                'deployment': '🧪'
            }.get(env['environment'], '📦')

            print(f"    {env_icon} {env['environment'].upper()}")
            print(f"       Total: {env['total']} | Online: {env['online']} | Offline: {env['offline']}")
            print(f"       Latest: {env['latest_heartbeat']}")

        print(f"\n  📊 SYSTEM METRICS:")
        print(f"    Active Alerts: {status['active_alerts']}")
        print(f"    Pending Messages: {status['pending_messages']}")

        print(f"\n{'='*70}")

    def run(self):
        """Main orchestration loop"""
        print(f"\n  Starting cloud orchestrator...")

        self.start_time = time.time()

        # Connect
        if not self.connect():
            print(f"  ❌ Failed to connect")
            return

        # Register
        if not self.register():
            print(f"  ❌ Failed to register")
            return

        print(f"\n  ✅ Railway orchestrator operational")
        print(f"  💡 Coordinating distributed agent mesh")
        print(f"  🔄 Heartbeat: {self.heartbeat_interval}s | Messages: {self.message_check_interval}s\n")

        self.running = True
        heartbeat_count = 0
        message_check_count = 0
        status_display_count = 0

        try:
            while self.running:
                # Check messages
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
                        status_display_count += 1

                        # Display status every 5 heartbeats (2.5 minutes)
                        if status_display_count >= 5:
                            self.display_status()
                            status_display_count = 0
                        else:
                            print(f"  💓 {datetime.now().strftime('%H:%M:%S')}")
                    else:
                        print(f"  ⚠️  Heartbeat failed, will retry...")

        except KeyboardInterrupt:
            print(f"\n\n  🛑 Stopping...")
            self.stop()
        except Exception as e:
            print(f"\n\n  ❌ Error: {e}")
            self.stop()

    def stop(self):
        """Stop orchestrator gracefully"""
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
                print(f"  ✅ Marked as offline")
            except:
                pass

            self.conn.close()

        uptime = int(time.time() - self.start_time) if hasattr(self, 'start_time') else 0
        print(f"  ⏱️  Uptime: {uptime} seconds")
        print(f"  ✅ Stopped\n")


if __name__ == "__main__":
    orchestrator = RailwayOrchestrator()
    orchestrator.run()
