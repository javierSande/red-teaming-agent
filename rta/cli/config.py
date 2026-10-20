"""Configuration for the temporary local CLI."""

import os
from typing import Any, Dict


CONFIG: Dict[str, Dict[str, Any]] = {
    "cli": {
        "rag_url": "http://127.0.0.1:8000",
        "top_k": 5,
    },
    "model": {
        "ollama_host": os.environ.get(
            "OLLAMA_HOST",
            "http://127.0.0.1:11434",
        ),
    },
}


def set_value(path: str, raw_value: str) -> None:
    """Validate and update a supported runtime configuration value."""
    supported = {
        "cli.rag_url": str,
        "cli.top_k": int,
        "model.ollama_host": str,
    }
    if path not in supported:
        raise ValueError(
            f"Unknown configuration key '{path}'. "
            f"Available keys: {', '.join(supported)}"
        )

    value: Any = raw_value
    if supported[path] is int:
        try:
            value = int(raw_value)
        except ValueError as exc:
            raise ValueError(f"{path} must be an integer") from exc
        if not 1 <= value <= 100:
            raise ValueError(f"{path} must be between 1 and 100")
    elif not raw_value.strip():
        raise ValueError(f"{path} must not be empty")

    section, key = path.split(".", 1)
    CONFIG[section][key] = value
