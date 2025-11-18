from fastapi import FastAPI, HTTPException, status, Request, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, conint
from typing import List, Optional, Dict, Union, Any
import logging
import uvicorn
import os
from contextvars import ContextVar
from pythonjsonlogger import jsonlogger
from fastapi.middleware.cors import CORSMiddleware
import uuid
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
import ollama

# ======== Configuration ========
load_dotenv()

# Global settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
QDRANT_FORCE_IGNORE_SSL = os.getenv("QDRANT_FORCE_IGNORE_SSL", "false").lower() == "true"

# Development environment configuration
DEV_QDRANT_URL = os.getenv("DEV_QDRANT_URL", "")
DEV_QDRANT_API_KEY = os.getenv("DEV_QDRANT_API_KEY", "")
DEV_QDRANT_VERIFY_SSL = os.getenv("DEV_QDRANT_VERIFY_SSL", "false").lower() == "true"

# Production environment configuration
PROD_QDRANT_URL = os.getenv("PROD_QDRANT_URL", "")
PROD_QDRANT_API_KEY = os.getenv("PROD_QDRANT_API_KEY", "")
PROD_QDRANT_VERIFY_SSL = os.getenv("PROD_QDRANT_VERIFY_SSL", "true").lower() == "true"

# Fallback configuration (backward compatibility)
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
QDRANT_VERIFY_SSL = os.getenv("QDRANT_VERIFY_SSL", "true").lower() == "true"
QDRANT_HOST = os.getenv("QDRANT_HOST", "192.168.153.47")

# Other services
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "192.168.153.46")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
CONTEXT_WINDOW_SIZE = int(os.getenv("CONTEXT_WINDOW_SIZE", "5"))

# Embedding configuration
DEFAULT_EMBEDDING_MODEL = os.getenv("DEFAULT_EMBEDDING_MODEL", "mxbai-embed-large")
DEFAULT_VECTOR_SIZE = int(os.getenv("DEFAULT_VECTOR_SIZE", "1024"))

# API Key Authentication
API_KEY = os.getenv("API_KEY", "")
API_KEY_ENABLED = os.getenv("API_KEY_ENABLED", "false").lower() == "true"
# ===============================

# ======== Logging Setup ========
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if os.getenv("DEBUG") else logging.INFO)

correlation_id = ContextVar("correlation_id", default="")

class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id.get()
        return True

formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(correlation_id)s %(message)s'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.addFilter(CorrelationIdFilter())
logger.addHandler(handler)
# ===============================

# ======== Configuration Validation ========
def validate_production_config():
    """Validate configuration based on environment mode"""
    if ENVIRONMENT == "production":
        # Determine which URL to check (PROD_QDRANT_URL takes precedence)
        qdrant_url = PROD_QDRANT_URL or QDRANT_URL or f"http://{QDRANT_HOST}"
        
        # Require HTTPS in production
        if not qdrant_url.startswith("https://"):
            logger.error(
                "Production mode requires HTTPS connection to Qdrant",
                extra={"qdrant_url": qdrant_url}
            )
            raise ValueError("Production mode requires QDRANT_URL or PROD_QDRANT_URL with https:// scheme")
        
        # Require API key in production
        api_key = PROD_QDRANT_API_KEY or QDRANT_API_KEY
        if not api_key:
            logger.error("Production mode requires QDRANT_API_KEY or PROD_QDRANT_API_KEY to be configured")
            raise ValueError("Production mode requires QDRANT_API_KEY or PROD_QDRANT_API_KEY")
        
        logger.info("Production configuration validated successfully", extra={
            "https_enabled": True,
            "api_key_configured": True
        })
    else:
        # Log development mode configuration
        dev_url = DEV_QDRANT_URL or QDRANT_URL or f"http://{QDRANT_HOST}"
        dev_api_key = DEV_QDRANT_API_KEY or QDRANT_API_KEY
        
        logger.info(
            "Running in development mode",
            extra={
                "https_enabled": dev_url.startswith("https://") if dev_url else False,
                "api_key_configured": bool(dev_api_key)
            }
        )

