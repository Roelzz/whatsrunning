# whatsrunning

Visual insight into Docker containers, networks, server ports, and Nginx Proxy Manager mappings.

## Quick Start

1. Copy `.env.example` to `.env` and configure credentials
2. Run: `uv run reflex run`
3. Visit: http://localhost:3000

## Configuration

See `.env.example` for all available settings.

## Development

```bash
uv sync                    # Install dependencies
uv run reflex run          # Run dev server
uv run pytest              # Run tests
uv run ruff check .        # Lint
uv run ruff format .       # Format
```

## Docker Deployment

1. Configure NPM volume in docker-compose.yml:
   - Find your NPM volume: `docker volume ls | grep nginx`
   - Update external volume name in docker-compose.yml

2. Build and run:
   ```bash
   docker-compose up --build -d
   ```

3. Access: http://localhost:2009
