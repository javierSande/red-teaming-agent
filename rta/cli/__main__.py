import argparse
import sys
from typing import Any, Optional

import requests

from rta.cli import output
from rta.cli.config import CONFIG, set_value
from rta.cli.local_client import LocalRtaClient


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interactive CLI for testing RTA agents.")
    parser.add_argument("--agent", help="Agent to use. Omit to show the interactive menu.")
    parser.add_argument("--query", help="Run one query and exit.")
    parser.add_argument("--rag-url", default=None)
    parser.add_argument("--ollama-host", default=None)
    parser.add_argument("--json", action="store_true", help="Print one-shot results as JSON.")
    return parser


def _create_client(args: argparse.Namespace) -> Any:
    return LocalRtaClient(
        CONFIG["cli"]["rag_url"],
        CONFIG["model"]["ollama_host"],
    )


def run(args: argparse.Namespace) -> int:
    client = _create_client(args)
    if not args.json:
        output.banner()
    try:
        if not args.json:
            output.print_health(client.health())
        agents = client.agents()
    except (requests.RequestException, ValueError) as exc:
        print(output.style(f"Unable to connect to RTA: {exc}", output.RED), file=sys.stderr)
        return 1

    selected = args.agent
    while selected is None:
        selected = output.print_agents(agents)
        if selected is None:
            return 0
        if selected == "":
            selected = None

    if selected not in agents:
        print(output.style(f"Unknown agent: {selected}", output.RED), file=sys.stderr)
        return 2

    if args.query is not None:
        try:
            output.print_result(client.run(selected, args.query), args.json)
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            print(output.style(f"Query failed: {exc}", output.RED), file=sys.stderr)
            return 1
        return 0

    print(f"\n{output.style('Connected to agent', output.BOLD)}: "
          f"{output.style(selected, output.GREEN)}")
    print(output.style(
        "Enter a query, ':config' to view settings, or 'q' to quit.",
        output.DIM,
    ))
    while True:
        try:
            query = input(output.style("\nrta> ", output.CYAN, output.BOLD)).strip()
        except EOFError:
            print()
            return 0
        if query.lower() in {"q", "quit", "exit"}:
            print(output.style("Goodbye.", output.DIM))
            return 0
        if query.lower().startswith(":config"):
            try:
                config_change = output.parse_config_command(query)
                if config_change is None:
                    output.print_config(CONFIG)
                    continue
                path, value = config_change
                set_value(path, value)
                client = _create_client(args)
                print(output.style(f"Updated {path}.", output.GREEN))
                if path in {"cli.rag_url", "model.ollama_host"}:
                    output.print_health(client.health())
            except (ValueError, requests.RequestException) as exc:
                print(output.style(f"Configuration failed: {exc}", output.RED))
            continue
        if not query:
            print(output.style("Query cannot be empty.", output.YELLOW))
            continue
        try:
            output.print_result(client.run(selected, query))
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            print(output.style(f"Query failed: {exc}", output.RED), file=sys.stderr)


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.rag_url is not None:
        CONFIG["cli"]["rag_url"] = args.rag_url
    if args.ollama_host is not None:
        CONFIG["model"]["ollama_host"] = args.ollama_host
    top_k = CONFIG["cli"]["top_k"]
    if not isinstance(top_k, int) or not 1 <= top_k <= 100:
        print("The configured cli.top_k must be an integer between 1 and 100.", file=sys.stderr)
        return 2
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
