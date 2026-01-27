import os
from whatsrunning.logger import get_logger

def test_logger_respects_log_level():
    """Logger should respect LOG_LEVEL env var"""
    os.environ["LOG_LEVEL"] = "ERROR"
    logger = get_logger()
    # ERROR level is 40 in loguru
    assert logger._core.min_level == 40
