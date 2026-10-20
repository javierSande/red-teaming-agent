# Information Retrieval Agent

The information retrieval agent combines semantic search from the local RAG
service with a local Ollama model. It retrieves the most relevant indexed
chunks, places them in a bounded prompt context, and asks the model to answer
the user's question using that context.

The agent does not execute commands, discover targets, or validate assessment
scope. It is a knowledge-retrieval component for the broader agent system.

## Flow

![Information retrieval agent flow](/docs/images/retrieval-agent-flow.svg)

## Components

- [`rta/agents/retrieval_agent.py`](../../../../rta/agents/retrieval_agent.py)
  - `InformationRetrievalAgent`
  - Retrieves context and invokes Ollama.
- [`rta/tools/rag_client.py`](../../../../rta/tools/rag_client.py)
  - HTTP client for the RAG service.
- [`rta/core/model.py`](../../../../rta/core/model.py)
  - Provider-neutral `Model`, `ChatMessage`, and `ModelResponse` types.
- [`rta/core/ollama_model.py`](../../../../rta/core/ollama_model.py)
  - Ollama implementation of the `Model` interface.
- [`rta/agents/config.py`](../../../../rta/agents/config.py)
  - Retrieval model and temperature defaults.
- [`services/rag/README.md`](../../../../docs/services/rag/README.md)
  - RAG service setup and API documentation.

## Prerequisites

1. Start the RAG service and make sure it is reachable.
2. Install the agent dependencies, including `requests` and the Ollama Python
   client.
3. Start Ollama and pull the configured model:

```bash
ollama pull qwen2.5-coder:14b
```

The Ollama endpoint is configurable. By default it uses
`http://127.0.0.1:11434`, or the value of the `OLLAMA_HOST` environment
variable.

## Usage

```python
from rta.agents.retrieval_agent import InformationRetrievalAgent
from rta.tools.rag_client import RAGClient

client = RAGClient("http://127.0.0.1:8000", timeout=30)
agent = InformationRetrievalAgent(
    client,
    ollama_host="http://127.0.0.1:11434",
)

result = agent.run("How can SUID binaries be identified?", top_k=5)
print(result["response"])
print(result["cited_sources"])
```

### Use a remote Ollama server

Set `OLLAMA_HOST` before creating the agent:

```bash
export OLLAMA_HOST=http://192.168.1.20:11434
```

```python
agent = InformationRetrievalAgent(rag_client)
```

The host is resolved when `agents.config` is imported. Set the environment
variable before starting the process, or pass `ollama_host` explicitly to the
agent constructor.

### Replace the model implementation

Agents depend on the provider-neutral `Model` abstraction rather than directly
on Ollama. A compatible implementation can be injected:

```python
from rta.core import Model, ModelResponse

class TestModel(Model):
    def chat(self, *, model, messages, options=None):
        self.validate_request(model, messages)
        return ModelResponse(content="mocked answer")

agent = InformationRetrievalAgent(
    rag_client,
    model=TestModel(),
)
```

This makes it possible to use another local model server, a test double, or a
future provider adapter without changing the agent. New code should import
model types from `core`.

## RAG client contract

`RAGClient` sends:

```json
{
  "query": "How can SUID binaries be identified?",
  "top_k": 5
}
```

to `POST /query` and expects the RAG response field
`retrieved_documents`. It applies:

- Non-empty query validation.
- `top_k` validation in the range `1..100`.
- A configurable positive HTTP timeout.
- HTTP error propagation via `raise_for_status()`.
- Response-shape validation.

## Agent result

`InformationRetrievalAgent.run()` returns:

```python
{
    "query": "...",
    "response": "...",
    "raw_context": [...],
    "cited_sources": ["path/to/source.md"]
}
```

`raw_context` contains the RAG result objects, including content, metadata, and
distance. `cited_sources` is derived from each result's `metadata.source`.
Documents with missing or empty content are omitted when building the prompt.
The raw results remain available in `raw_context`.

## Error behavior

- Empty prompts, invalid `top_k`, empty RAG base URLs, and non-positive
  timeouts raise `ValueError`.
- Network failures and non-2xx RAG responses are propagated by `requests`.
- Malformed RAG responses raise `ValueError`.
- An empty model response raises `RuntimeError`.

The agent does not silently convert retrieval or model failures into an
apparently successful answer.
