"""
Logging configuration for the application.
"""
import logging
import sys
from typing import Dict, Any
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging():
    """Set up application logging."""
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)

    # Create JSON formatter for production
    if not settings.DEBUG:
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Set up specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


class RequestLogger:
    """Middleware for logging HTTP requests."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def log_request(
        self,
        method: str,
        url: str,
        status_code: int,
        duration: float,
        user_id: str = None
    ):
        """Log HTTP request details."""
        log_data: Dict[str, Any] = {
            "method": method,
            "url": url,
            "status_code": status_code,
            "duration": duration,
        }

        if user_id:
            log_data["user_id"] = user_id

        if status_code >= 400:
            self.logger.error("Request failed", extra=log_data)
        else:
            self.logger.info("Request completed", extra=log_data)