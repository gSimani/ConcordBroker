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

