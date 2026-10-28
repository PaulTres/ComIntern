# ComIntern

Compliance readiness for small and medium companies in the **EU, Germany and Romania**, built by
team *DigitalEconomyCybersecurityTeam1* for the Digital Economy course.

Companies without dedicated compliance staff face NIS2, GDPR, the AI Act and a dozen national laws at
once, and usually find out what applies to them only when a customer audit, a deadline or a fine forces
the question. ComIntern answers that question first: which regulations apply and why, what each one asks
for, how far the company is, and what to do next. It is meant as the cheap first step before paying a
consultant.

> ComIntern gives guidance, not legal advice. The regulation catalog and the updates feed are curated by
> hand, and the assistant's answers come from a local language model and can be wrong. Check thresholds,
> dates and obligations against the official sources linked in the app.

**New here?** [FIRST_RUN.md](FIRST_RUN.md) has only the steps for the very first start.

## Contents

- [What it does](#what-it-does)
- [What it costs: nothing](#what-it-costs-nothing)
- [How it fits together](#how-it-fits-together)
- [Before you start](#before-you-start)
- [Option A: run everything in Docker](#option-a-run-everything-in-docker-easiest)
- [Option B: run the API and the frontend on your machine](#option-b-run-the-api-and-the-frontend-on-your-machine-for-development)
- [Official regulation texts for the assistant](#official-regulation-texts-for-the-assistant)
- [Using the app](#using-the-app)
- [Configuration](#configuration)
- [Adding content](#adding-content)
- [The frontend](#the-frontend)
- [Tests and checks](#tests-and-checks)
- [Database migrations](#database-migrations)
- [The API](#the-api)
- [Troubleshooting](#troubleshooting)
- [Working on the code](#working-on-the-code)

## What it does

1. **Onboarding questionnaire**: six short steps about countries, size, sector, data and technology,
   finance and supply chain.
2. **Applicability engine**: decides which of 18 regulations apply and writes down why.
   - EU: GDPR, NIS2, AI Act, DORA, CSRD, CSDDD, Whistleblowing Directive, AML Regulation
   - Germany: BDSG, NIS2 (NIS2UmsuCG / BSIG), LkSG, HinSchG, GwG
   - Romania: Law 190/2018, NIS2 (OUG 155/2024), Law 361/2022, Law 129/2019, RO e-Factura
3. **Requirement checklists**: every regulation is broken into requirements, each with a priority
   (1 to 3), a legal reference and a hint at the typical evidence. You set a status, write a note and
   attach documents.
4. **Dashboard**: a weighted readiness score overall and per regulation, the next steps ordered by
   priority, recent evidence and relevant updates.
5. **Regulatory updates**: new deadlines, amendments and guidance for the regulations that apply to you.
6. **Compliance assistant**: a chat that streams its answers as they are written.
   - The **knowledge agent** answers what a regulation says, from the ComIntern catalog, the official
     texts in `regulation_texts/` and your uploaded evidence, and lists its sources.
   - A **regulation agent** (one per applicable regulation, for example the "GDPR agent") reads your
     checklist and evidence for that regulation and tells you what to do next and which document would
     prove it.
   - An **orchestrator** decides which agent answers each message. Answers can be written in plain
     language or for management, IT or legal readers.

## What it costs: nothing

Every part is free and runs on your own computer. There are no API keys, no paid cloud services and no
per-question fees. The only cost is your laptop's disk, memory and electricity.

| Part | What it is | Where it runs | Cost |
|---|---|---|---|
| PostgreSQL 16 | Database: users, companies, checklists, documents, conversations | Docker container `db` | Free, open source |
| Qdrant 1.19 | Vector database: the passages the assistant searches | Docker container `qdrant` | Free, open source, self-hosted (no Qdrant Cloud) |
| FastAPI, LangChain, LangGraph, deepagents | The API and the agents | Docker container `api` (or `uv run comintern`) | Free, open source libraries |
| FastEmbed + `paraphrase-multilingual-mpnet-base-v2` | Embedding model: turns text into vectors, in English, German and Romanian | **Inside the API**, on the CPU; downloaded once from Hugging Face (about 1 GB) | Free |
| Ollama + `gemma4:12b` (or `llama3.2:3b`) | Chat model: writes the answers | **On your machine, outside Docker**, so it can use your GPU | Free |
| Next.js | The web app | Docker container `frontend` (or `npm run dev`) | Free, open source |
| Docker | Runs the containers | Your machine | [Colima](https://github.com/abiosoft/colima) is free and open source; Docker Desktop is free for personal use, education and small companies (see its licence) |

Ollama hosts only the chat model. The embedding model is not an Ollama model: FastEmbed downloads it
from Hugging Face the first time `seed` or the API runs, into `.cache/fastembed/` (option B) or the
Docker volume `comintern_models` (option A). [FIRST_RUN.md](FIRST_RUN.md#where-the-embedding-model-comes-from)
has the details.

## How it fits together

```
 Browser ──> frontend (Next.js, :3000) ──> api (FastAPI, :8000) ──┬──> PostgreSQL (:5432)   app data
                                                                  ├──> Qdrant (:6333)       passages of the catalog, official texts, evidence
                                                                  └──> Ollama (:11434)      chat model, on your machine
                                           the api also holds the embedding model (FastEmbed)
```

**One chat turn:** the frontend posts the question to `POST /api/v1/chat/stream`. The orchestrator
chooses an agent. The knowledge agent searches Qdrant (public passages plus your own company's evidence
only), then streams an answer with its sources; a regulation agent also reads your checklist for that
regulation. The answer arrives as server-sent events (`progress`, `delta`, `payload`, `final`, `error`)
and is saved with the conversation in PostgreSQL.

**The knowledge base:** `comintern-seed` cuts the catalog and every file in `regulation_texts/` into
passages, embeds them with FastEmbed and stores them in one Qdrant collection. Each evidence upload is
indexed the same way, tagged with its company, so one company never sees another's documents.

| Folder | What is in it |
|---|---|
| `src/comintern/` | The API (Python package `comintern`) |
| `src/comintern/api/` | App factory, lifespan (builds everything once), dependencies, routes under `/api/v1` |
| `src/comintern/services/`, `repositories/`, `schemas/`, `models/` | Business logic → database access → ORM tables; `models/` holds the request and response models and the enums |
| `src/comintern/agents/` | The orchestrator, the knowledge agent and the regulation agent, with their prompts |
| `src/comintern/rules/` | The applicability rule engine and the scoring (pure functions) |
| `src/comintern/catalog/` | The YAML data: questionnaire, regulations with their requirements, updates feed |
| `src/comintern/llm/`, `embedding/`, `vector_store/` | One factory each: the provider is chosen in `.env` |
| `alembic/` | Database migrations |
| `tests/` | Pytest tests; they need neither Docker nor Ollama |
| `frontend/` | The Next.js web app |
| `regulation_texts/` | Official regulation texts for the assistant (empty until you add them) |
| `dev/docker-compose.yml` | Only PostgreSQL and Qdrant, for local development |
| `docker-compose.yml` | The whole stack |

## Before you start

| You need | Why | Check |
|---|---|---|
| Docker with Compose v2.24 or newer (Docker Desktop, or Colima on macOS) | PostgreSQL, Qdrant and the whole stack | `docker compose version` |
| [Ollama](https://ollama.com/download), running | The chat model | `curl http://localhost:11434/api/version` |
| About 12 GB of free disk and 16 GB of RAM for the default model | `gemma4:12b` is 7.4 GB; the embedding model is 1 GB | |

Only for running the API and the frontend outside Docker (option B):

| You need | Check |
|---|---|
| [uv](https://docs.astral.sh/uv/) (it installs Python 3.14 for you) | `uv --version` |
| Node.js 22 or newer and npm | `node --version` |

With Colima, give the VM enough memory: `colima start --cpu 4 --memory 8`.

### Get the chat model

```bash
ollama pull gemma4:12b
```

Ollama must be running: the desktop app, or `ollama serve` in a terminal. On a laptop with less than
16 GB of RAM, use the smaller model instead: `ollama pull llama3.2:3b`, then set
`LLM__MODEL_NAME=llama3.2:3b` in `.env`. The model must support tool calling: `gemma4:12b` and
`llama3.2:3b` do.

## Option A: run everything in Docker (easiest)

Everything except Ollama runs in containers: PostgreSQL, Qdrant, the API (with LangChain, the agents
and the embedding model) and the frontend.

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

What happens on start, in order:

1. `db` (PostgreSQL) and `qdrant` start.
2. `qdrant-init` creates the vector collection, then exits.
3. `migrate` creates or updates the tables, then exits.
4. `seed` loads the regulation catalog into PostgreSQL, creates the demo login, and indexes the
   catalog and `regulation_texts/` into Qdrant, then exits. It runs on every start and is safe to repeat.
5. `api` and `frontend` start.

**The first start takes several minutes**: the images are built and `seed` downloads the embedding
model (about 1 GB) into a Docker volume. Later starts reuse it.

```bash
docker compose ps                # what is running
docker compose logs -f api       # the API's log
docker compose down              # stop; the data stays
docker compose down -v           # stop and delete all data (database, vectors, uploads, model cache)
```

The containers reach Ollama on your machine through `host.docker.internal`. If Ollama runs elsewhere,
set `DOCKER_OLLAMA_URL` in `.env`.

## Option B: run the API and the frontend on your machine (for development)

Use this when you change the code: the API reloads on save and you can use a debugger. Only PostgreSQL
and Qdrant run in Docker.

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

To look at the data with a database client (PyCharm, DataGrip, DBeaver): host `localhost`, port `5432`,
database, user and password all `comintern`. Qdrant has a web UI at http://localhost:6333/dashboard.

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

## Official regulation texts for the assistant

The app works without them: the assistant then answers from the ComIntern catalog only (summaries,
requirements, references). With the official texts it can quote the law itself. None are in the
repository; download the ones you want and put each in the folder named after its regulation code:

```
regulation_texts/
  EU_GDPR/gdpr_2016_679_en.pdf
  EU_NIS2/nis2_2022_2555_en.pdf
  RO_NIS2/oug_155_2024_ro.pdf
```

| Folder | Regulation | Official source |
|---|---|---|
| `EU_GDPR` | GDPR | https://eur-lex.europa.eu/eli/reg/2016/679/oj |
| `EU_NIS2` | NIS2 | https://eur-lex.europa.eu/eli/dir/2022/2555/oj |
| `EU_AI_ACT` | AI Act | https://eur-lex.europa.eu/eli/reg/2024/1689/oj |
| `EU_DORA` | DORA | https://eur-lex.europa.eu/eli/reg/2022/2554/oj |
| `EU_CSRD` | CSRD | https://eur-lex.europa.eu/eli/dir/2022/2464/oj |
| `EU_CSDDD` | CSDDD | https://eur-lex.europa.eu/eli/dir/2024/1760/oj |
| `EU_WHISTLEBLOWING` | Whistleblowing (EU) | https://eur-lex.europa.eu/eli/dir/2019/1937/oj |
| `EU_AML` | AML (EU) | https://eur-lex.europa.eu/eli/reg/2024/1624/oj |
| `DE_BDSG` | BDSG | https://www.gesetze-im-internet.de/bdsg_2018/ |
| `DE_NIS2_BSIG` | NIS2 (DE) | https://www.bsi.bund.de/ |
| `DE_LKSG` | LkSG | https://www.gesetze-im-internet.de/lksg/ |
| `DE_HINSCHG` | HinSchG | https://www.gesetze-im-internet.de/hinschg/ |
| `DE_GWG` | GwG | https://www.gesetze-im-internet.de/gwg_2017/ |
| `RO_LAW_190_2018` | Law 190/2018 | https://www.dataprotection.ro/ |
| `RO_NIS2` | NIS2 (RO) | https://dnsc.ro/ |
| `RO_LAW_361_2022` | Law 361/2022 | https://www.integritate.eu/ |
| `RO_LAW_129_2019` | Law 129/2019 | https://www.onpcsb.ro/ |
| `RO_EFACTURA` | RO e-Factura | https://www.anaf.ro/ |

Accepted formats: `.pdf`, `.docx`, `.txt`, `.md`. Romanian laws are also on
https://legislatie.just.ro. Then index them:

- Option A: `docker compose up` again (the `seed` service reads `regulation_texts/` on every start).
- Option B: `uv run comintern-seed`.

Seeding replaces the passages of every file, so running it again is safe. Check each site's reuse terms
before committing a downloaded file; the EUR-Lex texts may be reused.

## Using the app

1. **Sign in** at http://localhost:3000 with the demo account the seed created: email
   `demo@comintern-demo.eu`, password `comintern-demo`. Its company, Demo Software SRL, has already
   answered the questionnaire. Or create your own account; each account belongs to one company.
2. **Answer the questionnaire** (new accounts). The result page lists the regulations that apply, grouped by
   jurisdiction, each with the reason why.
3. **Work through a regulation.** Open it from *Regulations*, expand a requirement, set its status,
   attach evidence and write a note (saved when you leave the field). The score updates at once.
4. **Watch the dashboard** for the overall score, the next steps and recent evidence.
5. **Ask the assistant.** Pick a regulation's agent to get advice about your own checklist, or keep
   *All Regulations* for general questions. The first answer is slower while Ollama loads the model.
6. **Change your answers** under *Company* to run the assessment again; statuses and documents are kept.

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
| `DEMO_ACCOUNT__ENABLED`, `__EMAIL`, `__PASSWORD` | `true`, `demo@comintern-demo.eu`, `comintern-demo` | The demo login `comintern-seed` creates; its company and answers are in `src/comintern/catalog/demo_company.yaml`. The password is public: turn it off anywhere but your own machine |

## Adding content

- **A regulation**: add an entry to `src/comintern/catalog/regulations/{eu,de,ro}.yaml`, then run
  `make seed`. Each entry has `applicability.triggers` (conditions on the questionnaire answers, each
  with a readable `reason`) and `requirements` (`key`, `title`, `description`, `reference`, `weight`
  1 to 3, `evidence_hint`). Seeding is idempotent, keyed by `code` and `key`.
- **A question**: edit `src/comintern/catalog/questionnaire.yaml`.
- **An update**: edit `src/comintern/catalog/updates.yaml`, then `make seed`.
- **An official text**: see [Official regulation texts](#official-regulation-texts-for-the-assistant).

Conditions are `{field, op, value}` (ops: `eq`, `ne`, `truthy`, `gt`, `gte`, `lt`, `lte`, `in`,
`contains`, `contains_any`) or the combinators `all`, `any`, `not`. Besides the answers, the derived
fields `in_eu`, `size_class` (EU SME definition), `medium_or_larger` and `nis2_annex` (`I` or `II`) are
available (`src/comintern/rules/applicability.py`).

### Scoring

Per regulation: Σ(weight × status value) / Σ(weight), where compliant = 1, in progress = 0.5,
not started = 0, and not-applicable requirements are left out. The overall score weights each regulation
by its total requirement weight. Levels: below 50 at risk, 50 to 79 needs work, 80 and above audit-ready.

## The frontend

The web app follows Apple's Human Interface Guidelines: the system font, Apple's system colors, light
and dark mode from the operating system, inset grouped lists, segmented controls, native pop-up menus
and 44-point touch targets. On wide screens there is a sidebar; on phones a tab bar at the bottom, with
the company profile behind the avatar at the top right.

| Where | What |
|---|---|
| `frontend/src/app/` | One folder per page; `(app)/` holds the signed-in pages |
| `frontend/src/app/globals.css` | The color and font tokens, light and dark |
| `frontend/src/components/list.tsx` | `Section`, `Row`, `RowText`, `IconTile`, `EmptyState`, `Loading` |
| `frontend/src/components/controls.tsx` | `SegmentedControl` and `Select` |
| `frontend/src/components/app-shell.tsx` | Sidebar, tab bar and the large-title `PageHeader` |
| `frontend/src/lib/api.ts` | The API client and the chat stream reader |

Use these building blocks for a new page instead of new styles, so the app stays consistent.

## Tests and checks

```bash
uv run pytest            # 22 tests; no Docker, no Ollama
uv run ruff check .
uv run ruff format --check .
cd frontend && npm run lint && npx tsc --noEmit
docker compose build frontend    # the production build of the frontend
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

All routes are under `/api/v1`; open http://localhost:8000/docs for the full contract. Sign-in uses a
bearer token from `/auth/login` or `/auth/register`.

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
| `Connection to localhost:5432 refused` | PostgreSQL is not running: `docker compose -f dev/docker-compose.yml up -d` (option B) or `docker compose up` (option A); with Colima, `colima start` first |
| A port is already taken (5432, 6333, 8000 or 3000) | Stop the other program, or set `POSTGRES_PORT`, `QDRANT_PORT` (dev stack), `API_PORT`, `FRONTEND_PORT` (full stack) in `.env` and update the URLs that use them |
| The assistant answers "could not finish the answer" | Ollama is not running or the model is not pulled: `ollama list`; in Docker, check `DOCKER_OLLAMA_URL` |
| Answers are very slow | Use `llama3.2:3b`, keep `LLM__REASONING=false`, and close other heavy apps; the first answer also loads the model into memory |
| `Collection comintern not found` | The dev stack's `qdrant-init` did not run: `docker compose -f dev/docker-compose.yml up -d` again |
| The frontend says it cannot reach the API | Is the API up (`curl http://localhost:8000/api/v1/health`)? Is your frontend origin in `CORS__ORIGINS`? |
| Registration says the email is not valid | Addresses on reserved domains such as `.test` are refused; use any normal-looking address, nothing is sent to it |
| `--mount option requires BuildKit` | You are building an old Dockerfile; pull the latest code |
| Start from scratch | `docker compose down -v`, or for the dev stack `docker compose -f dev/docker-compose.yml down -v` and delete `data/`; [FIRST_RUN.md](FIRST_RUN.md#delete-everything) also removes the images and the models |

## Working on the code

- Branch from `main`, open a pull request, and keep secrets out of git: `.env`, `data/` and `.cache/`
  are ignored.
- Layers point one way: route → service → repository. A service opens the database session; a
  repository never commits.
- Anything someone might configure differently (a model, a limit, a URL) belongs in the settings and in
  `.env.example`, not in the code.
- Comments explain why, not what: a name that needs a comment to be understood needs a better name.
