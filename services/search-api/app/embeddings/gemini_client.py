"""
Google Gemini embedding client implementation.

Integrates with the Gemini Embeddings API for query-time embedding generation.
"""

import logging
import requests
from typing import List, Optional

from app.embeddings.base import EmbeddingProviderError

logger = logging.getLogger(__name__)


class GeminiEmbeddingClient:
    """
    Embedding client for Google Gemini.
    
    Uses the Gemini Embeddings API with configurable task types and dimensionality.
    Designed for RETRIEVAL_QUERY task type (query-time embeddings).
    """

    # Gemini API endpoint
    EMBED_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"
    BATCH_EMBED_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-001",
        task_type: str = "RETRIEVAL_QUERY",
        output_dimensionality: Optional[int] = 768,
        timeout: int = 5,
    ):
        """
        Initialize Gemini embedding client.

        Args:
            api_key: Gemini API key for authentication.
            model: Gemini embedding model name (default: gemini-embedding-001).
            task_type: Task type for embeddings (default: RETRIEVAL_QUERY).
            output_dimensionality: Output vector dimension (default: 768).
                Must match Qdrant collection vector size.
            timeout: Request timeout in seconds (default: 5).

        Raises:
            ValueError: If api_key is empty or output_dimensionality is invalid.
        """
        if not api_key or not api_key.strip():
            raise ValueError("api_key cannot be empty")
        
        if output_dimensionality and output_dimensionality not in [128, 256, 512, 768, 1536, 2048, 3072]:
            logger.warning(
                f"output_dimensionality={output_dimensionality} is not a recommended value. "
                "Recommended: 768, 1536, or 3072."
            )

        self.api_key = api_key
        self.model = model
        self.task_type = task_type
        self.output_dimensionality = output_dimensionality
        self.timeout = timeout

        logger.info(
            f"Initialized GeminiEmbeddingClient with model={model}, "
            f"task_type={task_type}, output_dim={output_dimensionality}"
        )

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using Gemini.

        Uses batch embedding endpoint for efficiency.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingProviderError: On Gemini API failures.
            ValueError: On invalid input.
        """
        if not texts:
            raise ValueError("texts list cannot be empty")

        for text in texts:
            if not text or not text.strip():
                raise ValueError("text cannot be empty or whitespace-only")

        try:
            # Build batch request payload
            # Note: batchEmbedContents expects "requests" array with each request
            # containing model, content, task_type, and output_dimensionality
            requests_payload = []
            for text in texts:
                req = {
                    "model": f"models/{self.model}",
                    "content": {"parts": [{"text": text}]},
                }
                if self.task_type:
                    req["task_type"] = self.task_type
                if self.output_dimensionality:
                    req["output_dimensionality"] = self.output_dimensionality
                
                requests_payload.append(req)

            payload = {"requests": requests_payload}

            # Call Gemini batch embeddings API
            url = self.BATCH_EMBED_ENDPOINT.format(model=self.model)
            headers = {
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            # Handle errors
            if response.status_code != 200:
                error_detail = self._sanitize_error(response)
                logger.error(f"Gemini API error: {response.status_code} - {error_detail}")
                raise EmbeddingProviderError(
                    f"Gemini API returned {response.status_code}: {error_detail}"
                )

            # Parse response
            data = response.json()
            embeddings = []
            
            for embedding_response in data.get("embeddings", []):
                values = embedding_response.get("values", [])
                if not values:
                    raise EmbeddingProviderError("Gemini returned empty embedding")
                embeddings.append(values)

            if len(embeddings) != len(texts):
                raise EmbeddingProviderError(
                    f"Gemini returned {len(embeddings)} embeddings for {len(texts)} texts"
                )

            logger.debug(f"Generated {len(embeddings)} embeddings via Gemini")
            return embeddings

        except requests.exceptions.Timeout:
            logger.error("Gemini API request timed out")
            raise EmbeddingProviderError("Gemini API request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API request error: {e}")
            raise EmbeddingProviderError(f"Gemini API request failed: {e}") from e
        except EmbeddingProviderError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Gemini embedding: {e}")
            raise EmbeddingProviderError(f"Gemini embedding failed: {e}") from e

    def embed_one(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using Gemini.

        Args:
            text: Text string to embed.

        Returns:
            Embedding vector.

        Raises:
            EmbeddingProviderError: On Gemini API failures.
            ValueError: On invalid input.
        """
        if not text or not text.strip():
            raise ValueError("text cannot be empty or whitespace-only")

        try:
            # Build request payload
            payload = {
                "content": {"parts": [{"text": text}]},
            }
            if self.task_type:
                payload["task_type"] = self.task_type
            if self.output_dimensionality:
                payload["output_dimensionality"] = self.output_dimensionality

            # Call Gemini embeddings API
            url = self.EMBED_ENDPOINT.format(model=self.model)
            headers = {
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            # Handle errors
            if response.status_code != 200:
                error_detail = self._sanitize_error(response)
                logger.error(f"Gemini API error: {response.status_code} - {error_detail}")
                raise EmbeddingProviderError(
                    f"Gemini API returned {response.status_code}: {error_detail}"
                )

            # Parse response
            data = response.json()
            embedding_data = data.get("embedding", {})
            values = embedding_data.get("values", [])
            
            if not values:
                raise EmbeddingProviderError("Gemini returned empty embedding")

            logger.debug(f"Generated single embedding via Gemini (dim={len(values)})")
            return values

        except requests.exceptions.Timeout:
            logger.error("Gemini API request timed out")
            raise EmbeddingProviderError("Gemini API request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API request error: {e}")
            raise EmbeddingProviderError(f"Gemini API request failed: {e}") from e
        except EmbeddingProviderError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Gemini embedding: {e}")
            raise EmbeddingProviderError(f"Gemini embedding failed: {e}") from e

    def _sanitize_error(self, response: requests.Response) -> str:
        """
        Sanitize error response for logging/client display.
        
        Removes sensitive information while preserving useful error details.
        
        Args:
            response: HTTP response object.
            
        Returns:
            Sanitized error message.
        """
        try:
            error_json = response.json()
            # Extract error message if available
            if "error" in error_json:
                error_obj = error_json["error"]
                if isinstance(error_obj, dict):
                    return error_obj.get("message", "Unknown error")
                return str(error_obj)
            return "Unknown error"
        except Exception:
            return response.text[:200] if response.text else "Unknown error"
