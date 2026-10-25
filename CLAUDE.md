# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

**Infra Mind** — an AI infrastructure advisory platform. A user submits an assessment
(business context, workloads, compliance, budget); a set of specialised LLM agents
analyses it and produces multi-cloud (AWS / Azure / GCP) recommendations, cost
forecasts, compliance findings and reports.

- `src/infra_mind/` — FastAPI backend (Python 3.11, MongoDB via Beanie/Motor, Redis, Celery)
- `frontend-react/` — Next.js 15 App Router frontend (React 19, TypeScript, MUI v6, Redux Toolkit)
- `tests/` — backend pytest suite; frontend Jest tests live in `frontend-react/src/**/__tests__/`
- `k8s/`, `nginx/`, `redis/`, `docker-compose*.yml`, `Dockerfile` — deployment
- `scripts/` — ops scripts; `scripts/dev/` — local dev utilities (seed data, DB audit, demo run)
- `docs/` — operational docs; `docs/archive/` — historical notes, not maintained

## Commands

```bash
# Full stack (MongoDB, Redis, API on :8000, frontend on :3000)
cp .env.example .env            # then fill in LLM keys
docker-compose up -d

# Backend
pip install -e ".[dev]"
uvicorn src.infra_mind.main:app --reload       # API docs at http://localhost:8000/docs
pytest tests/                                    # unit tests
RUN_INTEGRATION_TESTS=1 pytest tests/           # also run @pytest.mark.integration tests (skipped by default)

# Frontend (run inside frontend-react/)
npm ci
npm run dev
npm run build
npm test            # Jest
npm run lint
npm run type-check  # must stay at 0 errors; next build also enforces types and lint
```

`make help` lists Makefile targets (dev-up, test, lint, deploy-*, db-*).

## Backend architecture

- **Entry point:** `src/infra_mind/main.py` — app factory and lifespan (DB init), mounts the API
  under `/api` and a WebSocket at `/ws` that clients use to subscribe to workflow/assessment progress.
- **Routing:** `api/routes.py` composes `api/endpoints/*.py` into `/api/v1/...` and `/api/v2/...`.
  The frontend uses v2 for assessments.
- **Assessment pipeline:** `POST /api/v2/assessments/{id}/start` → `start_assessment_workflow`
  in `api/endpoints/assessments.py` (background task) → `workflows/parallel_assessment_workflow.py`.
  In `assessments.py` the name `AssessmentWorkflow` is an alias for `ParallelAssessmentWorkflow`.
  Phases: data validation → 10 agents in parallel (`asyncio.gather`) → synthesis →
  professional services (compliance engine, cost modelling, reports). Failed or timed-out agents
  are marked `failed`/`timeout` and contribute no recommendations.
- `workflows/assessment_workflow.py` is the older sequential workflow (exported as
  `SequentialAssessmentWorkflow`). It substitutes generic placeholder recommendations when an agent
  can't run; these are tagged `fallback: True` and listed in `synthesis_metadata.fallback_agents`.
- **Agents:** `agents/` — one module per `AgentRole` (CTO, cloud engineer, research, MLOps,
  infrastructure, compliance, AI consultant, web research, simulation, chatbot, report generator),
  all built on `agents/base.py`.
- **LLM layer:** `llm/` — provider abstraction (OpenAI, Azure OpenAI, Gemini), prompt management and
  sanitisation, token budgets, cost tracking.
- **Cloud:** `cloud/` — provider clients behind `cloud/unified.py`.
- **Models:** `models/` are Beanie documents (MongoDB); `schemas/` and `forms/` handle request validation.
- **Config:** `core/config.py` — Pydantic settings, env prefix `INFRA_MIND_`. Use `get_settings()`.
- `core/` holds cross-cutting concerns (auth/JWT/RBAC, rate limiting, caching, metrics, security
  middleware). Several caching modules overlap; check for an existing helper before adding one.

## Frontend architecture

- App Router pages in `frontend-react/src/app/<route>/page.tsx`; mostly client components.
- API access through `src/services/api.ts`; state in `src/store/slices/`; path alias `@/*` → `src/*`.
- The root layout wraps pages in `<Suspense>` because many pages call `useSearchParams()`.
- `next.config.ts` rewrites `/api/*` to `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

## Conventions and gotchas

- Root `.gitignore` ignores `*.json` (to keep cloud credential files out of git) with exceptions
  for `package.json`, `package-lock.json` and `tsconfig.json`. A new JSON file you want
  committed needs its own exception.
- Never commit real secrets. `.env`, `.env.*` are ignored; only `.env.example` and
  `.env.*.example` templates are tracked. `k8s/secrets*.yaml` contain `CHANGE-ME` placeholders only.
- Tests that need live MongoDB / a running API are opt-in: `@pytest.mark.integration` tests run only with
  `RUN_INTEGRATION_TESTS=1`; some modules use their own flags (`RUN_WORKFLOW_EXECUTION_TESTS=1`,
  `RUN_ADDITIONAL_FEATURES_TESTS=1`).
- Don't add new one-off scripts or status/summary markdown files at the repo root; put utilities
  in `scripts/dev/` and docs in `docs/`.
