# whatsrunning/state.py
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

    def login(self, form_data: dict):
        """Validate credentials and set authentication state"""
        username = form_data.get("username", "")
        password = form_data.get("password", "")

        expected_username = os.getenv("AUTH_USERNAME", "admin")
        expected_password = os.getenv("AUTH_PASSWORD", "admin")

        if secrets.compare_digest(username, expected_username) and secrets.compare_digest(password, expected_password):
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
        self.selected_node = node_data
