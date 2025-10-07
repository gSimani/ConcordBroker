# Complete Execution Plan: 100% Florida Data Automation

**Date**: October 5, 2025
**Status**: Ready for Phased Deployment
**Target**: 100% Blueprint Completion (from 39% → 100%)

---

## Executive Summary

This document provides a complete, step-by-step execution plan to achieve 100% of the Florida Data Automation blueprint using the full technology stack:

- **Frontend**: Vercel Pro (Next.js 14)
- **Backend**: Railway Pro (FastAPI)
- **Primary LLM**: OpenAI GPT-4 (Agent Lion)
- **Secondary LLM**: Gemma 3 270M (Hugging Face)
- **Database**: Supabase Pro (PostgreSQL + PostGIS + pgvector)
- **Memory**: Memvid system
- **Scraping**: Firecrawl + Playwright MCP
- **CDN**: Cloudflare
- **Monitoring**: Sentry + CodeCo

---

## Current Status (39% Complete)

### ✅ What's Working
- Railway deployment (FastAPI orchestrator)
- Basic DOR file downloads
- SHA256 delta detection
- Supabase storage
- Basic staging tables
- Production UPSERT
- Daily cron job (3 AM ET)

### ❌ What's Missing
- Proper database schemas (st g_*, core, gis)
- DOR Edit Guide validation
- FGIO parcel geometry
- County PA scraping (67 counties)
- RAG documentation system
- Gemma 3 270M classification
- Frontend dashboard
- Cloudflare CDN
- Materialized views

---

## Phase 1: Foundation (Days 1-5)

### Day 1: Database Schema Migration

**Agent**: Schema Architect Agent
**Technology**: PostgreSQL + PostGIS + pgvector
**Files Created**: ✅ `COMPLETE_SCHEMA_MIGRATION.sql`

**Steps**:
1. Open Supabase SQL Editor: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql
2. Copy contents of `COMPLETE_SCHEMA_MIGRATION.sql`
3. Paste and execute
4. Verify:
   ```sql
   SELECT schema_name FROM information_schema.schemata
   WHERE schema_name IN ('stg_nal', 'stg_sdf', 'stg_nap', 'core', 'gis');
   ```

**Deliverables**:
- ✅ stg_nal schema (NAL staging)
- ✅ stg_sdf schema (Sales staging)
- ✅ stg_nap schema (Tangible property staging)
- ✅ core schema (Production tables)
- ✅ gis schema (Parcel geometry)
- ✅ Materialized views (parcels_with_geometry, parcels_with_sales)

**Time**: 30 minutes

---

### Day 2-3: RAG Documentation System

**Agent**: RAG Documentation Agent
**Technology**: Supabase pgvector + OpenAI Embeddings
**Purpose**: Embed DOR documentation for AI-powered queries

**Setup Steps**:

1. **Enable pgvector extension**:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Create documentation tables**:
   ```sql
   CREATE TABLE docs_embeddings (
     id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
     document_type text, -- 'users_guide', 'edit_guide', 'submission_standards'
     section_title text,
     content text,
     embedding vector(1536),
     page_number int,
     created_at timestamptz DEFAULT now()
   );

   CREATE INDEX docs_embedding_idx ON docs_embeddings
   USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);
   ```

3. **Download DOR PDFs**:
   - 2025 Users Guide: https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/User%20Guides/2025%20Users%20guide%20and%20quick%20reference/2025_NAL_SDF_NAP_Users_Guide.pdf
   - 2025 Submission Standards: https://floridarevenue.com/property/Documents/2025FINALCompSubmStd.pdf
   - 2024 Edit Guide: https://floridarevenue.com/property/Documents/2024editguide.pdf

4. **Create embedding script** (`agents/rag_agent.py`):
   ```python
   import PyPDF2
   from openai import OpenAI
   from supabase import create_client

   client = OpenAI()
   supabase = create_client(URL, KEY)

   def chunk_pdf(pdf_path, chunk_size=512):
       # Extract text, chunk into 512-token segments
       pass

   def embed_and_store(chunks):
       for chunk in chunks:
           embedding = client.embeddings.create(
               model="text-embedding-3-small",
               input=chunk['text']
           ).data[0].embedding

           supabase.table('docs_embeddings').insert({
               'document_type': chunk['doc_type'],
               'content': chunk['text'],
               'embedding': embedding,
               'page_number': chunk['page']
           }).execute()
   ```

