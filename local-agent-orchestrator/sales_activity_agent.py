#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sales Activity Tracker Agent with Chain-of-Thought Reasoning
Monitors property sales patterns and detects market trends
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

class SalesActivityAgent:
    def __init__(self, check_interval=300):  # 5 minutes
        self.agent_id = f"sales-activity-{socket.gethostname()}"
        self.agent_name = "Sales Activity Tracker (CoT)"
        self.agent_type = "monitoring"
        self.environment = "pc"
        self.capabilities = ["sales_monitoring", "trend_detection", "chain_of_thought"]

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

    def analyze_sales_activity(self):
        """Analyze property sales with Chain-of-Thought reasoning"""
        self.analysis_count += 1
        self.thought_count = 0

        print("\n" + "=" * 70)
        print(f"  🔍 SALES ACTIVITY ANALYSIS - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 70)

        try:
            # Step 1: Count total sales
            self.think("Step 1: Counting total property sales")
            self.cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(sale_price) as total_volume
                FROM property_sales_history
                WHERE sale_price IS NOT NULL AND sale_price > 0;
            """)
            sales_data = self.cursor.fetchone()
            total_sales = sales_data['total'] if sales_data else 0
            total_volume = float(sales_data['total_volume']) if sales_data and sales_data['total_volume'] else 0

            self.think(f"Found {total_sales:,} total sales", {
                'total': total_sales,
                'total_volume': total_volume
            })

            # Step 2: Analyze recent sales (last 30 days)
            self.think("Step 2: Analyzing recent sales activity (last 30 days)")
            self.cursor.execute("""
                SELECT COUNT(*) as recent_count,
                       AVG(sale_price) as avg_price,
                       SUM(sale_price) as recent_volume
                FROM property_sales_history
                WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days'
                AND sale_price IS NOT NULL AND sale_price > 0;
            """)
            recent_data = self.cursor.fetchone()
            recent_count = recent_data['recent_count'] if recent_data else 0
            avg_price = float(recent_data['avg_price']) if recent_data and recent_data['avg_price'] else 0
            recent_volume = float(recent_data['recent_volume']) if recent_data and recent_data['recent_volume'] else 0

            self.think(f"Recent sales: {recent_count:,} in last 30 days", {
                'recent_count': recent_count,
                'avg_price': avg_price,
                'recent_volume': recent_volume
            })

            if recent_count > 0:
                self.think(f"→ Average sale price: ${avg_price:,.2f}")
                self.think(f"→ Total volume: ${recent_volume:,.2f}")

            # Step 3: Analyze by county
            self.think("Step 3: Analyzing sales by county")
            self.cursor.execute("""
                SELECT county, COUNT(*) as count,
                       AVG(sale_price) as avg_price
                FROM property_sales_history
                WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days'
                AND sale_price IS NOT NULL AND sale_price > 0
                GROUP BY county
                ORDER BY count DESC
                LIMIT 5;
            """)
            county_sales = self.cursor.fetchall()

            if county_sales:
                counties = []
                for row in county_sales:
                    avg = float(row['avg_price']) if row['avg_price'] else 0
                    counties.append(f"{row['county']} ({row['count']:,} sales, avg ${avg:,.0f})")

                self.think(f"Top counties: {', '.join(counties[:3])}")

            # Step 4: Detect hot markets (high activity)
            self.think("Step 4: Detecting hot markets")
            self.cursor.execute("""
                SELECT county,
                       COUNT(*) as sales_30d,
                       AVG(sale_price) as avg_price_30d
                FROM property_sales_history
                WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days'
                AND sale_price IS NOT NULL AND sale_price > 0
                GROUP BY county
                HAVING COUNT(*) > 100
                ORDER BY COUNT(*) DESC
                LIMIT 5;
            """)
            hot_markets = self.cursor.fetchall()

            if hot_markets:
                self.think(f"Found {len(hot_markets)} hot markets (>100 sales in 30d)")
                for market in hot_markets[:3]:
                    avg = float(market['avg_price_30d']) if market['avg_price_30d'] else 0
                    self.think(f"→ {market['county']}: {market['sales_30d']:,} sales, avg ${avg:,.0f}")

                # Alert on hot markets
                self.send_alert(
                    'hot_market',
                    'medium',
                    f'{len(hot_markets)} counties with >100 sales in 30 days',
                    {'hot_markets': [m['county'] for m in hot_markets]}
                )
            else:
                self.think("No hot markets detected")

            # Step 5: Analyze price trends
            self.think("Step 5: Analyzing price trends")
            self.cursor.execute("""
                SELECT
                    AVG(CASE WHEN sale_date >= CURRENT_DATE - INTERVAL '30 days'
                             THEN sale_price END) as avg_30d,
                    AVG(CASE WHEN sale_date >= CURRENT_DATE - INTERVAL '60 days'
                             AND sale_date < CURRENT_DATE - INTERVAL '30 days'
                             THEN sale_price END) as avg_60d
                FROM property_sales_history
                WHERE sale_price IS NOT NULL AND sale_price > 0;
            """)
            trend_data = self.cursor.fetchone()
            avg_30d = float(trend_data['avg_30d']) if trend_data and trend_data['avg_30d'] else 0
            avg_60d = float(trend_data['avg_60d']) if trend_data and trend_data['avg_60d'] else 0

            if avg_30d > 0 and avg_60d > 0:
                price_change = ((avg_30d - avg_60d) / avg_60d) * 100
                self.think(f"Price trend: {price_change:+.1f}% vs previous 30 days", {
                    'avg_30d': avg_30d,
                    'avg_60d': avg_60d,
                    'change_pct': price_change
                })

                if abs(price_change) > 10:
                    self.think(f"⚠️ SIGNIFICANT price movement detected: {price_change:+.1f}%")
                    self.send_alert(
                        'price_movement',
                        'high' if abs(price_change) > 20 else 'medium',
                        f'Sales prices {"increased" if price_change > 0 else "decreased"} {abs(price_change):.1f}%',
                        {'change_pct': price_change}
                    )
            else:
                self.think("Insufficient data for price trend analysis")

            # Step 6: Calculate activity score
            self.think("Step 6: Calculating market activity score")
            activity_score = 0

            if recent_count > 1000:
                activity_score += 30
            elif recent_count > 500:
                activity_score += 20
            elif recent_count > 100:
                activity_score += 10

            if hot_markets:
                activity_score += 40

            if avg_price > 200000:
                activity_score += 30

            self.think(f"Market activity score: {activity_score}/100")

            # Step 7: Generate final assessment
            self.think("Step 7: Generating final assessment")

            assessment = f"{total_sales:,} total sales; {recent_count:,} in last 30d; "
            if avg_price > 0:
                assessment += f"avg price ${avg_price:,.0f}; "
            if hot_markets:
                assessment += f"{len(hot_markets)} hot markets; "
            assessment += f"activity score: {activity_score}/100"

            self.think(f"Conclusion: {assessment}")

            # Record metrics
            self.record_metric("sales", "total_sales", total_sales)
            self.record_metric("sales", "recent_sales_30d", recent_count)
            self.record_metric("sales", "avg_sale_price", avg_price)
            self.record_metric("sales", "activity_score", activity_score)
            if avg_price > 0 and avg_60d > 0:
                self.record_metric("sales", "price_change_pct", price_change)

            print("=" * 70)
            print(f"  ✅ Analysis complete - {self.thought_count} reasoning steps")
            print("=" * 70)

            return {
                'success': True,
                'total_sales': total_sales,
                'recent_count': recent_count,
                'avg_price': avg_price,
                'activity_score': activity_score,
                'assessment': assessment
            }

        except Exception as e:
            print(f"\n[ERROR] Analysis failed: {e}")
            self.think(f"ERROR during analysis: {e}")
            return {'success': False, 'error': str(e)}

    def run(self):
        """Main agent loop"""
        print("=" * 70)
        print("  📊 SALES ACTIVITY TRACKER AGENT (Chain-of-Thought)")
        print("=" * 70)
        print(f"\n  Agent ID: {self.agent_id}")
        print(f"  Monitors: property_sales_history")
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
                result = self.analyze_sales_activity()

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
    agent = SalesActivityAgent(check_interval=300)  # Check every 5 minutes
    agent.run()
