Changelog

Unreleased (2025-11-05)

- Features
  - RealAuction: 48‑county database implementation, architecture, and UI links (site links components, integration into Property tabs, tooltips).
  - Tax Deed Sales: Larger text, comprehensive stats, county filter, and per‑county “scrape” button.
  - Data quality & dashboards: Completed data quality verification dashboard; property type identification (three‑part solution).
  - Data ingestion/processing: On‑demand sales history scraping system; Direct PostgreSQL bulk loader analysis and implementation.
  - Agents/monitoring: Multi‑channel notifications; real‑time Agent Dashboard (Chain‑of‑Thought/Chain‑of‑Agents); specialized monitoring agents.
  - UI/UX: Searchable county dropdown (all 67 FL counties); owner notes section; larger owner box; Main USE/SubUSE on MiniPropertyCards; icon mapping for property types.

- Fixes
  - Counties and links: Corrected county metadata to 48; fixed BROWARD appraiser links (fnumber) and MIAMI‑DADE folio search.
  - Filters and counts: Fixed industrial filters; accurate property counts; critical filter bug resolved (now 10.3M filterable); complete property count accounting (9.1M tracked marks achieved in phases).
  - Sales history & details: Fixed Last Sale/Living Area display across dataset; resolved display bug affecting 637,890 records.
  - Data integrity: Added value filtering and corrected property classification.
  - TypeScript correctness: Project‑wide cleanup to 0 errors; numerous targeted fixes (PropertySearch, QueryProvider, OptimizedPropertyList, RUM, address‑autocomplete, [id].tsx, PostgREST subquery assertions, property types, interfaces, readonly arrays, deprecations, router Link usage, etc.).

- Infrastructure / Optimization
  - Tier 1 Phase 1 production infra and database performance optimizations.
  - Backend separation and port fixes; corrected Supabase count query.
  - Supabase migrations and deployment guides (including nullable parcel_id notes).

- Documentation
  - RealAuction 48‑county architecture and county analysis.
  - Deployment summaries; visual architecture diagrams; phase completion summaries.
  - Railway quick starts; PostgreSQL bulk loader quick start; RPC implementation guide.
  - Comprehensive audits and master control/summary docs.

- Notes
  - Service‑role key verified via REST and in the RealAuction configuration loader (backend‑only access path). Anon key intentionally not rotated until project completion.
  - Secret‑scanning noise temporarily suppressed during active development; to be tightened post‑rotation.
  - Full raw commit history is exported to ALL_COMMITS.log for detailed reference (hash | date | subject).

Proposed Versioning

- v0.10.0 (2025-11-05) — RealAuction Integration + 0 TS Errors
  - Scope: RealAuction DB + UI links across 48 counties, Tax Deed Sales UX, data quality dashboard, agents/monitoring, infra optimizations, TypeScript cleanup to 0 errors.
  - Diffstat (last ~90 commits): 579 files changed, 102,945 insertions(+), 8,768 deletions(-)
  - Key commits (representative):
    - 5469a0c feat: Add Florida RealAuction sites database implementation
    - 4d31656 feat: Add RealAuction site links UI components
    - 659aca5 feat: Integrate RealAuction site links into Property tabs
    - dc73bef feat: Add Tooltip UI component for auction site links
    - c35051b fix: Correct metadata to reflect 48 Florida counties (not 47)
    - 5bbf6b8 docs: Add 48-county RealAuction scraper system architecture
    - 5c83235 feat: Enhanced Tax Deed scraping with complete data capture and SUNBIZ linking
    - 6eaf1a7 feat: Complete data quality verification and dashboard
    - 84f7c55 feat: Complete property type identification system with 3-part solution
    - e400c2c feat: Achieve 100% TypeScript compliance (201 → 0 errors)
    - b8e8342 feat: Deploy Tier 1 database performance optimizations
    - 43d8530 feat: Tier 1 Phase 1 - Production Infrastructure & Database Optimization
    - 52e3589 docs: Add Railway orchestrator deployment guide and scripts
    - dc9a6f9 docs: Add Railway quick-start guide and API deployment script

- v0.9.0 (2025-10-XX) — Pre‑integration Stabilization
  - Scope: Property filters/counts stabilization, sales history display fixes, appraiser linking, initial RealAuction county analysis, TypeScript/type integrity improvements.
  - Key commits (representative):
    - 7a1920a fix: Complete property count accounting - all 9.1M properties now tracked
    - fe06eae fix: critical property filter bug - all 10.3M properties now filterable
    - e72ac50 fix: property detail page Last Sale and Living Area display for all 9.1M properties
    - 7f28efe fix: critical sales history display bug affecting all 637,890 records
    - 4415728 feat: Add BROWARD direct property appraiser links with fnumber parameter
    - 1617323 fix: Update MIAMI-DADE Property Appraiser links to use direct folio search
    - 681f23f feat: Complete RealAuction Florida counties analysis - 47 counties mapped
    - d3bab62 fix(PropertySearch): Fix 12 TypeScript errors - comprehensive type fixes
    - 9c2e4f5 fix: Complete [id].tsx TypeScript fixes (7 errors fixed)
    - 7d5f3df fix: Complete address-autocomplete TypeScript fixes (11 errors fixed)

Notes on Versioning
- No Git tags were found; the above versions are proposed groupings by scope and timeframe. If you prefer, I can add annotated tags (v0.9.0, v0.10.0) to match these sections.

Compare Links
- v0.9.0…v0.10.0: https://github.com/gSimani/ConcordBroker/compare/v0.9.0...v0.10.0
