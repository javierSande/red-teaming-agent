import logging
import os
import sys


DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging() -> None:
    """Configure process-wide logging for local and container execution."""
    level_name = os.getenv("RAG_LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    level = getattr(logging, level_name, None)
    if not isinstance(level, int):
        raise ValueError(
            f"Invalid RAG_LOG_LEVEL '{level_name}'. "
            "Use a standard logging level such as DEBUG, INFO, WARNING, or ERROR."
        )

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        stream=sys.stdout,
    )
