"""Logging configuration for the Sectoral API.

WHY configure logging explicitly?
- Default Python logging shows nothing below WARNING level.
- We want INFO-level logs from our app (screener fetches, tag generation)
  but only WARNING from noisy libraries (SQLAlchemy echo, httpx).
- Structured format with timestamps makes log analysis possible in
  production (Render's log viewer, future log aggregation).

USAGE:
    Import and call setup_logging() once at app startup (in main.py).
"""

import logging
import sys


def setup_logging(environment: str = "development") -> None:
    """Configure application-wide logging.

    Args:
        environment: 'development' for verbose, 'production' for concise.
    """
    log_level = logging.DEBUG if environment == "development" else logging.INFO

    # Format: timestamp, level, logger name, message.
    formatter = logging.Formatter(
        fmt="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (stdout for Render log collection).
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Root logger.
    root = logging.getLogger()
    root.setLevel(log_level)
    root.addHandler(handler)

    # Quieten noisy libraries.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)

    logging.info("Logging configured [%s] at %s level", environment, logging.getLevelName(log_level))
