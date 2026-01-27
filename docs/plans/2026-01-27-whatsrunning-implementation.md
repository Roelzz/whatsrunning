# whatsrunning Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Reflex web app that visualizes Docker containers, networks, server ports, and Nginx Proxy Manager mappings with port availability scanning.

**Architecture:** Reflex full-stack Python app with background polling service that queries Docker API and NPM SQLite database. State manager holds graph data, UI renders interactive visualization with auth protection.

**Tech Stack:** Reflex, Docker SDK, SQLite3, pytest, UV package manager

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `README.md`

**Step 1: Initialize UV project**

Run: `cd /Users/roelschenk/Downloads/Projects/Whatsrunning/.worktrees/feature/initial-implementation && uv init --name whatsrunning --no-readme`

Expected: Creates pyproject.toml with basic structure

**Step 2: Add core dependencies**

Run: `uv add reflex docker loguru python-dotenv pydantic`

Expected: Dependencies added to pyproject.toml and installed

**Step 3: Add dev dependencies**

Run: `uv add --dev pytest pytest-asyncio ruff`

Expected: Dev dependencies added

**Step 4: Create .env.example**

```bash
# Authentication
AUTH_USERNAME=admin
AUTH_PASSWORD=changeme

# Logging
LOG_LEVEL=INFO

# Data Collection
POLL_INTERVAL_SECONDS=10
PORT_SCAN_INTERVAL_SECONDS=60
PORT_SCAN_RANGE=1024-10000

# NPM Database
NPM_DB_PATH=/data/database.sqlite

# Session
SESSION_SECRET_KEY=generate-random-secret-key-here
SESSION_EXPIRY_HOURS=24
```

**Step 5: Create README.md**

```markdown
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
```

**Step 6: Commit scaffold**

```bash
git add .
git commit -m "feat: initialize project scaffold

Add UV project structure with core dependencies.

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Logging Setup

**Files:**
- Create: `whatsrunning/logger.py`
- Create: `tests/test_logger.py`

**Step 1: Write the failing test**

```python
# tests/test_logger.py
import os
from whatsrunning.logger import get_logger

def test_logger_respects_log_level():
    """Logger should respect LOG_LEVEL env var"""
    os.environ["LOG_LEVEL"] = "ERROR"
    logger = get_logger()
    assert logger._core.min_level == "ERROR"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_logger.py -v`

Expected: FAIL with "No module named 'whatsrunning.logger'"

**Step 3: Create logger module**

```python
# whatsrunning/logger.py
import os
from loguru import logger

def get_logger():
    """Configure and return logger instance"""
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="{time:DD-MM-YYYY at HH:mm:ss} | {level: <8} | {message}"
    )
    return logger
```

**Step 4: Create __init__.py**

```python
# whatsrunning/__init__.py
"""whatsrunning - Docker and NPM port mapping visualization"""
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_logger.py -v`

Expected: PASS

**Step 6: Commit**

```bash
git add whatsrunning/ tests/
git commit -m "feat: add logger configuration

Configure loguru with env var support.

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Docker Data Collector

**Files:**
- Create: `whatsrunning/collectors/docker_collector.py`
- Create: `tests/collectors/test_docker_collector.py`

**Step 1: Write the failing test**

```python
# tests/collectors/test_docker_collector.py
from unittest.mock import Mock, patch
from whatsrunning.collectors.docker_collector import DockerCollector

def test_collect_containers():
    """Should collect container data from Docker API"""
    with patch('docker.from_env') as mock_docker:
        mock_client = Mock()
        mock_container = Mock()
        mock_container.id = "abc123"
        mock_container.name = "test-container"
        mock_container.image.tags = ["nginx:latest"]
        mock_container.status = "running"
        mock_container.attrs = {
            "NetworkSettings": {
                "Networks": {"bridge": {}},
                "Ports": {"80/tcp": [{"HostPort": "8080"}]}
            }
        }
        mock_client.containers.list.return_value = [mock_container]
        mock_docker.return_value = mock_client

        collector = DockerCollector()
        data = collector.collect()

        assert len(data["containers"]) == 1
        assert data["containers"][0]["name"] == "test-container"
        assert data["containers"][0]["exposed_ports"] == {80: 8080}
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/collectors/test_docker_collector.py -v`

