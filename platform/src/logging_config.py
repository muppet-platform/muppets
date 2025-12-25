"""
Logging configuration for the Muppet Platform.

This module sets up structured logging with proper formatting,
handlers, and integration with AWS CloudWatch.
"""

import logging
import logging.config
import sys
from typing import Dict, Any


def setup_logging(log_level: str = "INFO") -> None:
    """
    Set up logging configuration for the platform.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """

    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(funcName)s(): %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": sys.stdout,
            },
            "error_console": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "stream": sys.stderr,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": "logs/platform.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": log_level,
                "handlers": ["console", "error_console"],
                "propagate": False,
            },
            "platform": {
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    # Create logs directory if it doesn't exist
    import os

    os.makedirs("logs", exist_ok=True)

    # Apply the logging configuration
    logging.config.dictConfig(logging_config)

    # Set up platform-specific logger
    logger = logging.getLogger("platform")
    logger.info(f"Logging configured with level: {log_level}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    Args:
        name: The logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"platform.{name}")


class StructuredLogger:
    """
    Structured logger wrapper for consistent logging across the platform.
    """

    def __init__(self, name: str):
        self.logger = get_logger(name)

    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        extra = {"structured_data": kwargs} if kwargs else {}
        self.logger.info(message, extra=extra)

    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        extra = {"structured_data": kwargs} if kwargs else {}
        self.logger.warning(message, extra=extra)

    def error(self, message: str, **kwargs):
        """Log error message with structured data."""
        extra = {"structured_data": kwargs} if kwargs else {}
        self.logger.error(message, extra=extra)

    def debug(self, message: str, **kwargs):
        """Log debug message with structured data."""
        extra = {"structured_data": kwargs} if kwargs else {}
        self.logger.debug(message, extra=extra)

    def exception(self, message: str, **kwargs):
        """Log exception with structured data."""
        extra = {"structured_data": kwargs} if kwargs else {}
        self.logger.exception(message, extra=extra)
