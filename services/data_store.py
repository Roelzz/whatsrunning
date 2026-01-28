# whatsrunning/services/data_store.py
from threading import Lock
from typing import Any


class DataStore:
    """Thread-safe singleton data store for application state"""

    _instance = None
    _lock = Lock()

    def __init__(self):
        self.data = {
            "containers": [],
            "networks": [],
            "host_ports": [],
            "npm_mappings": [],
            "free_ranges": [],
            "next_available": [],
            "used_ports": [],
            "scan_range": "",
            "last_updated": "",
            "expanded_containers": set(),  # Track expanded port groups
            "stacks": [],
            "expanded_stacks": set(),
        }

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def update(self, key: str, value: Any):
        with self._lock:
            self.data[key] = value

    def get(self, key: str) -> Any:
        with self._lock:
            return self.data.get(key)

    def get_all(self) -> dict:
        with self._lock:
            return self.data.copy()
