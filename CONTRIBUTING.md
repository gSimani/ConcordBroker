# Contributing to ConcordBroker

## PR Guidelines
- Use Conventional Commit titles: e.g., `feat: add X`, `fix: Y`, `docs: Z`, `chore: ...`
- Add a changeset when code behavior changes: `pnpm dlx changeset`
- Keep PRs focused (small, reviewable diffs).

## Running PR Checks Locally
- Node/TypeScript:
  - `pnpm -w -r -if-present lint`
  - `pnpm -w -r -if-present build`
- Python:
  - `python -m compileall .`

## Environment Setup
- Copy `.env.example` to `.env` or edit `.env.mcp` (local dev only).
- Do not commit real secrets. Frontend must only use anon keys.
- Quick env sanity: `python scripts/tools/preflight_env.py`

## Releases
- Merge PRs with changesets → Changesets opens a version PR → merge to publish.
- Pushing a `v*` tag also creates a GitHub Release and uploads assets.

## Supabase Access
- Backend: `SUPABASE_SERVICE_ROLE_KEY` (never expose to frontend)
- Frontend: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`

## AI Providers
- Preferred: Vercel AI Gateway (`AI_GATEWAY_API_KEY`).
- Fallback: OpenAI (`OPENAI_API_KEY`).
- Helper: `scripts/common/ai_client.py`.

## Dependency Updates
- Dependabot: weekly PRs for npm, pip, and GitHub Actions (small batches)
- Renovate: automated, configurable updates with grouping
  - Auto-merges minor/patch updates for devDependencies
  - Dashboard PR lists pending updates
- Prefer Renovate PRs for grouped updates; Dependabot PRs are fine for individual bumps.
