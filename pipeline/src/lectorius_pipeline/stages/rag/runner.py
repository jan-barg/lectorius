"""RAG stage runner — embed chunks and build FAISS index."""

import json
import logging
import os
from pathlib import Path

import faiss
import numpy as np
from supabase import create_client

from lectorius_pipeline.errors import RAGError
from lectorius_pipeline.schemas import Chunk, RAGMeta, RAGReport

from .embedder import Embedder

logger = logging.getLogger(__name__)


def run_rag(
    book_dir: Path,
    book_id: str,
    model: str | None = None,
    batch_size: int = 100,
) -> RAGReport:
    """Run the RAG stage: embed all chunks and build a FAISS index.

    Args:
        book_dir: Path to book output directory.
        book_id: Book identifier.
        model: Embedding model name. Defaults to text-embedding-3-small.
        batch_size: Chunks per API call.

    Returns:
        RAGReport with processing stats.

    Raises:
        RAGError: If the stage fails critically.
    """
    logger.info("Starting RAG stage for %s", book_id)

    # Load chunks
    chunks = _load_chunks(book_dir)
    logger.info("Loaded %d chunks for embedding", len(chunks))

    # Create embedder
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RAGError("OPENAI_API_KEY environment variable not set")

    embedder = Embedder(api_key=api_key, model=model or "text-embedding-3-small", batch_size=batch_size)

    # Batch embed all chunks
    all_embeddings: list[list[float]] = []
    total_batches = (len(chunks) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        start = batch_idx * batch_size
        end = min(start + batch_size, len(chunks))
        batch_texts = [c.text for c in chunks[start:end]]

        logger.info("Embedding batch %d/%d (%d chunks)", batch_idx + 1, total_batches, len(batch_texts))
        embeddings = embedder.embed_batch(batch_texts)
        all_embeddings.extend(embeddings)

    logger.info("Embedded %d chunks, building FAISS index", len(all_embeddings))

    # Build FAISS index
    embeddings_np = np.array(all_embeddings, dtype=np.float32)
    faiss.normalize_L2(embeddings_np)

    dimensions = embeddings_np.shape[1]
    index = faiss.IndexFlatIP(dimensions)  # inner product = cosine sim after L2 norm
    index.add(embeddings_np)

    # Save index
    rag_dir = book_dir / "rag"
    rag_dir.mkdir(parents=True, exist_ok=True)

    index_path = rag_dir / "index.faiss"
    faiss.write_index(index, str(index_path))
    logger.info("Wrote FAISS index: %d vectors, %d dimensions", index.ntotal, dimensions)

    # Write metadata
    meta_path = rag_dir / "meta.jsonl"
    with open(meta_path, "w") as f:
        for i, chunk in enumerate(chunks):
            meta = RAGMeta(
                vector_id=i,
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                chapter_id=chunk.chapter_id,
            )
            f.write(meta.model_dump_json() + "\n")
    logger.info("Wrote %d metadata entries to meta.jsonl", len(chunks))

    # Insert embeddings into Supabase pgvector
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not supabase_url or not supabase_key:
        raise RAGError("SUPABASE_URL or SUPABASE_SERVICE_KEY environment variable not set")

    supabase = create_client(supabase_url, supabase_key)

    rows = []
    for i, chunk in enumerate(chunks):
        rows.append({
            "book_id": book_id,
            "chunk_id": chunk.chunk_id,
            "chunk_index": chunk.chunk_index,
            "chapter_id": chunk.chapter_id,
            "embedding": embeddings_np[i].tolist(),
        })

    # Delete existing embeddings for this book (in case of re-run)
    supabase.table("book_embeddings").delete().eq("book_id", book_id).execute()

    # Insert in batches of 100
    insert_batch_size = 100
    total_insert_batches = (len(rows) + insert_batch_size - 1) // insert_batch_size
    for i in range(0, len(rows), insert_batch_size):
        batch = rows[i : i + insert_batch_size]
        supabase.table("book_embeddings").insert(batch).execute()
        logger.info(
            "Inserted embeddings batch %d/%d", i // insert_batch_size + 1, total_insert_batches
        )

    logger.info("Inserted %d embeddings to Supabase", len(rows))

    # Build report
    report = RAGReport(
        success=True,
        book_id=book_id,
        embedding_model=embedder.model,
        total_chunks=len(chunks),
        vectors_indexed=index.ntotal,
        dimensions=dimensions,
        index_type="IndexFlatIP",
    )

    # Write report
    reports_dir = book_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "rag.json"
    report_path.write_text(report.model_dump_json(indent=2))

    logger.info("RAG stage completed: %d vectors indexed", index.ntotal)
    return report


def _load_chunks(book_dir: Path) -> list[Chunk]:
    """Load chunks from chunks.jsonl."""
    chunks_path = book_dir / "chunks.jsonl"
    if not chunks_path.exists():
        raise RAGError(f"chunks.jsonl not found in {book_dir}")

    chunks: list[Chunk] = []
    with open(chunks_path) as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(Chunk.model_validate_json(line))

    if not chunks:
        raise RAGError("chunks.jsonl is empty")

    return chunks
