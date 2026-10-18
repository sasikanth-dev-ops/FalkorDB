# Deployment Guide — Railway (Backend + FalkorDB) + Streamlit Community Cloud (Frontend)

## Architecture

```
┌──────────────────────────────────────────┐
│  Streamlit Community Cloud               │
│  frontend/app.py                         │
│  Env: API_BASE_URL → Railway public URL  │
└────────────────┬─────────────────────────┘
                 │ HTTPS
┌────────────────▼─────────────────────────┐
│  Railway — FastAPI Service               │
│  uvicorn backend.main:app                │
│  Env: GEMINI_API_KEY, FALKORDB_HOST, ... │
└────────────────┬─────────────────────────┘
                 │ Private Railway network
┌────────────────▼─────────────────────────┐
│  Railway — FalkorDB Service              │
│  Docker image: falkordb/falkordb:latest  │
│  Port: 6379 (internal only)              │
└──────────────────────────────────────────┘
```

---

## Part 1 — Deploy FalkorDB on Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub.
2. Create a **New Project** → **Deploy a Docker Image**.
3. Image name: `falkordb/falkordb:latest`
4. In the service settings, set the **internal port** to `6379`.
5. Do **not** expose a public domain for FalkorDB — it only needs to be reachable privately within Railway.
6. Note the **private hostname** Railway assigns (e.g., `falkordb.railway.internal` or the service name).

---

## Part 2 — Deploy FastAPI Backend on Railway

### 2a. Connect your GitHub repo

1. In the same Railway project, click **+ New Service** → **GitHub Repo**.
2. Select your AI Career Mentor repository.
3. Railway auto-detects `nixpacks.toml` and `railway.toml` — it will run:
   - `pip install -r requirements-backend.txt` (install phase)
   - `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` (start command)

### 2b. Set environment variables

Go to **Variables** in the FastAPI service and add:

| Variable | Value |
|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` |
| `FALKORDB_HOST` | Railway private hostname for FalkorDB (e.g. `falkordb.railway.internal`) |
| `FALKORDB_PORT` | `6379` |
| `FALKORDB_GRAPH_NAME` | `career_mentor` |
| `APP_ENV` | `production` |
| `API_V1_PREFIX` | `/api/v1` |

Leave `FALKORDB_USERNAME` and `FALKORDB_PASSWORD` empty unless you configured auth on FalkorDB.

### 2c. Generate a public domain

In the FastAPI service settings → **Networking** → **Generate Domain**. You will get a URL like:
`https://ai-career-mentor-backend.up.railway.app`

Copy this URL — you need it for the frontend.

### 2d. Seed the graph database

After the service is running, bootstrap the FalkorDB graph once:

Option A — from your local machine:
```powershell
# Set FALKORDB_HOST to the temporary public URL if you expose FalkorDB publicly for seeding,
# OR use Railway CLI to run a one-off command:
railway run --service <your-backend-service-name> python -m backend.database.setup
```

Option B — via the Railway shell:
1. Open the backend service in Railway → **Shell** tab.
2. Run: `python -m backend.database.setup`

> If FalkorDB is unreachable (e.g. private networking delay), the backend will automatically activate the `InMemoryGraph` fallback with seed data. You can trigger re-seeding by restarting the service after FalkorDB is healthy.

---

## Part 3 — Deploy Streamlit Frontend on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**.
3. Choose your repository and set:
   - **Branch:** `main` (or your default branch)
   - **Main file path:** `frontend/app.py`
4. Click **Advanced settings** → **Secrets**, and paste:

```toml
API_BASE_URL = "https://ai-career-mentor-backend.up.railway.app"
```

Replace the URL with the actual Railway public domain from Part 2c.

5. Click **Deploy**. Streamlit Cloud will install from `requirements.txt` automatically.

> Streamlit Community Cloud exposes secrets as environment variables, so `os.getenv("API_BASE_URL")` in `api_client.py` picks it up with no code changes needed.

---

## Part 4 — Verify the deployment

1. Open your Streamlit app URL.
2. Check the sidebar — it should show **"FalkorDB & FastAPI Connected"** (green badge).
3. Select a seed student profile (e.g. `seed-student-001`).
4. Try a quick demo prompt in the AI Mentor Chat tab.

### Health check endpoints

- `GET https://<railway-backend-url>/health` → `{"status": "ok"}`
- `GET https://<railway-backend-url>/` → `{"name": "AI Career Mentor", "docs": "/docs"}`
- `GET https://<railway-backend-url>/docs` → FastAPI Swagger UI

---

## Environment variables reference

### Backend (Railway)

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Google Gemini API key for AI chat |
| `GEMINI_MODEL` | No | Model name, default `gemini-2.0-flash` |
| `FALKORDB_HOST` | Yes | Railway private hostname for FalkorDB |
| `FALKORDB_PORT` | No | Default `6379` |
| `FALKORDB_GRAPH_NAME` | No | Default `career_mentor` |
| `FALKORDB_USERNAME` | No | Leave empty if no auth |
| `FALKORDB_PASSWORD` | No | Leave empty if no auth |
| `APP_ENV` | No | Set to `production` |

### Frontend (Streamlit Community Cloud Secrets)

| Variable | Required | Description |
|---|---|---|
| `API_BASE_URL` | Yes | Full HTTPS URL of your Railway backend |

---

## Troubleshooting

**Backend shows "Using seeded in-memory graph" in logs**
→ FalkorDB is unreachable. Check `FALKORDB_HOST` matches the Railway private service name exactly.

**Streamlit shows "Backend Offline"**
→ The `API_BASE_URL` secret is missing or wrong, or the Railway backend service is not running.

**Chat returns 503**
→ `GEMINI_API_KEY` is missing or invalid on the Railway backend service.

**Railway build fails**
→ Check that `nixpacks.toml` and `requirements-backend.txt` are committed and pushed to your repo.

---

## Railway CLI (optional — for power users)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Log in
railway login

# Link to your project
railway link

# Run a one-off command in the backend service context
railway run python -m backend.database.setup

# View live logs
railway logs
```
