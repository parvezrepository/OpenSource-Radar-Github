"""Centralized logging configuration for OpenSource Radar."""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure rotating file and console logging."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "opensource_radar.log"

    level = getattr(logging, log_level.upper(), logging.INFO)
    logger = logging.getLogger("opensource_radar")
    logger.setLevel(level)

    # Prevent duplicate handlers if re-called
    if logger.handlers:
        return logger

    # Formatter: timestamp, level, module, message
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s:%(module)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler (5MB per file, max 3 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    return logger
