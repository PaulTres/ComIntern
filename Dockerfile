# The ComIntern API image. The same image runs the API (`comintern`), the migrations
# (`alembic upgrade head`) and the catalog seeding (`comintern-seed`).
# It uses no BuildKit-only features, so it also builds with Colima's classic builder.

ARG PYTHON_VERSION=3.14
ARG UV_VERSION=0.12.24

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv


FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

COPY --from=uv /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.14 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Dependencies first: this layer is reused until pyproject.toml or uv.lock change.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY README.md ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable


FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        ca-certificates \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/app \
    HF_HUB_DISABLE_TELEMETRY=1 \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=2

# Named volumes mounted on these folders inherit their ownership, so the image creates them
# owned by the app user first.
RUN useradd --create-home --home-dir /home/app --uid 10001 --shell /usr/sbin/nologin app \
    && mkdir -p /app/data/uploads /app/regulation_texts /opt/models \
    && chown -R app:app /app/data /app/regulation_texts /opt/models

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --chown=app:app alembic.ini ./alembic.ini
COPY --chown=app:app alembic ./alembic

USER app

EXPOSE 8000

CMD ["comintern"]
