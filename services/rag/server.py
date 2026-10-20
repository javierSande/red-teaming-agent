from contextlib import asynccontextmanager
import logging
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from .config import DEFAULT_DATA_DIR, DEFAULT_TOP_K, HOST, PORT
from .db import VectorDatabase
from .logging_config import configure_logging

# --- FastAPI Application Setup ---
configure_logging()
logger = logging.getLogger(__name__)
db = VectorDatabase()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup events for the FastAPI application."""
    logger.info("Starting RAG Knowledge Service")
    stats = db.synchronize_with_directory(DEFAULT_DATA_DIR)
    logger.info(
        "RAG Knowledge Service ready: files=%d chunks=%d",
        stats["files_processed"],
        stats["chunks_indexed"],
    )
    yield
    logger.info("Stopping RAG Knowledge Service")

app = FastAPI(
    title="Modular RAG Knowledge Service",
    description="Local document ingestion and contextual retrieval API.",
    version="0.1.0",
    lifespan=lifespan
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", uuid4().hex)
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Request failed: request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        raise

    duration_ms = (time.perf_counter() - started_at) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "Request completed: request_id=%s method=%s path=%s status=%d duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# --- Data Models ---

class LoadDocumentRequest(BaseModel):
    title: str = Field(..., description="Title of the document to be loaded.")
    content: str = Field(..., description="Raw text content of the document.")

class LoadDocumentResponse(BaseModel):
    status: str = Field("success", description="Status of the document load operation.")
    message: Optional[str] = Field(None, description="Additional information about the operation.")
    chunks_loaded: Optional[int] = Field(None, description="Number of chunks added to the database.")

class QueryResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    distance: float

class QueryRequest(BaseModel):
    query: str
    top_k: int = Field(DEFAULT_TOP_K, ge=1, le=100)

class QueryResponse(BaseModel):
    query: str
    result_count: int
    retrieved_documents: List[QueryResult]

# --- API Endpoints ---

@app.get("/health")
def health_check():
    """Returns the health status of the service and the number of documents in the database."""
    total_chunks = db.count()
    logger.debug("Health check: chunks=%d", total_chunks)
    return {
        "status": "online",
        "total_chunks_in_db": total_chunks
    }

@app.post("/documents/load", response_model=LoadDocumentResponse)
def load_document(request: LoadDocumentRequest):
    """Loads documents into the database either from raw text or by scanning a directory."""
    if not request.title:
        raise HTTPException(status_code=400, detail="Document title cannot be empty.")

    if not request.content:
        raise HTTPException(status_code=400, detail="Document content cannot be empty.")

    total_chunks = db.add_document(title=request.title, content=request.content)
    logger.info("API document load completed: title=%s chunks=%d", request.title, total_chunks)
    return LoadDocumentResponse(
        status="success",
        message=f"Document '{request.title}' loaded successfully.",
        chunks_loaded=total_chunks
    )

@app.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest):
    """Queries the database for the most relevant documents based on the provided query."""
    if not request.query:
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")

    results = db.query(query_text=request.query, top_k=request.top_k)
    logger.info("API query completed: top_k=%d results=%d", request.top_k, len(results))
    return QueryResponse(
        query=request.query,
        result_count=len(results),
        retrieved_documents=[
            QueryResult(
                content=res["document"],
                metadata=res["metadata"],
                distance=res["distance"]
            )
            for res in results
        ]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("rag.server:app", host=HOST, port=PORT, reload=True)