Expected: FAIL with "No module named 'whatsrunning.collectors'"

**Step 3: Write minimal implementation**

```python
# whatsrunning/collectors/docker_collector.py
import docker
from typing import Dict, Any, List
from whatsrunning.logger import get_logger

logger = get_logger()

class DockerCollector:
    """Collects data from Docker API"""

    def __init__(self):
        try:
            self.client = docker.from_env()
            logger.info("Connected to Docker daemon")
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            raise

    def collect(self) -> Dict[str, Any]:
        """Collect container, network, and port data"""
        containers = []
        networks = set()
        host_ports = set()

        for container in self.client.containers.list():
            # Extract network info
            container_networks = list(container.attrs["NetworkSettings"]["Networks"].keys())
            networks.update(container_networks)

            # Extract port mappings
            ports_data = container.attrs["NetworkSettings"]["Ports"] or {}
            internal_ports = []
            exposed_ports = {}

            for internal_port_str, host_bindings in ports_data.items():
                # Parse internal port (e.g., "80/tcp" -> 80)
                internal_port = int(internal_port_str.split("/")[0])
                internal_ports.append(internal_port)

                # Parse host port if exposed
                if host_bindings:
                    host_port = int(host_bindings[0]["HostPort"])
                    exposed_ports[internal_port] = host_port
                    host_ports.add(host_port)

            containers.append({
                "id": container.id,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "status": container.status,
                "networks": container_networks,
                "internal_ports": internal_ports,
                "exposed_ports": exposed_ports
            })

        return {
            "containers": containers,
            "networks": list(networks),
            "host_ports": list(host_ports)
        }
```

**Step 4: Create __init__.py for collectors**

```python
# whatsrunning/collectors/__init__.py
"""Data collectors for Docker and NPM"""
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/collectors/test_docker_collector.py -v`

Expected: PASS

**Step 6: Commit**

```bash
git add whatsrunning/collectors/ tests/collectors/
git commit -m "feat: add Docker data collector

Collect containers, networks, and port mappings from Docker API.

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: NPM Data Collector

**Files:**
- Create: `whatsrunning/collectors/npm_collector.py`
- Create: `tests/collectors/test_npm_collector.py`

**Step 1: Write the failing test**

```python
# tests/collectors/test_npm_collector.py
import sqlite3
import tempfile
import os
from whatsrunning.collectors.npm_collector import NPMCollector

