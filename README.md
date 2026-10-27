# ComIntern

Compliance readiness for small and medium companies in the **EU, Germany and Romania**, built by
team *DigitalEconomyCybersecurityTeam1* for the Digital Economy course.

SMEs without dedicated compliance staff face NIS2, GDPR, the AI Act and a dozen national laws at once.
ComIntern tells a company which regulations apply and why, what each one asks for, how far it is, and
what to do next: a cheap first step before paying a consultant.

> ComIntern gives guidance, not legal advice. The regulation catalog and the updates feed are curated by
> hand, and the assistant's answers come from a local language model and can be wrong. Check thresholds,
> dates and obligations against the official sources linked in the app.

## What it does

1. **Onboarding questionnaire**: size, sector, countries, data, AI and finance questions.
2. **Applicability engine**: which of 18 regulations apply and why (GDPR, NIS2, AI Act, DORA, CSRD,
   CSDDD, Whistleblowing, AML; BDSG, NIS2/BSIG, LkSG, HinSchG, GwG; Law 190/2018, OUG 155/2024,
   Law 361/2022, Law 129/2019, RO e-Factura).
3. **Requirement checklists**: a status and a note per requirement, and evidence documents.
4. **Dashboard**: a weighted score overall and per regulation, open tasks, recent evidence.
5. **Regulatory updates feed**: deadlines and amendments for your regulations.
6. **Compliance assistant**: a chat that streams its answers.
   - The **knowledge agent** answers what a regulation says, from the ComIntern catalog, the official
     texts in `regulation_texts/` and your uploaded evidence, and lists its sources.
   - The **regulation agent** (one per applicable regulation, e.g. "GDPR agent") reads your checklist
     and evidence for that regulation and tells you what to do next and which document would prove it.
   - An **orchestrator** decides which agent answers each message. Answers can be written for
     management, IT or legal readers.

