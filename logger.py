import os
from loguru import logger


def get_logger():
    """Configure and return logger instance"""
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="{time:DD-MM-YYYY at HH:mm:ss} | {level: <8} | {message}",
    )
    return logger
