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

## Deployment

See `docker-compose.yml` for deployment instructions.
