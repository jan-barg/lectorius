"""RAG stage — embed chunks and upload to Supabase pgvector."""

from .runner import run_rag

__all__ = ["run_rag"]
