FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --target /app/dependencies .

FROM python:3.12-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/dependencies" \
    APP_ENV="local"
COPY --from=builder /app/dependencies /app/dependencies
COPY config/ /app/config/
COPY examples/read_config.py /app/
CMD ["python", "read_config.py"]
