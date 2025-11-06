# ConcordBroker


## Local Environment & AI Provider

- Environment files
  - Use `.env.mcp` for local development (server-side only secrets).
  - Frontend must only use public vars: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
  - Backend uses `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (never expose to frontend).

- Quick env check
  - `python scripts/tools/preflight_env.py` (prints presence, no secret values)

- Supabase smoke test (backend)
  - `python -c "from dotenv import load_dotenv; import os; from supabase import create_client; load_dotenv('.env.mcp'); c=create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY')); print(c.table('auction_sites').select('county').limit(3).execute().data)"`

- AI provider selection
  - Preferred: Vercel AI Gateway (`AI_GATEWAY_API_KEY`) → `https://ai-gateway.vercel.sh/v1`
  - Fallback: OpenAI (`OPENAI_API_KEY`) → `https://api.openai.com/v1`
  - Helper: `from scripts.common.ai_client import get_openai_client_config`

Example (Python):

```python
from dotenv import load_dotenv
from scripts.common.ai_client import get_openai_client_config
import os, requests, json

load_dotenv('.env.mcp')
base_url, api_key = get_openai_client_config()
headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
payload = {'model': 'gpt-4o-mini', 'messages': [{'role': 'user', 'content': 'ping'}]}
print(requests.post(f'{base_url}/chat/completions', headers=headers, data=json.dumps(payload)).json())
```
