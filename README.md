# ComIntern

Compliance readiness web app for companies operating in the **EU, Germany and Romania**.

1. **Onboarding questionnaire**: size, sector, countries, data, AI and finance questions.
2. **Applicability engine**: shows which regulations apply and why (GDPR, NIS2, AI Act, DORA, CSRD, CSDDD,
   BDSG, NIS2/BSIG, LkSG, HinSchG, GwG, Law 190/2018, OUG 155/2024, Law 361/2022, Law 129/2019, RO e-Factura, …).
3. **Requirement checklists**: set a status per requirement, add notes and upload evidence documents.
4. **Dashboard**: weighted compliance score overall and per regulation, next steps, recent evidence.
5. **Regulatory updates feed**: deadlines and amendments for your regulations.
6. **Assistant (planned)**: a RAG agent over regulation texts and uploaded evidence. The API contract and
   text extraction of uploads are already in place.

> ComIntern gives guidance, not legal advice. The regulation catalog and update feed are curated by hand.
> Verify thresholds and dates against the linked official sources before relying on them.

## Stack

| Part | Tech |
|---|---|
| `frontend/` | Next.js 16 (App Router), React 19, Tailwind CSS 4, shadcn/ui (Base UI) |
| `backend/` | FastAPI, SQLAlchemy 2, SQLite (Postgres-ready), JWT auth, pypdf / python-docx |

## Running locally

```bash
# Backend (http://localhost:8000, API docs at /docs)
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload

# Frontend (http://localhost:3000)
cd frontend
npm install
npm run dev
```

Or with Docker: `docker compose up --build`.

The database is created and the catalog is seeded automatically on startup.

## Tests

```bash
cd backend && .venv/bin/python -m pytest
cd frontend && npm run lint && npm run build
```

## Where things live

| What | Where |
|---|---|
| Questionnaire (steps, questions, `show_if` conditions) | `backend/app/data/questionnaire.yaml` |
| Regulation catalog (applicability rules + requirements) | `backend/app/data/regulations/{eu,de,ro}.yaml` |
| Regulatory updates feed | `backend/app/data/updates.yaml` |
| Rule engine | `backend/app/services/applicability.py` |
| Scoring | `backend/app/services/scoring.py` |
| Upload text extraction (RAG input) | `backend/app/services/text_extraction.py` |
| Assistant stub (RAG entry point) | `backend/app/api/assistant.py` |

### Adding a regulation

Add an entry to one of the YAML files. Each entry has `applicability.triggers` (conditions on the company
profile, with a human-readable `reason`) and a list of `requirements` (`key`, `title`, `description`,
`reference`, `weight` 1–3, `evidence_hint`). Restart the backend; seeding is idempotent, keyed by `code`/`key`.

Conditions are `{field, op, value}` (ops: `eq`, `ne`, `truthy`, `gt`, `gte`, `lt`, `lte`, `in`, `contains`,
`contains_any`) or combinators `all` / `any` / `not`. Besides the questionnaire answers, the derived fields
`in_eu`, `size_class` (EU SME definition), `medium_or_larger` and `nis2_annex` (`I` / `II`) are available.

### Scoring

Per regulation: Σ(weight × status value) / Σ(weight), where compliant = 1, in progress = 0.5,
not started = 0, and not-applicable requirements are excluded. The overall score weights each regulation by
its total requirement weight. Levels: < 50 at risk, 50–79 needs work, ≥ 80 audit-ready.

## Roadmap

- RAG assistant: chunk + embed `Document.extracted_text` and official texts in
  `backend/app/data/regulation_texts/`, store in pgvector, answer via the Claude API with citations
- Alembic migrations and Postgres for production
- Automated update monitoring (EUR-Lex, BSI, DNSC, ANAF feeds)
- Multiple users per company with roles; audit export (PDF report per regulation)