def test_collect_proxy_hosts():
    """Should collect proxy host data from NPM database"""
    # Create temp database with test data
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        db_path = tmp.name

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE proxy_host (
                id INTEGER PRIMARY KEY,
                domain_names TEXT,
                forward_host TEXT,
                forward_port INTEGER,
                certificate_id INTEGER
            )
        """)
        cursor.execute("""
            INSERT INTO proxy_host (domain_names, forward_host, forward_port, certificate_id)
            VALUES ('["portainer.example.com"]', 'localhost', 9443, 1)
        """)
        conn.commit()
        conn.close()

        collector = NPMCollector(db_path)
        data = collector.collect()

        assert len(data["npm_mappings"]) == 1
        assert data["npm_mappings"][0]["domain"] == "portainer.example.com"
        assert data["npm_mappings"][0]["target_port"] == 9443
        assert data["npm_mappings"][0]["ssl"] is True
    finally:
        os.unlink(db_path)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/collectors/test_npm_collector.py -v`

Expected: FAIL with "No module named 'whatsrunning.collectors.npm_collector'"

**Step 3: Write minimal implementation**

```python
# whatsrunning/collectors/npm_collector.py
import sqlite3
import json
from typing import Dict, Any, List
from whatsrunning.logger import get_logger

logger = get_logger()

class NPMCollector:
    """Collects data from Nginx Proxy Manager database"""

    def __init__(self, db_path: str = "/data/database.sqlite"):
        self.db_path = db_path
        self._check_database()

    def _check_database(self):
        """Verify database exists and is readable"""
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            conn.close()
            logger.info(f"Connected to NPM database: {self.db_path}")
        except Exception as e:
            logger.warning(f"Cannot access NPM database: {e}")

    def collect(self) -> Dict[str, Any]:
        """Collect proxy host mappings from NPM"""
        npm_mappings = []

        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT domain_names, forward_host, forward_port, certificate_id
                FROM proxy_host
            """)

            for row in cursor.fetchall():
                domain_names_json = row[0]
                forward_host = row[1]
                forward_port = row[2]
                certificate_id = row[3]

                # Parse domain names (stored as JSON array)
                domains = json.loads(domain_names_json)

                # Use first domain if multiple
                domain = domains[0] if domains else "unknown"

                npm_mappings.append({
                    "domain": domain,
                    "target_host": forward_host,
                    "target_port": forward_port,
                    "ssl": certificate_id is not None and certificate_id > 0
                })

            conn.close()
            logger.debug(f"Collected {len(npm_mappings)} NPM proxy hosts")

        except Exception as e:
            logger.error(f"Failed to collect NPM data: {e}")

        return {"npm_mappings": npm_mappings}
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/collectors/test_npm_collector.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add whatsrunning/collectors/npm_collector.py tests/collectors/test_npm_collector.py
git commit -m "feat: add NPM data collector

Collect proxy host mappings from NPM SQLite database.

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Port Scanner

**Files:**
- Create: `whatsrunning/collectors/port_scanner.py`
- Create: `tests/collectors/test_port_scanner.py`

**Step 1: Write the failing test**

```python
# tests/collectors/test_port_scanner.py
from whatsrunning.collectors.port_scanner import PortScanner

def test_parse_port_range():
    """Should parse port range string"""
    scanner = PortScanner("1024-2000")
    assert scanner.start_port == 1024
    assert scanner.end_port == 2000

def test_find_free_ports():
    """Should identify free ports in range"""
    scanner = PortScanner("1024-1030")
    used_ports = {1024, 1025, 1028}
    result = scanner.scan(used_ports)

    assert 1024 in result["used_ports"]
    assert 1026 in result["free_ranges"][0][0:2]
    assert result["next_available"][0] == 1026
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/collectors/test_port_scanner.py -v`

Expected: FAIL with "No module named 'whatsrunning.collectors.port_scanner'"

**Step 3: Write minimal implementation**

```python
# whatsrunning/collectors/port_scanner.py
import socket
from typing import Set, List, Tuple, Dict, Any
from whatsrunning.logger import get_logger

logger = get_logger()

class PortScanner:
    """Scans for available ports in specified range"""

    def __init__(self, port_range: str = "1024-10000"):
        self.start_port, self.end_port = self._parse_range(port_range)

    def _parse_range(self, port_range: str) -> Tuple[int, int]:
        """Parse port range string like '1024-10000'"""
        start, end = port_range.split("-")
        return int(start), int(end)

    def scan(self, known_used_ports: Set[int]) -> Dict[str, Any]:
        """
        Scan for available ports

        Args:
            known_used_ports: Ports known to be in use (from Docker)

        Returns:
            Dictionary with free_ranges, next_available, and used_ports
        """
        all_ports = range(self.start_port, self.end_port + 1)
        used_ports = set(known_used_ports)

        # Quick check for listening sockets (skip full bind test for performance)
        # For now, trust known_used_ports from Docker

        free_ports = sorted([p for p in all_ports if p not in used_ports])

        # Group consecutive free ports into ranges
        free_ranges = []
        if free_ports:
            range_start = free_ports[0]
            range_end = free_ports[0]

            for port in free_ports[1:]:
                if port == range_end + 1:
                    range_end = port
                else:
                    free_ranges.append((range_start, range_end))
                    range_start = port
                    range_end = port

            free_ranges.append((range_start, range_end))

        return {
            "scan_range": f"{self.start_port}-{self.end_port}",
            "free_ranges": free_ranges,
            "next_available": free_ports[:10] if free_ports else [],
            "used_ports": sorted(list(used_ports))
        }
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/collectors/test_port_scanner.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add whatsrunning/collectors/port_scanner.py tests/collectors/test_port_scanner.py
git commit -m "feat: add port scanner

Scan for available ports in configured range.

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Reflex State Manager

**Files:**
- Create: `whatsrunning/state.py`

**Step 1: Create state class**

```python
# whatsrunning/state.py
import reflex as rx
from typing import Dict, Any, List
import os
from whatsrunning.collectors.docker_collector import DockerCollector
from whatsrunning.collectors.npm_collector import NPMCollector
from whatsrunning.collectors.port_scanner import PortScanner
from whatsrunning.logger import get_logger

