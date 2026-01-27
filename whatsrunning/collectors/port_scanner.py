from typing import Set, Tuple, Dict, Any
from whatsrunning.logger import get_logger

logger = get_logger()

class PortScanner:
    """Scans for available ports in specified range"""

    def __init__(self, port_range: str = "1024-10000"):
        self.start_port, self.end_port = self._parse_range(port_range)

    def _parse_range(self, port_range: str) -> Tuple[int, int]:
        """Parse port range string like '1024-10000'"""
        try:
            parts = port_range.split("-")
            if len(parts) != 2:
                raise ValueError(f"Invalid port range format: {port_range}")
            start, end = int(parts[0]), int(parts[1])
            if start < 1 or end > 65535:
                raise ValueError(f"Port range must be between 1-65535: {port_range}")
            if start > end:
                raise ValueError(f"Start port must be <= end port: {port_range}")
            return start, end
        except (ValueError, AttributeError) as e:
            logger.error(f"Failed to parse port range: {e}")
            raise

    def scan(self, known_used_ports: Set[int]) -> Dict[str, Any]:
        """
        Scan for available ports

        Args:
            known_used_ports: Ports known to be in use (from Docker)

        Returns:
            Dictionary with free_ranges, next_available, and used_ports
        """
        all_ports = range(self.start_port, self.end_port + 1)
        used_ports = set(known_used_ports)

        free_ports = sorted([p for p in all_ports if p not in used_ports])

        # Group consecutive free ports into ranges
        free_ranges = []
        if free_ports:
            range_start = free_ports[0]
            range_end = free_ports[0]

            for port in free_ports[1:]:
                if port == range_end + 1:
                    range_end = port
                else:
                    free_ranges.append((range_start, range_end))
                    range_start = port
                    range_end = port

            free_ranges.append((range_start, range_end))

        return {
            "scan_range": f"{self.start_port}-{self.end_port}",
            "free_ranges": free_ranges,
            "next_available": free_ports[:10] if free_ports else [],
            "used_ports": sorted(list(used_ports))
        }
