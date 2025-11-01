#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Analysis Agent with Chain-of-Thought Reasoning
Analyzes overall market conditions across multiple data sources
"""

import os
import sys
import json
import time
import socket
from datetime import datetime, timedelta
from typing import Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv('.env.mcp')

import psycopg2
import psycopg2.extras

class MarketAnalysisAgent:
    def __init__(self, check_interval=600):  # 10 minutes
        self.agent_id = f"market-analysis-{socket.gethostname()}"
        self.agent_name = "Market Analysis Agent (CoT)"
        self.agent_type = "analysis"
        self.environment = "pc"
        self.capabilities = ["market_analysis", "trend_analysis", "chain_of_thought", "data_correlation"]

        self.check_interval = check_interval
        self.conn: Optional[psycopg2.extensions.connection] = None
        self.cursor: Optional[psycopg2.extras.RealDictCursor] = None

        self.thought_count = 0
        self.analysis_count = 0

    def connect(self):
        """Connect to Supabase database"""
        self.conn = psycopg2.connect(os.getenv('POSTGRES_URL_NON_POOLING'))
        self.conn.autocommit = True
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def register(self):
        """Register agent in agent_registry"""
        self.cursor.execute("""
            INSERT INTO agent_registry (
                agent_id, agent_name, agent_type, environment, capabilities, status
            ) VALUES (%s, %s, %s, %s, %s, 'online')
            ON CONFLICT (agent_id)
            DO UPDATE SET
                status = 'online',
                last_heartbeat = NOW(),
                agent_name = EXCLUDED.agent_name,
                agent_type = EXCLUDED.agent_type,
                capabilities = EXCLUDED.capabilities;
        """, (
            self.agent_id,
            self.agent_name,
            self.agent_type,
            self.environment,
            json.dumps(self.capabilities)
        ))

    def heartbeat(self):
        """Send heartbeat to indicate agent is alive"""
        self.cursor.execute("""
            UPDATE agent_registry
            SET last_heartbeat = NOW(), status = 'online'
            WHERE agent_id = %s;
        """, (self.agent_id,))

    def think(self, thought: str, data: dict = None):
        """Record a chain-of-thought reasoning step"""
        self.thought_count += 1
        print(f"  💭 {thought}")
        if data:
            print(f"     Data: {str(data)[:100]}...")

        # Store reasoning step in database
        self.cursor.execute("""
            INSERT INTO agent_metrics (
                agent_id, metric_type, metric_name, metric_value, metadata
            ) VALUES (%s, %s, %s, %s, %s::jsonb);
        """, (
            self.agent_id,
            "reasoning",
            "chain_of_thought_steps",
            self.thought_count,
            json.dumps({
                "thought": thought,
                "step": self.thought_count,
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
        ))

    def send_alert(self, alert_type: str, severity: str, message: str, metadata: dict = None):
        """Send alert to agent_alerts table"""
        print(f"  🚨 ALERT: [{severity}] {message}")

        self.cursor.execute("""
            INSERT INTO agent_alerts (
                agent_id, alert_type, severity, message, details, status
            ) VALUES (%s, %s, %s, %s, %s::jsonb, 'active');
        """, (
            self.agent_id,
            alert_type,
            severity,
            message,
            json.dumps(metadata) if metadata else None
        ))

    def record_metric(self, metric_type: str, metric_name: str, value: float, metadata: dict = None):
        """Record a metric"""
        self.cursor.execute("""
            INSERT INTO agent_metrics (
                agent_id, metric_type, metric_name, metric_value, metadata
            ) VALUES (%s, %s, %s, %s, %s::jsonb);
        """, (
            self.agent_id,
            metric_type,
            metric_name,
            value,
            json.dumps(metadata) if metadata else None
        ))

    def analyze_market_conditions(self):
        """Analyze overall market conditions with Chain-of-Thought reasoning"""
        self.analysis_count += 1
        self.thought_count = 0

        print("\n" + "=" * 70)
        print(f"  🔍 MARKET ANALYSIS - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 70)

        try:
            # Step 1: Inventory Analysis
            self.think("Step 1: Analyzing property inventory")
            self.cursor.execute("""
                SELECT COUNT(*) as total_properties,
                       AVG(just_value) FILTER (WHERE just_value > 0) as avg_value,
                       COUNT(DISTINCT county) as county_count
                FROM florida_parcels;
            """)
            inventory = self.cursor.fetchone()
            total_properties = inventory['total_properties'] if inventory else 0
            avg_value = float(inventory['avg_value']) if inventory and inventory['avg_value'] else 0
            county_count = inventory['county_count'] if inventory else 0

            self.think(f"Market inventory: {total_properties:,} properties across {county_count} counties", {
                'total': total_properties,
                'avg_value': avg_value,
                'counties': county_count
            })

            # Step 2: Sales Volume Analysis
            self.think("Step 2: Analyzing sales volume trends")
            self.cursor.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days') as sales_30d,
                    COUNT(*) FILTER (WHERE sale_date >= CURRENT_DATE - INTERVAL '90 days') as sales_90d,
                    AVG(sale_price) FILTER (WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days') as avg_price_30d
                FROM property_sales_history
                WHERE sale_price IS NOT NULL AND sale_price > 0;
            """)
            sales_volume = self.cursor.fetchone()
            sales_30d = sales_volume['sales_30d'] if sales_volume else 0
            sales_90d = sales_volume['sales_90d'] if sales_volume else 0
            avg_price_30d = float(sales_volume['avg_price_30d']) if sales_volume and sales_volume['avg_price_30d'] else 0

            self.think(f"Sales volume: {sales_30d:,} (30d), {sales_90d:,} (90d)", {
                'sales_30d': sales_30d,
                'sales_90d': sales_90d,
                'avg_price': avg_price_30d
            })

            # Calculate sales velocity
            if sales_90d > 0:
                sales_velocity = (sales_30d / (sales_90d / 3)) - 1  # vs average monthly
                self.think(f"→ Sales velocity: {sales_velocity:+.1%} vs 90d average", {
                    'velocity': sales_velocity
                })

                if sales_velocity > 0.20:
                    self.think("✓ Market is ACCELERATING")
                elif sales_velocity < -0.20:
                    self.think("⚠️ Market is DECELERATING")
                    self.send_alert(
                        'market_slowdown',
                        'medium',
                        f'Sales velocity down {abs(sales_velocity):.1%}',
                        {'velocity': sales_velocity}
                    )
                else:
                    self.think("✓ Market is STABLE")

            # Step 3: Distressed Properties Analysis
            self.think("Step 3: Analyzing distressed property indicators")
            self.cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM tax_deed_bidding_items WHERE item_status = 'active' OR item_status IS NULL) as active_tax_deeds,
                    (SELECT COUNT(*) FROM tax_certificates) as tax_certificates,
                    (SELECT COUNT(*) FROM active_tax_certificates) as active_certs
            """)
            distressed = self.cursor.fetchone()
            active_tax_deeds = distressed['active_tax_deeds'] if distressed else 0
            tax_certificates = distressed['tax_certificates'] if distressed else 0
            active_certs = distressed['active_certs'] if distressed else 0

            distress_ratio = (active_tax_deeds / total_properties * 100) if total_properties > 0 else 0

            self.think(f"Distressed indicators: {active_tax_deeds} tax deeds, {active_certs} active certificates", {
                'tax_deeds': active_tax_deeds,
                'certificates': tax_certificates,
                'distress_ratio': distress_ratio
            })

            if distress_ratio > 0.1:
                self.think(f"⚠️ Elevated distress ratio: {distress_ratio:.3f}%")

            # Step 4: Geographic Concentration
            self.think("Step 4: Analyzing geographic market concentration")
            self.cursor.execute("""
                SELECT county, COUNT(*) as property_count
                FROM florida_parcels
                GROUP BY county
                ORDER BY COUNT(*) DESC
                LIMIT 5;
            """)
            top_counties = self.cursor.fetchall()

            if top_counties:
                total_in_top = sum(c['property_count'] for c in top_counties)
                concentration = (total_in_top / total_properties * 100) if total_properties > 0 else 0

                top_list = [f"{c['county']} ({c['property_count']:,})" for c in top_counties]
                self.think(f"Top 5 counties: {', '.join(top_list[:3])}")
                self.think(f"→ Market concentration: {concentration:.1f}% in top 5 counties", {
                    'concentration': concentration
                })

            # Step 5: Value Distribution
            self.think("Step 5: Analyzing value distribution")
            self.cursor.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE just_value < 100000) as under_100k,
                    COUNT(*) FILTER (WHERE just_value >= 100000 AND just_value < 300000) as middle_100_300k,
                    COUNT(*) FILTER (WHERE just_value >= 300000 AND just_value < 500000) as middle_300_500k,
                    COUNT(*) FILTER (WHERE just_value >= 500000) as over_500k
                FROM florida_parcels
                WHERE just_value > 0;
            """)
            value_dist = self.cursor.fetchone()

            if value_dist:
                under_100k_pct = (value_dist['under_100k'] / total_properties * 100) if total_properties > 0 else 0
                over_500k_pct = (value_dist['over_500k'] / total_properties * 100) if total_properties > 0 else 0

                self.think(f"Value distribution: {under_100k_pct:.1f}% under $100K, {over_500k_pct:.1f}% over $500K", {
                    'under_100k_pct': under_100k_pct,
                    'over_500k_pct': over_500k_pct
                })

            # Step 6: Calculate Market Health Score
            self.think("Step 6: Calculating overall market health score")
            health_score = 50  # Start neutral

            # Positive factors
            if sales_30d > 1000:
                health_score += 15
            if avg_value > 200000:
                health_score += 10
            if sales_velocity > 0:
                health_score += 10

            # Negative factors
            if distress_ratio > 0.1:
                health_score -= 15
            if sales_velocity < -0.10:
                health_score -= 10

            health_score = max(0, min(100, health_score))  # Clamp 0-100

            self.think(f"Market health score: {health_score}/100")

            if health_score >= 75:
                market_condition = "STRONG"
            elif health_score >= 60:
                market_condition = "HEALTHY"
            elif health_score >= 40:
                market_condition = "MODERATE"
            else:
                market_condition = "WEAK"

            self.think(f"→ Overall market condition: {market_condition}")

            # Step 7: Generate Investment Opportunities
            self.think("Step 7: Identifying investment opportunities")

            opportunity_count = 0
            if distress_ratio > 0.05:
                opportunity_count += 1
                self.think("→ Distressed property opportunities available")

            if avg_price_30d > 0 and avg_price_30d < avg_value * 0.9:
                opportunity_count += 1
                self.think("→ Below-market sales detected")

            if sales_velocity > 0.15:
                opportunity_count += 1
                self.think("→ Rising market momentum")

            if opportunity_count == 0:
                self.think("No major investment opportunities detected")

            # Step 8: Final Assessment
            self.think("Step 8: Generating final market assessment")

            assessment = f"{total_properties:,} properties; {sales_30d:,} sales (30d); "
            assessment += f"health: {health_score}/100 ({market_condition}); "
            if sales_velocity:
                assessment += f"velocity: {sales_velocity:+.1%}; "
            assessment += f"{opportunity_count} opportunities"

            self.think(f"Conclusion: {assessment}")

            # Record metrics
            self.record_metric("market", "total_properties", total_properties)
            self.record_metric("market", "avg_property_value", avg_value)
            self.record_metric("market", "sales_30d", sales_30d)
            self.record_metric("market", "health_score", health_score)
            self.record_metric("market", "distress_ratio", distress_ratio)
            if sales_velocity:
                self.record_metric("market", "sales_velocity", sales_velocity)

            # Alert on weak market
            if health_score < 40:
                self.send_alert(
                    'weak_market',
                    'high',
                    f'Market health score is {health_score}/100',
                    {'health_score': health_score, 'condition': market_condition}
                )

            print("=" * 70)
            print(f"  ✅ Analysis complete - {self.thought_count} reasoning steps")
            print("=" * 70)

            return {
                'success': True,
                'health_score': health_score,
                'market_condition': market_condition,
                'sales_30d': sales_30d,
                'opportunity_count': opportunity_count,
                'assessment': assessment
            }

        except Exception as e:
            print(f"\n[ERROR] Analysis failed: {e}")
            self.think(f"ERROR during analysis: {e}")
            return {'success': False, 'error': str(e)}

    def run(self):
        """Main agent loop"""
        print("=" * 70)
        print("  📈 MARKET ANALYSIS AGENT (Chain-of-Thought)")
        print("=" * 70)
        print(f"\n  Agent ID: {self.agent_id}")
        print(f"  Analyzes: Overall market conditions")
        print(f"  Check Interval: {self.check_interval} seconds")
        print(f"  Reasoning Mode: Chain-of-Thought")

        print("\n  Connecting and registering...")
        self.connect()
        self.register()
        print("  ✅ Agent ready")
        print("\n  Press Ctrl+C to stop\n")

        iteration = 0
        last_heartbeat = time.time()

        try:
            while True:
                iteration += 1

                print("\n" + "=" * 70)
                print(f"  Iteration #{iteration}")
                print("=" * 70)

                # Run analysis
                result = self.analyze_market_conditions()

                # Send heartbeat every 30 seconds
                if time.time() - last_heartbeat >= 30:
                    self.heartbeat()
                    last_heartbeat = time.time()

                # Wait for next check
                print(f"\n  ⏳ Waiting {self.check_interval} seconds until next check...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\n  ⚠️  Agent stopped by user")
        finally:
            # Update status to offline
            self.cursor.execute("""
                UPDATE agent_registry
                SET status = 'offline', last_heartbeat = NOW()
                WHERE agent_id = %s;
            """, (self.agent_id,))

            self.cursor.close()
            self.conn.close()
            print("  ✅ Agent shut down cleanly")

if __name__ == "__main__":
    # Create and run agent
    agent = MarketAnalysisAgent(check_interval=600)  # Check every 10 minutes
    agent.run()
