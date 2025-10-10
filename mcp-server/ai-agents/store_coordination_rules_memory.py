#!/usr/bin/env python3
"""
Store Work Coordination Rules in Permanent AI Agent Memory

This script stores critical project coordination rules in the AI Agent Memory System
so that all future Claude Code sessions can access them.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_memory_system import AgentMemorySystem
from datetime import datetime

def store_coordination_rules():
    """Store all critical coordination rules in permanent memory"""

    memory = AgentMemorySystem(
        agent_id="concordbroker_system",
        task_context="work_coordination"
    )

    print("🧠 Storing Work Coordination Rules in Permanent Memory\n")

    # Rule 1: Single UI Architecture
    memory.store_long_term_knowledge(
        category="project_architecture",
        key="single_ui_rule",
        value={
            "rule": "ONE UI Website - ONE Port - ONE Branch",
            "ui_location": "apps/web/",
            "dev_port": 5191,
            "production_url": "https://www.concordbroker.com",
            "branch": "feature/ui-consolidation-unified",
            "enforcement": "Run 'npm run port:clean' at start of EVERY session",
            "violations": {
                "multiple_frontends": "FORBIDDEN - Never create apps/web2/, apps/new-ui/, etc.",
                "wrong_port": "FORBIDDEN - Any port other than 5191 is WRONG",
                "zombie_ports": "MUST KILL - Ports 5177-5180 are zombies"
            }
        }
    )
    print("✅ Stored: Single UI Architecture Rule")

    # Rule 2: Continuous Merge Policy
    memory.store_long_term_knowledge(
        category="git_workflow",
        key="continuous_merge_policy",
        value={
            "rule": "Commit immediately after EVERY feature",
            "workflow": [
                "git add <files>",
                "git commit -m 'descriptive message'",
                "git push origin <branch>"
            ],
            "frequency": "After EVERY feature/fix, no matter how small",
            "never": [
                "Never wait to commit multiple features at once",
                "Never have uncommitted changes at end of session",
                "Never skip pushing commits"
            ],
            "why": "Git is single source of truth - prevents duplicate work and work loss"
        }
    )
    print("✅ Stored: Continuous Merge Policy")

    # Rule 3: Session Start Protocol
    memory.store_long_term_knowledge(
        category="session_management",
        key="session_start_protocol",
        value={
            "rule": "Pull before starting ANY work",
            "mandatory_steps": [
                "git pull --rebase",
                "npm run port:clean",
                "npm run dev",
                "Open browser: http://localhost:5191"
            ],
            "checklist": {
                "read_session_lock": ".dev-session.json",
                "verify_port": "Should be 5191",
                "check_zombies": "Should be empty array",
                "verify_uncommitted": "Should be false"
            }
        }
    )
    print("✅ Stored: Session Start Protocol")

    # Rule 4: Work Verification Protocol
    memory.store_long_term_knowledge(
        category="session_management",
        key="work_verification_protocol",
        value={
            "rule": "Verify work complete before ending session",
            "command": "npm run verify:complete",
            "must_pass_checks": [
                "All changes committed to git",
                "All commits pushed to remote",
                "No zombie dev servers running",
                "Tests use standard port (5191)",
                "Session lock file exists",
                "Working on correct branch"
            ],
            "when_to_run": [
                "Before ending work session",
                "Before marking task 'complete'",
                "Daily standup check"
            ]
        }
    )
    print("✅ Stored: Work Verification Protocol")

    # Critical File Locations
    memory.store_long_term_knowledge(
        category="project_structure",
        key="critical_files",
        value={
            "frontend": {
                "main_search": "apps/web/src/pages/properties/PropertySearch.tsx",
                "property_detail": "apps/web/src/pages/property/EnhancedPropertyProfile.tsx",
                "mini_card": "apps/web/src/components/property/MiniPropertyCard.tsx",
                "search_bar": "apps/web/src/components/OptimizedSearchBar.tsx",
                "vite_config": "apps/web/vite.config.ts"
            },
            "backend": {
                "api": "apps/api/property_live_api.py",
                "mcp_server": "mcp-server/server.js"
            },
            "coordination": {
                "port_manager": "scripts/ensure-single-dev-server.cjs",
                "work_verifier": "scripts/verify-work-completion.cjs",
                "session_lock": ".dev-session.json"
            },
            "permanent_memory": "PERMANENT_MEMORY_COORDINATION_RULES.md"
        }
    )
    print("✅ Stored: Critical File Locations")

    # Database Information
    memory.store_long_term_knowledge(
        category="database",
        key="supabase_schema",
        value={
            "provider": "Supabase",
            "main_table": "florida_parcels",
            "total_properties": 9113150,
            "counties": 67,
            "critical_columns": [
                "parcel_id",
                "county",
                "owner_name",
                "phy_addr1",
                "phy_city",
                "just_value",
                "property_use",
                "year_built"
            ],
            "removed_columns": ["dor_uc", "property_use_code"],
            "note": "Column dor_uc does NOT exist - was removed in commit a7d2e54"
        }
    )
    print("✅ Stored: Database Schema Information")

    # Port Registry
    memory.store_long_term_knowledge(
        category="infrastructure",
        key="port_registry",
        value={
            "standard_dev_port": 5191,
            "zombie_ports_to_kill": [5177, 5178, 5179, 5180],
            "active_services": {
                "3001": "MCP Server (Primary)",
                "3005": "MCP Server (Ultimate)",
                "5191": "Dev Server (STANDARD)",
                "8000": "FastAPI Backend",
                "8001": "AI Data Flow Orchestrator (optional)",
                "8003": "LangChain Integration (optional)"
            },
            "enforcement": "Run 'npm run port:clean' to kill zombies"
        }
    )
    print("✅ Stored: Port Registry")

    # Common Mistakes and Solutions
    memory.store_long_term_knowledge(
        category="troubleshooting",
        key="common_mistakes",
        value={
            "multiple_dev_servers": {
                "problem": "Running npm run dev in multiple terminals",
                "solution": "Always run npm run port:clean first"
            },
            "uncommitted_work": {
                "problem": "Forgetting to commit at end of day",
                "solution": "Run npm run verify:complete - it will FAIL"
            },
            "working_on_old_code": {
                "problem": "Not pulling latest before starting",
                "solution": "ALWAYS git pull --rebase at session start"
            },
            "testing_wrong_port": {
                "problem": "Test files reference localhost:5177, 5178",
                "solution": "npm run verify:complete detects this"
            },
            "creating_new_frontend": {
                "problem": "Someone creates apps/web2/ or apps/new-ui/",
                "solution": "FORBIDDEN - There is ONLY ONE UI: apps/web/"
            }
        }
    )
    print("✅ Stored: Common Mistakes and Solutions")

    # Golden Rules
    memory.store_long_term_knowledge(
        category="principles",
        key="golden_rules",
        value={
            "rule_1": "If it's not committed and pushed to git, it doesn't exist",
            "rule_2": "If there's a zombie port, kill it",
            "rule_3": "If it's not on port 5191, it's wrong",
            "rule_4": "There is ONE UI website, not multiple",
            "rule_5": "Work merges continuously through immediate commits",
            "rule_6": "Always pull before starting work",
            "rule_7": "Always verify before ending session"
        }
    )
    print("✅ Stored: Golden Rules")

    # Critical Commands
    memory.store_long_term_knowledge(
        category="commands",
        key="critical_npm_scripts",
        value={
            "port_clean": {
                "command": "npm run port:clean",
                "purpose": "Kill zombie ports, show status",
                "when": "Start of every session"
            },
            "dev_clean": {
                "command": "npm run dev:clean",
                "purpose": "Kill zombies + start dev server",
                "when": "Starting fresh development"
            },
            "verify_complete": {
                "command": "npm run verify:complete",
                "purpose": "Verify work is saved and merged",
                "when": "End of session or before marking complete"
            },
            "port_check": {
                "command": "npm run port:check",
                "purpose": "Check port status without killing",
                "when": "Debugging port issues"
            }
        }
    )
    print("✅ Stored: Critical NPM Commands")

    # Recent Session History
    memory.add_to_session_history(
        event_type="coordination_system_implemented",
        details={
            "date": "2025-10-10",
            "commits": [
                "fc8fff1 - Port management & coordination system",
                "e124f36 - Enable all 9.1M Florida properties",
                "a7d2e54 - Fix dor_uc column error",
                "13165bb - Enable autocomplete search"
            ],
            "zombies_killed": 4,
            "zombie_ports": [5177, 5178, 5179, 5180],
            "standard_port_established": 5191,
            "scripts_created": [
                "scripts/ensure-single-dev-server.cjs",
                "scripts/verify-work-completion.cjs"
            ]
        }
    )
    print("✅ Stored: Recent Session History")

    # Store permanent reminder
    memory.store_long_term_knowledge(
        category="system",
        key="permanent_reminder",
        value={
            "message": "ConcordBroker has ONE UI website at apps/web/ running on port 5191. All work merges continuously through immediate git commits. Every session starts with 'git pull && npm run port:clean && npm run dev'. Every session ends with 'npm run verify:complete'. There are NO other frontends. There are NO other development ports. Zombie ports (5177-5180) are killed automatically.",
            "read_on_every_session": True,
            "importance": "CRITICAL",
            "documentation": "PERMANENT_MEMORY_COORDINATION_RULES.md"
        }
    )
    print("✅ Stored: Permanent Reminder\n")

    # Retrieve and display stored knowledge
    print("=" * 70)
    print("VERIFICATION: Retrieving Stored Knowledge")
    print("=" * 70 + "\n")

    single_ui = memory.retrieve_knowledge("project_architecture", "single_ui_rule")
    print(f"📋 Single UI Rule: Port {single_ui['dev_port']} → {single_ui['ui_location']}")

    merge_policy = memory.retrieve_knowledge("git_workflow", "continuous_merge_policy")
    print(f"📋 Merge Policy: {merge_policy['rule']}")

    golden_rules = memory.retrieve_knowledge("principles", "golden_rules")
    print(f"📋 Golden Rule #1: {golden_rules['rule_1']}")

    reminder = memory.retrieve_knowledge("system", "permanent_reminder")
    print(f"📋 Permanent Reminder Stored: {reminder['read_on_every_session']}")

    print("\n" + "=" * 70)
    print("✅ ALL COORDINATION RULES STORED IN PERMANENT MEMORY")
    print("=" * 70)
    print("\nLocation: AI Agent Memory System (Supabase)")
    print("Access: memory.retrieve_knowledge(category, key)")
    print("Persistence: PERMANENT - Survives all sessions")
    print("\nFuture sessions will automatically load these rules.")

    return True

if __name__ == "__main__":
    try:
        store_coordination_rules()
        print("\n✅ SUCCESS: Coordination rules stored in permanent memory")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
