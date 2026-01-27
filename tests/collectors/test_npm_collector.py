import sqlite3
import tempfile
import os
from collectors.npm_collector import NPMCollector


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


def test_collect_multiple_proxy_hosts():
    """Should handle multiple proxy hosts"""
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
            VALUES
                ('["app1.example.com"]', 'host1', 8080, 1),
                ('["app2.example.com"]', 'host2', 3000, 2)
        """)
        conn.commit()
        conn.close()

        collector = NPMCollector(db_path)
        data = collector.collect()

        assert len(data["npm_mappings"]) == 2
        assert data["npm_mappings"][0]["domain"] == "app1.example.com"
        assert data["npm_mappings"][1]["domain"] == "app2.example.com"
    finally:
        os.unlink(db_path)


def test_ssl_edge_cases():
    """Should handle SSL certificate edge cases"""
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
            VALUES
                ('["no-ssl.com"]', 'host1', 80, NULL),
                ('["zero-cert.com"]', 'host2', 80, 0),
                ('["has-ssl.com"]', 'host3', 443, 1)
        """)
        conn.commit()
        conn.close()

        collector = NPMCollector(db_path)
        data = collector.collect()

        assert len(data["npm_mappings"]) == 3
        assert data["npm_mappings"][0]["ssl"] is False  # NULL
        assert data["npm_mappings"][1]["ssl"] is False  # 0
        assert data["npm_mappings"][2]["ssl"] is True  # 1
    finally:
        os.unlink(db_path)


def test_empty_domain_names():
    """Should skip proxy hosts with empty domain_names array"""
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
            VALUES
                ('[]', 'host1', 8080, 1),
                ('["valid.com"]', 'host2', 3000, 1)
        """)
        conn.commit()
        conn.close()

        collector = NPMCollector(db_path)
        data = collector.collect()

        assert len(data["npm_mappings"]) == 1
        assert data["npm_mappings"][0]["domain"] == "valid.com"
    finally:
        os.unlink(db_path)
