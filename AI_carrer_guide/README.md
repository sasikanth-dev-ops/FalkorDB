# AI Career Mentor

An AI career co-pilot concept that connects a student's evolving skills, goals, and projects to relevant opportunities and practical learning steps. See [spec.md](./spec.md), [executive_summary.md](./executive_summary.md), and [demo_script.md](./demo_script.md) for the product and submission materials.

## Current build status

The foundation, API, Streamlit dashboard, first agent workflow, and first opportunity-ingestion slice are implemented. The app provides validated settings, a FalkorDB client connection, demo seed data, student profile APIs, graph-backed opportunity matching, chat memory orchestration, and configured-source scraping/normalization. Opportunity text ranking currently uses token overlap, not embeddings or a vector database. Live-source compatibility, authentication, and semantic vector retrieval remain in progress. Recommendations can expose bounded, multi-hop skill-prerequisite paths from FalkorDB and use those paths to order roadmap steps. Graph traversals use fixed, parameterized Cypher; the language model does not write database queries.

The seed opportunities are synthetic development fixtures that use `example.org` URLs. They are excluded from the opportunity explorer and chat recommendations by default. The explorer has an explicit opt-in toggle for viewing them, and they are never presented as clickable opportunity links.

### Graph Hacks submission note

The Graph Hacks brief requires the main FalkorDB implementation to be new work completed during the event, even when an existing project is continued. This workspace has no Git repository, so the dates of the existing FalkorDB implementation cannot be verified here. Preserve a clear record of in-event work and confirm the implementation's eligibility, submission project, and registration status before submitting. The live challenge page lists an end time of October 18, 2026 at 11:59 p.m. IST.

## Requirements

- Python 3.11+
- Docker Desktop with Docker Compose

## Run the graph bootstrap

From the project root in PowerShell:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up -d falkordb
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m backend.database.setup
```

The bootstrap is safe to rerun: it merges deterministic seed entities and checks whether the configured range indexes already exist before creating missing ones.

The project uses the official Python `falkordb` client to connect to a FalkorDB service. The database runs locally in Docker; `falkordblite` is not currently used as a Python package.
Docker publishes the FalkorDB API and Browser ports on `127.0.0.1` only; do not change those bindings for a public demo without adding authentication and access controls.

## Configuration

Copy `.env.example` to `.env` and adjust settings if necessary:

- `FALKORDB_HOST` and `FALKORDB_PORT`: FalkorDB service connection
- `FALKORDB_USERNAME` and `FALKORDB_PASSWORD`: optional authentication
- `FALKORDB_GRAPH_NAME`: graph selected by the application
- `GEMINI_API_KEY`: required for `POST /api/v1/chat/message`
- `GEMINI_MODEL`: Gemini model name (defaults to `gemini-3.8-flash`, with bounded request timeouts and no automatic retries)
- `UNSTOP_SCRAPE_URL`, `WEMAKEDEVS_SCRAPE_URL`, `GITHUB_BOUNTIES_SCRAPE_URL`: optional HTTPS page or JSON-feed URLs for opportunity ingestion

If Gemini times out, returns an unusable response, or the API quota is exhausted, chat uses a clearly labeled local fallback for learning resources and graph-backed recommendations. The fallback itself does not infer or save profile facts.

Never commit `.env` or credentials.

## Start the API

After the database is running and bootstrapped:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --reload-dir backend --reload-dir scrapers
```

Open `http://localhost:8000/docs` for the generated API reference. Current endpoints:

- `GET /api/v1/health`
- `GET /health` (unversioned readiness probe)
- `GET /api/v1/student/{student_id}`
- `POST /api/v1/student/profile`
- `GET /api/v1/opportunities`
- `POST /api/v1/opportunities/scrape`
- `GET /api/v1/graph/state/{student_id}`
- `GET /api/v1/roadmap?student_id={student_id}`
- `POST /api/v1/chat/message`

## Start the dashboard

In a second PowerShell window from the project root, run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend\app.py
```

Open `http://localhost:8501`. The dashboard connects to the API at `http://127.0.0.1:8000`; start the API first.

Opportunity filters include `student_id`, `type`, `category`, and `limit`. Profile writes upsert basic details and add or update the supplied skill and goal relationships.
The chat workflow requires a configured Gemini API key. It extracts only explicitly stated profile facts, persists those facts to FalkorDB, and uses current graph opportunity data to generate match context and roadmap steps. When Gemini is not configured, the chat endpoint returns `503` rather than pretending a response was generated.

### Opportunity ingestion

Configure source URLs in `.env`, then restart the API. The scraper supports JSON feeds with an `opportunities`, `events`, `results`, `items`, or `data` array, schema.org `Event` JSON-LD, WeMakeDevs hackathon listing cards, and GitHub issue-search API results. Source URLs must use HTTPS and the expected source hostname; redirects are rejected. Scraped records are normalized, assigned stable IDs based on source and URL, and upserted into FalkorDB with their required-skill edges.
The official WeMakeDevs hackathon listings page (`https://www.wemakedevs.org/hackathons`) is used automatically when `WEMAKEDEVS_SCRAPE_URL` is not set. Listing date ranges are normalized; expired dated listings are hidden from recommendations. Its published listing fields are used as-is; missing deadlines or skill requirements are shown as unavailable rather than fabricated. In the dashboard's **Ingestion & Scrapers** tab, select WeMakeDevs and run ingestion to refresh the real listings. Chat requests that mention hackathons restrict results to hackathon listings and rank them against the student's query; the opportunity explorer defaults to hackathons but also supports other types.

Example from PowerShell after configuring `UNSTOP_SCRAPE_URL`:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/opportunities/scrape `
  -ContentType application/json `
  -Body '{"sources":["unstop"]}'
```

The configured WeMakeDevs and GitHub sources were checked against their live pages/API. Unstop's current listing does not expose data supported by this adapter, so its URL remains unset until a compatible feed is available. GitHub search results can contain noisy or unverified bounty claims; review listings before acting on them. Keep the API bound to localhost: the scraping endpoint does not yet require authentication.

Example request after setting `GEMINI_API_KEY` in `.env` and restarting the API:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/chat/message `
  -ContentType application/json `
  -Body '{"student_id":"seed-student-001","message":"I am learning FastAPI and want to find an AI hackathon. Help me prepare."}'
```

This prototype does not yet have authentication or per-user authorization. Keep it bound to localhost and do not expose the API or personal graph data publicly until auth and access controls are implemented.