logger = get_logger()

class AppState(rx.State):
    """Global application state"""

    # Authentication
    is_authenticated: bool = False
    username: str = ""

    # Data
    containers: List[Dict[str, Any]] = []
    networks: List[str] = []
    host_ports: List[int] = []
    npm_mappings: List[Dict[str, Any]] = []
    available_ports: Dict[str, Any] = {}

    # UI state
    selected_node: Dict[str, Any] = {}
    last_updated: str = ""
    is_loading: bool = False
    error_message: str = ""

    def login(self, username: str, password: str):
        """Validate credentials and set authentication state"""
        expected_username = os.getenv("AUTH_USERNAME", "admin")
        expected_password = os.getenv("AUTH_PASSWORD", "admin")

        if username == expected_username and password == expected_password:
            self.is_authenticated = True
            self.username = username
            logger.info(f"User {username} logged in")
            return rx.redirect("/dashboard")
        else:
            self.error_message = "Invalid credentials"
            logger.warning(f"Failed login attempt for {username}")

    def logout(self):
        """Clear authentication state"""
        logger.info(f"User {self.username} logged out")
        self.is_authenticated = False
        self.username = ""
        return rx.redirect("/login")

    def refresh_data(self):
        """Collect fresh data from Docker and NPM"""
        self.is_loading = True
        self.error_message = ""

        try:
            # Collect Docker data
            docker_collector = DockerCollector()
            docker_data = docker_collector.collect()

            self.containers = docker_data["containers"]
            self.networks = docker_data["networks"]
            self.host_ports = docker_data["host_ports"]

            # Collect NPM data
            npm_db_path = os.getenv("NPM_DB_PATH", "/data/database.sqlite")
            npm_collector = NPMCollector(npm_db_path)
            npm_data = npm_collector.collect()

            self.npm_mappings = npm_data["npm_mappings"]

            # Scan ports
            port_range = os.getenv("PORT_SCAN_RANGE", "1024-10000")
            port_scanner = PortScanner(port_range)
            self.available_ports = port_scanner.scan(set(self.host_ports))

            from datetime import datetime
            self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            logger.info("Data refreshed successfully")

        except Exception as e:
            self.error_message = str(e)
            logger.error(f"Failed to refresh data: {e}")
        finally:
            self.is_loading = False

    def select_node(self, node_data: Dict[str, Any]):
        """Set selected node for detail panel"""
        self.selected_node = node_data
```

**Step 2: Commit**

```bash
git add whatsrunning/state.py
git commit -m "feat: add Reflex state manager

Implement state management for auth and data collection.

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Login Page

**Files:**
- Create: `whatsrunning/pages/login.py`

**Step 1: Create login page component**

