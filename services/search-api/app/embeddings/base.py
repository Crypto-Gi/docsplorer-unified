"""
Base embedding client protocol.

Defines the interface that all embedding providers must implement.
"""

from typing import List, Protocol


class EmbeddingClient(Protocol):
    """
    Protocol for embedding generation clients.
    
    All embedding providers (Ollama, Gemini, etc.) must implement this interface.
    """

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors, one per input text.
            Each vector is a list of floats.
            Order must match input order.

        Raises:
            EmbeddingProviderError: On provider-specific failures.
            ValueError: On invalid input (e.g., empty texts).
        """
        ...

    def embed_one(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Convenience method that wraps embed() for single-text use cases.

        Args:
            text: Text string to embed.

        Returns:
            Embedding vector as a list of floats.

        Raises:
            EmbeddingProviderError: On provider-specific failures.
            ValueError: On invalid input (e.g., empty text).
        """
        ...


class EmbeddingProviderError(Exception):
    """
    Base exception for embedding provider errors.
    
    Raised when an embedding provider encounters an error
    (network, auth, rate limit, etc.).
    """
    pass
