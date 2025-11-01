#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Permit Activity Tracker Agent - Chain-of-Thought Autonomous Monitoring
Monitors building permits and identifies development trends and hot zones
"""

import os
import sys
import time
import json
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
import socket

# Load environment from .env.mcp
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.mcp')
load_dotenv(env_path)

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

class PermitActivityAgent:
    """
    Permit Activity Tracker Agent with Chain-of-Thought reasoning

    Capabilities:
    - Monitors building_permits table for new activity
    - Identifies development hotspots and permit surges
    - Tracks permit types and construction values
    - Coordinates with Sales/Market agents for trend validation
    - Generates autonomous alerts for development clusters

    Chain-of-Thought: 12 steps per analysis cycle
    """

    def __init__(self, check_interval=300):
        """Initialize Permit Activity Tracker"""
        self.agent_id = f"permit-activity-{socket.gethostname()}"
        self.agent_name = "Permit Activity Tracker (CoT)"
        self.agent_type = "monitoring"
        self.environment = "pc"
        self.check_interval = check_interval  # 5 minutes

        self.capabilities = [
            "permit_monitoring",
            "development_tracking",
            "hotspot_detection",
            "construction_value_analysis",
            "trend_identification",
            "chain_of_thought"
        ]

        self.conn = None
        self.cursor = None
        self.running = False

        # Analysis tracking
        self.analysis_count = 0
        self.thought_count = 0

    def connect(self):
        """Connect to Supabase database"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('SUPABASE_HOST'),
                database=os.getenv('SUPABASE_DB'),
                user=os.getenv('SUPABASE_USER'),
                password=os.getenv('SUPABASE_PASSWORD'),
                port=os.getenv('SUPABASE_PORT', '5432')
            )
            self.cursor = self.conn.cursor()
            print(f"  ✅ Connected")
            return True
        except Exception as e:
            print(f"  ❌ Connection failed: {e}")
            return False

    def register(self):
        """Register agent in agent_registry"""
        try:
            self.cursor.execute("""
                INSERT INTO agent_registry (
                    agent_id, agent_name, agent_type, environment,
                    capabilities, status, last_heartbeat
                ) VALUES (%s, %s, %s, %s, %s::jsonb, %s, NOW())
                ON CONFLICT (agent_id)
                DO UPDATE SET
                    last_heartbeat = NOW(),
                    status = EXCLUDED.status,
                    capabilities = EXCLUDED.capabilities;
            """, (
                self.agent_id,
                self.agent_name,
                self.agent_type,
                self.environment,
                json.dumps(self.capabilities),
                'online'
            ))
            self.conn.commit()
            print(f"  ✅ Registered")
            return True
        except Exception as e:
            print(f"  ❌ Registration failed: {e}")
            return False

    def heartbeat(self):
        """Send heartbeat to show agent is alive"""
        try:
            self.cursor.execute("""
                UPDATE agent_registry
                SET last_heartbeat = NOW(), status = 'online'
                WHERE agent_id = %s;
            """, (self.agent_id,))
            self.conn.commit()
        except Exception as e:
            print(f"⚠️  Heartbeat failed: {e}")
            self.connect()
            self.register()

    def think(self, thought):
        """Chain-of-Thought: Record and display reasoning step"""
        self.thought_count += 1
        print(f"  💭 {thought}")

        try:
            self.cursor.execute("""
                INSERT INTO agent_metrics (
                    agent_id, metric_type, metric_name, metric_value, metadata
                ) VALUES (%s, %s, %s, %s, %s::jsonb);
            """, (
                self.agent_id,
                'reasoning',
                'chain_of_thought_steps',
                self.thought_count,
                json.dumps({"thought": thought, "analysis_count": self.analysis_count})
            ))
            self.conn.commit()
        except Exception as e:
            print(f"     ⚠️ Failed to record thought: {e}")

    def send_alert(self, alert_type, severity, message, details=None):
        """Send autonomous alert"""
        try:
            self.cursor.execute("""
                INSERT INTO agent_alerts (
                    agent_id, alert_type, severity, message, details, status
                ) VALUES (%s, %s, %s, %s, %s::jsonb, 'active');
            """, (
                self.agent_id,
                alert_type,
                severity,
                message,
                json.dumps(details or {})
            ))
            self.conn.commit()
            print(f"  🚨 ALERT: [{severity}] {message}")
        except Exception as e:
            print(f"     ⚠️ Failed to send alert: {e}")

    def record_metric(self, metric_name, metric_value, metadata=None):
        """Record performance metric"""
        try:
            self.cursor.execute("""
                INSERT INTO agent_metrics (
                    agent_id, metric_type, metric_name, metric_value, metadata
                ) VALUES (%s, %s, %s, %s, %s::jsonb);
            """, (
                self.agent_id,
                'permit',
                metric_name,
                metric_value,
                json.dumps(metadata or {})
            ))
            self.conn.commit()
        except Exception as e:
            print(f"     ⚠️ Failed to record metric: {e}")

    def send_message(self, to_agent_id, message_type, payload, priority=5):
        """Send message to another agent (Chain-of-Agents communication)"""
        try:
            self.cursor.execute("""
                INSERT INTO agent_messages (
                    from_agent_id, to_agent_id, message_type, payload, priority, status
                ) VALUES (%s, %s, %s, %s::jsonb, %s, 'pending');
            """, (
                self.agent_id,
                to_agent_id,
                message_type,
                json.dumps(payload),
                priority
            ))
            self.conn.commit()
        except Exception as e:
            print(f"     ⚠️ Failed to send message: {e}")

    def receive_messages(self):
        """Check for messages from other agents"""
        try:
            self.cursor.execute("""
                SELECT message_id, from_agent_id, message_type, payload
                FROM agent_messages
                WHERE to_agent_id = %s AND status = 'pending'
                ORDER BY priority ASC, created_at ASC
                LIMIT 10;
            """, (self.agent_id,))

            messages = []
            for row in self.cursor.fetchall():
                message_id, from_agent, msg_type, payload = row
                messages.append({
                    'id': message_id,
                    'from': from_agent,
                    'type': msg_type,
                    'payload': payload
                })

                self.cursor.execute("""
                    UPDATE agent_messages
                    SET status = 'processed', processed_at = NOW()
                    WHERE message_id = %s;
                """, (message_id,))

            self.conn.commit()
            return messages
        except Exception as e:
            print(f"     ⚠️ Failed to receive messages: {e}")
            return []

    def analyze_permit_activity(self):
        """
        Main analysis function with Chain-of-Thought reasoning
        12-step transparent decision-making process
        """
        self.analysis_count += 1
        self.thought_count = 0

        print("\n" + "="*70)
        print(f"  🔍 PERMIT ACTIVITY ANALYSIS - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)

        try:
            # STEP 1: Count total permits in database
            self.think("Step 1: Counting total building permits in database")
            self.cursor.execute("""
                SELECT COUNT(*) as total
                FROM building_permits;
            """)
            row = self.cursor.fetchone()
            total_permits = row[0] if row else 0
            self.think(f"Found {total_permits:,} total building permit records")
            self.record_metric('total_permits', total_permits)

            # STEP 2: Analyze recent permit activity (last 30 days)
            self.think("Step 2: Analyzing recent permit activity (last 30 days)")
            self.cursor.execute("""
                SELECT COUNT(*) as recent_count,
                       SUM(CAST(NULLIF(construction_value, '') AS NUMERIC)) as total_value
                FROM building_permits
                WHERE issue_date >= CURRENT_DATE - INTERVAL '30 days'
                  AND construction_value IS NOT NULL
                  AND construction_value != '';
            """)
            row = self.cursor.fetchone()
            if row:
                recent_count, total_value = row
                recent_count = recent_count if recent_count else 0
                total_value = float(total_value) if total_value else 0
                self.think(f"Recent permits: {recent_count:,} in last 30 days")
                self.think(f"Total construction value: ${total_value:,.2f}")
                self.record_metric('recent_permits_30d', recent_count)
                self.record_metric('total_construction_value_30d', total_value)

            # STEP 3: Identify permit type distribution
            self.think("Step 3: Analyzing permit type distribution")
            self.cursor.execute("""
                SELECT permit_type, COUNT(*) as count
                FROM building_permits
                WHERE issue_date >= CURRENT_DATE - INTERVAL '30 days'
                  AND permit_type IS NOT NULL
                GROUP BY permit_type
                ORDER BY count DESC
                LIMIT 5;
            """)

            permit_types = []
            for row in self.cursor.fetchall():
                ptype, count = row
                permit_types.append({'type': ptype, 'count': count})
                self.think(f"→ {ptype}: {count:,} permits")

            if permit_types:
                dominant_type = permit_types[0]
                self.record_metric('dominant_permit_type', dominant_type['count'],
                                 {'type': dominant_type['type']})

            # STEP 4: Detect permit surges (>50% increase vs previous 30 days)
            self.think("Step 4: Detecting permit volume surges")
            self.cursor.execute("""
                SELECT
                    COUNT(CASE WHEN issue_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as current_period,
                    COUNT(CASE WHEN issue_date >= CURRENT_DATE - INTERVAL '60 days'
                               AND issue_date < CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as previous_period
                FROM building_permits;
            """)
            row = self.cursor.fetchone()
            if row:
                current_period, previous_period = row
                current_period = current_period if current_period else 0
                previous_period = previous_period if previous_period else 0

                if previous_period > 0:
                    change_pct = ((current_period - previous_period) / previous_period) * 100
                    self.think(f"Permit volume trend: {change_pct:+.1f}% vs previous period")

                    if change_pct > 50:
                        self.think(f"⚠️ PERMIT SURGE: Volume increased {change_pct:.1f}%")
                        self.send_alert(
                            'permit_surge',
                            'high',
                            f'Building permit volume surged {change_pct:.1f}% in last 30 days',
                            {'current': current_period, 'previous': previous_period, 'change_pct': change_pct}
                        )
                    elif change_pct < -30:
                        self.think(f"⚠️ PERMIT SLOWDOWN: Volume decreased {abs(change_pct):.1f}%")

                    self.record_metric('permit_volume_change_pct', change_pct)

            # STEP 5: Identify geographic hotspots (by county/city)
            self.think("Step 5: Identifying development hotspots by location")
            self.cursor.execute("""
                SELECT county, city, COUNT(*) as permit_count
                FROM building_permits
                WHERE issue_date >= CURRENT_DATE - INTERVAL '30 days'
                  AND county IS NOT NULL
                GROUP BY county, city
                HAVING COUNT(*) > 10
                ORDER BY permit_count DESC
                LIMIT 5;
            """)

            hotspots = []
            for row in self.cursor.fetchall():
                county, city, permit_count = row
                hotspots.append({
                    'county': county,
                    'city': city if city else 'Unknown',
                    'permit_count': permit_count
                })

            if hotspots:
                top_hotspot = hotspots[0]
                self.think(f"Top development hotspot: {top_hotspot['city']}, {top_hotspot['county']} ({top_hotspot['permit_count']} permits)")

                if top_hotspot['permit_count'] > 50:
                    self.think(f"⚠️ DEVELOPMENT CLUSTER: {top_hotspot['city']} has high permit concentration")
                    self.send_alert(
                        'development_hotspot',
                        'medium',
                        f"Development cluster detected: {top_hotspot['city']}, {top_hotspot['county']} ({top_hotspot['permit_count']} permits)",
                        {'hotspots': hotspots[:3]}
                    )

                self.record_metric('top_hotspot_permits', top_hotspot['permit_count'],
                                 {'location': f"{top_hotspot['city']}, {top_hotspot['county']}"})

            # STEP 6: Calculate activity score (0-100)
            self.think("Step 6: Calculating permit activity score")

            activity_score = 50  # Start neutral

            # Volume factors
            if recent_count > 1000:
                activity_score += 20
                self.think("→ +20 points: High permit volume (>1000/month)")
            elif recent_count > 500:
                activity_score += 10
                self.think("→ +10 points: Moderate permit volume (500-1000/month)")
            elif recent_count < 100:
                activity_score -= 15
                self.think("→ -15 points: Low permit volume (<100/month)")

            # Value factors
            if total_value > 100000000:  # $100M
                activity_score += 15
                self.think("→ +15 points: High construction value (>$100M)")

            # Trend factors
            if change_pct > 30:
                activity_score += 10
                self.think("→ +10 points: Strong growth trend")
            elif change_pct < -20:
                activity_score -= 10
                self.think("→ -10 points: Declining trend")

            # Hotspot factors
            if hotspots and len(hotspots) >= 3:
                activity_score += 5
                self.think("→ +5 points: Multiple development hotspots")

            # Clamp to 0-100
            activity_score = max(0, min(100, activity_score))

            self.think(f"Final activity score: {activity_score}/100")
            self.record_metric('activity_score', activity_score)

            # STEP 7: Determine market development level
            self.think("Step 7: Determining market development level")
            if activity_score >= 75:
                development_level = "VERY ACTIVE"
                self.think("→ Development level: VERY ACTIVE (Strong construction growth)")
            elif activity_score >= 60:
                development_level = "ACTIVE"
                self.think("→ Development level: ACTIVE (Healthy development)")
            elif activity_score >= 40:
                development_level = "MODERATE"
                self.think("→ Development level: MODERATE (Steady activity)")
            else:
                development_level = "SLOW"
                self.think("→ Development level: SLOW (Limited activity)")

            # STEP 8: Analyze high-value construction projects (>$1M)
            self.think("Step 8: Identifying high-value construction projects (>$1M)")
            self.cursor.execute("""
                SELECT COUNT(*) as high_value_count,
                       SUM(CAST(construction_value AS NUMERIC)) as total_high_value
                FROM building_permits
                WHERE issue_date >= CURRENT_DATE - INTERVAL '30 days'
                  AND construction_value IS NOT NULL
                  AND construction_value != ''
                  AND CAST(construction_value AS NUMERIC) > 1000000;
            """)
            row = self.cursor.fetchone()
            if row:
                high_value_count, total_high_value = row
                high_value_count = high_value_count if high_value_count else 0
                total_high_value = float(total_high_value) if total_high_value else 0

                self.think(f"High-value projects: {high_value_count:,} (total: ${total_high_value:,.2f})")

                if high_value_count > 5:
                    self.think(f"⚠️ MAJOR PROJECTS: {high_value_count} high-value construction projects detected")

                self.record_metric('high_value_project_count', high_value_count)

            # STEP 9: Check for messages from other agents
            self.think("Step 9: Checking for messages from other agents")
            messages = self.receive_messages()
            if messages:
                self.think(f"Received {len(messages)} messages from other agents")
                for msg in messages:
                    self.think(f"→ Message from {msg['from']}: {msg['type']}")
            else:
                self.think("No messages from other agents")

            # STEP 10: Coordinate with Sales Activity Agent
            self.think("Step 10: Coordinating with Sales Activity Agent for trend validation")
            if hotspots and len(hotspots) > 0:
                # Share hotspot data with Sales Activity Agent
                self.send_message(
                    to_agent_id=f"sales-activity-{socket.gethostname()}",
                    message_type="info",
                    payload={
                        "source": "permit_activity",
                        "hotspots": hotspots[:3],
                        "context": "Development clusters may correlate with sales activity"
                    },
                    priority=6
                )
                self.think(f"→ Sent hotspot data to Sales Activity Agent")

            # STEP 11: Analyze residential vs commercial split
            self.think("Step 11: Analyzing residential vs commercial permit split")
            self.cursor.execute("""
                SELECT
                    COUNT(CASE WHEN permit_type ILIKE '%residential%' THEN 1 END) as residential,
                    COUNT(CASE WHEN permit_type ILIKE '%commercial%' THEN 1 END) as commercial,
                    COUNT(*) as total
                FROM building_permits
                WHERE issue_date >= CURRENT_DATE - INTERVAL '30 days';
            """)
            row = self.cursor.fetchone()
            if row:
                residential, commercial, total = row
                residential = residential if residential else 0
                commercial = commercial if commercial else 0
                total = total if total else 1

                res_pct = (residential / total) * 100 if total > 0 else 0
                com_pct = (commercial / total) * 100 if total > 0 else 0

                self.think(f"Permit mix: {res_pct:.1f}% residential, {com_pct:.1f}% commercial")

                if res_pct > 70:
                    self.think("→ Residential-heavy development (housing boom indicator)")
                elif com_pct > 40:
                    self.think("→ Significant commercial development (business growth)")

                self.record_metric('residential_pct', res_pct)
                self.record_metric('commercial_pct', com_pct)

            # STEP 12: Final summary and recommendations
            self.think("Step 12: Generating final permit activity summary")
            self.think(f"✅ Analysis complete: {total_permits:,} total | {recent_count} recent | Score: {activity_score}/100")

            # Return results
            return {
                'total_permits': total_permits,
                'recent_permits': recent_count,
                'construction_value': total_value,
                'activity_score': activity_score,
                'development_level': development_level,
                'hotspots': hotspots,
                'permit_types': permit_types,
                'high_value_projects': high_value_count if row else 0,
                'thought_steps': self.thought_count
            }

        except Exception as e:
            self.think(f"ERROR during analysis: {e}")
            print(f"\n[ERROR] Analysis failed: {e}")
            return None

    def run(self):
        """Main agent loop"""
        print("\n" + "="*70)
        print("  🏗️  PERMIT ACTIVITY TRACKER AGENT")
        print("="*70)
        print()
        print("  Features:")
        print("    ✓ Chain-of-Thought reasoning (12 steps)")
        print("    ✓ Development hotspot detection")
        print("    ✓ Permit surge alerts")
        print("    ✓ Chain-of-Agents coordination")
        print()

        print("  [1/3] Connecting...")
        if not self.connect():
            return

        print("  [2/3] Registering...")
        if not self.register():
            return

        print("  [3/3] Starting monitoring loop...")
        print(f"  ✅ Running (checking every {self.check_interval}s)")
        print()
        print("  Press Ctrl+C to stop")
        print()

        self.running = True

        try:
            while self.running:
                # Send heartbeat
                self.heartbeat()

                # Run analysis
                result = self.analyze_permit_activity()

                if result:
                    print(f"\n  ✅ Analysis #{self.analysis_count} complete")
                    print(f"     Thought steps: {result['thought_steps']}")
                    print(f"     Activity score: {result['activity_score']}/100")

                # Wait for next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\n  ⚠️  Stopping agent...")
            self.running = False

        # Mark offline
        try:
            self.cursor.execute("""
                UPDATE agent_registry
                SET status = 'offline'
                WHERE agent_id = %s;
            """, (self.agent_id,))
            self.conn.commit()
        except:
            pass

        if self.conn:
            self.conn.close()

        print("  ✅ Agent stopped")

if __name__ == "__main__":
    agent = PermitActivityAgent(check_interval=300)  # 5 minutes
    agent.run()
