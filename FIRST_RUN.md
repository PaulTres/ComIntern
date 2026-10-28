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

## 6. Optional: download the official regulation texts

The assistant works without them, answering from the ComIntern catalog. With them it can quote the
law itself. Save each file at the path in the last column (paths start at the repository folder,
`ComIntern/`); the folder name must be the regulation code, the file name can be anything ending in
`.pdf`, `.docx`, `.txt` or `.md`.

**EU** (English, EUR-Lex): the link opens the PDF; save it.

| Regulation | Download | Save as |
|---|---|---|
| GDPR, Regulation (EU) 2016/679 | [PDF](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32016R0679) | `ComIntern/regulation_texts/EU_GDPR/gdpr_2016_679.pdf` |
| NIS2, Directive (EU) 2022/2555 | [PDF](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32022L2555) | `ComIntern/regulation_texts/EU_NIS2/nis2_2022_2555.pdf` |
| AI Act, Regulation (EU) 2024/1689 | [PDF](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32024R1689) | `ComIntern/regulation_texts/EU_AI_ACT/ai_act_2024_1689.pdf` |
| DORA, Regulation (EU) 2022/2554 | [PDF](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32022R2554) | `ComIntern/regulation_texts/EU_DORA/dora_2022_2554.pdf` |
| CSRD, Directive (EU) 2022/2464 | [PDF](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32022L2464) | `ComIntern/regulation_texts/EU_CSRD/csrd_2022_2464.pdf` |
| CSDDD, Directive (EU) 2024/1760 | [PDF](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32024L1760) | `ComIntern/regulation_texts/EU_CSDDD/csddd_2024_1760.pdf` |
| Whistleblowing, Directive (EU) 2019/1937 | [PDF](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32019L1937) | `ComIntern/regulation_texts/EU_WHISTLEBLOWING/whistleblowing_2019_1937.pdf` |
| AML, Regulation (EU) 2024/1624 | [PDF](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32024R1624) | `ComIntern/regulation_texts/EU_AML/amlr_2024_1624.pdf` |

**Germany** (German, gesetze-im-internet.de): the link is the PDF.

| Regulation | Download | Save as |
|---|---|---|
| BDSG | [PDF](https://www.gesetze-im-internet.de/bdsg_2018/BDSG.pdf) | `ComIntern/regulation_texts/DE_BDSG/BDSG.pdf` |
| NIS2 (DE), BSI-Gesetz 2025 | [PDF](https://www.gesetze-im-internet.de/bsig_2025/BSIG.pdf) | `ComIntern/regulation_texts/DE_NIS2_BSIG/BSIG.pdf` |
| LkSG | [PDF](https://www.gesetze-im-internet.de/lksg/LkSG.pdf) | `ComIntern/regulation_texts/DE_LKSG/LkSG.pdf` |
| HinSchG | [PDF](https://www.gesetze-im-internet.de/hinschg/HinSchG.pdf) | `ComIntern/regulation_texts/DE_HINSCHG/HinSchG.pdf` |
| GwG | [PDF](https://www.gesetze-im-internet.de/gwg_2017/GwG.pdf) | `ComIntern/regulation_texts/DE_GWG/GwG.pdf` |

**Romania** (Romanian, legislatie.just.ro): the portal has no PDF button. Open the page, click
**Forma printabilă**, then print it with **Save as PDF** (Cmd+P on macOS, Ctrl+P on Windows).

| Regulation | Page | Save as |
|---|---|---|
| Law 190/2018 (GDPR measures) | [Legea 190/2018](https://legislatie.just.ro/Public/DetaliiDocumentAfis/203151) | `ComIntern/regulation_texts/RO_LAW_190_2018/legea_190_2018.pdf` |
| NIS2 (RO), OUG 155/2024 | [OUG 155/2024](https://legislatie.just.ro/Public/DetaliiDocumentAfis/293121) | `ComIntern/regulation_texts/RO_NIS2/oug_155_2024.pdf` |
| Law 361/2022 (whistleblowers) | [Legea 361/2022](https://legislatie.just.ro/Public/DetaliiDocumentAfis/265820) | `ComIntern/regulation_texts/RO_LAW_361_2022/legea_361_2022.pdf` |
| Law 129/2019 (anti-money laundering), updated form | [Legea 129/2019](https://legislatie.just.ro/Public/DetaliiDocumentAfis/305272) | `ComIntern/regulation_texts/RO_LAW_129_2019/legea_129_2019.pdf` |
| RO e-Factura, OUG 120/2021, updated form | [OUG 120/2021](https://legislatie.just.ro/Public/DetaliiDocumentAfis/310662) | `ComIntern/regulation_texts/RO_EFACTURA/oug_120_2021.pdf` |

Then index them; nothing else changes:

- Option A: `docker compose up` (the `seed` service reads `regulation_texts/` on every start).
- Option B: `uv run comintern-seed`.

The seed log names every file it indexed (`Indexed N passages of source=...`). Laws change: download
a text again when it is amended, then seed again. Git ignores these files (`regulation_texts/*/` in
`.gitignore`), so every colleague downloads their own copies.

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
