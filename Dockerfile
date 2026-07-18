FROM python:3.12.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy

RUN useradd --create-home --uid 10001 fredo
WORKDIR /app

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY schemas ./schemas
RUN pip install --no-cache-dir uv==0.10.9 \
    && uv sync --frozen --no-dev --no-editable \
    && mkdir /data \
    && chown fredo:fredo /data

ENV FREDO_STATE_DIR=/data \
    FREDO_GINSE_DATABASE=/data/ginse.sqlite3 \
    PATH=/app/.venv/bin:$PATH

USER fredo
EXPOSE 8080
VOLUME ["/data"]
CMD ["fredo", "serve"]
