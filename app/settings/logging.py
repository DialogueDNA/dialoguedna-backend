# app/settings/logging.py
# -*- coding: utf-8 -*-
"""
Central logging configuration.
- Uses dictConfig to set structured, leveled logging across the app.
- Uvicorn/fastapi logs are aligned.
"""
from __future__ import annotations
import logging
import logging.config
import os

def setup_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": fmt},
            "uvicorn": {"format": "%(levelprefix)s %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": level,
            },
        },
        "loggers": {
            "": {"handlers": ["console"], "level": level},  # root logger
            "uvicorn": {"handlers": ["console"], "level": level, "propagate": False},
            "uvicorn.error": {"level": level, "propagate": True},
            "uvicorn.access": {"handlers": ["console"], "level": level, "propagate": False},
            "fastapi": {"handlers": ["console"], "level": level, "propagate": False},
            "app": {"handlers": ["console"], "level": level, "propagate": False},
        },
    }
    logging.config.dictConfig(config)
    logging.getLogger(__name__).info("Logging configured (level=%s)", level)
