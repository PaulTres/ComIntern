# First run

The steps you do once, on a fresh clone. Everything else is in [README.md](README.md).

## 1. Install

| Tool | Check |
|---|---|
| Docker with Compose v2.24+ (Docker Desktop, or Colima: `colima start --cpu 4 --memory 8`) | `docker compose version` |
| [Ollama](https://ollama.com/download), running | `curl http://localhost:11434/api/version` |
| [uv](https://docs.astral.sh/uv/) (installs Python 3.14 itself) | `uv --version` |
| Node.js 22+ and npm | `node --version` |

Disk and memory: about 12 GB free and 16 GB RAM.

## 2. Pull the chat model

```bash
ollama pull gemma4:12b
```

With less than 16 GB RAM, pull `llama3.2:3b` instead and set `LLM__MODEL_NAME=llama3.2:3b` in `.env` (step 3).

## 3. Create `.env`

```bash
cp .env.example .env
```

Replace `JWT__SECRET_KEY` in `.env` with the output of:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Nothing else in `.env` needs changing.

## 4. Start it

Pick one.

**A. All in Docker:**

```bash
docker compose up --build
```

The first start takes several minutes: it builds the images, creates the tables, loads the catalog and
downloads the embedding model (about 1 GB).

**B. API and frontend on your machine (for development):**

```bash
uv sync
docker compose -f dev/docker-compose.yml up -d
uv run alembic upgrade head
uv run comintern-seed
uv run comintern
```

`comintern-seed` downloads the embedding model (about 1 GB) the first time. In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

## 5. Use it

Open http://localhost:3000 and sign in with the demo account that the seed step created:

| Field | Value |
|---|---|
| Email | `demo@comintern-demo.eu` |
| Password | `comintern-demo` |
| Company | Demo Software SRL, a 120-person managed IT services company in Romania and Germany |

The demo company has already answered the questionnaire, so 11 regulations apply to it and you can go
straight to the dashboard, the checklists and the assistant. To try the questionnaire yourself, create
your own account with **Create Account** (any normal-looking email, 8 or more characters of password;
nothing is ever sent to the email).

The seed creates the demo account only if it does not exist yet, so your changes to it are kept. Its
values come from `DEMO_ACCOUNT__*` in `.env`; the password is public, so set
`DEMO_ACCOUNT__ENABLED=false` anywhere but your own machine.

| What | Where |
|---|---|
| The app | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Qdrant dashboard | http://localhost:6333/dashboard |
| Database client | `localhost:5432`, database, user and password all `comintern` |

## After the first run

| Option | Every later start |
|---|---|
| A | `docker compose up` |
| B | `docker compose -f dev/docker-compose.yml up -d`, `uv run comintern`, and `npm run dev` in `frontend/` |

Run `uv run alembic upgrade head` again only after pulling a new migration, and `uv run comintern-seed`
only after the catalog or `regulation_texts/` changed.

## Where the embedding model comes from

The assistant needs an embedding model to search the regulations. It is **not** an Ollama model:
[FastEmbed](https://github.com/qdrant/fastembed) downloads it by itself (about 1 GB, from Hugging Face,
free) the first time `comintern-seed` or the API starts, and reuses it afterwards.

| | Option A (Docker) | Option B (on your machine) |
|---|---|---|
| Downloaded into | Docker volume `comintern_models` (`/opt/models/fastembed` in the containers) | `.cache/fastembed/` in the repository (ignored by git) |
| Set by | `EMBEDDINGS__CACHE_DIRECTORY` in `docker-compose.yml` | `EMBEDDINGS__CACHE_DIRECTORY` in `.env` |

The code is `src/comintern/embedding/fastembed_embedding.py`: `TextEmbedding(model_name, cache_dir)`
downloads the model `EMBEDDINGS__MODEL_NAME` when it is not in the cache yet.

## Delete everything

Stop and remove the containers, their networks, their data and their images, from the repository root.

The whole stack (option A):

```bash
docker compose down --volumes --rmi all --remove-orphans
```

The development PostgreSQL and Qdrant (option B):

```bash
docker compose -f dev/docker-compose.yml down --volumes --rmi all --remove-orphans
```

`down` stops and removes the containers and networks; `--volumes` deletes the database, the vectors,
the uploads and the Docker copy of the embedding model; `--rmi all` deletes the images, which are
downloaded or built again on the next start.

The embedding model and the uploads on your machine (option B):

```bash
rm -rf .cache/fastembed data
```

The chat model in Ollama (and the small one, if you pulled it):

```bash
ollama rm gemma4:12b
```

```bash
ollama rm llama3.2:3b
```

Check that nothing is left:

```bash
docker ps -a --filter name=comintern
```

```bash
docker volume ls --filter name=comintern
```

```bash
ollama list
```

To stop without deleting anything, use `docker compose stop` (or `docker compose -f dev/docker-compose.yml stop`);
`docker compose up` brings everything back with the data intact.
