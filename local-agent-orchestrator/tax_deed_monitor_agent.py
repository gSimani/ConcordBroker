#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tax Deed Monitor Agent with Chain-of-Thought Reasoning
Monitors tax deed auctions and identifies high-value opportunities
"""

import os
import sys
import json
import time
import socket
from datetime import datetime
from typing import Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv('.env.mcp')

import psycopg2
import psycopg2.extras

class TaxDeedMonitorAgent:
    def __init__(self, check_interval=300):  # 5 minutes
        self.agent_id = f"tax-deed-monitor-{socket.gethostname()}"
        self.agent_name = "Tax Deed Monitor (CoT)"
        self.agent_type = "monitoring"
        self.environment = "pc"
        self.capabilities = ["tax_monitoring", "opportunity_detection", "chain_of_thought"]

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

    def analyze_tax_deeds(self):
        """Analyze tax deed auctions with Chain-of-Thought reasoning"""
        self.analysis_count += 1
        self.thought_count = 0

        print("\n" + "=" * 70)
        print(f"  🔍 TAX DEED ANALYSIS - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 70)

        try:
            # Step 1: Count total tax deed auctions
            self.think("Step 1: Counting active tax deed auctions")
            self.cursor.execute("""
                SELECT COUNT(*) as total
                FROM tax_deed_auctions
                WHERE status = 'upcoming' OR status = 'active';
            """)
            auction_data = self.cursor.fetchone()
            total_auctions = auction_data['total'] if auction_data else 0

            self.think(f"Found {total_auctions:,} active/upcoming auctions", {'total': total_auctions})

            # Step 2: Count bidding items
            self.think("Step 2: Counting tax deed bidding items")
            self.cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(opening_bid) as total_opening_bid
                FROM tax_deed_bidding_items
                WHERE item_status = 'active' OR item_status IS NULL;
            """)
            items_data = self.cursor.fetchone()
            total_items = items_data['total'] if items_data else 0
            total_opening_bid = float(items_data['total_opening_bid']) if items_data and items_data['total_opening_bid'] else 0

            self.think(f"Found {total_items:,} bidding items", {
                'total_items': total_items,
                'total_opening_bid': total_opening_bid
            })

            # Step 3: Analyze high-value opportunities
            self.think("Step 3: Identifying high-value opportunities")
            self.cursor.execute("""
                SELECT parcel_id, tax_certificate_number as certificate_number,
                       opening_bid, assessed_value, close_time as sale_date,
                       'UNKNOWN' as county
                FROM tax_deed_bidding_items
                WHERE (item_status = 'active' OR item_status IS NULL)
                AND opening_bid > 10000
                ORDER BY opening_bid DESC
                LIMIT 10;
            """)
            high_value_items = self.cursor.fetchall()

            if high_value_items:
                self.think(f"Found {len(high_value_items)} high-value opportunities (>$10K opening bid)")

                for item in high_value_items[:3]:  # Show top 3
                    opening_bid = float(item['opening_bid']) if item['opening_bid'] else 0
                    self.think(
                        f"→ {item['county']} - {item['parcel_id']}: ${opening_bid:,.2f}",
                        {
                            'parcel': item['parcel_id'],
                            'bid': opening_bid,
                            'county': item['county']
                        }
                    )
            else:
                self.think("No high-value opportunities currently")

            # Step 4: Check for urgent auctions (within 7 days)
            self.think("Step 4: Checking for urgent upcoming auctions")
            self.cursor.execute("""
                SELECT COUNT(*) as urgent_count
                FROM tax_deed_bidding_items
                WHERE (item_status = 'active' OR item_status IS NULL)
                AND close_time::date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days';
            """)
            urgent_data = self.cursor.fetchone()
            urgent_count = urgent_data['urgent_count'] if urgent_data else 0

            if urgent_count > 0:
                self.think(f"⚠️ URGENT: {urgent_count} auctions in next 7 days")
                self.send_alert(
                    'urgent_auction',
                    'high',
                    f'{urgent_count} tax deed auctions happening within 7 days',
                    {'urgent_count': urgent_count}
                )
            else:
                self.think("✓ No urgent auctions in next 7 days")

            # Step 5: Analyze by status
            self.think("Step 5: Analyzing distribution by status")
            self.cursor.execute("""
                SELECT item_status, COUNT(*) as count,
                       SUM(opening_bid) as total_bids
                FROM tax_deed_bidding_items
                WHERE item_status IS NOT NULL
                GROUP BY item_status
                ORDER BY count DESC
                LIMIT 5;
            """)
            status_stats = self.cursor.fetchall()

            if status_stats:
                statuses = [f"{row['item_status']} ({row['count']})" for row in status_stats]
                self.think(f"Item statuses: {', '.join(statuses)}")

            # Step 6: Calculate opportunity score
            self.think("Step 6: Calculating opportunity score")
            opportunity_score = 0

            if total_items > 0:
                opportunity_score += 30
            if urgent_count > 0:
                opportunity_score += 40
            if high_value_items:
                opportunity_score += 30

            self.think(f"Opportunity score: {opportunity_score}/100")

            # Step 7: Generate final assessment
            self.think("Step 7: Generating final assessment")

            assessment = f"{total_auctions} auctions; {total_items} items; "
            if urgent_count > 0:
                assessment += f"URGENT: {urgent_count} within 7 days; "
            if high_value_items:
                assessment += f"{len(high_value_items)} high-value opportunities; "
            assessment += f"score: {opportunity_score}/100"

            self.think(f"Conclusion: {assessment}")

            # Record metrics
            self.record_metric("tax_deeds", "total_auctions", total_auctions)
            self.record_metric("tax_deeds", "total_items", total_items)
            self.record_metric("tax_deeds", "urgent_count", urgent_count)
            self.record_metric("tax_deeds", "opportunity_score", opportunity_score)
            self.record_metric("tax_deeds", "total_opening_bid", total_opening_bid)

            print("=" * 70)
            print(f"  ✅ Analysis complete - {self.thought_count} reasoning steps")
            print("=" * 70)

            return {
                'success': True,
                'total_auctions': total_auctions,
                'total_items': total_items,
                'urgent_count': urgent_count,
                'opportunity_score': opportunity_score,
                'assessment': assessment
            }

        except Exception as e:
            print(f"\n[ERROR] Analysis failed: {e}")
            self.think(f"ERROR during analysis: {e}")
            return {'success': False, 'error': str(e)}

    def run(self):
        """Main agent loop"""
        print("=" * 70)
        print("  🏛️ TAX DEED MONITOR AGENT (Chain-of-Thought)")
        print("=" * 70)
        print(f"\n  Agent ID: {self.agent_id}")
        print(f"  Monitors: tax_deed_auctions, tax_deed_bidding_items")
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
                result = self.analyze_tax_deeds()

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
    agent = TaxDeedMonitorAgent(check_interval=300)  # Check every 5 minutes
    agent.run()
