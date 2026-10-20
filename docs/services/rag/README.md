# RAG Knowledge Service

The RAG Knowledge Service is a local FastAPI service for indexing cybersecurity
reference material and retrieving relevant text chunks for an agent or operator.
It uses ChromaDB for persistent vector storage and a local
`all-MiniLM-L6-v2` Sentence Transformers model for embeddings.

The service is intended to run locally or in a container. It does not provide
an LLM, execute security commands, or authorize assessments. It only ingests
documents and returns similarity-search results. Use it with documents from
authorized sources and keep the service bound to a trusted network.

## Features

- Persistent ChromaDB storage under `services/rag/data/chroma_db/`.
- Automatic ingestion of supported files in `services/rag/data/raw_docs/` at startup.
- Recursive directory scanning for local source documents.
- Raw text ingestion through the HTTP API.
- Overlapping character-based chunks:
  - Chunk size: 1,000 characters.
  - Chunk overlap: 100 characters.
- Local embeddings using `all-MiniLM-L6-v2`.
- Interactive OpenAPI documentation at `/docs`.
- Application logging to standard output for local and container deployments.

Supported files for startup ingestion:

`.md`, `.txt`, `.pdf`, `.docx`, `.doc`, `.html`, `.htm`, `.json`, and `.csv`.

PDF, DOCX, and HTML extraction requires the corresponding dependencies listed
in [`services/rag/requirements.txt`](../../../services/rag/requirements.txt).

## Project layout

```text
RTA/
├── services/
│   └── rag/
│       ├── data/
│       │   ├── raw_docs/
│       │   └── chroma_db/
│       ├── requirements.txt
│       ├── Dockerfile
│       ├── __init__.py
│       ├── config.py
│       ├── db.py
│       ├── extractors.py
│       ├── logging_config.py
│       └── server.py
├── docs/
│   └── services/rag/README.md
```

The source files above are intentionally kept in one service directory:

```text
services/rag/
├── data/
│   ├── raw_docs/             # Documents scanned at service startup
│   └── chroma_db/            # Persistent ChromaDB files
├── requirements.txt
├── Dockerfile
└── server.py
```

## How ingestion works

When the service starts, it recursively scans `services/rag/data/raw_docs/`. Each supported
file is converted to text, split into overlapping chunks, embedded, and added
to the `cyber_knowledge` ChromaDB collection.

The service records each source path in chunk metadata and skips a source path
that is already indexed. This means startup synchronization is additive: edits
to an already-indexed file are not automatically re-indexed. To rebuild the
index, stop the service and remove the contents of `services/rag/data/chroma_db/`, then
start it again.

Documents can also be added directly through `POST /documents/load`. That
endpoint accepts raw text only; directory paths are not accepted through the
HTTP API.

## API

The default service address is `http://127.0.0.1:8000`.

### `GET /health`

Returns the service status and number of indexed chunks.

```json
{
  "status": "online",
  "total_chunks_in_db": 1420
}
```

### `POST /documents/load`

Adds one raw text document to the collection.

Request:

```json
{
  "title": "linux-privilege-escalation.md",
  "content": "# SUID binaries\nUse find to locate SUID files..."
}
```

Response:

```json
{
  "status": "success",
  "message": "Document 'linux-privilege-escalation.md' loaded successfully.",
  "chunks_loaded": 1
}
```

Both `title` and `content` must be non-empty.

### `POST /query`

Performs a similarity search. `top_k` defaults to `5` and must be between `1`
and `100`.

Request:

```json
{
  "query": "How can I enumerate SMB shares?",
  "top_k": 3
}
```

Response:

```json
{
  "query": "How can I enumerate SMB shares?",
  "result_count": 1,
  "retrieved_documents": [
    {
      "content": "Relevant indexed text...",
      "metadata": {
        "title": "smb.md",
        "source": "smb.md",
        "chunk_index": 0
      },
      "distance": 0.2415
    }
  ]
}
```

The `distance` is the value returned by ChromaDB for the configured collection;
consumers should use it for ranking rather than treating it as a probability.

## Run locally

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r services/rag/requirements.txt
python -m uvicorn services.rag.server:app --host 127.0.0.1 --port 8000
```

Place documents in `services/rag/data/raw_docs/` before launching the service. The first
startup may take time because the embedding model may need to be initialized.

Check the service:

```bash
curl http://127.0.0.1:8000/health
```

Query it:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"SUID privilege escalation","top_k":3}'
```

Open the API documentation at
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Run in Docker

Build the image from the service directory. The Dockerfile uses that directory
as its build context and copies the service directly into `/app`.

```bash
cd services/rag
docker build -t rta-rag .
```

Run the service:

```bash
docker run --rm \
  --name rta-rag \
  -p 127.0.0.1:8000:8000 \
  -v "$(pwd)/data/raw_docs:/app/rag/data/raw_docs:ro" \
  -v "$(pwd)/data/chroma_db:/app/rag/data/chroma_db" \
  rta-rag
```

The first volume makes local documents available to the container. The second
persists the generated ChromaDB index on the host. If the directories do not
exist, create them first:

```bash
mkdir -p data/raw_docs data/chroma_db
```

Verify the container:

```bash
curl http://127.0.0.1:8000/health
docker logs rta-rag
```

The port is explicitly bound to loopback in the example. Change the
`127.0.0.1:8000:8000` mapping only when the service must be reachable from
another trusted host, and protect it with appropriate network controls.

## Configuration

Runtime defaults are defined in [`services/rag/config.py`](../../../services/rag/config.py):

| Setting | Default |
| --- | --- |
| Host | `localhost` locally, `0.0.0.0` in the container command |
| Port | `8000` |
| Embedding model | `all-MiniLM-L6-v2` |
| Chunk size | `1000` characters |
| Chunk overlap | `100` characters |
| Default query results | `5` |

The current service settings are code-based; environment-variable configuration
is not implemented for them. Logging can be configured with the
`RAG_LOG_LEVEL` environment variable.

## Logging

The service writes logs to standard output. Each entry includes a timestamp,
severity, logger name, and message. The default level is `INFO`.

Set a different level when troubleshooting:

```bash
RAG_LOG_LEVEL=DEBUG python -m uvicorn services.rag.server:app --host 127.0.0.1 --port 8000
```

Supported standard levels include `DEBUG`, `INFO`, `WARNING`, and `ERROR`.
Invalid values prevent the service from starting instead of silently falling
back to an unexpected level.

HTTP requests include a generated `X-Request-ID` in the response. Clients may
send their own `X-Request-ID` to correlate requests with application logs.
Request logs include the HTTP method, path, status code, request ID, and
duration. Request bodies, query text, and document contents are intentionally
not logged.

In Docker, configure the level with `-e` and inspect the output with
`docker logs`:

```bash
docker run --rm \
  --name rta-rag \
  -e RAG_LOG_LEVEL=DEBUG \
  -p 127.0.0.1:8000:8000 \
  -v "$(pwd)/data/raw_docs:/app/rag/data/raw_docs:ro" \
  -v "$(pwd)/data/chroma_db:/app/rag/data/chroma_db" \
  rta-rag
```

## Operational notes

- ChromaDB and the embedding model are local dependencies, but the first model
  initialization may require access to an existing model cache or model
  download, depending on the environment.
- Do not mount sensitive documents into a container or expose the API beyond
  the intended trusted network.
- There is no authentication or authorization layer in this service.
- The service is a retrieval component for the broader red-team system; it
  does not perform target discovery, command execution, or safety validation.
