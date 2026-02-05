"""Logging configuration for the OSRS backend."""

import logging
import logging.config
import os
import sys
from typing import Any, Dict


def _build_logging_config() -> Dict[str, Any]:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)s %(name)s - %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
            "access": {
                "format": "%(asctime)s %(levelname)s %(name)s - %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "stream": sys.stdout,
                "formatter": "standard",
            },
            "access": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "stream": sys.stdout,
                "formatter": "access",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": log_level,
            },
            "uvicorn": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["access"],
                "level": log_level,
                "propagate": False,
            },
            "arq.worker": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
            "arq": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
        },
    }


_already_configured = False


def setup_logging() -> None:
    """
    Configure logging for API, ARQ worker and tasks to write to stdout.
    Idempotent: safe to call multiple times.
    """
    global _already_configured
    if _already_configured:
        return
    logging.config.dictConfig(_build_logging_config())
    _already_configured = True
