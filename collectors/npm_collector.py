import sqlite3
import json
from typing import Dict, Any
from logger import get_logger

logger = get_logger()


class NPMCollector:
    """Collects data from Nginx Proxy Manager database"""

    def __init__(self, db_path: str = "/data/database.sqlite"):
        self.db_path = db_path
        self._check_database()

    def _check_database(self):
        """Verify database exists and is readable"""
        try:
            with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True):
                pass
            logger.info(f"Connected to NPM database: {self.db_path}")
        except Exception as e:
            logger.warning(f"Cannot access NPM database: {e}")

    def collect(self) -> Dict[str, Any]:
        """Collect proxy host mappings from NPM"""
        npm_mappings = []

        try:
            with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True) as conn:
                cursor = conn.cursor()
                cursor.row_factory = sqlite3.Row

                cursor.execute("""
                    SELECT domain_names, forward_host, forward_port, certificate_id
                    FROM proxy_host
                """)

                for row in cursor.fetchall():
                    domains = json.loads(row["domain_names"])

                    if not domains:
                        continue

                    npm_mappings.append(
                        {
                            "domain": domains[0],
                            "target_host": row["forward_host"],
                            "target_port": row["forward_port"],
                            "ssl": row["certificate_id"] is not None and row["certificate_id"] > 0,
                        }
                    )

            logger.debug(f"Collected {len(npm_mappings)} NPM proxy hosts")

        except Exception as e:
            logger.error(f"Failed to collect NPM data: {e}")

        return {"npm_mappings": npm_mappings}
