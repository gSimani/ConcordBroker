#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway Cloud Orchestrator - 24/7 Agent Coordination
Runs in Railway cloud environment, coordinates with PC-based agents
"""

import os
import sys
import time
import json
import socket
import psycopg2
from datetime import datetime
from typing import Dict, List, Optional

# Configuration from environment variables
SUPABASE_HOST = os.getenv('SUPABASE_HOST')
SUPABASE_DB = os.getenv('SUPABASE_DB', 'postgres')
SUPABASE_USER = os.getenv('SUPABASE_USER', 'postgres')
SUPABASE_PASSWORD = os.getenv('SUPABASE_PASSWORD')
SUPABASE_PORT = int(os.getenv('SUPABASE_PORT', '5432'))

# Orchestrator configuration
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '60'))  # 1 minute
HEARTBEAT_INTERVAL = int(os.getenv('HEARTBEAT_INTERVAL', '30'))  # 30 seconds

class RailwayOrchestrator:
    """
    24/7 Cloud Orchestrator running in Railway
    Coordinates all agents, monitors health, sends alerts
    """

    def __init__(self):
        self.agent_id = f"railway-orchestrator-{socket.gethostname()}"
        self.agent_name = "Railway Cloud Orchestrator"
        self.conn = None
        self.cursor = None
        self.running = True
        self.last_heartbeat = 0

        print("\n" + "="*70)
        print("  🚂 RAILWAY CLOUD ORCHESTRATOR")
        print("="*70)
        print()
        print(f"  Agent ID: {self.agent_id}")
        print(f"  Environment: Railway Cloud")
        print(f"  Check Interval: {CHECK_INTERVAL}s")
        print(f"  Heartbeat Interval: {HEARTBEAT_INTERVAL}s")
        print()

    def connect(self) -> bool:
        """Connect to Supabase database"""
        try:
            print("  [1/3] Connecting to Supabase...")

            if not all([SUPABASE_HOST, SUPABASE_PASSWORD]):
                print("  ❌ Missing Supabase credentials")
                return False

            self.conn = psycopg2.connect(
                host=SUPABASE_HOST,
                database=SUPABASE_DB,
                user=SUPABASE_USER,
                password=SUPABASE_PASSWORD,
                port=SUPABASE_PORT,
                connect_timeout=10
            )
            self.cursor = self.conn.cursor()
            print("  ✅ Connected")
            return True

        except Exception as e:
            print(f"  ❌ Connection failed: {e}")
            return False

    def register(self) -> bool:
        """Register orchestrator in agent_registry"""
        try:
            print("  [2/3] Registering in agent registry...")

            self.cursor.execute("""
                INSERT INTO agent_registry (
                    agent_id, agent_name, agent_type, status,
                    last_heartbeat, capabilities, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (agent_id)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    last_heartbeat = EXCLUDED.last_heartbeat,
                    metadata = EXCLUDED.metadata;
            """, (
                self.agent_id,
                self.agent_name,
                'orchestrator',
                'online',
                datetime.now(),
                ['coordination', 'health_monitoring', 'cloud_24/7'],
                json.dumps({
                    'environment': 'railway',
                    'location': 'cloud',
                    'uptime_target': '99.9%'
                })
            ))
            self.conn.commit()

            print("  ✅ Registered")
            return True

        except Exception as e:
            print(f"  ❌ Registration failed: {e}")
            return False

    def heartbeat(self):
        """Send heartbeat to keep agent alive"""
        try:
            self.cursor.execute("""
                UPDATE agent_registry
                SET last_heartbeat = %s, status = 'online'
                WHERE agent_id = %s;
            """, (datetime.now(), self.agent_id))
            self.conn.commit()
            self.last_heartbeat = time.time()

        except Exception as e:
            print(f"  ⚠️  Heartbeat failed: {e}")
            # Attempt reconnection
            self.connect()

    def check_agent_health(self) -> Dict:
        """Check health of all agents"""
        try:
            # Get all agents
            self.cursor.execute("""
                SELECT agent_id, agent_name, status, last_heartbeat
                FROM agent_registry
                ORDER BY last_heartbeat DESC;
            """)
            agents = self.cursor.fetchall()

            online = 0
            offline = 0
            stale = 0

            for agent_id, agent_name, status, last_heartbeat in agents:
                if not last_heartbeat:
                    offline += 1
                    continue

                age_minutes = (datetime.now() - last_heartbeat).total_seconds() / 60

                if age_minutes < 2:
                    online += 1
                elif age_minutes < 10:
                    stale += 1
                else:
                    offline += 1

            return {
                'total': len(agents),
                'online': online,
                'stale': stale,
                'offline': offline,
                'health_percent': round((online / len(agents)) * 100) if agents else 0
            }

        except Exception as e:
            print(f"  ❌ Health check failed: {e}")
            return {'error': str(e)}

    def check_data_freshness(self) -> Dict:
        """Check if data is fresh"""
        try:
            # Check property data age
            self.cursor.execute("""
                SELECT MAX(created_at) as last_update
                FROM florida_parcels
                WHERE year = 2025;
            """)
            result = self.cursor.fetchone()

            if result and result[0]:
                last_update = result[0]
                age_days = (datetime.now() - last_update).days

                return {
                    'last_update': last_update.isoformat(),
                    'age_days': age_days,
                    'is_stale': age_days > 7
                }
            else:
                return {
                    'last_update': None,
                    'age_days': 999,
                    'is_stale': True
                }

        except Exception as e:
            print(f"  ❌ Data freshness check failed: {e}")
            return {'error': str(e)}

    def send_alert(self, alert_type: str, severity: str, message: str):
        """Send alert to agent_alerts table"""
        try:
            self.cursor.execute("""
                INSERT INTO agent_alerts (
                    agent_id, alert_type, severity, message, status
                ) VALUES (%s, %s, %s, %s, 'active');
            """, (self.agent_id, alert_type, severity, message))
            self.conn.commit()

        except Exception as e:
            print(f"  ❌ Alert failed: {e}")

    def monitor_system(self):
        """Main monitoring loop"""
        print("  [3/3] Starting monitoring loop...")
        print()
        print("="*70)
        print("  ✅ RAILWAY ORCHESTRATOR RUNNING")
        print("="*70)
        print()

        last_check = 0

        while self.running:
            try:
                current_time = time.time()

                # Send heartbeat every 30 seconds
                if current_time - self.last_heartbeat >= HEARTBEAT_INTERVAL:
                    self.heartbeat()

                # Run checks every minute
                if current_time - last_check >= CHECK_INTERVAL:
                    print(f"\n  🔍 System Check - {datetime.now().strftime('%H:%M:%S')}")
                    print("  " + "-"*66)

                    # Check agent health
                    health = self.check_agent_health()
                    if 'error' not in health:
                        print(f"  📊 Agent Health: {health['health_percent']}%")
                        print(f"     Online: {health['online']}, Stale: {health['stale']}, Offline: {health['offline']}")

                        # Alert if health drops below 70%
                        if health['health_percent'] < 70:
                            self.send_alert(
                                'system_health_low',
                                'high',
                                f"System health at {health['health_percent']}% ({health['online']}/{health['total']} agents online)"
                            )

                    # Check data freshness
                    data_status = self.check_data_freshness()
                    if 'error' not in data_status:
                        print(f"  📅 Data Age: {data_status['age_days']} days")

                        # Alert if data is stale
                        if data_status['is_stale']:
                            self.send_alert(
                                'data_stale',
                                'medium',
                                f"Property data is {data_status['age_days']} days old. Update recommended."
                            )

                    last_check = current_time

                # Sleep for a bit to avoid busy loop
                time.sleep(1)

            except KeyboardInterrupt:
                print("\n\n  🛑 Shutdown requested...")
                self.running = False
            except Exception as e:
                print(f"\n  ❌ Error in monitoring loop: {e}")
                time.sleep(10)  # Wait before retrying

    def run(self):
        """Main entry point"""
        if not self.connect():
            sys.exit(1)

        if not self.register():
            sys.exit(1)

        # Send initial heartbeat
        self.heartbeat()

        # Start monitoring
        try:
            self.monitor_system()
        finally:
            # Cleanup
            print("  🧹 Cleaning up...")
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            print("  ✅ Shutdown complete")


if __name__ == "__main__":
    orchestrator = RailwayOrchestrator()
    orchestrator.run()
