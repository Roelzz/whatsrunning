# tests/test_integration.py
import os
import pytest
from unittest.mock import Mock, patch
from state import AppState

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

@patch('collectors.docker_collector.docker.from_env')
@patch('collectors.npm_collector.sqlite3.connect')
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

    # Mock row with dictionary-like access
    mock_row = {
        "domain_names": '["example.com"]',
        "forward_host": 'localhost',
        "forward_port": 8080,
        "certificate_id": 1
    }
    mock_cursor.fetchall.return_value = [mock_row]
    mock_conn.cursor.return_value = mock_cursor

    # Make mock_conn work as context manager
    mock_conn.__enter__ = Mock(return_value=mock_conn)
    mock_conn.__exit__ = Mock(return_value=False)

    mock_sqlite.return_value = mock_conn

    # Run refresh
    state = AppState()
    state.refresh_data()

    # Verify Docker collector was called
    mock_docker.assert_called_once()
    mock_client.containers.list.assert_called_once()

    # Verify NPM collector was called
    mock_sqlite.assert_called()

    # Verify data collected
    assert len(state.containers) == 1
    assert state.containers[0]["name"] == "test"
    assert len(state.npm_mappings) == 1
    assert state.npm_mappings[0]["domain"] == "example.com"
    assert len(state.available_ports) > 0
