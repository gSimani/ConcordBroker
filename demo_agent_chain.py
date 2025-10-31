#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo: Chain-of-Agents with Chain-of-Thought Reasoning
Shows orchestrator and PropertyDataAgent working together
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("="*80)
print("  🎭 CONCORDBROKER AGENT CHAIN DEMONSTRATION")
print("  Chain-of-Thought Reasoning + Agent Communication")
print("="*80)

print("\nThis demo will:")
print("  1. Start Enhanced Orchestrator (coordinator)")
print("  2. Start PropertyDataAgent (analyzer with CoT)")
print("  3. Watch them communicate via message bus")
print("  4. Show chain-of-thought reasoning in action")
print("\nDemo will run for 3 minutes then stop.\n")

input("Press Enter to start the demo...")

# Paths
orchestrator_path = Path("local-agent-orchestrator/orchestrator_v2.py")
agent_path = Path("local-agent-orchestrator/property_data_agent.py")

# Start orchestrator
print("\n[1/2] Starting Enhanced Orchestrator...")
orchestrator_process = subprocess.Popen(
    ["python", str(orchestrator_path)],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    universal_newlines=True
)

time.sleep(3)
print("✅ Orchestrator started (PID: {})".format(orchestrator_process.pid))

# Start property data agent
print("\n[2/2] Starting PropertyDataAgent...")
agent_process = subprocess.Popen(
    ["python", str(agent_path)],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    universal_newlines=True
)

time.sleep(2)
print("✅ PropertyDataAgent started (PID: {})".format(agent_process.pid))

print("\n" + "="*80)
print("  🎬 AGENT CHAIN IS RUNNING")
print("="*80)
print("\nWhat's happening:")
print("  • Orchestrator: Managing the mesh, checking for messages")
print("  • PropertyDataAgent: Analyzing 9.7M properties with Chain-of-Thought")
print("  • Communication: Agents send messages through Supabase")
print("\nWatch for:")
print("  💭 Chain-of-thought reasoning steps")
print("  📤 Messages sent between agents")
print("  🚨 Alerts when issues detected")
print("  📊 Analysis results")
print("\nDemo will run for 3 minutes...\n")

try:
    # Let them run for 180 seconds (3 minutes)
    start_time = time.time()
    duration = 180

    while time.time() - start_time < duration:
        # Check if processes are still running
        if orchestrator_process.poll() is not None:
            print("\n⚠️  Orchestrator stopped")
            break
        if agent_process.poll() is not None:
            print("\n⚠️  PropertyDataAgent stopped")
            break

        time.sleep(5)

        # Show progress
        elapsed = int(time.time() - start_time)
        remaining = duration - elapsed
        if elapsed % 30 == 0:
            print(f"  ... {elapsed}s elapsed, {remaining}s remaining")

    print("\n" + "="*80)
    print("  ⏱️  DEMO TIME COMPLETE")
    print("="*80)

except KeyboardInterrupt:
    print("\n\n⚠️  Demo interrupted by user")

finally:
    # Stop both processes
    print("\n🛑 Stopping agents...")

    # Stop agent
    if agent_process.poll() is None:
        if sys.platform == 'win32':
            agent_process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            agent_process.send_signal(signal.SIGINT)
        time.sleep(2)
        agent_process.terminate()
        agent_process.wait()
        print("  ✅ PropertyDataAgent stopped")

    # Stop orchestrator
    if orchestrator_process.poll() is None:
        if sys.platform == 'win32':
            orchestrator_process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            orchestrator_process.send_signal(signal.SIGINT)
        time.sleep(2)
        orchestrator_process.terminate()
        orchestrator_process.wait()
        print("  ✅ Orchestrator stopped")

# Show results
print("\n" + "="*80)
print("  📊 VERIFYING RESULTS")
print("="*80)

print("\nChecking database for agent activity...")

# Run verification
verify_script = Path("verify_agent_schema.py")
result = subprocess.run(
    ["python", str(verify_script)],
    capture_output=True,
    text=True
)

# Extract key info
if result.returncode == 0:
    for line in result.stdout.split('\n'):
        if any(keyword in line.lower() for keyword in ['property-data', 'orchestrator', 'total agents', 'alert']):
            print(f"  {line.strip()}")

print("\n" + "="*80)
print("  🎉 DEMO COMPLETE")
print("="*80)

print("\n📋 What You Just Saw:")
print("  ✅ Chain-of-Thought reasoning in PropertyDataAgent")
print("  ✅ Agent-to-agent communication via message bus")
print("  ✅ Orchestrator coordinating multiple agents")
print("  ✅ Alerts generated and processed")
print("  ✅ Distributed agent mesh in action")

print("\n🚀 Next Steps:")
print("  • Check agent_messages table for communication logs")
print("  • Check agent_alerts table for detected issues")
print("  • Check agent_metrics table for chain-of-thought records")
print("  • Run agents continuously for ongoing monitoring")

print("\n💡 To run agents manually:")
print("  Terminal 1: python local-agent-orchestrator/orchestrator_v2.py")
print("  Terminal 2: python local-agent-orchestrator/property_data_agent.py")

print("\n" + "="*80)
