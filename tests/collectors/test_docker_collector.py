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

def test_container_with_no_exposed_ports():
    """Should handle containers with no exposed ports"""
    with patch('docker.from_env') as mock_docker:
        mock_client = Mock()
        mock_container = Mock()
        mock_container.id = "def456"
        mock_container.name = "internal-service"
        mock_container.image.tags = ["redis:latest"]
        mock_container.status = "running"
        mock_container.attrs = {
            "NetworkSettings": {
                "Networks": {"bridge": {}},
                "Ports": {"6379/tcp": None}
            }
        }
        mock_client.containers.list.return_value = [mock_container]
        mock_docker.return_value = mock_client

        collector = DockerCollector()
        data = collector.collect()

        assert len(data["containers"]) == 1
        assert data["containers"][0]["internal_ports"] == [6379]
        assert data["containers"][0]["exposed_ports"] == {}
        assert data["host_ports"] == []

def test_container_with_empty_image_tags():
    """Should handle containers with no image tags"""
    with patch('docker.from_env') as mock_docker:
        mock_client = Mock()
        mock_container = Mock()
        mock_container.id = "ghi789"
        mock_container.name = "unnamed-container"
        mock_container.image.tags = []
        mock_container.status = "running"
        mock_container.attrs = {
            "NetworkSettings": {
                "Networks": {"bridge": {}},
                "Ports": {}
            }
        }
        mock_client.containers.list.return_value = [mock_container]
        mock_docker.return_value = mock_client

        collector = DockerCollector()
        data = collector.collect()

        assert len(data["containers"]) == 1
        assert data["containers"][0]["image"] == "unknown"

def test_multiple_containers():
    """Should collect data from multiple containers"""
    with patch('docker.from_env') as mock_docker:
        mock_client = Mock()

        mock_container1 = Mock()
        mock_container1.id = "abc123"
        mock_container1.name = "web"
        mock_container1.image.tags = ["nginx:latest"]
        mock_container1.status = "running"
        mock_container1.attrs = {
            "NetworkSettings": {
                "Networks": {"web_network": {}},
                "Ports": {"80/tcp": [{"HostPort": "8080"}]}
            }
        }

        mock_container2 = Mock()
        mock_container2.id = "def456"
        mock_container2.name = "db"
        mock_container2.image.tags = ["postgres:15"]
        mock_container2.status = "running"
        mock_container2.attrs = {
            "NetworkSettings": {
                "Networks": {"db_network": {}},
                "Ports": {"5432/tcp": [{"HostPort": "5432"}]}
            }
        }

        mock_client.containers.list.return_value = [mock_container1, mock_container2]
        mock_docker.return_value = mock_client

        collector = DockerCollector()
        data = collector.collect()

        assert len(data["containers"]) == 2
        assert set(data["networks"]) == {"web_network", "db_network"}
        assert set(data["host_ports"]) == {8080, 5432}
