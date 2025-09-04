
# ConcordBroker – PDR (Project Design & Runbook) v0.1

**Owner:** ConcordBroker Team  
**Repo:** https://github.com/gSimani/ConcordBroker  
**Local path:** `C:\Users\gsima\Documents\MyProject\ConcordBroker`  
**Date:** 2025-09-03

> This PDR is the single source of truth. All agents (Claude Code, etc.) must **save** and **keep referencing this file**. Every change must go through PRs against this document first.

---

## 0) Kickoff – Claude Code control prompts

**Prompt 0.1 — Save and pin the PDR**
```
You are Claude Code acting as my project engineer. Create a new repo folder structure at C:\Users\gsima\Documents\MyProject\ConcordBroker and add a file docs/PDR.md with the full content I paste next (the ConcordBroker – PDR). Commit as "chore(docs): add PDR v0.1" and set it as a pinned reference for future tasks. For every task, read docs/PDR.md first and update it in the same PR when you change scope or decisions.
```

**Prompt 0.2 — Repo bootstrapping**
```
Initialize a new Git repo (if not already) in C:\Users\gsima\Documents\MyProject\ConcordBroker with a MIT LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, and .gitignore for Python/Node/Docker. Create 3 top-level packages: `apps/` (frontend, api, workers), `infra/` (IaC, scripts), `docs/`. Create a mono-repo PNPM workspace for the frontend and a Python `poetry` project for api/workers. Initialize CI with GitHub Actions for lint, test, build.
```

---

## 1) Scope & Goals

**Goal:** Acquire Broward investment properties by automating data collection (DOR assessment roll + Broward Official Records + Sunbiz), normalizing owners/entities, scoring and surfacing candidates via a Vercel UI. Avoid brittle scraping; use Playwright fallback for gaps only.

