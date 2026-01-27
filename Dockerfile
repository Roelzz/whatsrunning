FROM python:3.12-slim

WORKDIR /app

# Install uv and runtime dependencies for Reflex
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates unzip && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    rm -rf /var/lib/apt/lists/*

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY . .

# Expose Reflex ports
EXPOSE 3000
EXPOSE 8000

# Run Reflex in production mode
CMD ["uv", "run", "reflex", "run", "--env", "prod"]
