# 🧠 Project Memory System

This directory contains checkpoint snapshots and context information managed by The Historian sub-agent.

## Directory Structure

- **checkpoints/** - Significant milestone snapshots
- **sessions/** - Session-specific context and state
- **timeline/** - Chronological activity timeline
- **index/** - Search indexes for quick context retrieval
- **compressed/** - Compressed archives of old snapshots

## Snapshot Format

All snapshots are stored as LLM-readable Markdown files with:
- Timestamp and session ID
- Context summary
- Key decisions made
- Code changes overview
- Dependencies and integrations
- Next steps and TODOs
- Links to related snapshots

## Usage

These files provide context continuity across Claude Code sessions. They help:
- Resume work after interruptions
- Understand historical decisions
- Track project evolution
- Provide context for new team members
- Debug issues by reviewing past states

**Managed by**: The Historian Sub-Agent (Port 3012)
**Auto-updated**: Yes (every 5 minutes or on significant events)
**Format**: Markdown (optimized for LLM parsing)

---

## 🔒 Permanent Memory Documents

These documents contain PERMANENT rules and systems that must NEVER be forgotten:

### System Architecture & Testing
- **`AI_AGENT_TESTING_MANDATE.md`** 🔴 CRITICAL
  - PERMANENT rule: AI agents handle ALL testing
  - NEVER ask users to manually test
  - Verification protocol for all code changes
  - Enforcement: AUTOMATIC

- **`SUPABASE_REQUEST_PROTOCOL.md`** 🔴 CRITICAL
  - PERMANENT rule: All Supabase changes use structured requests
  - ALWAYS use title: "🗄️ GUY WE NEED YOUR HELP WITH SUPABASE"
  - ALWAYS provide JSON prompt (copy-paste ready)
  - ALWAYS rate response (1-10), iterate until 10/10
  - ALWAYS congratulate + joke at 10/10
  - Enforcement: MANDATORY

### Data Systems
- **`property-updates-permanent.md`**
  - Daily property update system (9.7M properties)
  - 67 Florida counties monitoring
  - Database schema requirements

### Property USE System
- **`PROPERTY_USE_SYSTEM_PERMANENT.md`**
  - Property classification system
  - DOR code mapping (60+ property types)
  - Component implementation guide

- **`PROPERTY_USE_WEBSITE_UPDATE_PLAN.md`**
  - Website-wide USE implementation roadmap
  - 13+ components requiring updates
  - Phase 2: ✅ COMPLETE (4/4 high-priority)

---

## 📚 How to Use Permanent Memory

1. **Read FIRST in every session** - These are core system rules
2. **Never modify** - These are permanent mandates
3. **Always reference** - When making related changes
4. **Always enforce** - Rules are not optional

---

**Remember:** If it's in `.memory/`, it's PERMANENT and MANDATORY.
