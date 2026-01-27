from collectors.port_scanner import PortScanner


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
    assert result["free_ranges"][0] == (1026, 1027)
    assert result["next_available"][0] == 1026


def test_all_ports_used():
    """Should handle case where all ports are used"""
    scanner = PortScanner("1024-1026")
    used_ports = {1024, 1025, 1026}
    result = scanner.scan(used_ports)

    assert result["free_ranges"] == []
    assert result["next_available"] == []
    assert len(result["used_ports"]) == 3


def test_no_ports_used():
    """Should handle case where no ports are used"""
    scanner = PortScanner("1024-1026")
    used_ports = set()
    result = scanner.scan(used_ports)

    assert result["free_ranges"] == [(1024, 1026)]
    assert result["next_available"] == [1024, 1025, 1026]
    assert result["used_ports"] == []


def test_invalid_port_range_format():
    """Should raise error for invalid port range format"""
    try:
        PortScanner("1024")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid port range format" in str(e)


def test_invalid_port_range_bounds():
    """Should raise error for out of bounds ports"""
    try:
        PortScanner("1024-70000")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must be between 1-65535" in str(e)


def test_invalid_port_range_order():
    """Should raise error when start > end"""
    try:
        PortScanner("2000-1024")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Start port must be <= end port" in str(e)
