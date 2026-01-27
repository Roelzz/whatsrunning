# whatsrunning

Visual insight into Docker containers, networks, server ports, and Nginx Proxy Manager mappings.

## Features

- Real-time Docker container and network monitoring
- Nginx Proxy Manager proxy host mapping visualization
- Port availability scanner
- Interactive network graph
- Secure authentication
- Low resource usage

## Quick Start

### Local Development

1. Clone and install dependencies:
   ```bash
   git clone <repo-url>
   cd whatsrunning
   uv sync
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. Run development server:
   ```bash
   uv run reflex run
   ```

4. Visit: http://localhost:3000

### Docker Deployment

1. Configure NPM volume in docker-compose.yml:
   ```bash
   # Find your NPM volume
   docker volume ls | grep nginx

   # Update docker-compose.yml:
   # Change 'npm_data' external volume name to match your NPM volume
   ```

2. Build and run:
   ```bash
   docker-compose up --build -d
   # or with podman
   podman-compose up --build -d
   ```

3. Access: http://localhost:2009

## Configuration

All configuration via environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTH_USERNAME` | Login username | `admin` |
| `AUTH_PASSWORD` | Login password | `admin` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `POLL_INTERVAL_SECONDS` | Data refresh interval | `10` |
| `PORT_SCAN_INTERVAL_SECONDS` | Port scan interval | `60` |
| `PORT_SCAN_RANGE` | Port range to scan | `1024-10000` |
| `NPM_DB_PATH` | Path to NPM database | `/data/database.sqlite` |
| `SESSION_SECRET_KEY` | Secret for sessions | (required) |
| `SESSION_EXPIRY_HOURS` | Session expiry time | `24` |

## Development

```bash
uv sync                    # Install dependencies
uv run reflex run          # Run dev server
uv run pytest              # Run tests
uv run ruff check .        # Lint
uv run ruff format .       # Format
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Requirements

- Python 3.12+
- Docker socket access (`/var/run/docker.sock`)
- Read access to NPM's SQLite database

## License

MIT