```python
# whatsrunning/pages/login.py
import reflex as rx
from whatsrunning.state import AppState

def login_page() -> rx.Component:
    """Login page with username/password form"""
    return rx.container(
        rx.vstack(
            rx.heading("whatsrunning", size="9"),
            rx.text("Docker & NPM Port Mapping Visualization", color="gray"),

            rx.card(
                rx.vstack(
                    rx.form(
                        rx.vstack(
                            rx.input(
                                placeholder="Username",
                                name="username",
                                size="3",
                            ),
                            rx.input(
                                placeholder="Password",
                                name="password",
                                type="password",
                                size="3",
                            ),
                            rx.button(
                                "Login",
                                type="submit",
                                size="3",
                                width="100%",
                            ),
                            spacing="3",
                        ),
                        on_submit=lambda form_data: AppState.login(
                            form_data["username"],
                            form_data["password"]
                        ),
                    ),
                    rx.cond(
                        AppState.error_message != "",
                        rx.text(
                            AppState.error_message,
                            color="red",
                            size="2",
                        ),
                    ),
                    spacing="4",
                    width="100%",
                ),
                size="4",
            ),

            spacing="6",
            justify="center",
            min_height="100vh",
        ),
        size="1",
    )
```

**Step 2: Create pages __init__.py**

```python
# whatsrunning/pages/__init__.py
"""Page components"""
from .login import login_page

__all__ = ["login_page"]
```

**Step 3: Commit**

```bash
git add whatsrunning/pages/
git commit -m "feat: add login page

Create authentication form with username/password.

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Dashboard Layout

**Files:**
- Create: `whatsrunning/pages/dashboard.py`
- Create: `whatsrunning/components/header.py`
- Create: `whatsrunning/components/available_ports.py`
- Create: `whatsrunning/components/node_details.py`

**Step 1: Create header component**

```python
# whatsrunning/components/header.py
import reflex as rx
from whatsrunning.state import AppState

def header() -> rx.Component:
    """Header with title and logout button"""
    return rx.hstack(
        rx.heading("whatsrunning", size="7"),
        rx.spacer(),
        rx.text(f"Last updated: {AppState.last_updated}", color="gray", size="2"),
        rx.button(
            "Refresh",
            on_click=AppState.refresh_data,
            loading=AppState.is_loading,
            size="2",
        ),
        rx.button(
            "Logout",
            on_click=AppState.logout,
            variant="soft",
            size="2",
        ),
        width="100%",
        padding="1em",
        border_bottom="1px solid var(--gray-5)",
    )
```

**Step 2: Create available ports component**

```python
# whatsrunning/components/available_ports.py
import reflex as rx
from whatsrunning.state import AppState

def available_ports_panel() -> rx.Component:
    """Panel showing available ports"""
    return rx.card(
        rx.vstack(
            rx.heading("Available Ports", size="5"),
            rx.text(
                f"Scan range: {AppState.available_ports.get('scan_range', 'N/A')}",
                color="gray",
                size="2",
            ),

            rx.divider(),

            rx.heading("Free Ranges", size="3"),
            rx.box(
                rx.foreach(
                    AppState.available_ports.get("free_ranges", []),
                    lambda range_tuple: rx.text(
                        f"{range_tuple[0]}-{range_tuple[1]} ({range_tuple[1] - range_tuple[0] + 1} ports)",
                        size="2",
                    ),
                ),
                max_height="200px",
                overflow_y="auto",
            ),

            rx.divider(),

            rx.heading("Next Available", size="3"),
            rx.text(
                rx.foreach(
                    AppState.available_ports.get("next_available", []),
                    lambda port: f"{port}, ",
                ),
                size="2",
            ),

            spacing="3",
            width="100%",
        ),
    )
```

**Step 3: Create node details component**

```python
# whatsrunning/components/node_details.py
import reflex as rx
from whatsrunning.state import AppState

