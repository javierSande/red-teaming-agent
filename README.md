# RTA (Red Teaming Agent)

An offline, local multi-agent system designed for automated cybersecurity assessments and security testing in isolated environments. The framework integrates local LLMs (via Ollama), a retrieval-augmented generation (RAG) knowledge engine, deterministic target-scope guardrails, and a Human-in-the-Loop (HITL) approval gateway before executing commands inside a sandboxed Docker environment.

---

## Features

* **Strict Scope Isolation:** Hardcoded IP and CIDR validation ensuring actions cannot run against unauthorized targets outside your predefined scope.
* **Human-in-the-Loop (HITL) Controls:** Requires explicit human operator authorization (`y/N`) before any CLI command executes in the sandbox.
* **Specialized Subagent Workflow:**
  * **Planner Agent:** Breaks down assessment objectives into structured subtasks.
  * **Recon Agent:** Formulates initial discovery and service enumeration commands.
  * **Analysis Agent:** Evaluates service configuration output and formulates specific testing checks.
  * **Reporting Agent:** Summarizes findings and execution history into Markdown reports.
* **Local Knowledge Retrieval (RAG):** Uses ChromaDB to index local reference notes and methodology documentation offline.
* **Containerized Execution Sandbox:** Runs commands inside an isolated Docker container, keeping the host operating system clean and safe.

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                        INTERFACE LAYER                          │
│         CLI Dashboard (rich / prompt_toolkit / Streamlit)       │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR & AGENT SYSTEM                    │
│  - Supervisor Router (LangGraph / State Machine)                 │
│  - Planner Agent | Recon Agent | Analysis Agent | Reporter Agent │
│  - Shared State Store (SQLite / JSON)                            │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                  LOCAL LLM INFERENCE ENGINE                        │
│  - Ollama Daemon ([http://127.0.0.1:11434](http://127.0.0.1:11434))│
│  - qwen2.5-coder:14b (Tooling) & llama3.1:8b (Summarization)       │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LOCAL KNOWLEDGE ENGINE (RAG)                   │
│  - ChromaDB + sentence-transformers (all-MiniLM-L6-v2)          │
│  - Offline Reference Notes & Documentation                      │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SAFETY & GUARDRAIL ENGINE                    │
│  - Target Scope Validator (Hardcoded CIDR Check via ipaddress)  │
│  - Command Syntax Sanitizer & Operator Blacklist                │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│               HUMAN-IN-THE-LOOP (HITL) GATEWAY                  │
│  - Operator Review & Interactive Confirmation Prompt (y/N)      │
└────────────────────────────────┬────────────────────────────────┘
                                 │ Approved Commands
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ISOLATED TOOL EXECUTOR                       │
│  - Persistent Docker Container Sandbox (Debian / Kali Base)     │
│  - Restricted Capability Profile & Isolated Local Network       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites & Dependencies

### System Requirements
* **OS:** Ubuntu 24.04 LTS (or compatible Linux distribution)
* **RAM:** 32 GB recommended (Minimum 16 GB for 8B/14B quantized models)
* **Software:** Docker Engine, Python 3.12+, Git, Curl

---

## Installation & Setup

### 1. Install System Dependencies & Docker

```bash
sudo apt update && sudo apt install -y docker.io git curl python3-pip python3-venv

# Add current user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Install & Start Ollama

```bash
# Install Ollama
curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh

# Pull primary local models
ollama pull qwen2.5-coder:14b
ollama pull llama3.1:8b
```

### 3. Clone Repository & Set Up Python Environment

```bash
git clone [https://github.com/your-username/cyber-agent-framework.git](https://github.com/your-username/cyber-agent-framework.git)
cd cyber-agent-framework

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

---

## Configuration

The current model and agent settings are defined in
[`rta/agents/config.py`](rta/agents/config.py), while the provider-neutral model
settings are in [`rta/core/config.py`](rta/core/config.py). Set the Ollama
endpoint before starting an agent:

```python
OLLAMA_HOST = "http://127.0.0.1:11434"
```

```bash
export OLLAMA_HOST=http://127.0.0.1:11434
```

Target-scope guardrails and command execution are planned framework
components; they are not implemented in the current tree.

---

## Current usage

The repository currently contains the RTA framework package, an independent RAG
service, and the information retrieval agent. Start the RAG service first by
following the [RAG service documentation](docs/services/rag/README.md).

Install all currently declared dependencies from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The retrieval agent is used as a Python component:

```python
from rta.agents.retrieval_agent import InformationRetrievalAgent
from rta.tools.rag_client import RAGClient

agent = InformationRetrievalAgent(
    RAGClient("http://127.0.0.1:8000"),
)
result = agent.run("How can SUID binaries be identified?")
```

See the [retrieval agent documentation](docs/rta/agents/retrieval_agent/README.md)
for model configuration and provider replacement.

To test the currently available agent through the temporary CLI:

```bash
python -m rta.cli
```

The CLI currently uses a temporary local adapter. Its defaults, including the
retrieval `top_k` value, are centralized in the temporary CLI configuration
table at [`rta/cli/config.py`](rta/cli/config.py).

### Build service images

Build every service image from the repository root:

```bash
./scripts/build_services.sh
```

The script discovers Dockerfiles under `services/*/`, builds each service using
that service's directory as the Docker build context, and tags images as
`rta-<service-name>`. For example, the RAG service is tagged `rta-rag`.

Use a different image-name prefix when needed:

```bash
DOCKER_IMAGE_PREFIX=my-project ./scripts/build_services.sh
```

## Project structure

```text
RTA/
├── rta/                  # Framework code used by agents
│   ├── core/             # Provider-neutral model abstractions
│   ├── agents/           # Agent implementations
│   ├── tools/            # Service clients and integrations
│   └── requirements.txt  # Framework dependencies
├── services/
│   └── rag/              # Independently deployable RAG service
├── docs/                 # Framework and service documentation
└── requirements.txt
```

---

## Disclaimer & Legal Notice

This project is created strictly for educational purposes, defensive security research, and authorized assessment of self-hosted local laboratory environments. All execution paths require manual approval and are strictly limited to hardcoded IP scopes. Always obtain explicit written permission before performing security evaluations on any network or system.