5. **Add search endpoint** to FastAPI:
   ```python
   @app.post("/api/docs/search")
   async def search_docs(query: str, top_k: int = 5):
       # Generate query embedding
       embedding = openai.embeddings.create(
           model="text-embedding-3-small",
           input=query
       ).data[0].embedding

       # Vector similarity search
       results = supabase.rpc('match_documents', {
           'query_embedding': embedding,
           'match_count': top_k
       }).execute()

       return {"results": results.data}
   ```

**Time**: 2 days

---

### Day 4-5: DOR Edit Guide Validation

**Agent**: DOR Validation Agent
**Technology**: Python + RAG + Gemma 3 270M
**Purpose**: Validate all records against DOR standards

**Steps**:

1. **Extract validation rules** from PDFs (using RAG):
   ```python
   # Query RAG for field specifications
   owner_name_spec = search_docs("What is maximum length for owner_name field?")
   # Response: "40 characters per 2025 Users Guide Section 3.2"
   ```

2. **Create validation engine** (`agents/validation_agent.py`):
   ```python
   class DORValidationAgent:
       def __init__(self):
           self.rules = self.load_validation_rules()

       def validate_record(self, record: dict) -> dict:
           errors = []
           warnings = []

           # Check field lengths
           if len(record.get('owner_name', '')) > 40:
               errors.append("owner_name exceeds 40 characters")

           # Check data types
           if record.get('just_value') and not isinstance(record['just_value'], (int, float)):
               errors.append("just_value must be numeric")

           # Check code lists (via Gemma 3 270M)
           if record.get('dor_uc'):
               if not self.validate_dor_code(record['dor_uc']):
                   errors.append(f"Invalid DOR use code: {record['dor_uc']}")

           confidence = 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.05)

           return {
               "valid": len(errors) == 0,
               "confidence": max(0, min(1, confidence)),
               "errors": errors,
               "warnings": warnings
           }

       def validate_dor_code(self, code: str) -> bool:
           # Use Gemma 3 270M for code classification
           response = requests.post(HF_INFERENCE_URL, json={
               "inputs": f"Is '{code}' a valid Florida DOR use code?",
               "parameters": {"max_length": 100}
           })
           return "yes" in response.json()[0]['generated_text'].lower()
   ```

3. **Integrate into ingestion pipeline**:
   ```python
   # In florida_data_orchestrator.py
   validator = DORValidationAgent()

   for record in parsed_records:
       result = validator.validate_record(record)

       if result['confidence'] < 0.8:
           # Flag for manual review
           supabase.table('validation_queue').insert(record).execute()
       elif result['valid']:
           # Insert to staging
           supabase.table('stg_nal.records_2025').insert(record).execute()
       else:
           # Log error
           logger.error(f"Rejected record: {result['errors']}")
   ```

**Time**: 2 days

---

## Phase 2: Data Acquisition (Days 6-12)

### Day 6-8: FGIO Parcel Geometry Integration

**Agent**: Geometry Integration Agent
**Technology**: GeoPandas + PostGIS
**Purpose**: Add parcel boundaries for map visualization

**Steps**:

1. **Download FGIO parcels** (ArcGIS REST API):
   ```python
   import geopandas as gpd

   # Florida Statewide Parcels Feature Service
   url = "https://services1.arcgis.com/...../FeatureServer/0/query"

   for county_code in range(1, 68):
       params = {
           'where': f"COUNTY_CODE = {county_code}",
           'outFields': '*',
           'f': 'geojson'
       }

       gdf = gpd.read_file(url, params=params)

       # Transform to WGS84
       gdf = gdf.to_crs(epsg=4326)

       # Load to PostGIS
       gdf.to_postgis('parcels_geometry', engine, schema='gis', if_exists='append')
   ```

2. **Build parcel crosswalk**:
   ```python
   # Match DOR parcel_id to FGIO parcel_id
   for county in counties:
       dor_parcels = supabase.table('core.parcels')\
           .select('parcel_id')\
           .eq('county_code', county)\
           .execute().data

       fgio_parcels = supabase.table('gis.parcels_geometry')\
           .select('fgio_parcel_id, centroid')\
           .eq('county_code', county)\
           .execute().data

       # Fuzzy match + spatial join
       matches = match_parcels(dor_parcels, fgio_parcels)

       # Store in xwalk table
       supabase.table('gis.parcel_key_xwalk').insert(matches).execute()
   ```

