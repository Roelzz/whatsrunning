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