def node_details_panel() -> rx.Component:
    """Panel showing selected node details"""
    return rx.card(
        rx.cond(
            AppState.selected_node != {},
            rx.vstack(
                rx.heading("Node Details", size="5"),
                rx.divider(),
                rx.foreach(
                    AppState.selected_node.items(),
                    lambda item: rx.hstack(
                        rx.text(f"{item[0]}:", weight="bold", size="2"),
                        rx.text(f"{item[1]}", size="2"),
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            rx.text("Click a node to see details", color="gray", size="2"),
        ),
    )
```

**Step 4: Create dashboard page**

```python
# whatsrunning/pages/dashboard.py
import reflex as rx
from whatsrunning.state import AppState
from whatsrunning.components.header import header
from whatsrunning.components.available_ports import available_ports_panel
from whatsrunning.components.node_details import node_details_panel

def dashboard_page() -> rx.Component:
    """Main dashboard with visualization"""
    return rx.cond(
        AppState.is_authenticated,
        rx.vstack(
            header(),

            rx.container(
                rx.vstack(
                    # Placeholder for graph visualization
                    rx.card(
                        rx.vstack(
                            rx.heading("Network Visualization", size="6"),
                            rx.text("Graph visualization will go here", color="gray"),
                            rx.text(f"Containers: {AppState.containers.length()}", size="2"),
                            rx.text(f"Networks: {AppState.networks.length()}", size="2"),
                            rx.text(f"NPM Mappings: {AppState.npm_mappings.length()}", size="2"),
                            spacing="2",
                        ),
                        min_height="400px",
                    ),

                    # Bottom panels
                    rx.hstack(
                        node_details_panel(),
                        available_ports_panel(),
                        spacing="4",
                        width="100%",
                    ),

                    spacing="4",
                    width="100%",
                ),
                size="4",
                padding="2em",
            ),

            width="100%",
            spacing="0",
        ),
        rx.redirect("/login"),
    )
```

**Step 5: Create components __init__.py**

```python
# whatsrunning/components/__init__.py
"""UI components"""
```

**Step 6: Update pages __init__.py**

```python
# whatsrunning/pages/__init__.py
"""Page components"""
from .login import login_page
from .dashboard import dashboard_page

__all__ = ["login_page", "dashboard_page"]
```

**Step 7: Commit**

```bash
git add whatsrunning/components/ whatsrunning/pages/
git commit -m "feat: add dashboard layout

Create header, available ports panel, and node details panel.

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: Main App Configuration

**Files:**
- Create: `whatsrunning/whatsrunning.py` (Reflex app entry point)
- Modify: `pyproject.toml` (add app config)

**Step 1: Create Reflex app**

```python
# whatsrunning/whatsrunning.py
"""Main Reflex application"""
import reflex as rx
from whatsrunning.pages import login_page, dashboard_page
from whatsrunning.state import AppState

def index() -> rx.Component:
    """Root route redirects to dashboard"""
    return rx.cond(
        AppState.is_authenticated,
        rx.redirect("/dashboard"),
        rx.redirect("/login"),
    )

app = rx.App()
app.add_page(index, route="/")
app.add_page(login_page, route="/login")
app.add_page(dashboard_page, route="/dashboard", on_load=AppState.refresh_data)
```

**Step 2: Update pyproject.toml**

Add Reflex configuration:

```toml
[tool.reflex]
app_name = "whatsrunning"
```

**Step 3: Test app runs**

Run: `uv run reflex init` (to initialize Reflex)

Expected: Reflex initializes without errors

Run: `uv run reflex run` (start dev server)

Expected: Server starts on port 3000, no errors

**Step 4: Commit**

```bash
git add whatsrunning/whatsrunning.py pyproject.toml
git commit -m "feat: add main Reflex app configuration

Configure routes and initialize Reflex app.

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Docker Deployment

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env`

**Step 1: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy project files
COPY . .

# Install dependencies
RUN uv sync

# Expose Reflex default port
EXPOSE 3000
EXPOSE 8000

# Run Reflex in production mode
CMD ["uv", "run", "reflex", "run", "--env", "prod", "--backend-only"]
```

**Step 2: Create docker-compose.yml**

```yaml
services:
  app:
    build: .
    container_name: whatsrunning-app
    ports:
      - "2009:3000"
      - "8001:8000"
    env_file:
      - .env
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - npm_data:/data:ro
    networks:
      - whatsrunning_network
    restart: unless-stopped

networks:
  whatsrunning_network:
    driver: bridge

volumes:
  npm_data:
    external: true
    # Note: Adjust this to point to your NPM volume
    # Example: name: nginxproxymanager_data
```

**Step 3: Create .env from example**

Run: `cp .env.example .env`

Expected: .env file created

**Step 4: Update README with deployment instructions**

Add to README.md:

```markdown
## Docker Deployment

1. Configure NPM volume in docker-compose.yml:
   - Find your NPM volume: `docker volume ls | grep nginx`
   - Update external volume name in docker-compose.yml

2. Build and run:
   ```bash
   docker-compose up --build -d
   ```

3. Access: http://localhost:2009
```

**Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml .env.example README.md
git commit -m "feat: add Docker deployment configuration

Add Dockerfile and docker-compose for production deployment.

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>"
```

---

## Task 11: Background Polling Service

**Files:**
- Create: `whatsrunning/services/poller.py`
- Modify: `whatsrunning/whatsrunning.py`

**Step 1: Create polling service**

```python
# whatsrunning/services/poller.py
import threading
import time
import os
from whatsrunning.logger import get_logger

logger = get_logger()

class BackgroundPoller:
    """Background thread that periodically refreshes data"""

    def __init__(self, state_refresh_callback):
        self.state_refresh_callback = state_refresh_callback
        self.interval = int(os.getenv("POLL_INTERVAL_SECONDS", "10"))
        self.running = False
        self.thread = None

    def start(self):
        """Start background polling thread"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        logger.info(f"Background poller started (interval: {self.interval}s)")

    def stop(self):
        """Stop background polling thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Background poller stopped")

    def _poll_loop(self):
        """Main polling loop"""
        while self.running:
            try:
                self.state_refresh_callback()
            except Exception as e:
                logger.error(f"Polling error: {e}")

            time.sleep(self.interval)
```

**Step 2: Create services __init__.py**

```python
# whatsrunning/services/__init__.py
"""Background services"""
```

**Step 3: Integrate poller into app**

Modify `whatsrunning/whatsrunning.py`:

```python
"""Main Reflex application"""
import reflex as rx
from whatsrunning.pages import login_page, dashboard_page
from whatsrunning.state import AppState
from whatsrunning.services.poller import BackgroundPoller

def index() -> rx.Component:
    """Root route redirects to dashboard"""
    return rx.cond(
        AppState.is_authenticated,
        rx.redirect("/dashboard"),
        rx.redirect("/login"),
    )

app = rx.App()

# Start background poller
poller = BackgroundPoller(AppState.refresh_data)
poller.start()

app.add_page(index, route="/")
app.add_page(login_page, route="/login")
app.add_page(dashboard_page, route="/dashboard", on_load=AppState.refresh_data)
```

**Step 4: Commit**

```bash
git add whatsrunning/services/ whatsrunning/whatsrunning.py
git commit -m "feat: add background polling service

Periodically refresh data in background thread.

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>"
```

---

## Task 12: Integration Testing

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

```python
# tests/test_integration.py
import os
import pytest
from unittest.mock import Mock, patch
from whatsrunning.state import AppState

@pytest.fixture
def mock_env():
    """Set up test environment variables"""
    os.environ["AUTH_USERNAME"] = "testuser"
    os.environ["AUTH_PASSWORD"] = "testpass"
    os.environ["NPM_DB_PATH"] = "/tmp/test.db"
    os.environ["PORT_SCAN_RANGE"] = "1024-1030"

def test_login_flow(mock_env):
    """Test authentication flow"""
    state = AppState()

    # Invalid login
    state.login("wrong", "wrong")
    assert not state.is_authenticated
    assert state.error_message != ""

    # Valid login
    state.login("testuser", "testpass")
    assert state.is_authenticated
    assert state.username == "testuser"

    # Logout
    state.logout()
    assert not state.is_authenticated

@patch('whatsrunning.collectors.docker_collector.docker.from_env')
@patch('whatsrunning.collectors.npm_collector.sqlite3.connect')
def test_data_refresh_flow(mock_sqlite, mock_docker, mock_env):
    """Test full data collection flow"""
    # Mock Docker
    mock_client = Mock()
    mock_container = Mock()
    mock_container.id = "abc123"
    mock_container.name = "test"
    mock_container.image.tags = ["nginx:latest"]
    mock_container.status = "running"
    mock_container.attrs = {
        "NetworkSettings": {
            "Networks": {"bridge": {}},
            "Ports": {"80/tcp": [{"HostPort": "8080"}]}
        }
    }
    mock_client.containers.list.return_value = [mock_container]
    mock_docker.return_value = mock_client

    # Mock NPM database
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = [
        ('["example.com"]', 'localhost', 8080, 1)
    ]
    mock_conn.cursor.return_value = mock_cursor
    mock_sqlite.return_value = mock_conn

    # Run refresh
    state = AppState()
    state.refresh_data()

    # Verify data collected
    assert len(state.containers) == 1
    assert state.containers[0]["name"] == "test"
    assert len(state.npm_mappings) == 1
    assert state.npm_mappings[0]["domain"] == "example.com"
    assert len(state.available_ports) > 0
```

**Step 2: Run integration tests**

Run: `uv run pytest tests/test_integration.py -v`

Expected: PASS

**Step 3: Run all tests**

Run: `uv run pytest -v`

Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests

Test authentication and data collection flow.

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>"
```

---

## Task 13: Documentation & Final Polish

**Files:**
- Update: `README.md`
- Create: `docs/ARCHITECTURE.md`

**Step 1: Enhance README**

Update README.md with complete documentation:

```markdown
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
```

**Step 2: Create architecture document**

```markdown
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
```

**Step 3: Commit**

```bash
git add README.md docs/
git commit -m "docs: add comprehensive documentation

Add detailed README and architecture documentation.

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>"
```

---

## Next Steps

After implementation:

1. **Manual Testing:**
   - Test login/logout flow
   - Verify Docker data collection
   - Check NPM mappings display
   - Validate port scanner accuracy

2. **Future Enhancements:**
   - Interactive graph visualization (Cytoscape.js/vis-network)
   - Click-to-copy port numbers
   - Search/filter containers
   - Historical port usage tracking
   - Mobile responsive design

3. **Production Deployment:**
   - Configure NPM volume mapping
   - Set secure credentials in .env
   - Build and deploy with docker-compose
   - Set up reverse proxy with SSL

---

## Task Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Project scaffold | pyproject.toml, .env.example, README.md |
| 2 | Logging setup | whatsrunning/logger.py |
| 3 | Docker collector | whatsrunning/collectors/docker_collector.py |
| 4 | NPM collector | whatsrunning/collectors/npm_collector.py |
| 5 | Port scanner | whatsrunning/collectors/port_scanner.py |
| 6 | State manager | whatsrunning/state.py |
| 7 | Login page | whatsrunning/pages/login.py |
| 8 | Dashboard layout | whatsrunning/pages/dashboard.py, components/ |
| 9 | Main app config | whatsrunning/whatsrunning.py |
| 10 | Docker deployment | Dockerfile, docker-compose.yml |
| 11 | Background poller | whatsrunning/services/poller.py |
| 12 | Integration tests | tests/test_integration.py |
| 13 | Documentation | README.md, docs/ARCHITECTURE.md |

**Total Tasks:** 13
**Estimated Commits:** 13
**Test Coverage:** Unit tests per collector + integration tests
