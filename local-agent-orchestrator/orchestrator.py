#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ConcordBroker Local Agent Orchestrator
Runs on your PC and coordinates with cloud agents
"""

import os
import sys
import time
import platform
import json
from datetime import datetime
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env.mcp')

try:
    import psycopg2
    import psycopg2.extras
    import psutil
except ImportError as e:
    print(f"[!] Missing dependency: {e}")
    print("[!] Installing requirements...")
    os.system(f"pip install -r {Path(__file__).parent / 'requirements.txt'}")
    import psycopg2
    import psycopg2.extras
    import psutil

class LocalOrchestrator:
    """Local PC Agent Orchestrator"""

    def __init__(self):
        self.agent_id = f"local-orchestrator-{platform.node()}"
        self.agent_name = f"Local PC Orchestrator ({platform.node()})"
        self.environment = "pc"
        self.conn = None
        self.running = False
        self.heartbeat_interval = 30  # seconds
        self.registered = False

    def connect(self):
        """Connect to Supabase"""
        try:
            conn_string = os.getenv('POSTGRES_URL_NON_POOLING')
            if not conn_string:
                raise Exception("POSTGRES_URL_NON_POOLING not found in environment")

            self.conn = psycopg2.connect(conn_string)
            self.conn.autocommit = True
            return True
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            return False

    def register(self):
        """Register orchestrator in agent registry"""
        if not self.conn:
            if not self.connect():
                return False

        try:
            cursor = self.conn.cursor()

            # Get system info
            cpu_count = psutil.cpu_count()
            ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)

            # Register
            cursor.execute("""
                INSERT INTO agent_registry (
                    agent_id,
                    agent_name,
                    agent_type,
                    environment,
                    status,
                    last_heartbeat,
                    capabilities,
                    metadata
                ) VALUES (
                    %s, %s, %s, %s, %s, NOW(),
                    %s::jsonb,
                    %s::jsonb
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
                    'started_at': datetime.now().isoformat()
                })
            ))

            cursor.close()
            self.registered = True
            return True

        except Exception as e:
            print(f"[ERROR] Registration failed: {e}")
            return False

    def send_heartbeat(self):
        """Send heartbeat to registry"""
        if not self.conn:
            if not self.connect():
                return False

        try:
            cursor = self.conn.cursor()

            # Get current resource usage
            cpu_percent = psutil.cpu_percent(interval=1)
            ram_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:\\').percent

            # Update registry
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
                    'timestamp': datetime.now().isoformat()
                }),
                self.agent_id
            ))

            cursor.close()
            return True

        except Exception as e:
            print(f"[ERROR] Heartbeat failed: {e}")
            # Try to reconnect
            self.conn = None
            return False

    def get_status(self):
        """Get current status from registry"""
        if not self.conn:
            if not self.connect():
                return None

        try:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cursor.execute("""
                SELECT agent_id, agent_name, status, last_heartbeat, metadata
                FROM agent_registry
                WHERE agent_id = %s;
            """, (self.agent_id,))

            result = cursor.fetchone()
            cursor.close()
            return result

        except Exception as e:
            print(f"[ERROR] Status check failed: {e}")
            return None

    def get_all_agents(self):
        """Get all agents in the system"""
        if not self.conn:
            if not self.connect():
                return []

        try:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cursor.execute("""
                SELECT agent_id, agent_name, agent_type, environment, status, last_heartbeat
                FROM agent_registry
                ORDER BY last_heartbeat DESC;
            """)

            results = cursor.fetchall()
            cursor.close()
            return results

        except Exception as e:
            print(f"[ERROR] Failed to get agents: {e}")
            return []

    def display_status(self):
        """Display current status"""
        print("\n" + "="*70)
        print(f"  LOCAL ORCHESTRATOR STATUS - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)

        # Get own status
        status = self.get_status()
        if status:
            print(f"\n  Agent ID: {status['agent_id']}")
            print(f"  Name: {status['agent_name']}")
            print(f"  Status: {status['status']}")
            print(f"  Last Heartbeat: {status['last_heartbeat']}")

            if status['metadata'] and 'resources' in status['metadata']:
                res = status['metadata']['resources']
                print(f"\n  System Resources:")
                print(f"    CPU: {res.get('cpu_percent', 0):.1f}%")
                print(f"    RAM: {res.get('ram_percent', 0):.1f}%")
                print(f"    Disk: {res.get('disk_percent', 0):.1f}%")

        # Get all agents
        print(f"\n  ALL AGENTS IN MESH:")
        agents = self.get_all_agents()
        if agents:
            for agent in agents:
                status_icon = "✅" if agent['status'] == 'online' else "❌"
                env_icon = {"pc": "💻", "railway": "🚂", "github": "🐙", "deployment": "🧪"}.get(agent['environment'], "📦")
                print(f"    {status_icon} {env_icon} {agent['agent_name']:<40} [{agent['environment']}]")
        else:
            print("    No other agents found")

        print("\n" + "="*70)

    def run(self):
        """Main run loop"""
        print("\n" + "="*70)
        print("  🚀 CONCORDBROKER LOCAL AGENT ORCHESTRATOR")
        print("="*70)
        print(f"\n  Hostname: {platform.node()}")
        print(f"  Platform: {platform.system()} {platform.release()}")
        print(f"  Python: {platform.python_version()}")
        print(f"  Agent ID: {self.agent_id}")

        # Connect
        print(f"\n  [1/3] Connecting to Supabase...")
        if not self.connect():
            print("  ❌ Connection failed. Check your .env.mcp file.")
            return

        print("  ✅ Connected")

        # Register
        print(f"  [2/3] Registering in agent registry...")
        if not self.register():
            print("  ❌ Registration failed.")
            return

        print("  ✅ Registered")

        # Start heartbeat loop
        print(f"  [3/3] Starting heartbeat loop (every {self.heartbeat_interval}s)...")
        print("  ✅ Orchestrator running")
        print("\n  Press Ctrl+C to stop\n")

        self.running = True
        heartbeat_count = 0

        try:
            while self.running:
                # Send heartbeat
                if self.send_heartbeat():
                    heartbeat_count += 1

                    # Display status every 5 heartbeats (2.5 minutes)
                    if heartbeat_count % 5 == 0:
                        self.display_status()
                    else:
                        print(f"  💓 Heartbeat #{heartbeat_count} sent at {datetime.now().strftime('%H:%M:%S')}")
                else:
                    print(f"  ⚠️  Heartbeat failed, will retry...")

                # Wait
                time.sleep(self.heartbeat_interval)

        except KeyboardInterrupt:
            print("\n\n  🛑 Stopping orchestrator...")
            self.stop()

    def stop(self):
        """Stop orchestrator"""
        self.running = False

        # Mark as offline
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
    orchestrator = LocalOrchestrator()
    orchestrator.run()