# Validate configuration at startup
validate_production_config()
# ===============================

# ======== API Key Authentication ========
security = HTTPBearer(auto_error=False)

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Verify API key from Authorization header.
    If API_KEY_ENABLED is false, authentication is bypassed.
    """
    if not API_KEY_ENABLED:
        # API key authentication is disabled
        return True
    
    if not API_KEY:
        logger.error("API_KEY_ENABLED is true but API_KEY is not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key authentication is enabled but not configured"
        )
    
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if credentials.credentials != API_KEY:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return True
# ===============================

# ======== Exception Classes ========
class SearchException(Exception):
    """Base exception for search-related errors"""

class EmbeddingError(SearchException):
    """Exception for embedding generation failures"""

class QdrantConnectionError(SearchException):
    """Exception for Qdrant connection issues"""
# ===============================

class SearchSystem:
    _qdrant_pool_dev = None
    _qdrant_pool_prod = None
    _ollama_pool = None

    def __init__(self, collection_name: str, use_production: bool = False,
                 qdrant_url: Optional[str] = None, 
                 qdrant_api_key: Optional[str] = None, 
                 qdrant_verify_ssl: Optional[bool] = None,
                 context_window_size: Optional[int] = None):
        self.collection_name = collection_name
        self.context_window_size = context_window_size if context_window_size is not None else CONTEXT_WINDOW_SIZE
        self.use_custom_client = any([qdrant_url, qdrant_api_key, qdrant_verify_ssl is not None])
        
        # Validate: cannot use both use_production flag and custom parameters
        if self.use_custom_client and use_production:
            raise ValueError("Cannot use both use_production flag and custom Qdrant parameters")
        
        if self.use_custom_client:
            # Create custom client for this request (ignore use_production)
            self.qclient = self._create_qdrant_client(
                qdrant_url, qdrant_api_key, qdrant_verify_ssl, use_production=False, is_pooled=False
            )
            self.custom_client = True
        else:
            # Use pooled client (dev or prod based on use_production flag)
            self.qclient = self._get_qdrant_client(use_production)
            self.custom_client = False
        
        self.oclient = self._get_ollama_client()
        self._ensure_collection()

    def __del__(self):
        """Close custom client when instance is destroyed"""
        if self.custom_client and hasattr(self, 'qclient'):
            try:
                self.qclient.close()
            except:
                pass

    @staticmethod
    def _create_qdrant_client(qdrant_url: Optional[str] = None,
                             qdrant_api_key: Optional[str] = None,
                             qdrant_verify_ssl: Optional[bool] = None,
                             use_production: bool = False,
                             is_pooled: bool = False) -> QdrantClient:
        """
        Create a Qdrant client with configuration priority:
        1. Request parameters (qdrant_url, qdrant_api_key, qdrant_verify_ssl)
        2. Environment-specific variables (DEV_* or PROD_* based on use_production)
        3. Generic environment variables (QDRANT_URL, QDRANT_API_KEY, QDRANT_VERIFY_SSL)
        4. Defaults (QDRANT_HOST with http://, no API key, verify SSL for HTTPS)
        """
        from urllib.parse import urlparse
        
        # Determine environment-specific variables
        if use_production:
            env_url = PROD_QDRANT_URL
            env_api_key = PROD_QDRANT_API_KEY
            env_verify_ssl = PROD_QDRANT_VERIFY_SSL
            env_name = "production"
        else:
            env_url = DEV_QDRANT_URL
            env_api_key = DEV_QDRANT_API_KEY
            env_verify_ssl = DEV_QDRANT_VERIFY_SSL
            env_name = "development"
        
        # Priority: Request param > Environment-specific > Generic env > Default
        final_url = qdrant_url or env_url or QDRANT_URL or f"http://{QDRANT_HOST}"
        final_api_key = qdrant_api_key or env_api_key or QDRANT_API_KEY or None
        
        # Parse URL to extract protocol, host, port
        parsed_url = urlparse(final_url)
        protocol = parsed_url.scheme or "http"
        host = parsed_url.hostname
        port = parsed_url.port
        
        # Determine if using HTTPS
        use_https = protocol == "https"
        
        # SSL verification priority
        if qdrant_verify_ssl is not None:
            # Priority 1: Request parameter
            verify_ssl = qdrant_verify_ssl
            config_source = "request_parameter"
        elif QDRANT_FORCE_IGNORE_SSL:
            # Priority 2: Force ignore SSL
            verify_ssl = False
            config_source = "QDRANT_FORCE_IGNORE_SSL"
        elif use_https:
            # Priority 3: Environment-specific > Generic env > Default
            verify_ssl = env_verify_ssl if env_url else QDRANT_VERIFY_SSL
            if env_url:
                config_source = f"{'PROD' if use_production else 'DEV'}_QDRANT_VERIFY_SSL"
            elif "QDRANT_VERIFY_SSL" in os.environ:
                config_source = "QDRANT_VERIFY_SSL"
            else:
                config_source = "default"
        else:
            # HTTP doesn't use SSL
            verify_ssl = False
            config_source = "not_applicable"
        
        # Build client parameters
        client_params = {
            "host": host,
            "timeout": 10,
            "prefer_grpc": True
        }
        
        # Add port if specified
        if port:
            client_params["port"] = port
        
        # Add HTTPS configuration
        if use_https:
            client_params["https"] = True
            client_params["verify"] = verify_ssl
        
        # Add API key if provided
        if final_api_key:
            client_params["api_key"] = final_api_key
        
        # Determine configuration sources for logging
        if qdrant_url:
            url_source = "request_parameter"
        elif env_url:
            url_source = f"{'PROD' if use_production else 'DEV'}_QDRANT_URL"
        elif QDRANT_URL:
            url_source = "QDRANT_URL"
        else:
            url_source = "QDRANT_HOST"
        
        if qdrant_api_key:
            api_key_source = "request_parameter"
        elif env_api_key:
            api_key_source = f"{'PROD' if use_production else 'DEV'}_QDRANT_API_KEY"
        elif QDRANT_API_KEY:
            api_key_source = "QDRANT_API_KEY"
        else:
            api_key_source = "none"
        
        # Log connection details (without API key)
        logger.info(
            "Initializing Qdrant connection",
            extra={
                "connection_type": "pooled" if is_pooled else "custom",
                "environment_mode": env_name,
                "protocol": protocol,
                "host": host,
                "port": port,
                "https": use_https,
                "verify_ssl": verify_ssl if use_https else None,
                "authenticated": bool(final_api_key),
                "global_environment": ENVIRONMENT,
                "config_sources": {
                    "url": url_source,
                    "api_key": api_key_source,
                    "verify_ssl": config_source
                }
            }
        )
        
        return QdrantClient(**client_params)

    @classmethod
    def _get_qdrant_client(cls, use_production: bool = False):
        """Get pooled Qdrant client using environment configuration"""
        pool_attr = '_qdrant_pool_prod' if use_production else '_qdrant_pool_dev'
        
        if getattr(cls, pool_attr) is None:
            try:
                client = cls._create_qdrant_client(
                    qdrant_url=None,
                    qdrant_api_key=None,
                    qdrant_verify_ssl=None,
                    use_production=use_production,
                    is_pooled=True
                )
                setattr(cls, pool_attr, client)
            except Exception as e:
                logger.error(f"Qdrant connection failed: {str(e)}")
                raise QdrantConnectionError("Database connection error")
        
        return getattr(cls, pool_attr)

    @classmethod
    def _get_ollama_client(cls):
        if cls._ollama_pool is None:
            try:
                cls._ollama_pool = ollama.Client(host=OLLAMA_HOST, timeout=10)
            except Exception as e:
                logger.error(f"Ollama connection failed: {str(e)}")
                raise ConnectionError("Embedding service unavailable")
        return cls._ollama_pool

    def _ensure_collection(self):
        if not self.qclient.collection_exists(self.collection_name):
            self.qclient.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=DEFAULT_VECTOR_SIZE,
                    distance=models.Distance.COSINE
                )
            )
            logger.info(f"Created collection '{self.collection_name}' with vector size {DEFAULT_VECTOR_SIZE}")

    def _has_page_structure(self, payload: Dict) -> bool:
        """Check if payload has page-based structure (non-strict validation)"""
        try:
            return (
                "pagecontent" in payload and
                isinstance(payload.get("pagecontent"), str) and
                len(payload.get("pagecontent", "")) > 0 and
                "metadata" in payload and
                "filename" in payload.get("metadata", {}) and
                "page_number" in payload.get("metadata", {}) and
                isinstance(payload["metadata"]["page_number"], int)
            )
        except (KeyError, TypeError):
            return False

    def _get_context_pages(self, filename: str, center_page_number: int) -> List[Dict]:
        try:
            window_size = self.context_window_size
            page_range = models.Range(
                gte=max(0, center_page_number - window_size),
                lte=min(1000, center_page_number + window_size)
            )
            
            logger.debug(f"Fetching context: file={filename}, center={center_page_number}, range={page_range.gte}-{page_range.lte}")
            
            # Calculate dynamic limit: 2 * window_size + 1 (center ± window)
            # Max window_size=11 → 23 pages, supports larger context windows
            max_pages = 2 * window_size + 1
            
            scroll_result = self.qclient.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.filename",
                            match=models.MatchText(text=filename)
                        ),
                        models.FieldCondition(
                            key="metadata.page_number",
                            range=page_range
                        )
                    ]
                ),
                with_payload=True,
                limit=max_pages
            )
            
            points = scroll_result[0]
            logger.debug(f"Retrieved {len(points)} points from scroll")
            
            valid_pages = [p.payload for p in points if self._has_page_structure(p.payload)]
            logger.debug(f"Valid pages after filtering: {len(valid_pages)}")
            
            return sorted(valid_pages, key=lambda x: x["metadata"]["page_number"])
        except Exception as e:
            logger.error(f"Context retrieval failed for page {center_page_number}: {str(e)}")
            return []

    def _generate_query_embedding(self, query: str, embedding_model: str) -> List[float]:
        try:
            embedding = self.oclient.embeddings(
                model=embedding_model,
                prompt=query
            )['embedding']
            logger.debug(f"Generated embedding for query: {query[:50]}...")
            return embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise EmbeddingError("Failed to process query") from e

    def _build_filter_conditions(self, filter_dict: Optional[Dict]) -> Optional[models.Filter]:
        """
        Build Qdrant filter from filter dictionary.
        
        Supports:
        - match_text: single string or array of strings (OR logic within field)
        - match_value: single value or array of values (OR logic within field)
        - gte/lte: range conditions for numeric fields
        
        All top-level field conditions are combined with AND logic.
        
        Args:
            filter_dict: Dictionary mapping field paths to condition dictionaries
            
        Returns:
            Qdrant Filter object or None if no valid conditions
            
        Examples:
            >>> # Array text filter
            >>> filter_dict = {
            ...     "metadata.category": {
            ...         "match_text": ["devops", "cloud"]
            ...     }
            ... }
            
            >>> # Range filter
            >>> filter_dict = {
            ...     "metadata.year": {
            ...         "gte": 2020,
            ...         "lte": 2024
            ...     }
            ... }
        """
        if not filter_dict:
            return None
        
        must_conditions = []
        
        try:
            for field_path, condition in filter_dict.items():
                # Handle match_text
                if "match_text" in condition:
                    condition_value = condition["match_text"]
                    
                    if isinstance(condition_value, list):
                        # Array of text values - use OR logic with should conditions
                        if len(condition_value) == 0:
                            logger.warning(f"Empty array for match_text on field {field_path}, skipping")
                            continue
                        
                        should_conditions = []
                        for text_value in condition_value:
                            should_conditions.append(
                                models.FieldCondition(
                                    key=field_path,
                                    match=models.MatchText(text=str(text_value))
                                )
                            )
                        # Wrap should conditions in a Filter for OR logic
                        must_conditions.append(
                            models.Filter(should=should_conditions)
                        )
                    else:
                        # Single text value
                        must_conditions.append(
                            models.FieldCondition(
                                key=field_path,
                                match=models.MatchText(text=str(condition_value))
                            )
                        )
                
                # Handle match_value
                elif "match_value" in condition:
                    condition_value = condition["match_value"]
                    
                    if isinstance(condition_value, list):
                        # Array of values - use MatchAny for OR logic
                        if len(condition_value) == 0:
                            logger.warning(f"Empty array for match_value on field {field_path}, skipping")
                            continue
                        
                        must_conditions.append(
                            models.FieldCondition(
                                key=field_path,
                                match=models.MatchAny(any=condition_value)
                            )
                        )
                    else:
                        # Single value
                        must_conditions.append(
                            models.FieldCondition(
                                key=field_path,
                                match=models.MatchValue(value=condition_value)
                            )
                        )
                
                # Handle range conditions (gte/lte)
                elif "gte" in condition or "lte" in condition:
                    range_params = {}
                    if "gte" in condition:
                        range_params["gte"] = condition["gte"]
                    if "lte" in condition:
                        range_params["lte"] = condition["lte"]
                    
                    # Validate range makes sense
                    if "gte" in range_params and "lte" in range_params:
                        if range_params["gte"] > range_params["lte"]:
                            logger.warning(f"Invalid range on field {field_path}: gte ({range_params['gte']}) > lte ({range_params['lte']})")
                    
                    must_conditions.append(
                        models.FieldCondition(
                            key=field_path,
                            range=models.Range(**range_params)
                        )
                    )
                else:
                    logger.warning(f"Unknown condition type for field {field_path}: {condition}")
            
            if must_conditions:
                logger.debug(f"Built filter with {len(must_conditions)} conditions")
                return models.Filter(must=must_conditions)
            
            return None
            
        except Exception as e:
            logger.error(f"Filter processing failed: {str(e)}", extra={
                "filter": filter_dict,
                "correlation_id": correlation_id.get()
            })
            raise SearchException("Invalid filter configuration") from e

    def batch_search(self, search_queries: List[str], filter: Optional[Dict], 
                    limit: int = 5, embedding_model: str = "mxbai-embed-large") -> List[List[Dict]]:
        try:
            # Build filter conditions using the new helper method
            filter_ = self._build_filter_conditions(filter)

            search_requests = []
            for query in search_queries:
                embedding = self._generate_query_embedding(query, embedding_model)
                search_requests.append(
                    models.QueryRequest(
                        query=embedding,
                        filter=filter_,
                        limit=limit,
                        with_payload=True
                    )
                )

            batch_response = self.qclient.query_batch_points(
                collection_name=self.collection_name,
                requests=search_requests
            )

            results = []
            for query_response in batch_response:
                query_results = []
                seen_pages = set()  # Track (filename, page_number) to deduplicate across results
                
                for scored_point in query_response.points:
                    payload = scored_point.payload
                    
                    # Detect collection type based on payload structure
                    has_page_structure = (
                        "metadata" in payload and
                        "filename" in payload.get("metadata", {}) and
                        "page_number" in payload.get("metadata", {})
                    )
                    
                    if has_page_structure:
                        # Page-based content collection (e.g., "content")
                        try:
                            context_pages = self._get_context_pages(
                                filename=payload["metadata"]["filename"],
                                center_page_number=payload["metadata"]["page_number"]
                            )
                            
                            # Deduplicate: filter out pages already seen in previous results
                            filename = payload["metadata"]["filename"]
                            unique_pages = []
                            for page in context_pages:
                                page_id = (filename, page["metadata"]["page_number"])
                                if page_id not in seen_pages:
                                    unique_pages.append(page)
                                    seen_pages.add(page_id)
                            
                            page_numbers = [p["metadata"]["page_number"] for p in unique_pages]
                            result = {
                                "filename": filename,
                                "score": scored_point.score,
                                "center_page": payload["metadata"]["page_number"],
                                "combined_page": " ".join(p.get("pagecontent", "") for p in unique_pages),
                                "page_numbers": page_numbers
                            }
                        except (KeyError, TypeError) as e:
                            logger.warning(f"Skipping malformed page-based payload: {str(e)}")
                            continue
                    else:
                        # Generic/flexible collection structure (e.g., filenames)
                        # Return clean, non-redundant fields
                        result = {
                            "score": scored_point.score
                        }
                        
                        # Extract filename from source or pagecontent
                        if "source" in payload:
                            result["filename"] = payload["source"]
                        elif "pagecontent" in payload:
                            result["filename"] = payload["pagecontent"]
                        
                        # Add metadata if present
                        if "metadata" in payload:
                            result["metadata"] = payload["metadata"]
                    
                    query_results.append(result)
                results.append(query_results)
            
            return results

        except Exception as e:
            logger.error(f"Batch search failed: {str(e)}")
            raise SearchException("Search operation failed") from e

# ======== FastAPI Setup ========
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    collection_name: str = Field(..., min_length=1, description="Name of the Qdrant collection")
    search_queries: List[str] = Field(..., min_items=1, description="List of search queries")
    filter: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Filter conditions. Each key is a metadata field path, value is a dict with 'match_text', 'match_value', 'gte', or 'lte'. Values can be single values or arrays for OR logic.")
    embedding_model: Optional[str] = Field(default=DEFAULT_EMBEDDING_MODEL, description="Ollama embedding model name")
    limit: Optional[conint(ge=1)] = Field(default=5, description="Maximum number of results per query")
    context_window_size: Optional[conint(ge=0)] = Field(default=None, description="Number of pages before/after match to retrieve. Overrides CONTEXT_WINDOW_SIZE env var.")
    use_production: Optional[bool] = Field(default=False, description="Use production environment configuration (PROD_* variables)")
    qdrant_url: Optional[str] = Field(default=None, description="Override Qdrant URL for this request")
    qdrant_api_key: Optional[str] = Field(default=None, description="Override Qdrant API key for this request")
    qdrant_verify_ssl: Optional[bool] = Field(default=None, description="Override SSL verification for this request")

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    corr_id = str(uuid.uuid4())
    correlation_id.set(corr_id)
    
    logger.info("Request started", extra={
        "path": request.url.path,
        "method": request.method,
        "client_ip": request.client.host if request.client else None
    })
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        raise
    finally:
        logger.info("Request completed")
    
    response.headers["X-Correlation-ID"] = corr_id
    return response

@app.get("/health")
async def health_check(authenticated: bool = Depends(verify_api_key)):
    return {
        "status": "ok",
        "services": {
            "qdrant": "ok" if (SearchSystem._qdrant_pool_dev or SearchSystem._qdrant_pool_prod) else "offline",
            "ollama": "ok" if SearchSystem._ollama_pool else "offline"
        }
    }

@app.post("/search", status_code=status.HTTP_200_OK)
async def search(request: Request, search_request: SearchRequest, authenticated: bool = Depends(verify_api_key)):
    try:
        # Log request with connection configuration
        logger.info("Search request received", extra={
            "collection": search_request.collection_name,
            "query_count": len(search_request.search_queries),
            "use_production": search_request.use_production,
            "custom_config": any([
                search_request.qdrant_url,
                search_request.qdrant_api_key,
                search_request.qdrant_verify_ssl is not None
            ])
        })
        
        # Create SearchSystem with connection parameters
        system = SearchSystem(
            collection_name=search_request.collection_name,
            use_production=search_request.use_production,
            qdrant_url=search_request.qdrant_url,
            qdrant_api_key=search_request.qdrant_api_key,
            qdrant_verify_ssl=search_request.qdrant_verify_ssl,
            context_window_size=search_request.context_window_size
        )
        
        results = system.batch_search(
            search_queries=search_request.search_queries,
            filter=search_request.filter,
            limit=search_request.limit,
            embedding_model=search_request.embedding_model
        )
        
        logger.debug("Search results generated", extra={
            "result_count": sum(len(r) for r in results)
        })
        return {"results": results}
    
    except ValueError as e:
        # Handle validation errors (e.g., conflicting parameters)
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except SearchException as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search processing failed"
        )
    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

class FilenameSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Fuzzy search query for filename")
    collection_name: str = Field(..., min_length=1, description="Name of the Qdrant collection")
    limit: Optional[conint(ge=1, le=1000)] = Field(default=10, description="Maximum number of matching filenames to return")
    use_production: Optional[bool] = Field(default=False, description="Use production environment configuration")
    qdrant_url: Optional[str] = Field(default=None, description="Override Qdrant URL")
    qdrant_api_key: Optional[str] = Field(default=None, description="Override Qdrant API key")
    qdrant_verify_ssl: Optional[bool] = Field(default=None, description="Override SSL verification")

@app.post("/search/filenames")
async def search_filenames(request: FilenameSearchRequest, authenticated: bool = Depends(verify_api_key)):
    """
    Fuzzy search on metadata.filename field and return matching filenames.
    Does not return page content - only unique filenames that match the query.
    
    Example: Searching "ecos 9.3" returns all files with "9.3" in the name.
    """
    correlation_id = str(uuid.uuid4())
    logger.info("Filename search request received", extra={
        "correlation_id": correlation_id,
        "query": request.query,
        "collection": request.collection_name,
        "limit": request.limit
    })
    
    try:
        # Create Qdrant client
        qclient = SearchSystem._create_qdrant_client(
            qdrant_url=request.qdrant_url,
            qdrant_api_key=request.qdrant_api_key,
            qdrant_verify_ssl=request.qdrant_verify_ssl,
            use_production=request.use_production
        )
        
        # Use scroll with match_text filter for fuzzy filename matching
        scroll_result = qclient.scroll(
            collection_name=request.collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.filename",
                        match=models.MatchText(text=request.query)
                    )
                ]
            ),
            limit=request.limit * 3,  # Get more to deduplicate
            with_payload=True
        )
        
        # Extract unique filenames
        filenames_set = set()
        results = []
        
        for point in scroll_result[0]:
            if "metadata" in point.payload and "filename" in point.payload["metadata"]:
                filename = point.payload["metadata"]["filename"]
                if filename not in filenames_set:
                    filenames_set.add(filename)
                    results.append({
                        "filename": filename,
                        "score": point.score if hasattr(point, 'score') else None
                    })
                    
                    # Stop when we have enough unique filenames
                    if len(results) >= request.limit:
                        break
        
        logger.info(f"Found {len(results)} unique matching filenames", extra={
            "correlation_id": correlation_id
        })
        
        return {
            "query": request.query,
            "total_matches": len(results),
            "filenames": results
        }
    
    except Exception as e:
        logger.error(f"Filename search failed: {str(e)}", extra={
            "correlation_id": correlation_id
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Filename search failed: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        timeout_keep_alive=REQUEST_TIMEOUT
    )
