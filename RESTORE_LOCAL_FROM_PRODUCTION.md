Restoring Local Properties Page from Production

Objective
- Make `http://localhost:5173/properties` render identically to `https://www.concordbroker.com/properties`, with working API calls, regardless of local source inconsistencies.

Baseline (already wired)
- `scripts/download_vercel_assets.py` downloads the live production UI into any folder (default `apps/web/dist`).
- `scripts/serve-dist.js` serves a static SPA with fallback and proxies `/api/*` to `API_PROXY`.
- `start-session.bat` prefers `apps/web/live-dist`, reads `RAILWAY_PUBLIC_URL.txt` to set `API_PROXY`, and falls back to `http://localhost:8001`.
- If `RAILWAY_TOKEN` is set and `RAILWAY_PUBLIC_URL.txt` is missing, `start-session.bat` auto-discovers the public Railway URL and writes it to that file.

Steps

1) Safety Baseline (non‑destructive)
- Quarantine nested git repo and stray files (already done in this repo). If needed again:
  - Move `railway-deploy/.git` → `railway-deploy/.git.backup_<timestamp>`
  - Move any `C:Users...` zero‑length files into `backups/strays/`

2) Download Production UI Snapshot
- PowerShell/CMD:
  - `python scripts/download_vercel_assets.py apps/web/live-dist`
- Result: `apps/web/live-dist/index.html` and `/assets/*` mirror production exactly.

3) Point Local UI to a Working Backend
- Use production API now (recommended):
  - CMD: `echo https://api.concordbroker.com > RAILWAY_PUBLIC_URL.txt`
  - PowerShell: `"https://api.concordbroker.com" | Out-File -NoNewline RAILWAY_PUBLIC_URL.txt`
- Or use Railway public URL:
  - If known, write it to `RAILWAY_PUBLIC_URL.txt`.
  - If unknown, auto-discover with token:
    - PowerShell:
      - `$env:RAILWAY_TOKEN="<YOUR_RAILWAY_TOKEN>"`
      - `node scripts/get-railway-url.cjs 05f5fbf4-f31c-4bdb-9022-3e987dd80fdb > RAILWAY_PUBLIC_URL.txt`
- Note: `concordbroker.railway.internal` is not publicly reachable; you need a public domain (e.g., `*.up.railway.app`).

4) Serve Locally (SPA + Proxy)
- Run: `start-session.bat`
- Behavior:
  - Prefers `apps/web/live-dist` and serves it at `http://localhost:5173`
  - Proxies `/api/*` to the URL from `RAILWAY_PUBLIC_URL.txt` (or to `API_PROXY` if set)
  - Falls back to local dev if no dist exists

5) Verification
- Open `http://localhost:5173/properties`
- Check DevTools → Network:
  - Assets load from `/assets/...` (200 OK)
  - API calls go to `/api/...` (proxied to your configured backend) with 200 responses
- Refresh on `/properties` should work (SPA fallback to `index.html`).

Fallbacks (if needed)
- Build from source:
  - `cd apps/web && npm install && npm run build`
  - `set DIST_DIR=apps/web/dist && node scripts/serve-dist.js` (CMD)
  - `$env:DIST_DIR="apps/web/dist"; node scripts/serve-dist.js` (PowerShell)
- Development mode with production API:
  - Keep using the static server with proxy; avoid putting prod secrets into `.env`.

Notes
- Do not edit `apps/web/.env` with production secrets. The proxy avoids CORS while keeping secrets server-side.
- After mission success, rotate keys and scrub repo history.

