import json
import os
import shlex
import sys
from typing import Any, Dict, List, Optional

_RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"


def style(text: str, *codes: str) -> str:
    if not sys.stdout.isatty() or "NO_COLOR" in os.environ:
        return text
    return f"{''.join(codes)}{text}{_RESET}"


def banner() -> None:
    print()
    print(style("+--------------------------------------+", CYAN))
    print(style("|        Red Teaming Agent (RTA)       |", BOLD, CYAN))
    print(style("|          Agent testing console       |", DIM, CYAN))
    print(style("+--------------------------------------+", CYAN))


def print_health(health: Dict[str, Any]) -> None:
    status = health.get("status", "unknown")
    chunks = health.get("total_chunks_in_db")
    suffix = f" ({chunks} chunks)" if chunks is not None else ""
    print(
        f"{style('RAG service', BOLD)}  "
        f"{style(str(status), GREEN if status == 'online' else YELLOW)}"
        f"{style(suffix, DIM)}"
    )


def print_agents(agents: List[str]) -> Optional[str]:
    print(style("\nAvailable agents", BOLD))
    for index, name in enumerate(agents, 1):
        print(f"  {style(str(index), CYAN)}. {name}")
    print(f"  {style('q', CYAN)}. quit")
    selection = input(style("\nSelect an agent: ", BOLD)).strip().lower()
    if selection in {"q", "quit"}:
        return None
    if selection.isdigit() and 1 <= int(selection) <= len(agents):
        return agents[int(selection) - 1]
    print(style("Invalid agent selection.", YELLOW))
    return ""


def print_result(result: Dict[str, Any], as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(style("\nResponse", BOLD, GREEN))
    print(style("-" * 40, DIM))
    print(result.get("response", ""))
    sources = result.get("cited_sources", [])
    if sources:
        print(style("\nSources", BOLD, CYAN))
        for source in sources:
            print(f"  - {source}")


def print_config(config: Dict[str, Dict[str, Any]]) -> None:
    print(style("\nConfiguration", BOLD, CYAN))
    for section, values in config.items():
        for key, value in values.items():
            print(f"  {section}.{key} = {value}")


def parse_config_command(command: str) -> Optional[tuple[str, str]]:
    """Parse ':config' or ':config set section.key value'."""
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"Invalid configuration command: {exc}") from exc

    if parts == [":config"] or parts == [":config", "show"]:
        return None
    if len(parts) == 4 and parts[:2] == [":config", "set"]:
        return parts[2], parts[3]
    raise ValueError(
        "Use ':config', or ':config set <section.key> <value>'."
    )
