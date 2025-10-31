#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PropertyDataAgent with Chain-of-Thought Reasoning
Monitors florida_parcels table and uses CoT to analyze data quality
"""

import os
import sys
import time
import json
import platform
from datetime import datetime, timedelta
from pathlib import Path

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env.mcp')

import psycopg2
import psycopg2.extras

class PropertyDataAgent:
    """
    Monitors property data with Chain-of-Thought reasoning
    """

    def __init__(self, orchestrator_id=None):
        self.agent_id = f"property-data-agent-{platform.node()}"
        self.agent_name = "Property Data Monitor (CoT)"
        self.orchestrator_id = orchestrator_id or f"local-orchestrator-{platform.node()}"
        self.environment = "pc"
        self.conn = None
        self.running = False
        self.check_interval = 60  # 1 minute (demo mode)
        self.thought_process = []  # Store chain of thought

    def connect(self):
        """Connect to database"""
        try:
            conn_string = os.getenv('POSTGRES_URL_NON_POOLING')
            self.conn = psycopg2.connect(conn_string)
            self.conn.autocommit = True
            return True
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            return False

    def register(self):
        """Register agent"""
        if not self.conn:
            if not self.connect():
                return False

        try:
            cursor = self.conn.cursor()
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
                    updated_at = NOW();
            """, (
                self.agent_id,
                self.agent_name,
                'monitoring',
                self.environment,
                'online',
                json.dumps({
                    'monitors': 'florida_parcels',
                    'reasoning': 'chain-of-thought',
                    'can_communicate': True,
                    'check_interval_seconds': self.check_interval
                }),
                json.dumps({
                    'orchestrator': self.orchestrator_id,
                    'started_at': datetime.now().isoformat()
                })
            ))

            # Register dependency on orchestrator
            cursor.execute("""
                INSERT INTO agent_dependencies (
                    agent_id, depends_on_agent_id, dependency_type, is_required
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (agent_id, depends_on_agent_id) DO NOTHING;
            """, (self.agent_id, self.orchestrator_id, 'reports_to', True))

            cursor.close()
            return True

        except Exception as e:
            print(f"[ERROR] Registration failed: {e}")
            return False

    def think(self, thought: str, data: dict = None):
        """
        Chain-of-Thought: Record a reasoning step
        """
        thought_entry = {
            'timestamp': datetime.now().isoformat(),
            'thought': thought,
            'data': data
        }
        self.thought_process.append(thought_entry)
        print(f"  💭 {thought}")
        if data:
            print(f"     Data: {json.dumps(data, default=str)[:100]}...")

    def analyze_property_data(self):
        """
        Analyze property data using Chain-of-Thought reasoning
        """
        print("\n" + "="*70)
        print(f"  🔍 PROPERTY DATA ANALYSIS - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)

        self.thought_process = []  # Reset thoughts

        if not self.conn:
            if not self.connect():
                return None

        try:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Step 1: Count total properties
            self.think("Step 1: Counting total properties in database")
            cursor.execute("SELECT COUNT(*) as total FROM florida_parcels;")
            total_result = cursor.fetchone()
            total_properties = total_result['total'] if total_result else 0
            self.think(f"Found {total_properties:,} total properties", {'total': total_properties})

            # Step 2: Check data freshness
            self.think("Step 2: Checking data freshness (last update)")
            cursor.execute("""
                SELECT MAX(update_date) as last_update
                FROM florida_parcels
                WHERE update_date IS NOT NULL;
            """)
            freshness = cursor.fetchone()
            last_update = freshness['last_update'] if freshness else None

            if last_update:
                age_days = (datetime.now(last_update.tzinfo) - last_update).days
                self.think(f"Data last updated {age_days} days ago", {'last_update': str(last_update), 'age_days': age_days})

                # Reasoning about freshness
                if age_days > 30:
                    self.think("⚠️ CONCERN: Data is stale (>30 days old)")
                    self.send_alert('data_staleness', 'medium', f'Property data is {age_days} days old')
                elif age_days > 7:
                    self.think("✓ Data is acceptable (7-30 days old)")
                else:
                    self.think("✓ Data is fresh (<7 days old)")
            else:
                self.think("⚠️ Cannot determine data freshness")

            # Step 3: Check null values
            self.think("Step 3: Analyzing data quality (null values)")
            cursor.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE owner_name IS NULL) as null_owners,
                    COUNT(*) FILTER (WHERE just_value IS NULL OR just_value = 0) as null_values,
                    COUNT(*) FILTER (WHERE property_use IS NULL) as null_use
                FROM florida_parcels;
            """)
            quality = cursor.fetchone()

            null_owner_pct = (quality['null_owners'] / total_properties * 100) if total_properties > 0 else 0
            null_value_pct = (quality['null_values'] / total_properties * 100) if total_properties > 0 else 0
            null_use_pct = (quality['null_use'] / total_properties * 100) if total_properties > 0 else 0

            self.think(f"Null owners: {null_owner_pct:.2f}%", {'null_count': quality['null_owners']})
            self.think(f"Null values: {null_value_pct:.2f}%", {'null_count': quality['null_values']})
            self.think(f"Null property use: {null_use_pct:.2f}%", {'null_count': quality['null_use']})

            # Reasoning about quality
            quality_issues = []
            if null_owner_pct > 10:
                self.think("⚠️ HIGH null owner percentage detected")
                quality_issues.append('high_null_owners')
                self.send_alert('data_quality', 'high', f'Null owners: {null_owner_pct:.2f}%')
            if null_value_pct > 5:
                self.think("⚠️ HIGH null value percentage detected")
                quality_issues.append('high_null_values')
                self.send_alert('data_quality', 'high', f'Null values: {null_value_pct:.2f}%')

            if not quality_issues:
                self.think("✓ Data quality is acceptable")

            # Step 4: Check for recent additions
            self.think("Step 4: Checking for recent property additions")
            cursor.execute("""
                SELECT COUNT(*) as recent_count
                FROM florida_parcels
                WHERE import_date > NOW() - INTERVAL '7 days';
            """)
            recent = cursor.fetchone()
            recent_count = recent['recent_count'] if recent else 0
            self.think(f"Found {recent_count:,} properties added in last 7 days", {'recent_count': recent_count})

            # Step 5: County distribution
            self.think("Step 5: Analyzing county distribution")
            cursor.execute("""
                SELECT county, COUNT(*) as count
                FROM florida_parcels
                GROUP BY county
                ORDER BY count DESC
                LIMIT 5;
            """)
            top_counties = cursor.fetchall()

            if top_counties:
                self.think(f"Top counties: {', '.join([f'{c['county']} ({c['count']:,})' for c in top_counties])}")

            # Step 6: Value analysis
            self.think("Step 6: Analyzing property values")
            cursor.execute("""
                SELECT
                    AVG(just_value) as avg_value,
                    MIN(just_value) as min_value,
                    MAX(just_value) as max_value
                FROM florida_parcels
                WHERE just_value > 0;
            """)
            values = cursor.fetchone()

            if values:
                avg_val = values['avg_value'] or 0
                self.think(f"Average property value: ${avg_val:,.2f}")

                # Reasoning about values
                if avg_val > 500000:
                    self.think("→ High average value suggests affluent areas or commercial properties")
                elif avg_val < 100000:
                    self.think("→ Low average value suggests rural areas or distressed properties")
                else:
                    self.think("→ Average value is in normal residential range")

            # Step 7: Final assessment
            self.think("Step 7: Generating final assessment")

            assessment = {
                'total_properties': total_properties,
                'data_freshness_days': age_days if last_update else None,
                'quality_score': 100 - (null_owner_pct + null_value_pct) / 2,
                'quality_issues': quality_issues,
                'recent_additions': recent_count,
                'average_value': float(values['avg_value']) if values else 0,
                'conclusion': self._generate_conclusion(
                    total_properties,
                    age_days if last_update else 999,
                    quality_issues,
                    recent_count
                )
            }

            self.think(f"Final quality score: {assessment['quality_score']:.1f}/100")
            self.think(f"Conclusion: {assessment['conclusion']}")

            # Store metrics
            self.store_metrics(assessment)

            # Check if we should communicate with other agents
            if quality_issues:
                self.think("→ Quality issues detected, should notify orchestrator")
                self.send_message_to_orchestrator({
                    'alert_type': 'data_quality_issues',
                    'issues': quality_issues,
                    'assessment': assessment
                })

            cursor.close()

            print("\n" + "="*70)
            print(f"  ✅ Analysis complete - {len(self.thought_process)} reasoning steps")
            print("="*70)

            return assessment

        except Exception as e:
            self.think(f"ERROR during analysis: {str(e)}")
            print(f"\n[ERROR] Analysis failed: {e}")
            return None

    def _generate_conclusion(self, total, age_days, issues, recent_count):
        """Generate human-readable conclusion from analysis"""
        if total == 0:
            return "No property data found in database"

        conclusion_parts = []

        # Data size assessment
        if total > 9000000:
            conclusion_parts.append(f"Large dataset ({total:,} properties)")
        elif total > 1000000:
            conclusion_parts.append(f"Substantial dataset ({total:,} properties)")
        else:
            conclusion_parts.append(f"Small dataset ({total:,} properties)")

        # Freshness assessment
        if age_days > 30:
            conclusion_parts.append("STALE DATA - needs update")
        elif age_days > 7:
            conclusion_parts.append("data is moderately fresh")
        else:
            conclusion_parts.append("data is current")

        # Quality assessment
        if len(issues) > 2:
            conclusion_parts.append("MULTIPLE quality issues detected")
        elif len(issues) > 0:
            conclusion_parts.append("some quality issues present")
        else:
            conclusion_parts.append("good data quality")

        # Activity assessment
        if recent_count > 10000:
            conclusion_parts.append(f"high update activity ({recent_count:,} recent)")
        elif recent_count > 0:
            conclusion_parts.append(f"some update activity ({recent_count:,} recent)")
        else:
            conclusion_parts.append("no recent updates")

        return "; ".join(conclusion_parts)

    def send_alert(self, alert_type, severity, message):
        """Send alert to agent_alerts table"""
        if not self.conn:
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO agent_alerts (
                    agent_id, alert_type, severity, message, status
                ) VALUES (%s, %s, %s, %s, 'active');
            """, (self.agent_id, alert_type, severity, message))
            cursor.close()
            print(f"  🚨 ALERT: [{severity}] {message}")
        except Exception as e:
            print(f"  [ERROR] Failed to send alert: {e}")

    def send_message_to_orchestrator(self, payload):
        """Send message to orchestrator"""
        if not self.conn:
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO agent_messages (
                    from_agent_id, to_agent_id, message_type, payload, priority
                ) VALUES (%s, %s, %s, %s::jsonb, %s);
            """, (
                self.agent_id,
                self.orchestrator_id,
                'alert',
                json.dumps(payload),
                3  # Medium-high priority
            ))
            cursor.close()
            print(f"  📤 Message sent to orchestrator")
        except Exception as e:
            print(f"  [ERROR] Failed to send message: {e}")

    def store_metrics(self, assessment):
        """Store analysis metrics"""
        if not self.conn:
            return

        try:
            cursor = self.conn.cursor()

            # Store quality score
            cursor.execute("""
                INSERT INTO agent_metrics (
                    agent_id, metric_type, metric_name, metric_value, metadata
                ) VALUES (%s, %s, %s, %s, %s::jsonb);
            """, (
                self.agent_id,
                'data_quality',
                'quality_score',
                assessment['quality_score'],
                json.dumps({
                    'total_properties': assessment['total_properties'],
                    'issues': assessment['quality_issues']
                })
            ))

            # Store chain of thought
            cursor.execute("""
                INSERT INTO agent_metrics (
                    agent_id, metric_type, metric_name, metric_value, metadata
                ) VALUES (%s, %s, %s, %s, %s::jsonb);
            """, (
                self.agent_id,
                'reasoning',
                'chain_of_thought_steps',
                len(self.thought_process),
                json.dumps({
                    'thoughts': self.thought_process[-5:]  # Last 5 thoughts
                })
            ))

            cursor.close()
        except Exception as e:
            print(f"  [ERROR] Failed to store metrics: {e}")

    def heartbeat(self):
        """Send heartbeat"""
        if not self.conn:
            if not self.connect():
                return False

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE agent_registry
                SET last_heartbeat = NOW(),
                    status = 'online',
                    updated_at = NOW()
                WHERE agent_id = %s;
            """, (self.agent_id,))
            cursor.close()
            return True
        except Exception as e:
            print(f"[ERROR] Heartbeat failed: {e}")
            return False

    def run(self):
        """Main run loop"""
        print("\n" + "="*70)
        print("  🤖 PROPERTY DATA AGENT (Chain-of-Thought)")
        print("="*70)
        print(f"\n  Agent ID: {self.agent_id}")
        print(f"  Monitors: florida_parcels table")
        print(f"  Check Interval: {self.check_interval} seconds")
        print(f"  Reasoning Mode: Chain-of-Thought")

        # Connect and register
        print(f"\n  Connecting and registering...")
        if not self.connect():
            print("  ❌ Connection failed")
            return

        if not self.register():
            print("  ❌ Registration failed")
            return

        print("  ✅ Agent ready")
        print("\n  Press Ctrl+C to stop\n")

        self.running = True
        iteration = 0

        try:
            while self.running:
                iteration += 1
                print(f"\n{'='*70}")
                print(f"  Iteration #{iteration}")
                print(f"{'='*70}")

                # Run analysis
                result = self.analyze_property_data()

                if result:
                    print(f"\n  ✅ Analysis #{iteration} complete")
                else:
                    print(f"\n  ⚠️  Analysis #{iteration} failed")

                # Heartbeat
                self.heartbeat()

                # Wait
                print(f"\n  ⏳ Waiting {self.check_interval} seconds until next check...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\n  🛑 Stopping agent...")
            self.stop()

    def stop(self):
        """Stop agent"""
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
    agent = PropertyDataAgent()
    agent.run()
