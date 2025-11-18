"""
Ollama embedding client implementation.

Wraps the existing Ollama embedding logic into the EmbeddingClient interface.
"""

import logging
from typing import List
from ollama import Client as OllamaClient

from app.embeddings.base import EmbeddingProviderError

logger = logging.getLogger(__name__)


class OllamaEmbeddingClient:
    """
    Embedding client for Ollama.
    
    Wraps the existing Ollama client to conform to the EmbeddingClient protocol.
    Preserves all current behavior for backward compatibility.
    """

    def __init__(self, host: str, model: str):
        """
        Initialize Ollama embedding client.

        Args:
            host: Ollama server host (e.g., "http://localhost:11434").
            model: Embedding model name (e.g., "mxbai-embed-large").
        """
        self.host = host
        self.model = model
        self.client = OllamaClient(host=host)
        logger.info(f"Initialized OllamaEmbeddingClient with host={host}, model={model}")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using Ollama.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingProviderError: On Ollama API failures.
            ValueError: On invalid input.
        """
        if not texts:
            raise ValueError("texts list cannot be empty")

        try:
            embeddings = []
            for text in texts:
                if not text or not text.strip():
                    raise ValueError("text cannot be empty or whitespace-only")
                
                # Call Ollama embeddings API (existing behavior)
                response = self.client.embeddings(model=self.model, prompt=text)
                embeddings.append(response["embedding"])
            
            logger.debug(f"Generated {len(embeddings)} embeddings via Ollama")
            return embeddings

        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            raise EmbeddingProviderError(f"Ollama embedding failed: {e}") from e

    def embed_one(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using Ollama.

        Args:
            text: Text string to embed.

        Returns:
            Embedding vector.

        Raises:
            EmbeddingProviderError: On Ollama API failures.
            ValueError: On invalid input.
        """
        if not text or not text.strip():
            raise ValueError("text cannot be empty or whitespace-only")

        try:
            # Call Ollama embeddings API (existing behavior)
            response = self.client.embeddings(model=self.model, prompt=text)
            embedding = response["embedding"]
            
            logger.debug(f"Generated single embedding via Ollama (dim={len(embedding)})")
            return embedding

        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            raise EmbeddingProviderError(f"Ollama embedding failed: {e}") from e
