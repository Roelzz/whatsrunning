from whatsrunning.collectors.port_scanner import PortScanner

def test_parse_port_range():
    """Should parse port range string"""
    scanner = PortScanner("1024-2000")
    assert scanner.start_port == 1024
    assert scanner.end_port == 2000

def test_find_free_ports():
    """Should identify free ports in range"""
    scanner = PortScanner("1024-1030")
    used_ports = {1024, 1025, 1028}
    result = scanner.scan(used_ports)

    assert 1024 in result["used_ports"]
    assert 1026 in result["free_ranges"][0][0:2]
    assert result["next_available"][0] == 1026
