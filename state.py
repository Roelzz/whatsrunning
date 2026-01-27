# whatsrunning/state.py
from dotenv import load_dotenv
load_dotenv()  # Load .env at module level

import reflex as rx
from typing import Dict, Any, List
import os
import secrets
from datetime import datetime
from collectors.docker_collector import DockerCollector
from collectors.npm_collector import NPMCollector
from collectors.port_scanner import PortScanner
from logger import get_logger

logger = get_logger()

class AppState(rx.State):
    """Global application state"""

    # Authentication
    is_authenticated: bool = False
    username: str = ""

    # Login form fields
    login_username: str = ""
    login_password: str = ""

    def set_login_username(self, value: str):
        """Set login username field"""
        self.login_username = value

    def set_login_password(self, value: str):
        """Set login password field"""
        self.login_password = value

    # Data
    containers: List[Dict[str, Any]] = []
    networks: List[str] = []
    host_ports: List[int] = []
    npm_mappings: List[Dict[str, Any]] = []
    available_ports: Dict[str, Any] = {}

    # Separate fields for port data (for Reflex type inference)
    scan_range: str = ""
    free_ranges: List[List[int]] = []
    next_available: List[int] = []
    used_ports: List[int] = []

    # UI state
    selected_node: Dict[str, Any] = {}
    last_updated: str = ""
    is_loading: bool = False
    error_message: str = ""

    def login(self):
        """Validate credentials and set authentication state"""
        import sys

        # Force output to stderr to ensure it's captured
        sys.stderr.write("=== LOGIN METHOD CALLED ===\n")
        sys.stderr.write(f"login_username: '{self.login_username}' (len={len(self.login_username)})\n")
        sys.stderr.write(f"login_password: '{self.login_password}' (len={len(self.login_password)})\n")
        sys.stderr.flush()

        expected_username = os.getenv("AUTH_USERNAME", "admin")
        expected_password = os.getenv("AUTH_PASSWORD", "admin")

        sys.stderr.write(f"Expected username: '{expected_username}' (len={len(expected_username)})\n")
        sys.stderr.write(f"Expected password: '{expected_password}' (len={len(expected_password)})\n")
        sys.stderr.flush()

        # Log types
        sys.stderr.write(f"Types - login: {type(self.login_username)}, expected: {type(expected_username)}\n")
        sys.stderr.flush()

        # Test comparison
        username_match = secrets.compare_digest(self.login_username, expected_username)
        password_match = secrets.compare_digest(self.login_password, expected_password)

        sys.stderr.write(f"Username match: {username_match}\n")
        sys.stderr.write(f"Password match: {password_match}\n")
        sys.stderr.flush()

        if username_match and password_match:
            self.is_authenticated = True
            self.username = self.login_username
            sys.stderr.write(f"✓ User {self.login_username} logged in successfully\n")
            sys.stderr.flush()
            logger.info(f"User {self.login_username} logged in successfully")
            # Clear login fields
            self.login_username = ""
            self.login_password = ""
            yield
            yield rx.redirect("/dashboard")
        else:
            sys.stderr.write(f"✗ AUTHENTICATION FAILED - username_match={username_match}, password_match={password_match}\n")
            sys.stderr.flush()
            self.error_message = "Invalid credentials"
            logger.warning(f"Failed login attempt for username: '{self.login_username}'")

    def logout(self):
        """Clear authentication state"""
        logger.info(f"User {self.username} logged out")
        self.is_authenticated = False
        self.username = ""
        yield
        yield rx.redirect("/login")

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
            port_data = port_scanner.scan(set(self.host_ports))

            self.available_ports = port_data
            self.scan_range = port_data.get("scan_range", "")
            self.free_ranges = [[r[0], r[1]] for r in port_data.get("free_ranges", [])]
            self.next_available = port_data.get("next_available", [])
            self.used_ports = port_data.get("used_ports", [])

            self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            logger.info("Data refreshed successfully")

        except Exception as e:
            self.error_message = str(e)
            logger.error(f"Failed to refresh data: {e}")
        finally:
            self.is_loading = False

    def select_node(self, node_data: Dict[str, Any]):
        """Set selected node for detail panel"""
        # Format all values to strings to prevent React rendering errors
        formatted_data = {}
        for key, value in node_data.items():
            if isinstance(value, (dict, list)):
                # Convert complex types to string representation
                formatted_data[key] = str(value)
            else:
                formatted_data[key] = value
        self.selected_node = formatted_data
