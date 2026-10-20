# RTA (Red Teaming Agent) Framework

The `rta/` package contains framework-side code for the Red Teaming Agent
system. It is separate from independently deployable services under
`services/`.

## Packages

- `rta/core/` — provider-neutral model abstractions and Ollama adapter.
- `rta/agents/` — agent implementations, including information retrieval.
- `rta/tools/` — clients for external services such as the RAG API.
- `rta/cli/` — temporary command-line interface for testing agents.
- `rta/cli/config.py` — defaults for the temporary local CLI.

The framework communicates with the RAG service over HTTP. The framework does
not import the RAG service implementation, and the RAG service does not depend
on the framework package.

See the [retrieval agent documentation](agents/retrieval_agent/README.md) and
the [RAG service documentation](../services/rag/README.md) for setup and usage.

## Interactive CLI

Use the temporary CLI to test agents before the complete orchestrator exists:

```bash
python -m rta.cli
```

The CLI currently uses a temporary in-process adapter. Its terminal
presentation is separate from that adapter, so the entire `rta/cli/` package
can be removed when a standalone host tool is introduced. Interactive output
includes a compact banner, connection status, readable response sections, and
cited sources. Colors are used when connected to a terminal and automatically
disabled for redirected output; set `NO_COLOR=1` to disable them explicitly.

For repeatable one-shot tests:

```bash
python -m rta.cli \
  --agent retrieval \
  --query "How can SUID binaries be identified?"
```

Configure service endpoints per invocation:

```bash
python -m rta.cli \
  --rag-url http://127.0.0.1:8000 \
  --ollama-host http://127.0.0.1:11434
```

Use `--json` with `--query` to make the result easy to consume from scripts.

### Configuration

CLI defaults are maintained in the [`CONFIG` table](../../rta/cli/config.py).
For example, change the default number of retrieved documents here:

```python
CONFIG = {
    "cli": {
        "top_k": 5,
    },
}
```

`top_k` is intentionally not a CLI option. It is a temporary local-client
default and can be removed with the rest of the CLI package later.

While the interactive CLI is running, use the configuration commands:

```text
:config
:config set cli.top_k 10
:config set cli.rag_url http://127.0.0.1:8001
:config set model.ollama_host http://127.0.0.1:11434
```

`:config` displays the current values. Updates are validated and apply to
subsequent queries. Changing `cli.rag_url` or `model.ollama_host` rebuilds the
temporary local client immediately.