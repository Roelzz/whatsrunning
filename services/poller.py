# whatsrunning/services/poller.py
from apscheduler.schedulers.background import BackgroundScheduler
from services.data_store import DataStore
from collectors.docker_collector import DockerCollector
from collectors.npm_collector import NPMCollector
from collectors.port_scanner import PortScanner
import os
from datetime import datetime
from logger import get_logger

logger = get_logger()


def refresh_data():
    """Collect data and update global store"""
    store = DataStore.get_instance()

    try:
        # Docker data
        docker_data = DockerCollector().collect()
        store.update("containers", docker_data["containers"])
        store.update("networks", docker_data["networks"])
        store.update("host_ports", docker_data["host_ports"])

        # NPM data
        npm_data = NPMCollector(os.getenv("NPM_DB_PATH", "/data/database.sqlite")).collect()
        store.update("npm_mappings", npm_data["npm_mappings"])

        # Port scan
        port_data = PortScanner(os.getenv("PORT_SCAN_RANGE", "1024-10000")).scan(
            set(docker_data["host_ports"])
        )
        store.update("scan_range", port_data["scan_range"])
        store.update("free_ranges", port_data["free_ranges"])
        store.update("next_available", port_data["next_available"])
        store.update("used_ports", port_data["used_ports"])

        store.update("last_updated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        logger.info("Data refresh completed")
    except Exception as e:
        logger.error(f"Data refresh failed: {e}")


class BackgroundPoller:
    """Background scheduler that periodically refreshes data"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        interval = int(os.getenv("POLL_INTERVAL_SECONDS", "10"))
        self.scheduler.add_job(func=refresh_data, trigger="interval", seconds=interval)

    def start(self):
        """Start background scheduler"""
        self.scheduler.start()
        logger.info("Background poller started")
        # Initial refresh
        refresh_data()
