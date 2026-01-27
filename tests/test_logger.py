import os
from whatsrunning.logger import get_logger

def test_logger_respects_log_level(capsys):
    """Logger should respect LOG_LEVEL env var"""
    original = os.environ.get("LOG_LEVEL")
    try:
        os.environ["LOG_LEVEL"] = "ERROR"
        logger = get_logger()
        logger.info("Should not appear")
        logger.error("Should appear")
        captured = capsys.readouterr()
        assert "Should not appear" not in captured.out
        assert "Should appear" in captured.out
    finally:
        if original:
            os.environ["LOG_LEVEL"] = original
        else:
            os.environ.pop("LOG_LEVEL", None)

def test_logger_default_level(capsys):
    """Logger should default to INFO level"""
    original = os.environ.get("LOG_LEVEL")
    try:
        os.environ.pop("LOG_LEVEL", None)
        logger = get_logger()
        logger.info("Should appear")
        captured = capsys.readouterr()
        assert "Should appear" in captured.out
    finally:
        if original:
            os.environ["LOG_LEVEL"] = original
