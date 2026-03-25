# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**광고판정 (AdJudge)** — AI-assisted outdoor advertising permit advisory system for Gangnam-gu civil servants. Given sign installation conditions, the system outputs a deterministic permit/report/prohibited decision with legal provisions, fees, and required documents.

Core design principle: **the rule engine is 100% deterministic (no LLM for decisions)**. LLM/RAG is used only for providing supporting legal text, not for making permit decisions.

## Development Commands

### Start all services
```bash
docker-compose up -d
```

### Backend (FastAPI, runs on :8000)
```bash
# Local dev (requires postgres running)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Or via docker with hot-reload (volume mounted)
docker-compose up backend
```

### Frontend (Next.js 14, runs on :3000)
```bash
cd frontend
npm install
npm run dev

# Build
npm run build
```

### Database setup
```bash
# Init schema (auto-run via Docker entrypoint)
# ./db/init.sql is mounted to postgres container

# Seed rules
docker exec -i adjudge-postgres psql -U adjudge adjudge < db/seed_rules.sql
```

### Ollama model setup
```bash
# Pull embedding model (required for RAG)
docker exec adjudge-ollama ollama pull nomic-embed-text
```

## Architecture

```
SignCheck/
├── backend/              # FastAPI app
│   ├── main.py           # App entry, CORS, router registration
│   ├── api/
│   │   ├── judge.py      # POST /api/v1/judge — core judgment endpoint
│   │   ├── chat.py       # POST /api/v1/chat — PrivateGPT-backed chatbot
│   │   └── admin.py      # /api/v1/admin/* — rule CRUD, logs, document ingestion
│   ├── engine/
│   │   ├── rule_engine.py    # Deterministic DB-based judgment logic
│   │   ├── fee_calculator.py # Fee calculation from fee_rule table
│   │   └── checklist.py      # Required document list from checklist_rule table
│   ├── services/
│   │   ├── rag_service.py        # pgvector similarity search via Ollama embeddings
│   │   └── privategpt_client.py  # PrivateGPT HTTP client (chat + document ingest)
│   └── db/
│       ├── __init__.py   # AsyncSession factory (DATABASE_URL env var)
│       └── models.py     # SQLAlchemy ORM models
├── frontend/             # Next.js 14 App Router
│   ├── app/page.tsx      # Main page: JudgeForm + JudgeResult + ChatBot
│   ├── components/       # JudgeForm, JudgeResult, ChatBot
│   └── lib/api.ts        # API client (NEXT_PUBLIC_API_URL)
├── db/
│   ├── init.sql          # Schema (pgvector extension + all tables)
│   └── seed_rules.sql    # Initial rule_condition/rule_effect data
└── docker-compose.yml    # postgres, ollama, backend, frontend
```

## Request Flow

`POST /api/v1/judge` pipeline:
1. **RuleEngine.judge()** — queries `rule_condition` + `rule_effect` tables in priority order → deterministic `permit`/`report`/`prohibited` decision
2. **fee_calculator** — looks up `fee_rule` table for base fee + lighting weight
3. **checklist** — looks up `checklist_rule` for required/optional documents
4. **rag_service.search()** — embeds query via Ollama → pgvector cosine similarity on `law_chunk` table → returns top-k legal provisions (non-blocking; failure is silently ignored)
5. **CaseLog** saved to DB with full input/output

## Database Schema Key Tables

- `document_master` + `provision` — law text hierarchy (national → Seoul → Gangnam-gu)
- `law_chunk` — vector-embedded chunks of provisions for RAG (768-dim, nomic-embed-text)
- `rule_condition` + `rule_effect` — judgment rules matched by priority; NULL fields = wildcard
- `fee_rule`, `checklist_rule`, `zone_rule` — supporting lookup tables
- `case_log` — audit log of every judgment request

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://adjudge:adjudge@localhost:5432/adjudge` | Backend DB |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama for embeddings |
| `PRIVATEGPT_URL` | `http://privategpt:8080` | PrivateGPT for chat |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend → backend |

## Key Design Decisions

- **Rule matching**: NULL columns in `rule_condition` act as wildcards. Rules matched by `priority ASC` — lower number = higher priority. Default fallback is `report` + 소심의 when no rule matches.
- **Two RAG systems**: `rag_service.py` uses pgvector + Ollama directly (for judgment provisions). `privategpt_client.py` uses PrivateGPT (for the chatbot). They are independent.
- **Admin rule management**: Rules are updated via `/api/v1/admin/rules` CRUD endpoints, not code changes — this is intentional per the PRD.
- **Tehranro special case**: Hard-coded in `rule_engine.py` — 돌출간판 is always prohibited on Tehranro-adjacent lots regardless of other rules.

## Execution Rules

### Backlog Maintenance

- When implementing work derived from [`docs/sign-rule-expansion-plan.md`](./docs/sign-rule-expansion-plan.md), update the backlog document as part of the same task flow.
- At minimum, reflect one of the following after each completed or materially progressed task:
  - task status (`todo`, `in_progress`, `done`, `blocked`)
  - implementation note with touched files
  - blocker or scope change
- Do not leave backlog updates as a separate follow-up item unless explicitly requested.

### Progress Reporting

- During multi-step implementation, provide short progress updates tied to the active backlog task IDs when possible.
- If task scope changes during implementation, update the backlog first, then continue coding.

### Parallel Work

- Prefer parallelizing independent exploration, file reads, validation, and test runs when the work can safely proceed in parallel.
- Keep code edits coordinated through a single final integration path to avoid conflicting changes.
- If a request can be decomposed into independent backlog tasks, execute discovery and verification in parallel, then merge results into the main branch of work.
