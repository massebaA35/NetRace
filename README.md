# NETRA

**Network Exploration, Threat & Relationship Analysis**

NETRA is an investigator-assistance prototype for exploring synthetic crime and intelligence records. It connects entities, relationships, alerts, evidence references, explainable graph metrics, human review, and evidence integrity verification in one focused workspace.

> This is an investigative decision-support system. Analytical scores, graph relationships, and AI-generated insights are not proof of criminal activity or guilt. Investigators must independently verify findings using authorized evidence and applicable procedures.

## Included prototype

- Dark, responsive investigator dashboard with live FastAPI data
- CASE-001 / Operation Nexus synthetic investigation with persons, organizations, phones, locations, relationships, alerts, communities, and evidence
- NetworkX degree, betweenness, closeness, and PageRank metrics
- Rule-based NLP extraction fallback and evidence spans
- Search, entity profile drawer, supporting evidence, explainable observation, and priority score
- Document upload validation for TXT, CSV, JSON, and PDF extensions
- Human-in-the-loop relationship review endpoint
- SHA-256 evidence hash response and verification endpoint
- Report generation endpoint with limitations and disclaimer
- Descriptive analysis of `crime_dataset.xlsx` with record counts, closure rate, city/domain distributions, demographics, weapons, hourly distribution, and monthly trend
- Optional PostgreSQL and Neo4j services through Docker Compose; the demo works with the in-memory fallback

## Run locally

**Setup environment:**

```powershell
cp .env.example .env
# Edit .env if needed (defaults work for local development)
```

**Backend:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:PYTHONPATH = "backend"
uvicorn app.main:app --app-dir backend --reload --port 8000
```

**Frontend** (in another terminal):

```powershell
npm.cmd install --prefix frontend
npm.cmd run dev --prefix frontend
```

Open `http://localhost:5173`. API docs are at `http://localhost:8000/docs`.

**Demo credentials:**
- Username: `admin`, `investigator`, or `analyst`
- Password: `netra-demo`

## Docker

`docker compose up --build` starts the frontend at `http://localhost:5173` and backend at `http://localhost:8000`. Add `--profile full` to start the optional PostgreSQL and Neo4j services.

## API highlights

**Dashboard & Cases:**
- `GET /api/dashboard` - Get dashboard KPIs and alerts
- `GET /api/cases` - List all investigation cases
- `GET /api/cases/{case_id}` - Get case details

**Graph & Entities:**
- `GET /api/graph/case/CASE-001?depth=2` - Get case entity graph
- `GET /api/entities?q=P014` - Search entities
- `GET /api/entities/{entity_id}` - Get entity profile
- `GET /api/entities/{entity_id}/notes` - Get entity notes

**Annotations & Review:**
- `POST /api/entities/{entity_id}/notes` - Add note to entity
- `POST /api/relationships/{rel_id}/notes` - Add note to relationship
- `GET /api/relationships/{rel_id}/notes` - Get relationship notes
- `GET /api/review` - Get pending relationships for review
- `POST /api/relationships/review` - Record review decision

**Evidence & Reports:**
- `POST /api/documents/upload` - Upload evidence documents
- `POST /api/evidence/{evidence_id}/verify` - Verify evidence integrity
- `POST /api/reports/generate` - Generate case report
- `GET /api/crime-analysis` - Analyze crime dataset

## New Features (Latest Release)

**Case Notes & Annotations System**
Investigators can now add private notes and annotations to entities and relationships:
- Add priority-tagged notes (low/normal/high) to entities
- Annotate relationship evidence with investigator insights
- Notes are persisted and retrievable for case documentation

**Configuration Management**
- Centralized environment configuration via `.env` file
- Support for multiple deployment modes (development, production, testing)
- Configurable CORS, JWT, database, and logging settings
- See `.env.example` for available options

**Improved Error Handling & Validation**
- PDF upload validation with magic byte detection
- Safe metric data type handling
- Consistent timestamp formatting across APIs
- Sorted timeline events by timestamp

**Refactored Codebase**
- Extracted hardcoded data into `app/data.py` for maintainability
- Cleaner `main.py` architecture
- Better separation of concerns

## Architecture and future scope

The API currently uses a deterministic synthetic fallback so the presentation works without external databases or AI providers. The `backend/app/ai` package owns extraction, graph metrics, and explanations. Neo4j, PostgreSQL, spaCy, transformer extraction, JWT persistence, audit event storage, PDF reports, and a permissioned ledger adapter can be integrated behind these boundaries for production hardening.

## Configuration

See `.env.example` for all available environment variables:
- `NETRA_ENV`: Environment mode (development/production/testing)
- `BACKEND_PORT`: API server port (default: 8000)
- `CORS_ORIGINS`: Allowed frontend origins
- `JWT_SECRET`: Secret key for token generation
- `DATABASE_URL`: PostgreSQL connection string (optional)
- `NEO4J_URI`: Neo4j connection URI (optional)
- `INTEGRATION_MODE`: Data source (synthetic/database/neo4j)
- `LOG_LEVEL`: Logging verbosity (DEBUG/INFO/WARNING/ERROR)