3. **Add GeoJSON endpoint**:
   ```python
   @app.get("/api/parcel/{county}/{parcel_id}/geometry")
   async def get_parcel_geometry(county: int, parcel_id: str):
       result = supabase.rpc('get_parcel_geojson', {
           'p_county': county,
           'p_parcel_id': parcel_id
       }).execute()

       return {"type": "Feature", "geometry": result.data}
   ```

**Time**: 3 days

---

### Day 9-12: County PA Scraping (67 Counties)

**Agent**: County Scraper Agent
**Technology**: Firecrawl + Playwright MCP
**Purpose**: Supplement DOR data with county-level sources

**Setup**:

1. **Deploy Firecrawl** (via Railway):
   ```bash
   # Add Firecrawl to requirements.txt
   echo "firecrawl-py==0.0.5" >> requirements.txt

   railway up
   ```

2. **Deploy Playwright MCP** (separate Railway service):
   ```dockerfile
   # Dockerfile.playwright
   FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY playwright_mcp_server.py .
   CMD ["python", "playwright_mcp_server.py"]
   ```

   ```python
   # playwright_mcp_server.py
   from fastapi import FastAPI
   from playwright.async_api import async_playwright

   app = FastAPI()

   @app.post("/scrape")
   async def scrape_page(url: str):
       async with async_playwright() as p:
           browser = await p.chromium.launch()
           page = await browser.new_page()
           await page.goto(url)
           await page.wait_for_load_state('networkidle')

           # Extract download links
           links = await page.eval_on_selector_all(
               'a[href*=".csv"], a[href*=".zip"]',
               'elements => elements.map(e => e.href)'
           )

           await browser.close()
           return {"links": links}
   ```

3. **Create county scraper configs**:
   ```python
   COUNTY_CONFIGS = {
       6: {  # Broward
           'name': 'Broward',
           'pa_url': 'https://bcpa.net/RecInfo.asp',
           'type': 'firecrawl',  # or 'playwright' for dynamic sites
           'selectors': {
               'download_page': '#DataDownloads',
               'csv_links': 'a[href$=".csv"]'
           }
       },
       13: {  # Miami-Dade
           'name': 'Miami-Dade',
           'pa_url': 'https://www.miamidade.gov/pa/property_search.asp',
           'type': 'playwright',  # Requires JavaScript rendering
           'selectors': {
               'search_button': '#btnSearch',
               'results_table': '.search-results'
           }
       },
       # ... all 67 counties
   }
   ```

4. **Implement scraper agent**:
   ```python
   from firecrawl import FirecrawlApp

   class CountyScraperAgent:
       def __init__(self):
           self.firecrawl = FirecrawlApp(api_key=os.getenv('FIRECRAWL_API_KEY'))
           self.playwright_url = os.getenv('PLAYWRIGHT_MCP_URL')

       async def scrape_county(self, county_code: int):
           config = COUNTY_CONFIGS[county_code]

           if config['type'] == 'firecrawl':
               result = self.firecrawl.scrape_url(config['pa_url'])
               links = self.extract_download_links(result['content'])
           else:
               # Use Playwright MCP for dynamic sites
               response = await httpx.post(f"{self.playwright_url}/scrape", json={
                   'url': config['pa_url']
               })
               links = response.json()['links']

           # Download and process files
           for link in links:
               await self.process_county_file(county_code, link)
   ```

**Time**: 4 days (research + implementation)

---

## Phase 3: Intelligence Layer (Days 13-18)

### Day 13-14: Gemma 3 270M Deployment

**Agent**: Code Classification Agent
**Technology**: Hugging Face Inference API
**Purpose**: Classify DOR code lists

**Steps**:

1. **Create Hugging Face Space**:
   - Go to https://huggingface.co/spaces
   - New Space → Gradio → GPU (T4 small)
   - Name: `florida-dor-code-classifier`

