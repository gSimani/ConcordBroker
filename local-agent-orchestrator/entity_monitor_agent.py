#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corporate Entity Monitor Agent - Chain-of-Thought Autonomous Monitoring
Monitors Florida Sunbiz entities and matches to property ownership
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

class EntityMonitorAgent:
    """
    Corporate Entity Monitor Agent with Chain-of-Thought reasoning

    Capabilities:
    - Monitors sunbiz_corporate and florida_entities tables
    - Detects new entity filings and status changes
    - Matches entities to property ownership
    - Identifies related entity networks
    - Coordinates with Property/Foreclosure agents
    - Generates autonomous alerts for ownership changes

    Chain-of-Thought: 18 steps per analysis cycle
    """

    def __init__(self, check_interval=600):
        """Initialize Entity Monitor Agent"""
        self.agent_id = f"entity-monitor-{socket.gethostname()}"
        self.agent_name = "Corporate Entity Monitor (CoT)"
        self.agent_type = "monitoring"
        self.environment = "pc"
        self.check_interval = check_interval  # 10 minutes

        self.capabilities = [
            "entity_monitoring",
            "ownership_tracking",
            "status_change_detection",
            "entity_network_analysis",
            "property_matching",
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
                'entity',
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

    def analyze_entities(self):
        """
        Main analysis function with Chain-of-Thought reasoning
        18-step transparent decision-making process
        """
        self.analysis_count += 1
        self.thought_count = 0

        print("\n" + "="*70)
        print(f"  🔍 ENTITY MONITORING ANALYSIS - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)

        try:
            # STEP 1: Count total entities in database
            self.think("Step 1: Counting total corporate entities in database")
            self.cursor.execute("""
                SELECT COUNT(*) as sunbiz_count
                FROM sunbiz_corporate;
            """)
            row = self.cursor.fetchone()
            sunbiz_count = row[0] if row else 0

            self.cursor.execute("""
                SELECT COUNT(*) as entities_count
                FROM florida_entities;
            """)
            row = self.cursor.fetchone()
            entities_count = row[0] if row else 0

            self.think(f"Found {sunbiz_count:,} Sunbiz corporate records")
            self.think(f"Found {entities_count:,} Florida entity records")
            self.record_metric('total_sunbiz_entities', sunbiz_count)
            self.record_metric('total_florida_entities', entities_count)

            # STEP 2: Analyze recent entity filings (last 30 days)
            self.think("Step 2: Analyzing recent entity filings (last 30 days)")
            self.cursor.execute("""
                SELECT COUNT(*) as recent_filings
                FROM sunbiz_corporate
                WHERE filing_date >= CURRENT_DATE - INTERVAL '30 days';
            """)
            row = self.cursor.fetchone()
            recent_filings = row[0] if row else 0
            self.think(f"Recent entity filings: {recent_filings:,} in last 30 days")
            self.record_metric('recent_filings_30d', recent_filings)

            # STEP 3: Detect status changes (Active → Dissolved/Inactive)
            self.think("Step 3: Detecting recent entity status changes")
            self.cursor.execute("""
                SELECT COUNT(*) as dissolved_count
                FROM sunbiz_corporate
                WHERE status IN ('DISSOLVED', 'INACTIVE', 'CANCELLED')
                  AND COALESCE(status_date, filing_date) >= CURRENT_DATE - INTERVAL '30 days';
            """)
            row = self.cursor.fetchone()
            dissolved_count = row[0] if row else 0

            if dissolved_count > 0:
                self.think(f"⚠️ STATUS CHANGES: {dissolved_count} entities dissolved/inactive in last 30 days")
                self.send_alert(
                    'entity_dissolutions',
                    'medium',
                    f'{dissolved_count} entities changed to dissolved/inactive status',
                    {'count': dissolved_count}
                )
            else:
                self.think("No recent entity dissolutions detected")

            self.record_metric('recent_dissolutions', dissolved_count)

            # STEP 4: Analyze entity types
            self.think("Step 4: Analyzing distribution of entity types")
            self.cursor.execute("""
                SELECT entity_type, COUNT(*) as count
                FROM florida_entities
                WHERE entity_type IS NOT NULL
                GROUP BY entity_type
                ORDER BY count DESC
                LIMIT 5;
            """)

            entity_types = []
            for row in self.cursor.fetchall():
                etype, count = row
                entity_types.append({'type': etype, 'count': count})
                self.think(f"→ {etype}: {count:,} entities")

            # STEP 5: Identify active LLCs vs Corporations
            self.think("Step 5: Comparing LLCs vs Corporations in active status")
            self.cursor.execute("""
                SELECT
                    COUNT(CASE WHEN entity_name ILIKE '%LLC%' OR entity_type LIKE '%LLC%' THEN 1 END) as llc_count,
                    COUNT(CASE WHEN entity_name ILIKE '%CORP%' OR entity_name ILIKE '%INC%'
                               OR entity_type LIKE '%CORP%' THEN 1 END) as corp_count,
                    COUNT(*) as total
                FROM sunbiz_corporate
                WHERE status = 'ACTIVE';
            """)
            row = self.cursor.fetchone()
            if row:
                llc_count, corp_count, total = row
                llc_pct = (llc_count / total * 100) if total > 0 else 0
                corp_pct = (corp_count / total * 100) if total > 0 else 0

                self.think(f"Active entities: {llc_pct:.1f}% LLCs, {corp_pct:.1f}% Corporations")
                self.record_metric('llc_percentage', llc_pct)
                self.record_metric('corp_percentage', corp_pct)

            # STEP 6: Match entities to property ownership
            self.think("Step 6: Matching corporate entities to property ownership")
            self.cursor.execute("""
                SELECT COUNT(DISTINCT p.parcel_id) as properties_with_corporate_owners
                FROM florida_parcels p
                WHERE p.owner_name ILIKE '%LLC%'
                   OR p.owner_name ILIKE '%CORP%'
                   OR p.owner_name ILIKE '%INC%'
                   OR p.owner_name ILIKE '%LTD%';
            """)
            row = self.cursor.fetchone()
            corporate_owned = row[0] if row else 0

            if corporate_owned > 0:
                total_properties = 10304043  # From earlier analysis
                corporate_pct = (corporate_owned / total_properties * 100) if total_properties > 0 else 0
                self.think(f"Corporate-owned properties: {corporate_owned:,} ({corporate_pct:.1f}% of total)")
                self.record_metric('corporate_owned_properties', corporate_owned)
                self.record_metric('corporate_ownership_pct', corporate_pct)

            # STEP 7: Identify entities with multiple properties
            self.think("Step 7: Identifying entities with multiple property holdings")
            self.cursor.execute("""
                SELECT COUNT(*) as multi_property_entities
                FROM (
                    SELECT owner_name, COUNT(*) as property_count
                    FROM florida_parcels
                    WHERE owner_name IS NOT NULL
                      AND (owner_name ILIKE '%LLC%'
                       OR owner_name ILIKE '%CORP%'
                       OR owner_name ILIKE '%INC%')
                    GROUP BY owner_name
                    HAVING COUNT(*) > 5
                ) sub;
            """)
            row = self.cursor.fetchone()
            multi_property_count = row[0] if row else 0

            if multi_property_count > 0:
                self.think(f"Found {multi_property_count:,} entities with 5+ properties (portfolio owners)")
                self.record_metric('portfolio_entities', multi_property_count)

            # STEP 8: Detect new high-value entity formations
            self.think("Step 8: Detecting new high-value entity formations")
            # Note: We don't have capital stock info in all cases, using filing date as proxy
            self.cursor.execute("""
                SELECT COUNT(*) as new_entities_7d
                FROM sunbiz_corporate
                WHERE filing_date >= CURRENT_DATE - INTERVAL '7 days'
                  AND status = 'ACTIVE';
            """)
            row = self.cursor.fetchone()
            new_entities_7d = row[0] if row else 0

            if new_entities_7d > 50:
                self.think(f"⚠️ HIGH FORMATION RATE: {new_entities_7d} new entities in last 7 days")
                self.send_alert(
                    'high_formation_rate',
                    'low',
                    f'{new_entities_7d} new business entities formed in last 7 days',
                    {'count': new_entities_7d}
                )
            else:
                self.think(f"Normal formation rate: {new_entities_7d} new entities in last 7 days")

            self.record_metric('new_entities_7d', new_entities_7d)

            # STEP 9: Identify dissolved entities with property holdings
            self.think("Step 9: Identifying dissolved entities still holding properties")
            self.cursor.execute("""
                SELECT COUNT(DISTINCT p.parcel_id) as orphaned_properties
                FROM florida_parcels p
                JOIN sunbiz_corporate s ON p.owner_name ILIKE '%' || s.entity_name || '%'
                WHERE s.status IN ('DISSOLVED', 'INACTIVE', 'CANCELLED')
                  AND p.owner_name IS NOT NULL
                LIMIT 1000;
            """)
            row = self.cursor.fetchone()
            orphaned_properties = row[0] if row else 0

            if orphaned_properties > 0:
                self.think(f"⚠️ ORPHANED ASSETS: {orphaned_properties} properties owned by dissolved entities")
                self.send_alert(
                    'orphaned_properties',
                    'medium',
                    f'{orphaned_properties} properties owned by dissolved/inactive entities',
                    {'count': orphaned_properties}
                )

            # STEP 10: Calculate entity health score (0-100)
            self.think("Step 10: Calculating entity ecosystem health score")

            health_score = 50  # Start neutral

            # Positive factors
            if new_entities_7d > 30:
                health_score += 15
                self.think("→ +15 points: Strong new entity formation rate")
            elif new_entities_7d < 10:
                health_score -= 10
                self.think("→ -10 points: Low entity formation rate")

            if dissolved_count < 50:
                health_score += 10
                self.think("→ +10 points: Low dissolution rate (healthy)")
            elif dissolved_count > 150:
                health_score -= 15
                self.think("→ -15 points: High dissolution rate (distress signal)")

            if corporate_owned > 1000000:
                health_score += 10
                self.think("→ +10 points: High corporate property ownership")

            # Negative factors
            if orphaned_properties > 100:
                health_score -= 20
                self.think("→ -20 points: Many orphaned properties (asset management issues)")

            # Clamp to 0-100
            health_score = max(0, min(100, health_score))

            self.think(f"Final entity ecosystem health: {health_score}/100")
            self.record_metric('entity_health_score', health_score)

            # STEP 11: Determine ecosystem status
            self.think("Step 11: Determining overall ecosystem status")
            if health_score >= 75:
                ecosystem_status = "THRIVING"
                self.think("→ Ecosystem status: THRIVING (Strong business environment)")
            elif health_score >= 60:
                ecosystem_status = "HEALTHY"
                self.think("→ Ecosystem status: HEALTHY (Normal activity)")
            elif health_score >= 40:
                ecosystem_status = "MODERATE"
                self.think("→ Ecosystem status: MODERATE (Some concerns)")
            else:
                ecosystem_status = "DISTRESSED"
                self.think("→ Ecosystem status: DISTRESSED (Potential issues)")

                self.send_alert(
                    'ecosystem_distress',
                    'high',
                    f'Entity ecosystem showing distress (score: {health_score}/100)',
                    {'score': health_score, 'status': ecosystem_status}
                )

            # STEP 12: Check for messages from other agents
            self.think("Step 12: Checking for messages from other agents")
            messages = self.receive_messages()
            if messages:
                self.think(f"Received {len(messages)} messages from other agents")
                for msg in messages:
                    self.think(f"→ Message from {msg['from']}: {msg['type']}")
            else:
                self.think("No messages from other agents")

            # STEP 13: Coordinate with Foreclosure Monitor
            self.think("Step 13: Coordinating with Foreclosure Monitor for distress signals")
            if dissolved_count > 0 or orphaned_properties > 0:
                # Share dissolved entity data with Foreclosure Monitor
                self.send_message(
                    to_agent_id=f"foreclosure-monitor-{socket.gethostname()}",
                    message_type="alert",
                    payload={
                        "source": "entity_monitor",
                        "dissolved_entities": dissolved_count,
                        "orphaned_properties": orphaned_properties,
                        "context": "Dissolved entities may have properties in foreclosure"
                    },
                    priority=6
                )
                self.think(f"→ Sent distress signals to Foreclosure Monitor")

            # STEP 14: Analyze entity name patterns for shell companies
            self.think("Step 14: Analyzing entity naming patterns for potential shell companies")
            self.cursor.execute("""
                SELECT COUNT(*) as generic_name_count
                FROM sunbiz_corporate
                WHERE entity_name SIMILAR TO '%[0-9]{3,}%'
                  OR entity_name ILIKE '%HOLDINGS%'
                  OR entity_name ILIKE '%VENTURES%'
                  OR entity_name ILIKE '%INVESTMENTS%'
                  AND status = 'ACTIVE'
                LIMIT 10000;
            """)
            row = self.cursor.fetchone()
            generic_names = row[0] if row else 0

            if generic_names > 0:
                self.think(f"Potential shell/holding companies: {generic_names:,} with generic naming patterns")
                self.record_metric('potential_shell_companies', generic_names)

            # STEP 15: Track registered agent concentrations
            self.think("Step 15: Identifying registered agent concentrations")
            self.cursor.execute("""
                SELECT registered_agent_name, COUNT(*) as entity_count
                FROM sunbiz_corporate
                WHERE registered_agent_name IS NOT NULL
                  AND status = 'ACTIVE'
                GROUP BY registered_agent_name
                ORDER BY entity_count DESC
                LIMIT 3;
            """)

            top_agents = []
            for row in self.cursor.fetchall():
                agent_name, entity_count = row
                if entity_count > 100:  # Only track significant concentrations
                    top_agents.append({'agent': agent_name, 'count': entity_count})
                    self.think(f"→ Top agent: {agent_name} ({entity_count:,} entities)")

            if top_agents:
                self.record_metric('top_registered_agent_count', top_agents[0]['count'],
                                 {'agent': top_agents[0]['agent']})

            # STEP 16: Calculate entity formation trend
            self.think("Step 16: Calculating entity formation trend (30d vs 60d)")
            self.cursor.execute("""
                SELECT
                    COUNT(CASE WHEN filing_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as current_30d,
                    COUNT(CASE WHEN filing_date >= CURRENT_DATE - INTERVAL '60 days'
                               AND filing_date < CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as previous_30d
                FROM sunbiz_corporate;
            """)
            row = self.cursor.fetchone()
            if row:
                current_30d, previous_30d = row
                current_30d = current_30d if current_30d else 0
                previous_30d = previous_30d if previous_30d else 0

                if previous_30d > 0:
                    trend_pct = ((current_30d - previous_30d) / previous_30d) * 100
                    self.think(f"Formation trend: {trend_pct:+.1f}% vs previous period")

                    if abs(trend_pct) > 25:
                        self.think(f"⚠️ SIGNIFICANT TREND: Entity formations {'surged' if trend_pct > 0 else 'dropped'} {abs(trend_pct):.1f}%")

                    self.record_metric('formation_trend_pct', trend_pct)

            # STEP 17: Identify potential investment entities
            self.think("Step 17: Identifying potential investment/acquisition entities")
            self.cursor.execute("""
                SELECT COUNT(*) as investment_entities
                FROM sunbiz_corporate
                WHERE (entity_name ILIKE '%INVESTMENT%'
                   OR entity_name ILIKE '%CAPITAL%'
                   OR entity_name ILIKE '%FUND%'
                   OR entity_name ILIKE '%ACQUISITION%')
                  AND status = 'ACTIVE'
                  AND filing_date >= CURRENT_DATE - INTERVAL '180 days';
            """)
            row = self.cursor.fetchone()
            investment_entities = row[0] if row else 0

            if investment_entities > 0:
                self.think(f"Recently formed investment entities: {investment_entities:,} (6-month window)")
                self.record_metric('recent_investment_entities', investment_entities)

            # STEP 18: Final summary
            self.think("Step 18: Generating final entity monitoring summary")
            self.think(f"✅ Analysis complete: {sunbiz_count:,} entities | {dissolved_count} dissolved | Health: {health_score}/100")

            # Return results
            return {
                'total_sunbiz_entities': sunbiz_count,
                'total_florida_entities': entities_count,
                'recent_filings': recent_filings,
                'recent_dissolutions': dissolved_count,
                'corporate_owned_properties': corporate_owned,
                'portfolio_entities': multi_property_count,
                'orphaned_properties': orphaned_properties,
                'health_score': health_score,
                'ecosystem_status': ecosystem_status,
                'new_entities_7d': new_entities_7d,
                'thought_steps': self.thought_count
            }

        except Exception as e:
            self.think(f"ERROR during analysis: {e}")
            print(f"\n[ERROR] Analysis failed: {e}")
            return None

    def run(self):
        """Main agent loop"""
        print("\n" + "="*70)
        print("  🏢  CORPORATE ENTITY MONITOR AGENT")
        print("="*70)
        print()
        print("  Features:")
        print("    ✓ Chain-of-Thought reasoning (18 steps)")
        print("    ✓ Entity status change detection")
        print("    ✓ Property ownership matching")
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
                result = self.analyze_entities()

                if result:
                    print(f"\n  ✅ Analysis #{self.analysis_count} complete")
                    print(f"     Thought steps: {result['thought_steps']}")
                    print(f"     Health score: {result['health_score']}/100")

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
    agent = EntityMonitorAgent(check_interval=600)  # 10 minutes
    agent.run()
