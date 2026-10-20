from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

ORCHESTRATOR_MODEL = "qwen2.5-coder:14b"

RETRIEVAL_MODEL = "qwen2.5-coder:14b"
RETRIEVAL_TEMPERATURE = 0.2
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")