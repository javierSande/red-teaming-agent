from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parent
DATA_DIR = SERVICE_DIR / "data"

RAW_DOCS_DIR = DATA_DIR / "raw_docs"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"
DEFAULT_DATA_DIR = RAW_DOCS_DIR

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = 5
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 100
SUPPORTED_FILE_EXTENSIONS = {".md", ".txt", ".pdf", ".docx", ".doc", ".html", ".htm", ".json", ".csv"}

HOST = "localhost"
PORT = 8000