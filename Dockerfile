FROM python:3.12-slim

WORKDIR /app

# Copy all files first
COPY . .

# Install uv
ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

# Add uv to PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Install dependencies using uv pip (no package build needed for Reflex apps)
RUN uv pip install --system --no-cache \
    docker>=7.1.0 \
    loguru>=0.7.3 \
    pydantic>=2.12.5 \
    python-dotenv>=1.2.1 \
    reflex>=0.8.26

# Expose Reflex default port
EXPOSE 3000
EXPOSE 8000

# Run Reflex in production mode
CMD ["reflex", "run", "--env", "prod"]
