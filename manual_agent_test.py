#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manual Agent Test - Run PropertyDataAgent Once
Shows Chain-of-Thought reasoning in action
"""

import os
import sys
from pathlib import Path

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "local-agent-orchestrator"))

from dotenv import load_dotenv
load_dotenv('.env.mcp')

# Import the agent directly
from property_data_agent import PropertyDataAgent

def main():
    print("\n" + "=" * 80)
    print("  🧪 MANUAL AGENT TEST: Chain-of-Thought Demonstration")
    print("=" * 80)

    print("\n  Creating PropertyDataAgent...")
    agent = PropertyDataAgent()

    print("  Connecting to database...")
    if not agent.connect():
        print("  ❌ Connection failed")
        return

    print("  ✅ Connected")

    print("\n  Running single analysis with Chain-of-Thought reasoning...")
    print("  Watch for 💭 symbols - each one is a reasoning step\n")

    # Run one analysis
    result = agent.analyze_property_data()

    if result:
        print("\n" + "=" * 80)
        print("  ✅ ANALYSIS COMPLETE")
        print("=" * 80)

        print(f"\n  Final Assessment:")
        print(f"    • Total Properties: {result['total_properties']:,}")
        print(f"    • Data Freshness: {result['data_freshness_days']} days")
        print(f"    • Quality Score: {result['quality_score']:.1f}/100")
        print(f"    • Quality Issues: {', '.join(result['quality_issues']) if result['quality_issues'] else 'None'}")
        print(f"    • Recent Additions: {result['recent_additions']:,}")
        print(f"    • Average Value: ${result['average_value']:,.2f}")
        print(f"\n  Conclusion: {result['conclusion']}")

        print("\n" + "=" * 80)
        print("  📊 CHAIN-OF-THOUGHT SUMMARY")
        print("=" * 80)

        print(f"\n  The agent made {len(agent.thought_process)} reasoning steps:")
        for i, thought in enumerate(agent.thought_process[:10], 1):  # Show first 10
            print(f"    {i}. {thought['thought']}")

        if len(agent.thought_process) > 10:
            print(f"    ... and {len(agent.thought_process) - 10} more steps")

    else:
        print("\n  ❌ Analysis failed")

    # Clean up
    agent.conn.close()

    print("\n" + "=" * 80)
    print("  🎉 DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\n  This shows:")
    print("    ✅ Chain-of-Thought reasoning (transparent AI)")
    print("    ✅ PropertyDataAgent analyzing 9.7M properties")
    print("    ✅ Data quality assessment")
    print("    ✅ Autonomous decision-making")
    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()
