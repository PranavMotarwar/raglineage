"""Logging utilities."""

import logging
import sys
from typing import Any


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Logging level

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
