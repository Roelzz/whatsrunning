# whatsrunning Architecture

## Overview

whatsrunning is a Reflex-based web application that provides real-time visualization of Docker containers, networks, server ports, and Nginx Proxy Manager mappings.

## Components

### Data Collection Layer

**DockerCollector** (`whatsrunning/collectors/docker_collector.py`)
- Connects to Docker daemon via `/var/run/docker.sock`
- Queries running containers, networks, and port bindings
- Extracts internal and exposed port mappings

**NPMCollector** (`whatsrunning/collectors/npm_collector.py`)
- Reads Nginx Proxy Manager's SQLite database
- Extracts proxy host configurations
- Parses domain names, forward hosts/ports, SSL status

**PortScanner** (`whatsrunning/collectors/port_scanner.py`)
- Scans configured port range for availability
- Identifies free port ranges
- Provides next available ports

### Application Layer

**AppState** (`whatsrunning/state.py`)
- Reflex state manager
- Holds collected data in memory
- Manages authentication state
- Coordinates data refresh

**BackgroundPoller** (`whatsrunning/services/poller.py`)
- Runs in background thread
- Periodically triggers data refresh
- Configurable polling interval

### Presentation Layer

**Pages** (`whatsrunning/pages/`)
- `login.py` - Authentication form
- `dashboard.py` - Main visualization dashboard

**Components** (`whatsrunning/components/`)
- `header.py` - Top navigation with refresh/logout
- `available_ports.py` - Port availability panel
- `node_details.py` - Selected node details panel

## Data Flow

1. **Background Poller** triggers refresh every N seconds
2. **Collectors** query Docker API and NPM database
3. **AppState** updates with fresh data
4. **Reflex** automatically re-renders UI components
5. **User** sees updated visualization

## Authentication

- Simple username/password from environment variables
- Session-based with secure cookies
- All routes protected except `/login`
- 24-hour session expiry (configurable)

## Deployment

### Development
- Reflex dev server on port 3000
- Hot reload enabled
- Direct filesystem access

### Production (Docker)
- Reflex production mode
- Backend on port 8000, frontend on port 3000
- Exposed as port 2009 on host
- Volumes:
  - `/var/run/docker.sock` (read-only) - Docker access
  - NPM database volume (read-only) - NPM data access

## Performance Considerations

- Background polling reduces UI blocking
- Port scanning uses quick socket checks
- Data cached in memory between polls
- Configurable intervals for resource tuning

## Security

- Authentication required for all routes
- Read-only access to Docker socket
- Read-only access to NPM database
- Session secrets from environment
- No external network dependencies
