#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Control Script - Start All Autonomous Agents
Starts the complete autonomous agent system with all specialized agents
"""

import os
import sys
import subprocess
import time
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def print_banner():
    print("=" * 80)
    print("  🤖 CONCORDBROKER AUTONOMOUS AGENT SYSTEM")
    print("  Master Control - Starting All Agents")
    print("=" * 80)
    print()

def print_agent_info():
    print("  Starting 10 Specialized Agents:")
    print()
    print("  1. 💻 Local Orchestrator")
    print("     - Coordinates all PC agents")
    print()
    print("  2. 🔍 Property Data Monitor (7-step CoT)")
    print("     - Monitors 10.3M properties")
    print()
    print("  3. 🏛️  Tax Deed Monitor (14-step CoT)")
    print("     - Tracks auctions and opportunities")
    print()
    print("  4. 📊 Sales Activity Tracker (13-step CoT)")
    print("     - Analyzes 633K sales")
    print()
    print("  5. 📈 Market Analysis (20-step CoT)")
    print("     - Market health scoring")
    print()
    print("  6. 🏠 Foreclosure Monitor (15-step CoT) ✨ NEW")
    print("     - Investment opportunities")
    print()
    print("  7. 🏗️  Permit Activity Tracker (12-step CoT) ✨ NEW")
    print("     - Development hotspots")
    print()
    print("  8. 🏢 Corporate Entity Monitor (18-step CoT) ✨ NEW")
    print("     - Entity ownership tracking")
    print()
    print("  9. 🧠 Pattern Analyzer (25+ step CoT + ML) ✨ NEW")
    print("     - Machine learning & auto-tuning")
    print()
    print("  10. 📈 Market Predictor (30-step CoT + Forecasting) ✨ NEW")
    print("      - Time-series predictions")
    print()
    print("=" * 80)
    print()
    print("  TOTAL: 154+ Chain-of-Thought steps per cycle!")
    print()
    print("=" * 80)
    print()

def start_agent(agent_name, script_path):
    """Start an agent in a new process"""
    print(f"  ▶️  Starting {agent_name}...")

    if sys.platform == 'win32':
        # Windows: start in new window
        process = subprocess.Popen(
            ['start', 'cmd', '/k', 'python', script_path],
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        # Unix: start in background
        process = subprocess.Popen(
            ['python', script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    time.sleep(2)  # Give agent time to start
    print(f"  ✅ {agent_name} started")
    return process

def main():
    print_banner()
    print_agent_info()

    print("  Starting agents...")
    print()

    agents = [
        ("Local Orchestrator", "local-agent-orchestrator/orchestrator_v2.py"),
        ("Property Data Monitor", "local-agent-orchestrator/property_data_agent.py"),
        ("Tax Deed Monitor", "local-agent-orchestrator/tax_deed_monitor_agent.py"),
        ("Sales Activity Tracker", "local-agent-orchestrator/sales_activity_agent.py"),
        ("Market Analysis Agent", "local-agent-orchestrator/market_analysis_agent.py"),
        ("Foreclosure Monitor", "local-agent-orchestrator/foreclosure_monitor_agent.py"),
        ("Permit Activity Tracker", "local-agent-orchestrator/permit_activity_agent.py"),
        ("Corporate Entity Monitor", "local-agent-orchestrator/entity_monitor_agent.py"),
        ("Pattern Analyzer", "local-agent-orchestrator/pattern_analyzer_agent.py"),
        ("Market Predictor", "local-agent-orchestrator/market_predictor_agent.py"),
    ]

    processes = []

    for agent_name, script_path in agents:
        try:
            process = start_agent(agent_name, script_path)
            processes.append((agent_name, process))
        except Exception as e:
            print(f"  ❌ Failed to start {agent_name}: {e}")

    print()
    print("=" * 80)
    print("  ✅ ALL AGENTS STARTED")
    print("=" * 80)
    print()
    print("  Agent Windows:")
    print("    - Each agent is running in its own console window")
    print("    - Close individual windows to stop specific agents")
    print("    - Or press Ctrl+C in each window")
    print()
    print("  Monitoring:")
    print("    - Check agent activity: python check_agent_activity.py")
    print("    - Watch real-time: python watch_agent_activity.py")
    print("    - Test system: python test_specialized_agents.py")
    print()
    print("  Documentation:")
    print("    - System overview: SPECIALIZED_AGENTS_COMPLETE.md")
    print("    - Quick start: START_HERE.md")
    print("    - Cloud deployment: RAILWAY_DEPLOYMENT_GUIDE.md")
    print()
    print("=" * 80)
    print()
    print(f"  🎉 Autonomous Agent System Operational - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("  Your agents are now:")
    print("    • Monitoring 10.3M properties + 15M entities")
    print("    • Analyzing 633K sales + foreclosures + permits")
    print("    • Tracking tax deeds + corporate ownership")
    print("    • Scoring market health + investment opportunities")
    print("    • Learning patterns + predicting trends")
    print("    • Auto-tuning performance + forecasting (7d/30d/90d)")
    print("    • Making 154+ transparent Chain-of-Thought decisions/cycle")
    print("    • Generating autonomous alerts + recommendations")
    print()
    print("  Press Enter to exit (agents will continue running)...")

    try:
        input()
    except KeyboardInterrupt:
        print("\n\n  Exiting master control (agents still running)")

    print()
    print("  Note: Agents are running in separate windows.")
    print("  They will continue running until you close their windows.")
    print()

if __name__ == "__main__":
    main()
