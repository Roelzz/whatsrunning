FROM python:3.12-slim

WORKDIR /app

# Install uv
ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

# Add uv to PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project itself
RUN uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY . .

# Expose Reflex default port
EXPOSE 3000
EXPOSE 8000

# Run Reflex in production mode
CMD ["uv", "run", "reflex", "run", "--env", "prod"]
