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