Everything runs locally and costs nothing: PostgreSQL and Qdrant in Docker, the embedding model
(FastEmbed) inside the API, and the chat model in [Ollama](https://ollama.com) on your machine.

## How it fits together

```
 Browser ──> frontend (Next.js, :3000) ──> api (FastAPI, :8000) ──┬──> PostgreSQL   users, companies, checklists, documents, conversations
                                                                  ├──> Qdrant       passages of the catalog, official texts and evidence
                                                                  └──> Ollama       chat model (runs natively on your machine, :11434)
```

| Folder | What is in it |
|---|---|
| `src/comintern/` | The API (Python package `comintern`) |
| `src/comintern/api/` | App factory, lifespan (builds everything once), dependencies, routes under `/api/v1` |
| `src/comintern/services/`, `repositories/`, `schemas/`, `models/` | Business logic → database access → ORM tables; `models/` holds the request/response models and enums |
| `src/comintern/agents/` | The orchestrator, the knowledge agent and the regulation agent |
| `src/comintern/rules/` | The applicability rule engine and the scoring (pure functions) |
| `src/comintern/catalog/` | The YAML data: questionnaire, regulations with their requirements, updates feed |
| `src/comintern/llm/`, `embedding/`, `vector_store/` | One factory each: the provider is chosen in `.env` |
| `alembic/` | Database migrations |
| `tests/` | Pytest tests; they need neither Docker nor Ollama |
| `frontend/` | The Next.js web app |
| `regulation_texts/` | Official regulation texts for the assistant (see its README) |
| `dev/docker-compose.yml` | Only PostgreSQL and Qdrant, for local development |
| `docker-compose.yml` | The whole stack |

## Before you start

| You need | Why | Check |
|---|---|---|
| Docker with Compose v2.24 or newer (Docker Desktop, or [Colima](https://github.com/abiosoft/colima) on macOS) | PostgreSQL, Qdrant, and the whole stack | `docker compose version` |
| [Ollama](https://ollama.com/download) | The chat model | `ollama --version` |
| About 12 GB of free disk and 16 GB of RAM for the default model | `gemma4:12b` is 7.4 GB; the embedding model is 1 GB | |

Only for running the API and the frontend outside Docker:

| You need | Check |
|---|---|
| [uv](https://docs.astral.sh/uv/) (it installs Python 3.14 for you) | `uv --version` |
| Node.js 22 or newer and npm | `node --version` |

With Colima, give the VM enough memory: `colima start --cpu 4 --memory 8`.

### Get the chat model

```bash
ollama pull gemma4:12b
```

Ollama must be running (the desktop app, or `ollama serve` in a terminal). Check it with
`curl http://localhost:11434/api/version`. On a laptop with less than 16 GB of RAM, use the smaller
model instead: `ollama pull llama3.2:3b`, then set `LLM__MODEL_NAME=llama3.2:3b` in `.env`. The model
must support tool calling: `gemma4:12b` and `llama3.2:3b` do.

## Option A: run everything in Docker (easiest)

```bash
cp .env.example .env
```

Put a random value in `JWT__SECRET_KEY` in `.env`; this prints one:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Then start the stack:

```bash
docker compose up --build
```

Open http://localhost:3000, create an account and fill in the questionnaire. The API documentation is
at http://localhost:8000/docs.

What happens on start, in order: PostgreSQL and Qdrant start, `qdrant-init` creates the vector
collection, `migrate` creates the tables, `seed` loads the regulation catalog and indexes it for the
assistant, then `api` and `frontend` start. **The first start takes several minutes**: the images are
built and `seed` downloads the embedding model (about 1 GB) into a Docker volume. Later starts reuse it.

```bash
docker compose ps                # what is running
docker compose logs -f api       # the API's log
docker compose down              # stop; the data stays
docker compose down -v           # stop and delete all data (database, vectors, uploads, model cache)
```

The containers reach Ollama on your machine through `host.docker.internal`. If Ollama runs elsewhere,
set `DOCKER_OLLAMA_URL` in `.env`.

## Option B: run the API and the frontend on your machine (for development)

Use this when you change the code: the API reloads on save and you can use a debugger.

```bash
uv sync                                         # creates .venv with Python 3.14 and every dependency
cp .env.example .env                            # then set JWT__SECRET_KEY as in option A
docker compose -f dev/docker-compose.yml up -d  # PostgreSQL on localhost:5432, Qdrant on localhost:6333
uv run alembic upgrade head                     # create the tables
uv run comintern-seed                           # load the catalog and index it (first run downloads 1 GB)
uv run comintern                                # the API on http://127.0.0.1:8000
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev                                     # http://localhost:3000
```

The frontend calls the API at `http://localhost:8000` unless `NEXT_PUBLIC_API_URL` says otherwise.

The `Makefile` wraps the same commands; `make help` lists them:

| Command | Does |
|---|---|
| `make sync` | `uv sync` |
| `make infra` / `make infra-down` | Start / stop the dev PostgreSQL and Qdrant |
| `make migrate` | `uv run alembic upgrade head` |
| `make seed` | `uv run comintern-seed` |
| `make run` | `uv run comintern` |
| `make dev` | The API with hot reload |
| `make test` / `make lint` / `make format` | Pytest / ruff check / ruff format |
| `make up` / `make down` | The whole stack in Docker |

On Windows without `make`, run the commands in the right column directly (WSL 2 is the easiest
setup; the project has not been tested on native Windows).

## Configuration

Every setting is in `.env`; `.env.example` documents each one. Nested keys use `__`:
`LLM__MODEL_NAME` is the `model_name` of the `llm` group in `src/comintern/configuration/config.py`.
`.env` is never committed.

| Setting | Default | What it changes |
|---|---|---|
| `LLM__MODEL_NAME` | `gemma4:12b` | The Ollama model; it must support tool calling |
| `LLM__REASONING` | `false` | `true` lets a thinking model think first: better on hard questions, about ten times slower |
| `LLM__MAX_TOKENS` | `1024` | Longest answer |
| `EMBEDDINGS__MODEL_NAME` / `EMBEDDINGS__SIZE` | `paraphrase-multilingual-mpnet-base-v2` / `768` | The embedding model (English, German, Romanian); changing it means a new Qdrant collection of the new size and `make seed` |
| `KNOWLEDGE_AGENT__TOP_K`, `__SIMILARITY_SCORE` | `6`, `0.3` | How many passages the assistant reads, and how close they must be |
| `DOCUMENTS__MAX_FILE_SIZE_BYTES` | 25 MB | Largest evidence upload |
| `JWT__EXPIRE_MINUTES` | `1440` | How long a login lasts |

## Adding content

- **Official regulation texts** for the assistant: put PDF, DOCX, TXT or MD files in
  `regulation_texts/<REGULATION_CODE>/` and run `make seed` (see `regulation_texts/README.md`).
- **A regulation**: add an entry to `src/comintern/catalog/regulations/{eu,de,ro}.yaml`, then run
  `make seed`. Each entry has `applicability.triggers` (conditions on the questionnaire answers, each
  with a readable `reason`) and `requirements` (`key`, `title`, `description`, `reference`, `weight`
  1 to 3, `evidence_hint`). Seeding is idempotent, keyed by `code` and `key`.
- **A question**: edit `src/comintern/catalog/questionnaire.yaml`.
- **An update**: edit `src/comintern/catalog/updates.yaml`, then `make seed`.

Conditions are `{field, op, value}` (ops: `eq`, `ne`, `truthy`, `gt`, `gte`, `lt`, `lte`, `in`,
`contains`, `contains_any`) or the combinators `all`, `any`, `not`. Besides the answers, the derived
fields `in_eu`, `size_class` (EU SME definition), `medium_or_larger` and `nis2_annex` (`I` or `II`) are
available (`src/comintern/rules/applicability.py`).

### Scoring

Per regulation: Σ(weight × status value) / Σ(weight), where compliant = 1, in progress = 0.5,
not started = 0, and not-applicable requirements are left out. The overall score weights each regulation
by its total requirement weight. Levels: below 50 at risk, 50 to 79 needs work, 80 and above audit-ready.

## Tests and checks

```bash
uv run pytest            # 21 tests; no Docker, no Ollama
uv run ruff check .
uv run ruff format --check .
cd frontend && npm run lint && npm run build
```

## Database migrations

The tables come only from Alembic migrations, never from `create_all`.

```bash
uv run alembic upgrade head                                     # apply
uv run alembic revision --autogenerate -m "add the x column"    # after changing src/comintern/schemas/
uv run alembic check                                            # models and database agree
```

Read every generated migration before committing it.

## The API

All routes are under `/api/v1`; open `/docs` for the full contract. Sign-in uses a bearer token from
`/auth/login` or `/auth/register`.

| Area | Routes |
|---|---|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Company | `GET /questionnaire`, `GET`/`PUT /company`, `GET /company/regulations` |
| Compliance | `GET /regulations/{code}`, `PUT /requirements/{id}/status`, `GET /dashboard`, `GET /updates`, `GET /catalog` |
| Evidence | `GET`/`POST /documents`, `GET /documents/{id}/download`, `DELETE /documents/{id}` |
| Assistant | `POST /chat/stream` (server-sent events: `progress`, `delta`, `payload`, `final`, `error`), `GET /conversations`, `GET /conversations/{id}/messages` |
| Health | `GET /health` |

Errors always look like `{"code": "DOCUMENT_NOT_FOUND", "detail": "Document not found"}`.

## Troubleshooting

| Problem | Fix |
|---|---|
| A port is already taken (5432, 6333, 8000 or 3000) | Stop the other program, or set `POSTGRES_PORT`, `QDRANT_PORT` (dev stack), `API_PORT`, `FRONTEND_PORT` (full stack) in `.env` and update the URLs that use them |
| The assistant answers "could not finish the answer" | Ollama is not running or the model is not pulled: `ollama list`; in Docker, check `DOCKER_OLLAMA_URL` |
| Answers are very slow | Use `llama3.2:3b`, keep `LLM__REASONING=false`, and close other heavy apps; the first answer also loads the model into memory |
| `Collection comintern not found` | The dev stack's `qdrant-init` did not run: `docker compose -f dev/docker-compose.yml up -d` again |
| The frontend says it cannot reach the API | Is the API up (`curl http://localhost:8000/api/v1/health`)? Is your frontend origin in `CORS__ORIGINS`? |
| `--mount option requires BuildKit` | You are building an old Dockerfile; pull the latest code |
| The frontend build fails with `Failed to fetch Geist from Google Fonts` or `Can't resolve '@vercel/turbopack-next/internal/font/google/font'` | The build downloads its fonts and the download failed: check your internet connection and run `docker compose build frontend` again |
| Start from scratch | `docker compose down -v`, or for the dev stack `docker compose -f dev/docker-compose.yml down -v` and delete `data/` |

## Working on the code

- Branch from `main`, open a pull request, and keep secrets out of git: `.env`, `data/` and `.cache/`
  are ignored.
- Layers point one way: route → service → repository. A service opens the database session; a
  repository never commits.
- Anything someone might configure differently (a model, a limit, a URL) belongs in the settings and in
  `.env.example`, not in the code.
