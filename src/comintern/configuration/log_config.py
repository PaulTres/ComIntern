"""Logging for the application and the server."""

import logging.config

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(level: str) -> None:
    """
    Send application and uvicorn logs to the console in one format.

    :param level: The root logging level, e.g. INFO.
    """
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"default": {"format": LOG_FORMAT}},
            "handlers": {
                "console": {"class": "logging.StreamHandler", "formatter": "default"}
            },
            "loggers": {
                "uvicorn": {"handlers": ["console"], "propagate": False},
                "uvicorn.access": {"handlers": ["console"], "propagate": False},
                # One line per Qdrant and Ollama request drowns the application's own logs.
                "httpx": {"level": "WARNING"},
            },
            "root": {"level": level, "handlers": ["console"]},
        }
    )