2. **Deploy Gemma 3 270M**:
   ```python
   # app.py (Hugging Face Space)
   import gradio as gr
   from transformers import AutoTokenizer, AutoModelForCausalLM

   model_name = "google/gemma-3-27b-it"
   tokenizer = AutoTokenizer.from_pretrained(model_name)
   model = AutoModelForCausalLM.from_pretrained(
       model_name,
       device_map="auto",
       load_in_4bit=True  # Quantized for T4
   )

   # Load DOR code lists
   LAND_USE_CODES = {
       "0000": "Vacant residential",
       "0001": "Single family",
       "0002": "Mobile home",
       # ... all codes from 2025 Users Guide Appendix A
   }

   def classify_code(code: str, context: str = "") -> dict:
       prompt = f"""Is '{code}' a valid Florida DOR land use code?

       Context: {context}

       Reference codes: {list(LAND_USE_CODES.keys())[:20]}...

       Respond with JSON:
       {{"valid": true/false, "description": "...", "confidence": 0.0-1.0}}
       """

       inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
       outputs = model.generate(**inputs, max_length=200)
       result = tokenizer.decode(outputs[0])

       return parse_json_response(result)

   iface = gr.Interface(fn=classify_code, inputs=["text", "text"], outputs="json")
   iface.launch()
   ```

3. **Create API wrapper**:
   ```python
   # In Railway backend
   HF_SPACE_URL = "https://your-space.hf.space/api/predict"

   def validate_land_use_code(code: str) -> bool:
       response = httpx.post(HF_SPACE_URL, json={
           "data": [code, ""]
       })
       result = response.json()['data'][0]
       return result['valid'] and result['confidence'] > 0.8
   ```

**Time**: 2 days

---

### Day 15-16: Memvid Memory System

**Agent**: Memvid Memory Agent
**Technology**: Memvid + Supabase
**Purpose**: Persistent agent memory

**Steps**:

1. **Install Memvid**:
   ```bash
   pip install memvid
   ```

2. **Initialize Memvid store**:
   ```python
   from memvid import Memvid

   memvid = Memvid(
       backend='supabase',
       connection_string=os.getenv('SUPABASE_URL')
   )

   # Create memory schema
   supabase.sql("""
   CREATE TABLE IF NOT EXISTS agent_memory (
       id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
       agent_name text NOT NULL,
       memory_type text, -- 'pattern', 'error_resolution', 'optimization'
       situation jsonb,
       outcome jsonb,
       embedding vector(1536),
       success_rate numeric(3,2),
       usage_count int DEFAULT 0,
       created_at timestamptz DEFAULT now(),
       last_used timestamptz
   );
   """).execute()
   ```

3. **Integrate into agents**:
   ```python
   class SchemaArchitectAgent:
       def __init__(self):
           self.memory = memvid.get_namespace('schema_architect')

       def execute_task(self, task: dict):
           # Check memory for similar tasks
           similar = self.memory.search(
               query=task['description'],
               top_k=3
           )

           if similar:
               logger.info(f"Found {len(similar)} similar past tasks")
               # Apply learned strategy
               strategy = similar[0]['outcome']['strategy']

           # Execute task
           result = self.do_work(task, strategy=strategy)

           # Store outcome
           self.memory.store({
               'situation': task,
               'outcome': result,
               'success': result['status'] == 'SUCCESS'
           })

           return result
   ```

**Time**: 2 days

---

### Day 17-18: Agent Lion Master Orchestrator

**Agent**: Agent Lion
**Technology**: OpenAI GPT-4 + LangChain + Memvid
**Purpose**: Dynamic agent generation and coordination

**Architecture**:

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

