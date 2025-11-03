# Full Audit - Agent Roster

- code-audit-agent: Codebase auditor â€” static analysis, type checks, lint, dependency and structure review.
   - subagent: spell-lint-agent - Scans for spelling issues in code and docs, and common error patterns
- db-audit-agent: Supabase database auditor â€” enumerates schemas, tables, FKs, RLS, functions, views, and maps data flows to UI.
   - subagent: db-relationship-visualizer - Builds entity-relationship map and highlights orphaned relations
   - subagent: db-policy-auditor - Audits RLS and policies for coverage and leaks
- research-agent: Research agent â€” surveys recent fixes and best practices; proposes modern approaches and enhancements.
   - subagent: trend-watcher - Gathers recent techniques (requires network) and summarizes applicability
- ui-audit-agent: UI auditor â€” inventories components, inspects console/network, verifies data placement with Playwright.
   - subagent: ui-visual-verifier - Uses Playwright MCP to capture screenshots and verify UI against expectations

