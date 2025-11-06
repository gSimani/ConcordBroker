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

## Maintainers Guide

- Branching and Merges
  - Open PRs against `main`; linear history is enforced (squash or rebase merges only).
  - Required checks: `PR Checks / changeset-check`, `PR Checks / node-ts`, `PR Checks / python-syntax`, and `Semantic Pull Request`.
  - Auto-merge: Add the label `automerge` to a PR. Once all checks pass, the workflow will squash-merge automatically.

- Changesets and Releases
  - For behavior changes, add a changeset: `pnpm dlx changeset` and commit the generated file.
  - Merging to `main` triggers the Changesets workflow, which opens a version PR; merging that PR publishes releases.
  - Pushing a `v*` tag also creates a GitHub Release and uploads standard assets (CHANGELOG, ALL_COMMITS.log).

- Environment & Secrets
  - Use `.env.mcp` locally for server-only secrets; do not commit real secrets.
  - Frontend must only use anon/public vars. Backend scripts use the service role key.

- Dependency PRs
  - Renovate groups updates and auto-merges minor/patch for devDependencies.
  - Dependabot opens weekly smaller PRs for npm, pip, and Actions.
  - Prefer labeling low-risk dependency PRs with `automerge` after checks are green.

- Security Notes
  - Service role keys must never be exposed in frontend code or public logs.
  - Verify scripts and tools should read keys via `.env.mcp` with overrides (no inline credentials).
