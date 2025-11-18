"""
Configuration module for Qdrant RAG MCP Server.

Handles environment variables and provides fallback to app defaults.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class MCPConfig:
    """Configuration for MCP server with environment variable support."""
    
    def __init__(self):
        # API Configuration
        self.api_url = os.getenv("SEARCH_API_URL", "http://localhost:8001")
        self.api_key = os.getenv("SEARCH_API_KEY")  # Optional
        
        # Qdrant Configuration
        self.qdrant_host = os.getenv("QDRANT_HOST")  # Optional override
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")  # Optional override
        self.qdrant_collection = os.getenv("QDRANT_COLLECTION", "content")
        
        # Ollama Configuration
        self.ollama_url = os.getenv("OLLAMA_HOST")  # Optional override
        self.ollama_api_key = os.getenv("OLLAMA_API_KEY")  # Optional for Ollama Cloud
        
        # Embedding Configuration (provider-specific)
        self.embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "bge-m3")
        self.embedding_dimensions = int(os.getenv("OLLAMA_EMBEDDING_DIMENSIONS", "1024"))
        
        # Default Settings
        self.use_production = os.getenv("USE_PRODUCTION", "true").lower() == "true"
        self.default_context_window = int(os.getenv("CONTEXT_WINDOW_SIZE", "5"))
        self.default_limit = int(os.getenv("DEFAULT_RESULT_LIMIT", "2"))
    
    def get_headers(self) -> dict:
        """
        Build HTTP headers with optional API key authentication.
        
        Returns:
            dict: Headers for API requests
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def build_search_payload(
        self,
        search_queries: list[str],
        limit: Optional[int] = None,
        context_window_size: Optional[int] = None,
        filter_dict: Optional[dict] = None
    ) -> dict:
        """
        Build API request payload with MCP config + LLM parameters.
        
        Args:
            search_queries: List of search query strings
            limit: Max results per query (uses default if None)
            context_window_size: Pages before/after match (uses default if None)
            filter_dict: Optional filter conditions
            
        Returns:
            dict: Complete API request payload
        """
        payload = {
            "search_queries": search_queries,
            "collection_name": self.qdrant_collection,
            "limit": limit or self.default_limit,
            "embedding_model": self.embedding_model,
            "context_window_size": context_window_size or self.default_context_window,
            "use_production": self.use_production
        }
        
        # Add optional filter
        if filter_dict:
            payload["filter"] = filter_dict
        
        # Override with MCP config if set (allows bypassing app defaults)
        if self.qdrant_host:
            payload["qdrant_url"] = self.qdrant_host
        if self.qdrant_api_key:
            payload["qdrant_api_key"] = self.qdrant_api_key
        if self.ollama_url:
            payload["ollama_url"] = self.ollama_url
        if self.ollama_api_key:
            payload["ollama_api_key"] = self.ollama_api_key
            
        return payload
    
    def __repr__(self) -> str:
        """String representation (hides sensitive data)."""
        return (
            f"MCPConfig("
            f"api_url={self.api_url}, "
            f"api_key={'***' if self.api_key else 'None'}, "
            f"collection={self.qdrant_collection}, "
            f"embedding_model={self.embedding_model})"
        )
