#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Foreclosure Monitor Agent - Chain-of-Thought Autonomous Monitoring
Monitors foreclosure activity and identifies high-value investment opportunities
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

class ForeclosureMonitorAgent:
    """
    Foreclosure Monitor Agent with Chain-of-Thought reasoning

    Capabilities:
    - Monitors foreclosure_activity table for new filings
    - Identifies high-value foreclosure opportunities (>$100K)
    - Tracks auction dates and urgency
    - Coordinates with Market Analysis Agent for area context
    - Generates autonomous alerts for investment opportunities

    Chain-of-Thought: 15 steps per analysis cycle
    """

    def __init__(self, check_interval=300):
        """Initialize Foreclosure Monitor Agent"""
        self.agent_id = f"foreclosure-monitor-{socket.gethostname()}"
        self.agent_name = "Foreclosure Monitor (CoT)"
        self.agent_type = "monitoring"
        self.environment = "pc"
        self.check_interval = check_interval  # 5 minutes

        self.capabilities = [
            "foreclosure_tracking",
            "auction_monitoring",
            "value_assessment",
            "urgency_detection",
            "opportunity_scoring",
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
            # Try to reconnect
            self.connect()
            self.register()

    def think(self, thought):
        """
        Chain-of-Thought: Record and display reasoning step
        Stores in agent_metrics for full audit trail
        """
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
                'foreclosure',
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

                # Mark as processed
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

    def analyze_foreclosures(self):
        """
        Main analysis function with Chain-of-Thought reasoning
        15-step transparent decision-making process
        """
        self.analysis_count += 1
        self.thought_count = 0

        print("\n" + "="*70)
        print(f"  🔍 FORECLOSURE ANALYSIS - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)

        try:
            # STEP 1: Count total foreclosure records
            self.think("Step 1: Counting total foreclosure records in database")
            self.cursor.execute("""
                SELECT COUNT(*) as total
                FROM foreclosure_activity;
            """)
            row = self.cursor.fetchone()
            total_foreclosures = row[0] if row else 0
            self.think(f"Found {total_foreclosures:,} total foreclosure records")
            self.record_metric('total_foreclosures', total_foreclosures)

            # STEP 2: Analyze recent filings (last 30 days)
            self.think("Step 2: Analyzing recent foreclosure filings (last 30 days)")
            self.cursor.execute("""
                SELECT COUNT(*) as recent_count,
                       AVG(CAST(assessed_value AS NUMERIC)) as avg_value
                FROM foreclosure_activity
                WHERE filing_date >= CURRENT_DATE - INTERVAL '30 days'
                  AND assessed_value IS NOT NULL;
            """)
            row = self.cursor.fetchone()
            if row:
                recent_count, avg_value = row
                recent_count = recent_count if recent_count else 0
                avg_value = float(avg_value) if avg_value else 0
                self.think(f"Recent filings: {recent_count:,} in last 30 days")
                self.think(f"Average assessed value: ${avg_value:,.2f}")
                self.record_metric('recent_filings_30d', recent_count)
                self.record_metric('avg_assessed_value', avg_value)

            # STEP 3: Identify high-value foreclosures (>$100K)
            self.think("Step 3: Identifying high-value foreclosure opportunities (>$100K)")
            self.cursor.execute("""
                SELECT COUNT(*) as high_value_count,
                       SUM(CAST(assessed_value AS NUMERIC)) as total_value
                FROM foreclosure_activity
                WHERE assessed_value IS NOT NULL
                  AND CAST(assessed_value AS NUMERIC) > 100000
                  AND status IN ('active', 'pending', 'scheduled');
            """)
            row = self.cursor.fetchone()
            if row:
                high_value_count, total_value = row
                high_value_count = high_value_count if high_value_count else 0
                total_value = float(total_value) if total_value else 0
                self.think(f"High-value opportunities: {high_value_count:,} properties")
                self.think(f"Total high-value portfolio: ${total_value:,.2f}")

                if high_value_count > 0:
                    self.think(f"⚠️ OPPORTUNITY: {high_value_count} high-value foreclosures detected")
                    self.send_alert(
                        'high_value_foreclosures',
                        'high',
                        f'{high_value_count} high-value foreclosure opportunities (>${100000:,})',
                        {'count': high_value_count, 'total_value': total_value}
                    )

                self.record_metric('high_value_count', high_value_count)
                self.record_metric('high_value_total', total_value)

            # STEP 4: Check for urgent auctions (within 14 days)
            self.think("Step 4: Checking for urgent auction dates (within 14 days)")
            self.cursor.execute("""
                SELECT COUNT(*) as urgent_count,
                       MIN(auction_date) as nearest_auction
                FROM foreclosure_activity
                WHERE auction_date IS NOT NULL
                  AND auction_date <= CURRENT_DATE + INTERVAL '14 days'
                  AND auction_date >= CURRENT_DATE
                  AND status IN ('active', 'scheduled');
            """)
            row = self.cursor.fetchone()
            if row:
                urgent_count, nearest_auction = row
                urgent_count = urgent_count if urgent_count else 0

                if urgent_count > 0:
                    days_until = (nearest_auction - datetime.now().date()).days
                    self.think(f"⚠️ URGENT: {urgent_count} auctions within 14 days")
                    self.think(f"Nearest auction: {nearest_auction} ({days_until} days from now)")

                    self.send_alert(
                        'urgent_auctions',
                        'high' if days_until <= 7 else 'medium',
                        f'{urgent_count} urgent foreclosure auctions within 14 days',
                        {'count': urgent_count, 'nearest_date': str(nearest_auction), 'days_until': days_until}
                    )
                else:
                    self.think("No urgent auctions detected in next 14 days")

                self.record_metric('urgent_auctions', urgent_count)

            # STEP 5: Analyze by county distribution
            self.think("Step 5: Analyzing foreclosure distribution by county")
            self.cursor.execute("""
                SELECT county, COUNT(*) as count
                FROM foreclosure_activity
                WHERE county IS NOT NULL
                  AND status IN ('active', 'pending', 'scheduled')
                GROUP BY county
                ORDER BY count DESC
                LIMIT 5;
            """)

            county_data = []
            for row in self.cursor.fetchall():
                county, count = row
                county_data.append({'county': county, 'count': count})

            if county_data:
                top_county = county_data[0]
                self.think(f"Top foreclosure county: {top_county['county']} ({top_county['count']:,} cases)")

                # Check if concentration is high (>30% in one county)
                if total_foreclosures > 0:
                    concentration = (top_county['count'] / total_foreclosures) * 100
                    if concentration > 30:
                        self.think(f"⚠️ HIGH CONCENTRATION: {concentration:.1f}% of foreclosures in {top_county['county']}")

            # STEP 6: Calculate opportunity score (0-100)
            self.think("Step 6: Calculating overall foreclosure opportunity score")

            opportunity_score = 50  # Start neutral

            # Positive factors
            if high_value_count > 10:
                opportunity_score += 20
                self.think("→ +20 points: Substantial high-value inventory (>10 properties)")
            elif high_value_count > 5:
                opportunity_score += 10
                self.think("→ +10 points: Moderate high-value inventory (5-10 properties)")

            if urgent_count > 5:
                opportunity_score += 15
                self.think("→ +15 points: Multiple urgent opportunities (>5 auctions)")
            elif urgent_count > 0:
                opportunity_score += 5
                self.think("→ +5 points: Some urgent opportunities")

            if recent_count > 100:
                opportunity_score += 10
                self.think("→ +10 points: High recent activity (>100 filings/month)")

            # Negative factors
            if recent_count < 20:
                opportunity_score -= 15
                self.think("→ -15 points: Low recent activity (<20 filings/month)")

            if high_value_count == 0:
                opportunity_score -= 20
                self.think("→ -20 points: No high-value opportunities available")

            # Clamp to 0-100
            opportunity_score = max(0, min(100, opportunity_score))

            self.think(f"Final opportunity score: {opportunity_score}/100")
            self.record_metric('opportunity_score', opportunity_score)

            # STEP 7: Determine opportunity level
            self.think("Step 7: Determining overall opportunity level")
            if opportunity_score >= 75:
                opportunity_level = "EXCELLENT"
                self.think("→ Opportunity level: EXCELLENT (Strong buyer's market)")
            elif opportunity_score >= 60:
                opportunity_level = "GOOD"
                self.think("→ Opportunity level: GOOD (Favorable conditions)")
            elif opportunity_score >= 40:
                opportunity_level = "MODERATE"
                self.think("→ Opportunity level: MODERATE (Average market)")
            else:
                opportunity_level = "LIMITED"
                self.think("→ Opportunity level: LIMITED (Few opportunities)")

                if opportunity_score < 30:
                    self.send_alert(
                        'low_opportunity',
                        'low',
                        'Limited foreclosure investment opportunities currently available',
                        {'score': opportunity_score}
                    )

            # STEP 8: Check for messages from other agents (Chain-of-Agents)
            self.think("Step 8: Checking for messages from other agents")
            messages = self.receive_messages()
            if messages:
                self.think(f"Received {len(messages)} messages from other agents")
                for msg in messages:
                    self.think(f"→ Message from {msg['from']}: {msg['type']}")
            else:
                self.think("No messages from other agents")

            # STEP 9: Query Market Analysis Agent for context (if available)
            self.think("Step 9: Requesting market context from Market Analysis Agent")
            if high_value_count > 0 and county_data:
                # Request market health for top foreclosure county
                self.send_message(
                    to_agent_id=f"market-analysis-{socket.gethostname()}",
                    message_type="query",
                    payload={
                        "request": "market_health",
                        "county": top_county['county'],
                        "context": "foreclosure_analysis"
                    },
                    priority=5
                )
                self.think(f"→ Sent market health query for {top_county['county']}")

            # STEP 10: Analyze property types in foreclosure
            self.think("Step 10: Analyzing property types in foreclosure")
            self.cursor.execute("""
                SELECT property_use, COUNT(*) as count
                FROM foreclosure_activity
                WHERE property_use IS NOT NULL
                  AND status IN ('active', 'pending', 'scheduled')
                GROUP BY property_use
                ORDER BY count DESC
                LIMIT 3;
            """)

            property_types = []
            for row in self.cursor.fetchall():
                prop_type, count = row
                property_types.append({'type': prop_type, 'count': count})
                self.think(f"→ {prop_type}: {count:,} properties")

            # STEP 11: Calculate average days in foreclosure
            self.think("Step 11: Calculating average time in foreclosure process")
            self.cursor.execute("""
                SELECT AVG(EXTRACT(DAY FROM (COALESCE(auction_date, CURRENT_DATE) - filing_date))) as avg_days
                FROM foreclosure_activity
                WHERE filing_date IS NOT NULL
                  AND status IN ('active', 'pending', 'scheduled');
            """)
            row = self.cursor.fetchone()
            if row and row[0]:
                avg_days = int(row[0])
                self.think(f"Average foreclosure duration: {avg_days} days")
                self.record_metric('avg_foreclosure_duration', avg_days)

                if avg_days > 180:
                    self.think("→ Long foreclosure timeline indicates backlog")
                elif avg_days < 60:
                    self.think("→ Fast foreclosure timeline indicates efficient processing")

            # STEP 12: Identify potential investment opportunities
            self.think("Step 12: Identifying top investment opportunities")
            self.cursor.execute("""
                SELECT parcel_id, county, assessed_value, auction_date,
                       EXTRACT(DAY FROM (auction_date - CURRENT_DATE)) as days_until_auction
                FROM foreclosure_activity
                WHERE assessed_value IS NOT NULL
                  AND CAST(assessed_value AS NUMERIC) > 100000
                  AND auction_date >= CURRENT_DATE
                  AND status IN ('active', 'scheduled')
                ORDER BY CAST(assessed_value AS NUMERIC) DESC
                LIMIT 5;
            """)

            opportunities = []
            for row in self.cursor.fetchall():
                parcel_id, county, assessed_value, auction_date, days_until = row
                opportunities.append({
                    'parcel_id': parcel_id,
                    'county': county,
                    'value': float(assessed_value),
                    'auction_date': str(auction_date),
                    'days_until': int(days_until) if days_until else None
                })

            if opportunities:
                self.think(f"Top investment opportunity: ${opportunities[0]['value']:,.2f} in {opportunities[0]['county']}")
                self.record_metric('top_opportunity_value', opportunities[0]['value'])

            # STEP 13: Calculate month-over-month change
            self.think("Step 13: Calculating month-over-month filing trend")
            self.cursor.execute("""
                SELECT
                    COUNT(CASE WHEN filing_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as current_month,
                    COUNT(CASE WHEN filing_date >= CURRENT_DATE - INTERVAL '60 days'
                               AND filing_date < CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as previous_month
                FROM foreclosure_activity;
            """)
            row = self.cursor.fetchone()
            if row:
                current_month, previous_month = row
                current_month = current_month if current_month else 0
                previous_month = previous_month if previous_month else 0

                if previous_month > 0:
                    change_pct = ((current_month - previous_month) / previous_month) * 100
                    self.think(f"Filing trend: {change_pct:+.1f}% vs previous month")

                    if abs(change_pct) > 20:
                        self.think(f"⚠️ SIGNIFICANT CHANGE: Foreclosure filings {'increased' if change_pct > 0 else 'decreased'} {abs(change_pct):.1f}%")
                        self.send_alert(
                            'filing_trend',
                            'medium',
                            f"Foreclosure filings {'increased' if change_pct > 0 else 'decreased'} {abs(change_pct):.1f}% month-over-month",
                            {'current': current_month, 'previous': previous_month, 'change_pct': change_pct}
                        )

                    self.record_metric('filing_change_pct', change_pct)

            # STEP 14: Generate foreclosure health indicator
            self.think("Step 14: Generating foreclosure market health indicator")

            # Lower foreclosure rate = healthier market
            # Higher opportunity score = better for investors
            market_health = "HEALTHY" if recent_count < 100 else "DISTRESSED" if recent_count > 300 else "MODERATE"
            investor_climate = "FAVORABLE" if opportunity_score > 60 else "CHALLENGING" if opportunity_score < 40 else "NEUTRAL"

            self.think(f"→ Market health: {market_health}")
            self.think(f"→ Investor climate: {investor_climate}")

            # STEP 15: Final summary
            self.think("Step 15: Generating final foreclosure analysis summary")
            self.think(f"✅ Analysis complete: {total_foreclosures:,} total | {high_value_count} high-value | Score: {opportunity_score}/100")

            # Return results
            return {
                'total_foreclosures': total_foreclosures,
                'recent_filings': recent_count,
                'high_value_count': high_value_count,
                'urgent_auctions': urgent_count,
                'opportunity_score': opportunity_score,
                'opportunity_level': opportunity_level,
                'market_health': market_health,
                'investor_climate': investor_climate,
                'top_opportunities': opportunities,
                'thought_steps': self.thought_count
            }

        except Exception as e:
            self.think(f"ERROR during analysis: {e}")
            print(f"\n[ERROR] Analysis failed: {e}")
            return None

    def run(self):
        """Main agent loop"""
        print("\n" + "="*70)
        print("  🏛️  FORECLOSURE MONITOR AGENT")
        print("="*70)
        print()
        print("  Features:")
        print("    ✓ Chain-of-Thought reasoning (15 steps)")
        print("    ✓ High-value opportunity detection")
        print("    ✓ Urgent auction alerts")
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
                result = self.analyze_foreclosures()

                if result:
                    print(f"\n  ✅ Analysis #{self.analysis_count} complete")
                    print(f"     Thought steps: {result['thought_steps']}")
                    print(f"     Opportunity score: {result['opportunity_score']}/100")

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
    agent = ForeclosureMonitorAgent(check_interval=300)  # 5 minutes
    agent.run()
