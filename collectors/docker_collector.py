import docker
from typing import Dict, Any
from logger import get_logger

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
            container_networks = list(container.attrs["NetworkSettings"]["Networks"].keys())
            networks.update(container_networks)

            # Extract Docker Compose labels
            labels = container.attrs.get("Config", {}).get("Labels", {})
            compose_project = labels.get("com.docker.compose.project")
            compose_service = labels.get("com.docker.compose.service")
            compose_version = labels.get("com.docker.compose.version")
            compose_working_dir = labels.get("com.docker.compose.project.working_dir")

            # Use "Standalone" for containers without compose project
            stack_name = compose_project if compose_project else "Standalone"

            ports_data = container.attrs["NetworkSettings"]["Ports"] or {}
            internal_ports = []
            exposed_ports = {}

            for internal_port_str, host_bindings in ports_data.items():
                try:
                    internal_port = int(internal_port_str.split("/")[0])
                    internal_ports.append(internal_port)

                    if host_bindings:
                        host_port = int(host_bindings[0]["HostPort"])
                        exposed_ports[internal_port] = host_port
                        host_ports.add(host_port)
                except (ValueError, KeyError, IndexError) as e:
                    logger.warning(f"Failed to parse port '{internal_port_str}': {e}")
                    continue

            image_tag = (
                container.image.tags[0]
                if (container.image.tags and len(container.image.tags) > 0)
                else "unknown"
            )
            containers.append(
                {
                    "id": container.id,
                    "name": container.name,
                    "image": image_tag,
                    "status": container.status,
                    "networks": container_networks,
                    "internal_ports": internal_ports,
                    "exposed_ports": exposed_ports,
                    "stack": stack_name,
                    "compose_service": compose_service,
                    "compose_version": compose_version,
                    "compose_working_dir": compose_working_dir,
                }
            )

        # Build stack metadata
        stacks = {}
        for container in containers:
            stack_name = container["stack"]
            if stack_name not in stacks:
                stacks[stack_name] = {
                    "name": stack_name,
                    "containers": [],
                    "container_count": 0,
                    "running_count": 0,
                    "compose_version": container.get("compose_version"),
                    "compose_working_dir": container.get("compose_working_dir"),
                }

            stacks[stack_name]["containers"].append(container["id"])
            stacks[stack_name]["container_count"] += 1
            if container["status"] == "running":
                stacks[stack_name]["running_count"] += 1

        return {
            "containers": containers,
            "networks": list(networks),
            "host_ports": list(host_ports),
            "stacks": list(stacks.values()),
        }
