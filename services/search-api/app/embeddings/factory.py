"""
Embedding provider factory.

Creates the appropriate embedding client based on environment configuration.
"""

import logging
import os
from typing import Optional

from app.embeddings.base import EmbeddingClient
from app.embeddings.ollama_client import OllamaEmbeddingClient
from app.embeddings.gemini_client import GeminiEmbeddingClient

logger = logging.getLogger(__name__)


class EmbeddingProviderFactory:
    """
    Factory for creating embedding provider clients.
    
    Reads environment variables to determine which provider to use
    and instantiates the appropriate client.
    """

    @staticmethod
    def from_env() -> EmbeddingClient:
        """
        Create an embedding client based on environment configuration.

        Environment Variables:
            EMBEDDING_PROVIDER: Provider name ("ollama" or "gemini"). Default: "ollama".
            
            For Ollama:
                OLLAMA_HOST: Ollama server host.
                OLLAMA_EMBEDDING_MODEL: Ollama model name.
            
            For Gemini:
                GEMINI_API_KEY: Gemini API key (required).
                GEMINI_EMBEDDING_MODEL: Gemini model name (default: gemini-embedding-001).
                GEMINI_EMBEDDING_TASK_TYPE: Task type (default: RETRIEVAL_QUERY).
                GEMINI_EMBEDDING_DIM: Output dimensionality (default: 768).

        Returns:
            Configured embedding client instance.

        Raises:
            ValueError: If configuration is invalid or missing required values.
        """
        provider = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()

        logger.info(f"Initializing embedding provider: {provider}")

        if provider == "ollama":
            return EmbeddingProviderFactory._create_ollama_client()
        elif provider == "gemini":
            return EmbeddingProviderFactory._create_gemini_client()
        else:
            raise ValueError(
                f"Unknown EMBEDDING_PROVIDER: {provider}. "
                "Supported values: 'ollama', 'gemini'"
            )

    @staticmethod
    def _create_ollama_client() -> OllamaEmbeddingClient:
        """
        Create Ollama embedding client from environment.

        Returns:
            Configured OllamaEmbeddingClient.

        Raises:
            ValueError: If required env vars are missing.
        """
        host = os.getenv("OLLAMA_HOST")
        # Prefer unified OLLAMA_EMBEDDING_MODEL, fall back to legacy DEFAULT_EMBEDDING_MODEL for compatibility
        model = os.getenv("OLLAMA_EMBEDDING_MODEL") or os.getenv("DEFAULT_EMBEDDING_MODEL")

        if not host:
            raise ValueError("OLLAMA_HOST is required when EMBEDDING_PROVIDER=ollama")
        if not model:
            raise ValueError("OLLAMA_EMBEDDING_MODEL is required when EMBEDDING_PROVIDER=ollama")

        return OllamaEmbeddingClient(host=host, model=model)

    @staticmethod
    def _create_gemini_client() -> GeminiEmbeddingClient:
        """
        Create Gemini embedding client from environment.

        Returns:
            Configured GeminiEmbeddingClient.

        Raises:
            ValueError: If required env vars are missing.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini. "
                "Please set this environment variable with your Gemini API key."
            )

        model = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
        task_type = os.getenv("GEMINI_EMBEDDING_TASK_TYPE", "RETRIEVAL_QUERY")
        
        # Parse output dimensionality
        dim_str = os.getenv("GEMINI_EMBEDDING_DIM", "768")
        try:
            output_dim = int(dim_str) if dim_str else 768
        except ValueError:
            raise ValueError(
                f"GEMINI_EMBEDDING_DIM must be an integer, got: {dim_str}"
            )

        return GeminiEmbeddingClient(
            api_key=api_key,
            model=model,
            task_type=task_type,
            output_dimensionality=output_dim,
        )
