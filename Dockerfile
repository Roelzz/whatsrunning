# Multi-stage build: copy uv from official image
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv

FROM python:3.12-slim

WORKDIR /app

# Copy uv binary from official image
COPY --from=uv /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project itself
# Use cache mount for faster rebuilds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY . .

# Expose Reflex ports
EXPOSE 3000
EXPOSE 8000

# Run Reflex in production mode
CMD ["uv", "run", "reflex", "run", "--env", "prod"]
