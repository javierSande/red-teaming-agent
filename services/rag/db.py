import os
import logging
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions

from .config import (CHROMA_DB_DIR, DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE,
                     DEFAULT_DATA_DIR, DEFAULT_TOP_K, EMBEDDING_MODEL_NAME,
                     SUPPORTED_FILE_EXTENSIONS)
from .extractors import FileExtractor

logger = logging.getLogger(__name__)


class VectorDatabase:
    def __init__(self):
        # Initialize the ChromaDB client and set up the embedding function
        self.client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )

        # Create or retrieve the collection for storing documents
        self.collection = self.client.get_or_create_collection(
            name="cyber_knowledge",
            embedding_function=self.embedding_fn
        )
        logger.info(
            "Vector database initialized: path=%s collection=%s chunks=%d",
            CHROMA_DB_DIR,
            self.collection.name,
            self.collection.count(),
        )

    def _chunk_documents(self,
                         document: str,
                         chunk_size: int = DEFAULT_CHUNK_SIZE,
                         chunk_overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[str]:
        """Splits documents into smaller chunks for better retrieval."""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size")

        chunks = []
        start_index = 0
        while start_index < len(document):
            end_index = min(start_index + chunk_size, len(document))
            chunk = document[start_index:end_index]
            chunks.append(chunk)
            start_index = end_index - chunk_overlap
        return chunks

    def add_document(self,
                     title: str,
                     content: str,
                     source: Optional[str] = None) -> int:
        """Adds a single document to the database."""
        chunks = self._chunk_documents(content)
        documents, metadatas, ids = [], [], []
        document_id = f"{title}_{os.urandom(4).hex()}"

        if not source:
            source = f"remote://{document_id}"

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{idx}"
            documents.append(chunk)
            metadatas.append({
                "title": title,
                "source": source,
                "chunk_index": idx
            })
            ids.append(chunk_id)

        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        logger.info(
            "Document indexed: title=%s source=%s chunks=%d",
            title,
            source,
            len(documents),
        )
        return len(documents)

    def get_indexed_documents(self) -> set[str]:
        """Returns a list of all indexed documents with their metadata."""
        results = self.collection.get(include=["metadatas"])
        if results and "metadatas" in results:
            return {meta["source"] for meta in results["metadatas"] if "source" in meta}
        return set()

    def synchronize_with_directory(self, directory_path: str = DEFAULT_DATA_DIR) -> Dict[str, int]:
        """Synchronizes the database with the default data directory."""
        directory_path = Path(directory_path)
        logger.info("Starting directory synchronization: path=%s", directory_path)
        indexed_documents = self.get_indexed_documents()
        new_total_files = 0
        new_total_chunks = 0

        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in SUPPORTED_FILE_EXTENSIONS:
                    relative_path = file_path.relative_to(directory_path).as_posix()
                    if relative_path in indexed_documents:
                        logger.debug("Skipping already indexed source: source=%s", relative_path)
                        continue
                    try:
                        content = FileExtractor.extract_text(file_path)
                        if content:
                            chunks_added = self.add_document(title=relative_path,
                                                             content=content,
                                                             source=str(relative_path))
                            new_total_chunks += chunks_added
                            new_total_files += 1

                    except (OSError, ValueError, ImportError) as exc:
                        logger.exception("Error processing source: path=%s", file_path)

        stats = {
            "files_processed": new_total_files,
            "chunks_indexed": new_total_chunks
        }
        logger.info(
            "Directory synchronization complete: path=%s files=%d chunks=%d",
            directory_path,
            new_total_files,
            new_total_chunks,
        )
        return stats

    def delete_all_documents(self) -> None:
        """Deletes all documents from the database."""
        self.collection.delete(where={})
        logger.warning("All indexed documents deleted: collection=%s", self.collection.name)

    def query(self,
              query_text: str,
              top_k: int = DEFAULT_TOP_K) -> List[Dict]:
        """Queries the database for the most relevant documents."""
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k
        )
        formatted_results = []

        if results and results["documents"]:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results.get("distances", [[]])[0]

            for doc, meta, distance in zip(documents, metadatas, distances):
                formatted_results.append({
                    "document": doc,
                    "metadata": meta,
                    "distance": distance
                })

        logger.info("Query completed: top_k=%d results=%d", top_k, len(formatted_results))
        return formatted_results

    def count(self) -> int:
        """Returns the total number of documents in the database."""
        return self.collection.count()