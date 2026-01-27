import docker
from typing import Dict, Any, List
from whatsrunning.logger import get_logger

logger = get_logger()

class DockerCollector:
    """Collects data from Docker API"""

    def __init__(self):
        try:
            self.client = docker.from_env()
            logger.info("Connected to Docker daemon")
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            raise

    def collect(self) -> Dict[str, Any]:
        """Collect container, network, and port data"""
        containers = []
        networks = set()
        host_ports = set()

        for container in self.client.containers.list():
            # Extract network info
            container_networks = list(container.attrs["NetworkSettings"]["Networks"].keys())
            networks.update(container_networks)

            # Extract port mappings
            ports_data = container.attrs["NetworkSettings"]["Ports"] or {}
            internal_ports = []
            exposed_ports = {}

            for internal_port_str, host_bindings in ports_data.items():
                # Parse internal port (e.g., "80/tcp" -> 80)
                internal_port = int(internal_port_str.split("/")[0])
                internal_ports.append(internal_port)

                # Parse host port if exposed
                if host_bindings:
                    host_port = int(host_bindings[0]["HostPort"])
                    exposed_ports[internal_port] = host_port
                    host_ports.add(host_port)

            containers.append({
                "id": container.id,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "status": container.status,
                "networks": container_networks,
                "internal_ports": internal_ports,
                "exposed_ports": exposed_ports
            })

        return {
            "containers": containers,
            "networks": list(networks),
            "host_ports": list(host_ports)
        }
