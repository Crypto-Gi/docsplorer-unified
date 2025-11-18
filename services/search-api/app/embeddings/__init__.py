"""
Embedding provider abstraction for the semantic search API.

This module provides a pluggable architecture for embedding generation,
allowing the service to use different providers (Ollama, Gemini, etc.)
without changing core search logic.
"""

from app.embeddings.base import EmbeddingClient
from app.embeddings.factory import EmbeddingProviderFactory
from app.embeddings.ollama_client import OllamaEmbeddingClient
from app.embeddings.gemini_client import GeminiEmbeddingClient

__all__ = [
    "EmbeddingClient",
    "EmbeddingProviderFactory",
    "OllamaEmbeddingClient",
    "GeminiEmbeddingClient",
]
