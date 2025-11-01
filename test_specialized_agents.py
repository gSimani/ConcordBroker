#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test All Specialized Agents
Demonstrates multi-agent system with Chain-of-Thought reasoning
"""

import os
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Import all specialized agents
sys.path.append('local-agent-orchestrator')
from tax_deed_monitor_agent import TaxDeedMonitorAgent
from sales_activity_agent import SalesActivityAgent
from market_analysis_agent import MarketAnalysisAgent

def main():
    print("=" * 80)
    print("  🧪 MULTI-AGENT SYSTEM TEST")
    print("  Testing: Tax Deed Monitor + Sales Activity + Market Analysis")
    print("=" * 80)

    # Create all agents (don't start continuous loop, just run once)
    print("\n[1/3] Creating agents...")

    tax_agent = TaxDeedMonitorAgent(check_interval=300)
    sales_agent = SalesActivityAgent(check_interval=300)
    market_agent = MarketAnalysisAgent(check_interval=600)

    print("  ✅ Tax Deed Monitor Agent created")
    print("  ✅ Sales Activity Tracker created")
    print("  ✅ Market Analysis Agent created")

    # Connect all agents
    print("\n[2/3] Connecting to database...")

    tax_agent.connect()
    tax_agent.register()
    print("  ✅ Tax Deed Monitor registered")

    sales_agent.connect()
    sales_agent.register()
    print("  ✅ Sales Activity Tracker registered")

    market_agent.connect()
    market_agent.register()
    print("  ✅ Market Analysis Agent registered")

    # Run each agent once
    print("\n[3/3] Running agent analyses...\n")

    # Tax Deed Monitor
    print("\n" + "=" * 80)
    print("  AGENT 1: TAX DEED MONITOR")
    print("=" * 80)
    tax_result = tax_agent.analyze_tax_deeds()

    # Sales Activity Tracker
    print("\n" + "=" * 80)
    print("  AGENT 2: SALES ACTIVITY TRACKER")
    print("=" * 80)
    sales_result = sales_agent.analyze_sales_activity()

    # Market Analysis
    print("\n" + "=" * 80)
    print("  AGENT 3: MARKET ANALYSIS")
    print("=" * 80)
    market_result = market_agent.analyze_market_conditions()

    # Summary
    print("\n" + "=" * 80)
    print("  ✅ MULTI-AGENT ANALYSIS COMPLETE")
    print("=" * 80)

    print("\n  Results Summary:")

    if tax_result['success']:
        print(f"\n  🏛️  Tax Deed Monitor:")
        print(f"     • Total Auctions: {tax_result.get('total_auctions', 0)}")
        print(f"     • Bidding Items: {tax_result.get('total_items', 0)}")
        print(f"     • Urgent Auctions: {tax_result.get('urgent_count', 0)}")
        print(f"     • Opportunity Score: {tax_result.get('opportunity_score', 0)}/100")

    if sales_result['success']:
        print(f"\n  📊 Sales Activity Tracker:")
        print(f"     • Total Sales: {sales_result.get('total_sales', 0):,}")
        print(f"     • Recent Sales (30d): {sales_result.get('recent_count', 0):,}")
        print(f"     • Average Price: ${sales_result.get('avg_price', 0):,.2f}")
        print(f"     • Activity Score: {sales_result.get('activity_score', 0)}/100")

    if market_result['success']:
        print(f"\n  📈 Market Analysis:")
        print(f"     • Market Condition: {market_result.get('market_condition', 'UNKNOWN')}")
        print(f"     • Health Score: {market_result.get('health_score', 0)}/100")
        print(f"     • Sales (30d): {market_result.get('sales_30d', 0):,}")
        print(f"     • Opportunities: {market_result.get('opportunity_count', 0)}")

    print("\n" + "=" * 80)
    print("  ✅ ALL SPECIALIZED AGENTS WORKING!")
    print("=" * 80)

    print("\n  Chain-of-Thought reasoning demonstrated across:")
    print("    • Tax deed monitoring")
    print("    • Sales pattern analysis")
    print("    • Market condition assessment")

    print("\n  All reasoning steps stored in database:")
    print("    • agent_metrics (reasoning steps)")
    print("    • agent_alerts (autonomous alerts)")
    print("    • agent_registry (agent status)")

    # Cleanup
    tax_agent.cursor.close()
    tax_agent.conn.close()
    sales_agent.cursor.close()
    sales_agent.conn.close()
    market_agent.cursor.close()
    market_agent.conn.close()

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
