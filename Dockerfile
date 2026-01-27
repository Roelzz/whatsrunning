FROM python:3.12-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies (frozen lockfile, no dev dependencies)
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Expose Reflex default port
EXPOSE 3000
EXPOSE 8000

# Run Reflex in production mode
CMD ["uv", "run", "reflex", "run", "--env", "prod"]
