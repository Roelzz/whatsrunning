# whatsrunning - Design Document

**Date:** 2026-01-27
**Purpose:** Visual insight into Docker containers, networks, server ports, and Nginx Proxy Manager mappings

## Overview

whatsrunning is a self-hosted web application that visualizes the complete port mapping chain from Docker containers through server ports to public URLs via Nginx Proxy Manager. Built for personal use on a home server running Portainer and Coolify.

## Architecture

### Components

**Data Layer:**
- Docker API client (`docker` Python library) - queries running containers, networks, port bindings
- NPM SQLite reader (`sqlite3`) - reads proxy hosts from NPM's database file
- Polling service - refreshes data every 5-10 seconds (configurable)
- Port scanner - checks port availability in specified range

**Application Layer:**
- Reflex state manager - holds container/network/proxy/port data in memory
- Auth middleware - validates session against env var credentials
- Data transformer - converts raw data into visualization-ready graph structure

**Presentation Layer:**
- Login page - username/password form with session management
- Main dashboard - interactive network visualization with detail panels
- Available ports panel - shows free ports in configured range

**Deployment:**
- Single Docker container
- Volumes mounted:
  - `/var/run/docker.sock` - read Docker state
  - `/npm-db:/data:ro` - read NPM's SQLite database (read-only)
- Port 2009 exposed for web access
- Session stored in-memory

## Data Model

### Collected Data Structure

```python
{
  "containers": [
    {
      "id": "abc123",
      "name": "portainer",
      "image": "portainer/portainer-ce",
      "status": "running",
      "networks": ["portainer_network"],
      "internal_ports": [9000],
      "exposed_ports": {9000: 9443}  # internal: host
    }
  ],
  "networks": ["portainer_network", "coolify_network"],
  "host_ports": [9443, 2009, 3000],
  "npm_mappings": [
    {
      "domain": "portainer.example.com",
      "target_host": "localhost",
      "target_port": 9443,
      "ssl": true
    }
  ],
  "available_ports": {
    "scan_range": "1024-10000",
    "free_ranges": [(1024, 1999), (2010, 2099)],
    "next_available": [1024, 1025, 1026],
    "used_ports": [2000, 2009, 3000, 9000, 9443]
  }
}
```

### Data Flow

1. **Every 5-10 seconds (main poll):**
   - Query Docker API for containers, networks, port bindings
   - Read NPM SQLite `proxy_host` table for domain mappings
   - Update Reflex state
   - UI auto-refreshes via Reflex reactive model

2. **Every 30-60 seconds (port scan):**
   - Check configured port range for availability
   - Use `socket.connect_ex()` with 0.1s timeout
   - Update available ports in state

## Visualization

### Graph Layout

Hierarchical flow showing:
```
[Container Networks] → [Containers] → [Server] → [NPM] → [Public URLs]
```

### Node Types & Colors

- **Blue:** Docker networks
- **Green:** Containers (with internal ports)
- **Orange:** Server (exposed host ports)
- **Red:** NPM proxy hosts
- **Purple:** Public URLs/domains

### Interactions

- Click node → show details panel
  - Container: image, status, all ports, networks
  - Server port: which containers bind to it, NPM mappings
  - NPM host: domain, SSL status, upstream target
- Pan/zoom for large graphs
- Hover for quick info tooltip

## UI Structure

```
┌─────────────────────────────────────────────────────┐
│ Header: whatsrunning            [Refresh] [Logout] │
├─────────────────────────────────────────────────────┤
│                                                     │
│                                                     │
│        [Network Graph Visualization]                │
│                                                     │
│                                                     │
├─────────────────────────────────────────────────────┤
│ ┌─────────────────────┐  ┌─────────────────────┐  │
│ │ Node Details Panel  │  │ Available Ports     │  │
│ │ (when node clicked) │  │                     │  │
│ │                     │  │ Free ranges:        │  │
│ │ Container: portainer│  │ • 1024-1999 (976)  │  │
│ │ Image: portainer-ce │  │ • 2010-2099 (90)   │  │
│ │ Internal: 9000      │  │                     │  │
│ │ Exposed: 9443       │  │ Next: 1024, 1025.. │  │
│ │ Network: portainer_ │  │                     │  │
│ └─────────────────────┘  │ Used: 2009, 9443.. │  │
│                          └─────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Available Ports Panel

- Shows free port ranges in configured scan range (default 1024-10000)
- Lists next N available ports for quick reference
- Click to copy port to clipboard
- Shows used ports for context

## Authentication

**Simple env var-based auth:**
- `AUTH_USERNAME` and `AUTH_PASSWORD` in .env
- Session-based (cookie with 24h expiry)
- All routes protected except `/login`
- Logout clears session

**Flow:**
1. User visits site → redirected to `/login`
2. Submit username/password → validate against env vars
3. Create session cookie → redirect to dashboard
4. Session valid → access granted
5. Logout or expiry → redirect to login

## Error Handling

### Docker Socket
- Check availability on startup, fail fast if not mounted
- Log warning if connection lost, show "disconnected" in UI
- Retry connection every 30 seconds

### NPM Database
- Check file exists and is readable on startup
- Handle locked database (NPM writing) - retry after 1s
- If unavailable, show containers/ports but indicate "NPM data unavailable"

### Port Mapping Edge Cases
- Internal-only ports (not exposed to host) - show in container node only
- NPM proxying to external services (not in Docker) - show as "external target"
- Multiple containers with same internal port on same network - show all connections

### Authentication
- Invalid credentials - show error, don't reveal which field is wrong
- Session expiry - redirect to login, preserve attempted URL
- Missing env vars - fail startup with clear error message

### Performance
- If >50 containers, add filtering/search to UI
- Configurable polling interval via `POLL_INTERVAL_SECONDS` env var
- Port scan timeout to prevent hanging (max 0.1s per port)

## Configuration

### Environment Variables

```bash
# Authentication (required)
AUTH_USERNAME=admin
AUTH_PASSWORD=your-secure-password

# Logging
LOG_LEVEL=INFO

# Data Collection
POLL_INTERVAL_SECONDS=10
PORT_SCAN_INTERVAL_SECONDS=60
PORT_SCAN_RANGE=1024-10000

# NPM Database Path (inside container)
NPM_DB_PATH=/data/database.sqlite

# Session
SESSION_SECRET_KEY=generate-random-secret-here
SESSION_EXPIRY_HOURS=24
```

## Technology Stack

- **Framework:** Reflex (Python full-stack)
- **Container runtime:** Docker API via `docker` library
- **Database:** SQLite (read-only access to NPM's database)
- **Visualization:** Reflex components + embedded JavaScript graph library (Cytoscape.js or vis-network)
- **Auth:** Session-based with secure cookies
- **Deployment:** Docker container on port 2009

## Docker Setup

### Volumes Required
- `/var/run/docker.sock:/var/run/docker.sock:ro` - Read Docker state
- `npm_data:/data:ro` - Read NPM's database (adjust to your NPM volume)

### Network
- Bridge network, container accessible on port 2009

## Future Enhancements (Out of Scope)

- Historical tracking of port usage
- Alerting when ports conflict
- Multi-user support with different permissions
- Export graph as image
- Mobile-responsive design
- Real-time updates via WebSockets (currently polling)
- Integration with other proxies (Traefik, Caddy)
