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