**Primary Filters:** City (Broward list), Main Use (00–99 family), Sub-Use (e.g., Industrial→43 Lumber Yards).  
**Outputs:** Ranked property list with links (BCPA record, Google Maps, Building Card/Sketch, Instrument #), and contact graph (entity → officers/agents / phones/emails when available).

---

## 2) Architecture (Modern Full-Stack)

- **Frontend**: Vercel (Vite/React + Tailwind + shadcn)
- **Backend API**: FastAPI on Railway
- **Data Workers (ETL)**: Railway cron containers (Python, Polars/DuckDB)
- **DB**: Supabase (Postgres + [pgvector])
- **Vector/RAG**: for docs/rules only (not parcel facts)
- **Auth/Verify**: Twilio Verify (SMS + Email/SendGrid)
- **Email**: Twilio SendGrid (domain verified)
- **CDN/Protection**: Cloudflare
- **Scraping Fallback**: Playwright MCP runners on Railway
- **Error Tracking**: Sentry (+ CodeCo if required)

**Data Sources**
- Florida DOR: NAL/SDF (+ annual GIS)
- Broward Official Records: daily DOC/NME/LGL/LNK (+ IMG)
- Sunbiz: daily + quarterly SFTP bulk

---

## 3) Security & Secrets (MANDATORY)

- **Do NOT commit secrets.** Use Railway/Vercel/Supabase secret stores for env vars. Prefer central secret manager (Infisical) with per-env injectors.
- Rotate any credentials previously exposed.
- Enforce RLS in Supabase and API token scopes; enable CORS allowlist for Vercel domain.

**Prompt 3.1 — Secrets baseline**
```
Create infra/secrets/.template.env containing placeholders for: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET, OPENAI_API_KEY, HF_TOKEN, SENTRY_DSN, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, SENDGRID_API_KEY, TWILIO_VERIFY_SERVICE_SID, SENDGRID_FROM_EMAIL, FRONTEND_URL, BACKEND_URL. Add a README explaining how to load env vars in Railway/Vercel and to never commit real values.
```

---

## 4) Data Model (Supabase)

### 4.1 Core tables
- **parcels**(folio PK, county_code, city, main_use, sub_use, situs_addr, mailing_addr, owner_raw, owner_entity_id, land_value, just_value, assessed_soh, taxable, living_area, land_sf, bldg_sf, units, beds, baths, eff_year, act_year, taxing_auth_code, last_roll_year, last_seen_at)
- **sales**(folio FK, sale_date, price, sale_type, book_page, instrument_no, qualified_flag, multi_parcel_flag)
- **recorded_docs**(instrument_no PK, doc_type, rec_datetime, consideration, first_parcel, legal_summary)
- **doc_parcels**(instrument_no FK, folio FK)
- **entities**(id PK, name, fei_ein, status, principal_addr, reg_agent_id, created_date)
- **officers**(id PK, entity_id FK, name, title, addr, is_manager)
- **parcel_entity_links**(folio, entity_id, match_method, confidence)
- **jobs**(id, job_type, started_at, finished_at, ok, rows, notes)

### 4.2 Indexing
- `parcels(city, main_use, sub_use)`; `sales(folio, sale_date desc)`; `recorded_docs(rec_datetime desc)`; vector index for free-text notes.

**Prompt 4.1 — SQL**
```
Generate SQL (Postgres) to create the tables above with appropriate data types, primary/foreign keys, indexes, and RLS policies: users can read only through API service role; public read disabled. Output as db/schema.sql. Also generate db/policies.sql enabling read via a service role and denying anon.
```

---

## 5) ETL Pipelines (Railway workers)

### 5.1 DOR Assessment Roll Loader (NAL/SDF)
- **Schedule:** run manually for each new drop (prelim/final/post-VAB). Year is a parameter.
- **Tasks:**
  1. Download latest **NAL** and **SDF** for Broward (county 16).
  2. Parse CSV with Polars; select fields per mapping; normalize city/use codes.
  3. Upsert into `parcels` & `sales` (flag source=`DOR`).
- **Edge cases:** confidential records removed; handle missing fields gracefully.

**Prompt 5.1 — DOR loader**
```
Create apps/workers/dor_loader/ with a Python script using Polars to accept args `--year 2024 --county 16 --nal path --sdf path`. Map NAL columns to parcels fields (include eff_year, act_year, living_area, units, land_value, exemptions to compute taxable). For SDF, join on parcel id to populate sales. Use asyncpg for batch upserts. Add tests with small sample CSVs.
```

### 5.2 Broward Official Records Loader (daily)
- **Schedule:** every morning 7:15 AM ET.
- **Tasks:** connect to Broward FTP; download `*-doc-ver.txt`, `*-nme-ver.txt`, `*-lgl-ver.txt`, `*-lnk-ver.txt`; parse fixed-width/tab files; insert into `recorded_docs` and `doc_parcels`.
- **Join:** link docs→parcels by parcel id; link new deeds to `sales` when price present.

**Prompt 5.2 — OR loader**
```
Create apps/workers/or_loader/ that uses aioftp/curl to fetch yesterday's verified files from ftp://crpublic@bcftp.broward.org/Official_Records_Download. Implement parsers for DOC/NME/LGL/LNK per the ExportFilesLayout spec. Upsert to recorded_docs and doc_parcels. Record a jobs row with counts. Add idempotency (do not double-insert same instrument).
```

### 5.3 Sunbiz Loader (daily + quarterly)
- **Schedule:** daily 8:00 AM ET; quarterly full refresh.
- **Tasks:** connect via SFTP to `sftp.floridados.gov` (Public/PubAccess1845!), pull corporate daily + events; quarterly `cordata.zip` etc.; parse fixed-width per the Data Usage Guide; upsert into `entities`, `officers`.
- **Entity resolution:** deterministic string norms; then fuzzy (rapidfuzz) to map parcel owner names → entity.

**Prompt 5.3 — Sunbiz loader**
```
Create apps/workers/sunbiz_loader/ with Paramiko SFTP client to pull daily files into /data/raw/sunbiz/YYYY-MM-DD. Write a fixed-width parser (layout from Data Usage Guide) that outputs parquet. Upsert entities/officers; build a matching module that normalizes LLC/INC punctuation, strips stopwords, and uses a token-set ratio threshold to link parcels.owner_raw to entities.name. Emit parcel_entity_links with confidence.
```

### 5.4 Playwright Fallback Scraper (city/use-code sweeps)
- **Use only if InfoBroward/commercial export not available**.
- Iterate City × Use Code; submit BCPA ASP forms; parse results; persist folio list.

**Prompt 5.4 — Scraper**
```
Create apps/workers/bcpa_scraper/ using Playwright (Chromium). Implement a task `sweep --city "COCONUT CREEK" --use-codes 43,48` that posts the classic address search, paginates results, and extracts parcel IDs + basic fields. Use a rotating user-agent, polite delays, and caching. Save pages to /data/cache/bcpa.
```

---

## 6) Scoring & Selection

- Rule-based score combining: Use Code weight, recent deed/mortgage, price/land-SF deviation vs. peers, large Assessed vs. Just delta, age. Communicate as transparent components.

**Prompt 6.1 — Scorer**
```
Add apps/api/services/score.py with a pure-Python scoring function that ingests a parcel row + recent sales comparables (same city/use) and outputs a 0–100 score + feature breakdown. Include unit tests with fixtures.
```

---

## 7) Backend API (FastAPI on Railway)

**Endpoints**
- `GET /health`
- `GET /cities` (from normalized list)
- `GET /use-codes` (main + sub)
- `GET /parcels/search?city=&main_use=&sub_use=&min_land_sf=&max_age=&min_score=`
- `GET /parcel/{folio}` (joins sales, docs, entity)
- `GET /entity/{id}`

**Prompt 7.1 — FastAPI skeleton**
```
Create apps/api/ with FastAPI. Implement the endpoints above, using asyncpg connection pooling to Supabase. Add CORS for FRONTEND_URL. Add pydantic models; include pagination. Provide an OpenAPI schema and a /_debug/sql endpoint gated by ADMIN_TOKEN.
```

---

## 8) Frontend (Vercel)

- Vite/React + Tailwind + shadcn. 2 pages: **Search** and **Parcel Details**.
- Filters: City (multi), Main Use (pill group), Sub-Use (multi-select), range inputs for land SF and year built, sort by score/date.
- Result row actions: BCPA Page, Google Maps, Instrument link, Building Card/Sketch.

**Prompt 8.1 — UI**
```
Create apps/web/ (Vite + React + Tailwind + shadcn). Build a Search page with filters bound to /parcels/search and a table that shows score, owner, use, values, last sale, actions. Build a Parcel Details page that calls /parcel/{folio}. Add an Entities page for officer graph.
```

---

## 9) Authentication & Notifications (Twilio Verify + SendGrid)

### 9.1 Configure SendGrid domain
- Add DNS records (as provided) and verify in SendGrid/Twilio Verify Email.
- Set From: `no-reply@concordbroker.com` (or subdomain like `mail.`).

**Prompt 9.1 — DNS readme**
```
Create docs/sendgrid_dns.md describing the 5 CNAME + 1 TXT records already provisioned and how to verify them in SendGrid + Twilio Verify Email. Add a checklist to confirm SPF/DKIM/DMARC pass before enabling production.
```

### 9.2 Twilio Verify services
- Create Verify Service for SMS + Email; store `TWILIO_VERIFY_SERVICE_SID`.
- API flow: `/auth/start` (send verification to phone/email) → `/auth/check` (verify code) → issue JWT.

**Prompt 9.2 — Verify integration**
```
Add apps/api/auth/verify.py using twilio-python. Implement POST /auth/start {channel: sms|email, to} to send a verification, and POST /auth/check {to, code} to verify. On success, create or upsert a user in Supabase and return a JWT signed with SECRET.
```

### 9.3 Transactional email (SendGrid)
- Templates: Welcome, New Match Alert, Weekly Digest.

**Prompt 9.3 — Email client**
```
Add apps/api/services/email.py wrapping SendGrid (dynamic templates). Provide send_welcome(user), send_new_match(parcel), send_weekly_digest(list). Read SENDGRID_API_KEY and default FROM from env.
```

---

## 10) Observability & Ops

- **Sentry**: API + workers; release tagging via Git SHA; set alerts.
- **Health checks**: /health; worker heartbeats update `jobs` table.
- **Cloudflare**: cache GET /parcels/search for 5m; WAF bot mode.

**Prompt 10.1 — Sentry**
```
Integrate Sentry SDK in apps/api and all workers. Environment from ENV (dev/stage/prod). Add middleware to log request ids and SQL timings.
```

---

## 11) Deployment

**Railway**
- One service per worker + one for api. Use Dockerfiles with small slim images. Schedule OR/Sunbiz jobs.

**Vercel**
- Build apps/web; set env `NEXT_PUBLIC_API_URL`.

**Prompt 11.1 — Docker & CI**
```
Create Dockerfiles for apps/api and each worker with python:3.11-slim, installing only required deps. Add .github/workflows/ci.yml to lint (ruff), test (pytest), type-check (mypy), and build containers. Add Railway service.json and vercel.json.
```

---

## 12) Data Quality & Testing

- Contract tests for each feed (column presence, types, rowcount sanity).  
- Idempotency tests for loaders.  
- Golden-file tests for parsers (sample inputs→expected parquet).

**Prompt 12.1 — QA**
```
Add tests/ with pytest that validate parsers for NAL, SDF, DOC/NME/LGL, and Sunbiz fixed-width. Include fixtures and golden parquet files under tests/data.
```

---

## 13) Roadmap (next 4 weeks)

- **W1:** Schema, DOR+Sunbiz loaders, API skeleton
- **W2:** OR loader, scorer, basic UI
- **W3:** Twilio Verify, SendGrid emails, Cloudflare, Sentry
- **W4:** Playwright fallback, polish UI, performance, docs

**Prompt 13.1 — Issues**
```
Create GitHub milestones and issues from the roadmap with detailed acceptance criteria. Assign default labels (etl, api, web, auth, infra, docs).
```

---

## 14) Appendices

- **Field mappings** NAL→`parcels`, SDF→`sales`, DOC/LGL→`recorded_docs` & `doc_parcels` (to be filled during 5.x tasks).
- **City list** (BCPA select) cache updater task.
- **Use Code taxonomy** embed from BCPA use_code list.

**Prompt 14.1 — Taxonomy**
```
Create a static JSON for use codes (main class 00–99 and subcodes) and a small script to regenerate from the public page. Expose via /use-codes API.
```
