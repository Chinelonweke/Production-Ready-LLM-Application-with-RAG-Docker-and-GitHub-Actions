# app/models/__init__.py
"""
Models package for data structures and database interfaces.

This package contains:
- Vector store management with FREE HuggingFace embeddings
- Data models
- Database interfaces

Features:
- FREE embeddings using HuggingFace all-MiniLM-L6-v2
- No API keys required for embeddings
- Local processing for privacy
- ChromaDB for vector storage
"""

from .vector_store import VectorStore

__all__ = ["VectorStore"]

# Version info
__version__ = "2.0.0"
__embedding_model__ = "HuggingFace: all-MiniLM-L6-v2"
__embedding_cost__ = "FREE"