class AgentLion:
    """
    Master orchestrator using chain-of-thought reasoning
    Dynamically generates and coordinates specialized agents
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        self.memory = memvid.get_namespace('agent_lion')
        self.active_agents = {}

    def plan(self, goal: str) -> list:
        """Chain-of-thought planning"""
        prompt = f"""
        Goal: {goal}

        Use chain-of-thought reasoning to:
        1. Break down the goal into sub-tasks
        2. Identify which specialized agents are needed
        3. Determine task dependencies
        4. Create execution sequence

        Available agent types:
        - SchemaArchitect: Database design
        - DORValidator: Data validation
        - GeometryIntegrator: Parcel boundaries
        - CountyScraper: PA site scraping
        - CodeClassifier: DOR code validation

        Respond with JSON execution plan.
        """

        response = self.llm.invoke(prompt)
        plan = json.loads(response.content)

        # Store plan in memory
        self.memory.store({
            'goal': goal,
            'plan': plan,
            'timestamp': datetime.now()
        })

        return plan['tasks']

    def generate_agent(self, agent_type: str, config: dict):
        """Dynamically generate specialized agent"""
        if agent_type == 'CountyScraper':
            return CountyScraperAgent(county_code=config['county'])
        elif agent_type == 'DORValidator':
            return DORValidationAgent(rules=config['rules'])
        # ... etc

    def execute_plan(self, plan: list):
        """Execute plan with parallel agents where possible"""
        results = []

        for task in plan:
            # Check dependencies
            if self.dependencies_met(task, results):
                # Generate agent
                agent = self.generate_agent(task['agent_type'], task['config'])

                # Execute
                if task.get('parallel', False):
                    # Run in background
                    future = asyncio.create_task(agent.execute(task))
                    self.active_agents[task['id']] = future
                else:
                    # Run synchronously
                    result = await agent.execute(task)
                    results.append(result)

        # Wait for all parallel agents
        await asyncio.gather(*self.active_agents.values())

        return results

# Usage
lion = AgentLion()
plan = lion.plan("Ingest all 67 Florida counties with validation")
results = await lion.execute_plan(plan)
```

**Time**: 2 days

---

## Phase 4: User Experience (Days 19-25)

### Day 19-22: Vercel Frontend Dashboard

**Technology**: Next.js 14 + React 18 + Tailwind + shadcn/ui
**Features**: Status grid, parcel search, interactive maps

**Setup**:

1. **Create Next.js 14 app**:
   ```bash
   npx create-next-app@latest florida-dashboard --typescript --tailwind --app
   cd florida-dashboard
   npm install @shadcn/ui leaflet react-leaflet
   ```

2. **Build pages**:

   **app/page.tsx** (Dashboard):
   ```typescript
   export default function Dashboard() {
     const [counties, setCounties] = useState<County[]>([])

     useEffect(() => {
       fetch('https://api.railway.app/api/county/all/status')
         .then(res => res.json())
         .then(data => setCounties(data))
     }, [])

     return (
       <div className="grid grid-cols-8 gap-4">
         {counties.map(county => (
           <CountyCard
             key={county.code}
             name={county.name}
             status={county.last_sync_status}
             lastSync={county.last_sync_at}
             dataQuality={county.data_quality_score}
           />
         ))}
       </div>
     )
   }
   ```

   **app/search/page.tsx** (Parcel Search):
   ```typescript
   export default function ParcelSearch() {
     const [results, setResults] = useState([])

     const search = async (county: string, parcelId: string) => {
       const res = await fetch(`/api/parcel/${county}/${parcelId}`)
       const data = await res.json()
       setResults([data])
     }

     return (
       <div>
         <SearchForm onSearch={search} />
         <ResultsList results={results} />
         <ParcelMap parcel={results[0]} />
       </div>
     )
   }
   ```

   **components/ParcelMap.tsx**:
   ```typescript
   import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet'

   export function ParcelMap({ parcel }) {
     const [geometry, setGeometry] = useState(null)

     useEffect(() => {
       if (parcel) {
         fetch(`/api/parcel/${parcel.county}/${parcel.parcel_id}/geometry`)
           .then(res => res.json())
           .then(setGeometry)
       }
     }, [parcel])

     return (
       <MapContainer center={[27.9, -81.5]} zoom={7}>
         <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
         {geometry && <GeoJSON data={geometry} />}
       </MapContainer>
     )
   }
   ```

3. **Deploy to Vercel**:
   ```bash
   vercel --prod
   ```

**Time**: 4 days

---

### Day 23-24: Cloudflare CDN

**Purpose**: Performance + DDoS protection

**Steps**:

1. **Add site to Cloudflare**:
   - Go to https://dash.cloudflare.com
   - Add site: concordbroker.com
   - Update nameservers

2. **Configure DNS**:
   ```
   Type    Name    Target
   CNAME   www     cname.vercel-dns.com
   A       api     railway-ip-address
   A       data    railway-data-service-ip
   ```

3. **Set caching rules**:
   - Cache Level: Standard
   - Browser TTL: 4 hours
   - Cache Rules:
     - `/api/parcel/*` → Cache 5 min
     - `/api/county/*` → Cache 15 min
     - `/api/search/*` → No cache
     - `/api/ingest/*` → No cache

4. **Enable rate limiting**:
   - `/api/*` → 100 req/min per IP
   - `/api/ingest/run` → 10 req/hour

5. **Add firewall rules**:
   - Block known bots (exclude good bots)
   - Challenge suspicious IPs
   - Allow US + known VPNs

**Time**: 2 days

---

### Day 25: Sentry + CodeCo Integration

**Steps**:

1. **Add Sentry to all services**:
   ```python
   # Railway backend
   import sentry_sdk

   sentry_sdk.init(
       dsn=os.getenv("SENTRY_DSN"),
       traces_sample_rate=0.1,
       profiles_sample_rate=0.1
   )
   ```

   ```typescript
   // Vercel frontend
   import * as Sentry from "@sentry/nextjs"

   Sentry.init({
     dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
     tracesSampleRate: 0.1
   })
   ```

2. **Configure CodeCo**:
   - Connect GitHub repo
   - Enable auto-fix PRs
   - Set review thresholds

**Time**: 1 day

---

## Phase 5: Testing & Launch (Days 26-30)

### Day 26-28: End-to-End Testing

**Test Scenarios**:

1. **Data ingestion flow**:
   - Trigger manual sync
   - Verify files downloaded
   - Check staging tables populated
   - Confirm validation executed
   - Verify production updates
   - Check geometry joins

2. **API endpoints**:
   - Test all parcel endpoints
   - Verify search functionality
   - Check documentation RAG
   - Test admin functions

3. **Frontend**:
   - Navigate all pages
   - Search parcels
   - View maps
   - Trigger manual sync

4. **Performance**:
   - API response times < 500ms
   - Dashboard load < 2s
   - Map render < 3s

**Time**: 3 days

---

### Day 29-30: Production Launch

**Checklist**:

- [ ] All 67 counties configured
- [ ] Database schemas deployed
- [ ] Validation rules active
- [ ] FGIO geometry loaded
- [ ] RAG system functional
- [ ] Gemma 3 270M deployed
- [ ] Memvid storing memories
- [ ] Agent Lion orchestrating
- [ ] Frontend deployed
- [ ] Cloudflare configured
- [ ] Sentry monitoring
- [ ] Daily cron verified
- [ ] Backups enabled
- [ ] Documentation complete

**Time**: 2 days

---

## Success Metrics (100% Completion)

### Coverage
- ✅ 67/67 counties automated
- ✅ 3 data sources per county (NAL, SDF, NAP)
- ✅ Daily updates (< 4 hour lag)
- ✅ 100% DOR Edit Guide compliance

### Performance
- ✅ API response < 500ms (p95)
- ✅ Dashboard load < 2s
- ✅ Map render < 3s
- ✅ Search results < 1s

### Quality
- ✅ Data quality score > 95%
- ✅ Validation pass rate > 98%
- ✅ Geometry match rate > 90%
- ✅ Error rate < 0.1%

### Reliability
- ✅ Uptime > 99.9%
- ✅ Zero data loss
- ✅ Recovery time < 15 min
- ✅ Daily backups verified

---

## Cost Estimate (Monthly)

| Component | Service | Cost |
|-----------|---------|------|
| Frontend | Vercel Pro | $20 |
| Backend | Railway Pro (2 services) | $30 |
| Database | Supabase Pro | $25 |
| LLM Primary | OpenAI API | $50-100 |
| LLM Secondary | Hugging Face (T4) | $15 |
| Scraping | Firecrawl | $20 |
| CDN | Cloudflare Pro | $20 |
| Monitoring | Sentry | $26 |
| **Total** | | **$206-256/month** |

---

## Next Actions (Immediate)

1. **Deploy Schema Migration** (TODAY):
   - Open Supabase SQL Editor
   - Run `COMPLETE_SCHEMA_MIGRATION.sql`
   - Verify all schemas created

2. **Set up OpenAI API Key** (TODAY):
   - Add to Railway environment variables
   - Test Agent Lion basic functionality

3. **Start Phase 1** (This Week):
   - Complete RAG documentation system
   - Build DOR validation engine
   - Test with Broward County (pilot)

4. **Order Resources**:
   - Hugging Face GPU space
   - Cloudflare Pro account
   - Firecrawl API access

---

## Timeline Summary

- **Week 1**: Foundation (schemas, RAG, validation)
- **Week 2**: Data acquisition (geometry, county scraping)
- **Week 3**: Intelligence (Gemma 3, Memvid, Agent Lion)
- **Week 4**: UX (frontend, Cloudflare, monitoring)
- **Week 5**: Testing & launch

**Total Duration**: 30 days
**Total Cost**: $206-256/month operational
**One-time Setup**: ~40 hours of development

---

**Status**: Ready to Execute
**First Step**: Deploy `COMPLETE_SCHEMA_MIGRATION.sql` to Supabase
**Contact**: Execute via Agent Lion orchestrator or manual deployment
