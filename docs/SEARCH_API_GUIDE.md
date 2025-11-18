# Search API Usage Guide

This guide explains how to use the **Docsplorer Search API** directly via `curl` commands. It covers all endpoints, environment variable implications, and how to override settings per request.

---

## Table of Contents

1. [What is the Search API?](#what-is-the-search-api)
2. [Starting the Search API](#starting-the-search-api)
3. [Environment Variables Explained](#environment-variables-explained)
4. [API Endpoints](#api-endpoints)
   - [Health Check](#1-health-check)
   - [Fuzzy Filename Search](#2-fuzzy-filename-search)
   - [Semantic Content Search](#3-semantic-content-search)
5. [Overriding Configuration in Requests](#overriding-configuration-in-requests)
6. [Common Use Cases](#common-use-cases)
7. [Troubleshooting](#troubleshooting)

---

## What is the Search API?

The Search API is a **FastAPI service** that:

- Connects to a **Qdrant vector database** to store and search document embeddings.
- Generates **embeddings** using either **Ollama** (local) or **Gemini** (cloud API).
- Provides endpoints for:
  - **Fuzzy filename search** – discover documents by partial filename.
  - **Semantic content search** – find relevant passages in documents using natural language queries.

Think of it as a smart search engine for your technical documentation.

---

## Starting the Search API

### Option 1: Using Docker Compose (Recommended)

From the repo root:

```bash
docker compose up search-api
```

The API will be available at:

```
http://localhost:8001
```

(Port is controlled by `SEARCH_API_PORT` in `.env`.)

### Option 2: Running Locally (Without Docker)

From `services/search-api`:

```bash
cd services/search-api
pip install -r app/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at:

```
http://localhost:8000
```

---

## Environment Variables Explained

The Search API reads configuration from the `.env` file at the repo root. Here's what each variable does and when you need to set it.

### Global Settings

```bash
# ENVIRONMENT: Controls validation strictness.
#   - "development" => relaxed (no HTTPS/API key enforcement for Qdrant).
#   - "production"  => strict (requires HTTPS + API key for Qdrant).
ENVIRONMENT=development

# DEBUG: Extra verbose logging.
#   - "true"  => detailed logs for troubleshooting.
#   - "false" => normal logs.
DEBUG=false

# REQUEST_TIMEOUT: HTTP timeout (in seconds) for outgoing calls.
#   - Increase if your Qdrant/Ollama/Gemini is slow or on a remote network.
REQUEST_TIMEOUT=30
```

**When to change**:
- Set `ENVIRONMENT=production` when deploying to a real server.
- Set `DEBUG=true` when troubleshooting errors.

---

### API Key Authentication

```bash
# SEARCH_API_KEY_ENABLED: Whether the Search API requires an API key.
#   - "true"  => clients must send "Authorization: Bearer <key>" header.
#   - "false" => no authentication (good for local dev).
SEARCH_API_KEY_ENABLED=false

# SEARCH_API_KEY: The actual API key (if enabled).
SEARCH_API_KEY=
```

**When to change**:
- Enable in production to secure your API.
- Set a strong random key (e.g., `openssl rand -hex 32`).

**Example curl with API key**:

```bash
curl -X POST http://localhost:8001/search \
  -H "Authorization: Bearer your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{"search_queries": ["security"], "collection_name": "content"}'
```

---

### Qdrant Configuration

The Search API can connect to **two Qdrant instances**: dev and prod.

#### Dev Qdrant (for local/lab use)

```bash
# QDRANT_DEV_URL: URL of your dev Qdrant instance.
#   - Example (local Docker):  http://localhost:6333
#   - Example (remote server):  http://192.168.1.100:6333
QDRANT_DEV_URL=http://localhost:6333

# QDRANT_DEV_API_KEY: API key for dev Qdrant (if it requires auth).
QDRANT_DEV_API_KEY=

# QDRANT_DEV_VERIFY_SSL: Whether to verify TLS certificates for HTTPS URLs.
#   - false => ignore cert errors (useful for self-signed certs).
#   - true  => verify certs (recommended for real TLS).
QDRANT_DEV_VERIFY_SSL=false
```

#### Prod Qdrant (for production deployments)

```bash
# QDRANT_PROD_URL: URL of your production Qdrant instance.
#   - Should be https:// in real production.
QDRANT_PROD_URL=

# QDRANT_PROD_API_KEY: API key for production Qdrant.
QDRANT_PROD_API_KEY=

# QDRANT_PROD_VERIFY_SSL: Whether to verify TLS certificates.
#   - Keep this "true" in production.
QDRANT_PROD_VERIFY_SSL=true
```

#### Which Qdrant is used?

Controlled by the `use_production` flag in each request:

- `use_production=false` → uses `QDRANT_DEV_*` settings.
- `use_production=true` → uses `QDRANT_PROD_*` settings.

**Default**: `use_production=false` (uses dev Qdrant).

---

### Embedding Provider

The Search API can generate embeddings using **Ollama** (local) or **Gemini** (cloud).

```bash
# EMBEDDING_PROVIDER: Which embedding backend to use.
#   - "ollama" => use a local Ollama server.
#   - "gemini" => use Google Gemini API.
EMBEDDING_PROVIDER=ollama
```

#### Ollama Configuration (when EMBEDDING_PROVIDER=ollama)

```bash
# OLLAMA_HOST: URL of your Ollama server.
#   - Example (local):  http://localhost:11434
#   - Example (remote): http://192.168.1.50:11434
OLLAMA_HOST=http://localhost:11434

# OLLAMA_API_KEY: Optional API key for Ollama (rarely needed).
OLLAMA_API_KEY=

# OLLAMA_EMBEDDING_MODEL: Model name to use for embeddings.
#   - Must match a model you have pulled in Ollama.
#   - Examples: bge-m3, mxbai-embed-large, nomic-embed-text
OLLAMA_EMBEDDING_MODEL=bge-m3

# OLLAMA_EMBEDDING_DIMENSIONS: Vector size of the model.
#   - Must match the model's actual dimension and your Qdrant collection.
OLLAMA_EMBEDDING_DIMENSIONS=1024
```

**When to change**:
- Set `OLLAMA_HOST` to your Ollama server's IP if it's on another machine.
- Change `OLLAMA_EMBEDDING_MODEL` to match the model you want to use.
- Update `OLLAMA_EMBEDDING_DIMENSIONS` to match the model (e.g., 768 for some models, 1024 for bge-m3).

#### Gemini Configuration (when EMBEDDING_PROVIDER=gemini)

```bash
# GEMINI_API_KEY: Your Google Gemini API key (required).
GEMINI_API_KEY=

# GEMINI_EMBEDDING_MODEL: Gemini model ID.
GEMINI_EMBEDDING_MODEL=gemini-embedding-001

# GEMINI_EMBEDDING_TASK_TYPE: Task type for embeddings.
GEMINI_EMBEDDING_TASK_TYPE=RETRIEVAL_QUERY

# GEMINI_EMBEDDING_DIMENSIONS: Output dimension.
GEMINI_EMBEDDING_DIMENSIONS=768
```

**When to change**:
- Set `GEMINI_API_KEY` when using Gemini.
- Adjust dimensions if using a different Gemini model.

---

### Search Defaults

```bash
# CONTEXT_WINDOW_SIZE: How many pages before/after a match to retrieve.
#   - Example: 5 => center page ±5 pages (11-page window total).
CONTEXT_WINDOW_SIZE=5

# DEFAULT_RESULT_LIMIT: Default max results per query.
DEFAULT_RESULT_LIMIT=2

# USE_PRODUCTION: Default value for use_production flag.
#   - false => use QDRANT_DEV_* by default.
#   - true  => use QDRANT_PROD_* by default.
USE_PRODUCTION=false
```

**When to change**:
- Increase `CONTEXT_WINDOW_SIZE` if you want more context around matches.
- Increase `DEFAULT_RESULT_LIMIT` if you want more results per query.
- Set `USE_PRODUCTION=true` in production deployments.

---

## API Endpoints

### 1. Health Check

**Endpoint**: `GET /health`

**Purpose**: Check if the Search API is running.

**Example**:

```bash
curl http://localhost:8001/health
```

**Response**:

```json
{
  "status": "healthy"
}
```

---

### 2. Fuzzy Filename Search

**Endpoint**: `POST /search/filenames`

**Purpose**: Discover documents by partial filename (fuzzy matching).

**Use when**: You don't know the exact filename and want to find candidate documents.

#### Request Body

```json
{
  "query": "ECOS 9.2",
  "collection_name": "content",
  "limit": 5,
  "use_production": false
}
```

**Fields**:

- `query` (string, required): Partial filename to search for.
- `collection_name` (string, required): Qdrant collection name.
- `limit` (integer, optional): Max number of filenames to return. Default: 2.
- `use_production` (boolean, optional): Use prod Qdrant? Default: false.

#### Example curl

```bash
curl -X POST http://localhost:8001/search/filenames \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ECOS 9.2",
    "collection_name": "content",
    "limit": 5
  }'
```

#### Response

```json
{
  "query": "ECOS 9.2",
  "total_matches": 3,
  "filenames": [
    {
      "filename": "ECOS_9.2.4.0_Release_Notes_RevB",
      "score": 0.95
    },
    {
      "filename": "ECOS_9.2.3.0_Release_Notes_RevA",
      "score": 0.89
    },
    {
      "filename": "ECOS_9.2.5.0_Release_Notes_RevC",
      "score": 0.87
    }
  ]
}
```

**What the response means**:

- `total_matches`: How many unique filenames matched.
- `filenames`: List of matching filenames with relevance scores (0-1, higher is better).

---

### 3. Semantic Content Search

**Endpoint**: `POST /search`

**Purpose**: Search for content within documents using natural language queries.

**Use when**: You know which document(s) to search and want to find relevant passages.

#### Request Body

```json
{
  "search_queries": ["security vulnerabilities", "performance improvements"],
  "collection_name": "content",
  "filter": {
    "metadata.filename": {
      "match_text": "ECOS_9.2.4.0_Release_Notes_RevB"
    }
  },
  "limit": 2,
  "context_window_size": 5,
  "use_production": false
}
```

**Fields**:

- `search_queries` (array of strings, required): One or more search queries.
- `collection_name` (string, required): Qdrant collection name.
- `filter` (object, optional): Filter by metadata (e.g., filename, category).
- `limit` (integer, optional): Max results per query. Default: from `.env`.
- `context_window_size` (integer, optional): Pages before/after match. Default: from `.env`.
- `use_production` (boolean, optional): Use prod Qdrant? Default: from `.env`.

#### Example curl (single query, single file)

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_queries": ["security vulnerabilities"],
    "collection_name": "content",
    "filter": {
      "metadata.filename": {
        "match_text": "ECOS_9.2.4.0"
      }
    },
    "limit": 2,
    "context_window_size": 5
  }'
```

#### Response

```json
{
  "results": [
    [
      {
        "filename": "ECOS_9.2.4.0_Release_Notes_RevB",
        "score": 0.87,
        "center_page": 12,
        "combined_page": "... page 7 content ...\n... page 8 content ...\n... [CENTER PAGE 12] ...\n... page 13 content ...\n... page 17 content ...",
        "page_numbers": [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
      },
      {
        "filename": "ECOS_9.2.4.0_Release_Notes_RevB",
        "score": 0.82,
        "center_page": 45,
        "combined_page": "... page 40 content ...\n... [CENTER PAGE 45] ...\n... page 50 content ...",
        "page_numbers": [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50]
      }
    ]
  ]
}
```

**What the response means**:

- `results`: Array of result sets (one per query).
- Each result:
  - `filename`: Document name.
  - `score`: Relevance score (0-1, higher is better).
  - `center_page`: The page number that matched the query.
  - `combined_page`: Text from center page ± context window (combined into one string).
  - `page_numbers`: List of page numbers included in `combined_page`.

---

## Overriding Configuration in Requests

You can **override** `.env` settings on a per-request basis by including extra fields in the request body.

### Example: Override Qdrant URL

If you want to use a **different Qdrant instance** for one specific request (without changing `.env`):

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_queries": ["performance"],
    "collection_name": "content",
    "qdrant_url": "http://192.168.1.200:6333",
    "qdrant_api_key": "custom-key-here",
    "limit": 3
  }'
```

**What happens**:

- The Search API will connect to `http://192.168.1.200:6333` **for this request only**.
- It will use `custom-key-here` as the API key.
- All other requests still use the `.env` settings.

### Example: Override Embedding Model

If you want to use a **different Ollama model** for one request:

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_queries": ["DHCP"],
    "collection_name": "content",
    "embedding_model": "nomic-embed-text",
    "limit": 2
  }'
```

**What happens**:

- The Search API will generate embeddings using `nomic-embed-text` **for this request only**.
- Other requests still use `OLLAMA_EMBEDDING_MODEL` from `.env`.

### Example: Use Production Qdrant for One Request

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_queries": ["CVE-2023"],
    "collection_name": "content",
    "use_production": true,
    "limit": 5
  }'
```

**What happens**:

- The Search API will use `QDRANT_PROD_URL` and `QDRANT_PROD_API_KEY` **for this request only**.
- Other requests still use dev Qdrant (if `USE_PRODUCTION=false` in `.env`).

---

## Common Use Cases

### Use Case 1: Find All Documents About "DHCP"

**Step 1**: Discover candidate documents.

```bash
curl -X POST http://localhost:8001/search/filenames \
  -H "Content-Type: application/json" \
  -d '{
    "query": "DHCP",
    "collection_name": "content",
    "limit": 10
  }'
```

**Step 2**: Search within the most relevant document.

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_queries": ["DHCP configuration"],
    "collection_name": "content",
    "filter": {
      "metadata.filename": {
        "match_text": "ECOS_9.2.4.0_Release_Notes_RevB"
      }
    },
    "limit": 3,
    "context_window_size": 7
  }'
```

---

### Use Case 2: Compare Security Fixes Across Two Versions

**Query both versions in one request**:

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_queries": ["security fixes"],
    "collection_name": "content",
    "filter": {
      "metadata.filename": {
        "match_text": ["ECOS_9.2.4.0", "ECOS_9.2.5.0"]
      }
    },
    "limit": 2,
    "context_window_size": 5
  }'
```

**What happens**:

- The filter uses an **array** of filenames, so results will include matches from **both** documents.
- You can then compare the `combined_page` content for each version.

---

### Use Case 3: Search Multiple Topics in One Document

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_queries": ["security", "performance", "bug fixes"],
    "collection_name": "content",
    "filter": {
      "metadata.filename": {
        "match_text": "ECOS_9.2.4.0"
      }
    },
    "limit": 2
  }'
```

**What happens**:

- The API will run **3 separate searches** (one per query).
- `results` will be an array with 3 elements (one per query).
- Each element contains up to 2 results.

---

### Use Case 4: Search with Custom Qdrant Instance (Cloud)

If you're using a **cloud-hosted Qdrant** (e.g., Qdrant Cloud), override the URL and API key per request:

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_queries": ["security vulnerabilities and patches"],
    "collection_name": "content",
    "limit": 1,
    "embedding_model": "bge-m3",
    "context_window_size": 1,
    "filter": {
      "metadata.filename": {
        "match_value": "ECOS_9.2.11.1_Release_Notes_RevA"
      }
    },
    "qdrant_url": "https://your-cluster.us-east-1.aws.cloud.qdrant.io:6333",
    "qdrant_api_key": "your-qdrant-api-key",
    "use_production": false
  }' | jq '.'
```

**What happens**:

- Connects to your cloud Qdrant instance for this request.
- Uses `match_value` (exact match) instead of `match_text` (fuzzy).
- Returns results with 1-page context window.

---

### Use Case 5: OR Logic – Search Across Multiple Files

Search for a topic in **multiple documents** (OR logic):

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_queries": [
      "DHCP server configuration",
      "network troubleshooting steps"
    ],
    "collection_name": "content",
    "limit": 1,
    "embedding_model": "bge-m3",
    "context_window_size": 1,
    "filter": {
      "metadata.filename": {
        "match_value": [
          "ECOS_9.2.11.1_Release_Notes_RevA",
          "ECOS_9.3.6.0_Release_Notes_RevB",
          "ECOS_9.3.7.0_Release_Notes_RevB"
        ]
      }
    },
    "use_production": false
  }' | jq -C '.'
```

**What happens**:

- Runs **2 queries** (DHCP, network troubleshooting).
- Each query searches **3 files** (OR logic: results from any of the 3 files).
- Returns up to 1 result per query per file.
- `jq -C` adds color to the JSON output.

---

### Use Case 6: AND Logic – Filter by File AND Page Range

Search within a **specific file** AND **specific page range** (AND logic):

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_queries": ["DHCP configuration"],
    "collection_name": "content",
    "limit": 3,
    "embedding_model": "bge-m3",
    "context_window_size": 2,
    "filter": {
      "metadata.filename": {
        "match_value": "ECOS_9.2.11.1_Release_Notes_RevA"
      },
      "metadata.page_number": {
        "gte": 10,
        "lte": 50
      }
    }
  }' | jq '.results[0][] | {filename, score, center_page, page_numbers}'
```

**What happens**:

- Searches **only** in `ECOS_9.2.11.1_Release_Notes_RevA`.
- **Only** considers pages 10-50.
- Returns up to 3 results with 2-page context window.
- `jq` extracts just the key fields (filename, score, center_page, page_numbers).

---

### Use Case 7: No Context Window (Center Page Only)

Get **only the matching page** without surrounding context:

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_queries": ["DHCP server"],
    "collection_name": "content",
    "limit": 2,
    "embedding_model": "bge-m3",
    "context_window_size": 0,
    "filter": {
      "metadata.filename": {
        "match_value": "ECOS_9.2.11.1_Release_Notes_RevA"
      },
      "metadata.page_number": {
        "gte": 5,
        "lte": 15
      }
    }
  }' | jq '.results[0][] | {filename, score, center_page, page_numbers}'
```

**What happens**:

- `context_window_size: 0` means **no surrounding pages**.
- `combined_page` will contain **only the center page** content.
- `page_numbers` will be a single-element array (e.g., `[12]`).

---

### Use Case 8: Filename Search with Production Qdrant

Discover filenames using the **production Qdrant instance**:

```bash
curl -X POST http://localhost:8001/search/filenames \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ECOS_9.3.7.0_Release_Notes_RevB",
    "collection_name": "content",
    "limit": 1,
    "use_production": true
  }' | jq '.'
```

**What happens**:

- Uses `QDRANT_PROD_URL` and `QDRANT_PROD_API_KEY` from `.env`.
- Searches for filenames matching "ECOS_9.3.7.0_Release_Notes_RevB".
- Returns up to 1 matching filename.

---

### Use Case 9: Using Gemini Embeddings

If you've configured the Search API to use **Gemini** instead of Ollama:

**In `.env`**:

```bash
EMBEDDING_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_TASK_TYPE=RETRIEVAL_QUERY
GEMINI_EMBEDDING_DIMENSIONS=768
```

**Then run the same curl commands** (no changes needed):

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_queries": ["ecos 9.3"],
    "collection_name": "filenames",
    "limit": 3,
    "use_production": true
  }' | jq '.'
```

**What happens**:

- The Search API uses **Gemini** to generate embeddings (instead of Ollama).
- No request changes needed; the provider is selected by backend `.env` config.
- Works with all endpoints (`/search`, `/search/filenames`).

**Note**: You can also override the embedding model per request if using Ollama:

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_queries": ["DHCP"],
    "collection_name": "content",
    "embedding_model": "granite-embedding:30m",
    "limit": 3
  }'
```

But when `EMBEDDING_PROVIDER=gemini`, the `embedding_model` field is ignored (Gemini uses the model from `.env`).

---

## Advanced Filtering Reference

### Filter Types

The `filter` field supports multiple condition types:

#### 1. `match_value` (Exact Match)

```json
"filter": {
  "metadata.filename": {
    "match_value": "ECOS_9.2.11.1_Release_Notes_RevA"
  }
}
```

- Matches **exactly** the specified value.
- Can be a **single value** or **array** (OR logic).

#### 2. `match_text` (Fuzzy Match)

```json
"filter": {
  "metadata.filename": {
    "match_text": "ECOS_9.2"
  }
}
```

- Matches **partial** text (fuzzy).
- Can be a **single string** or **array** (OR logic).

#### 3. `gte` / `lte` (Range)

```json
"filter": {
  "metadata.page_number": {
    "gte": 10,
    "lte": 50
  }
}
```

- `gte`: Greater than or equal to.
- `lte`: Less than or equal to.
- Use for numeric fields (e.g., page numbers, years).

### Combining Filters (AND Logic)

Multiple top-level fields are combined with **AND**:

```json
"filter": {
  "metadata.filename": {
    "match_value": "ECOS_9.2.11.1_Release_Notes_RevA"
  },
  "metadata.page_number": {
    "gte": 10,
    "lte": 50
  }
}
```

**Meaning**: Results must be from `ECOS_9.2.11.1_Release_Notes_RevA` **AND** pages 10-50.

### OR Logic Within a Field

Use an **array** for OR logic:

```json
"filter": {
  "metadata.filename": {
    "match_value": [
      "ECOS_9.2.11.1_Release_Notes_RevA",
      "ECOS_9.3.6.0_Release_Notes_RevB"
    ]
  }
}
```

**Meaning**: Results from `ECOS_9.2.11.1_Release_Notes_RevA` **OR** `ECOS_9.3.6.0_Release_Notes_RevB`.

---

## Troubleshooting

### Error: "Qdrant connection failed"

**Cause**: The Search API cannot reach your Qdrant instance.

**Fix**:

1. Check that Qdrant is running:

   ```bash
   curl http://localhost:6333/collections
   ```

2. Verify `QDRANT_DEV_URL` in `.env` matches your Qdrant's actual URL.
3. If Qdrant is on another machine, use the IP address (e.g., `http://192.168.1.100:6333`).

---

### Error: "Embedding client configuration error: OLLAMA_EMBEDDING_MODEL is required"

**Cause**: `EMBEDDING_PROVIDER=ollama` but `OLLAMA_EMBEDDING_MODEL` is not set in `.env`.

**Fix**:

1. Open `.env` and set:

   ```bash
   OLLAMA_EMBEDDING_MODEL=bge-m3
   ```

2. Restart the Search API:

   ```bash
   docker compose restart search-api
   ```

---

### Error: "Collection 'content' does not exist"

**Cause**: The Qdrant collection specified in the request doesn't exist.

**Fix**:

1. Create the collection in Qdrant (or use the correct collection name in your request).
2. Example using Qdrant API:

   ```bash
   curl -X PUT http://localhost:6333/collections/content \
     -H "Content-Type: application/json" \
     -d '{
       "vectors": {
         "size": 1024,
         "distance": "Cosine"
       }
     }'
   ```

---

### Error: "401 Unauthorized"

**Cause**: `SEARCH_API_KEY_ENABLED=true` but you didn't send an API key.

**Fix**:

Add the `Authorization` header:

```bash
curl -X POST http://localhost:8001/search \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"search_queries": ["test"], "collection_name": "content"}'
```

---

## Summary

- **Health check**: `GET /health` – verify the API is running.
- **Filename search**: `POST /search/filenames` – discover documents by partial name.
- **Content search**: `POST /search` – find relevant passages using natural language.
- **Override settings**: Include `qdrant_url`, `embedding_model`, `use_production`, etc. in request body.
- **`.env` controls defaults**: Set once, use everywhere (unless overridden per request).

For production use, remember to:

- Set `ENVIRONMENT=production`.
- Enable `SEARCH_API_KEY_ENABLED=true` and set a strong key.
- Use `QDRANT_PROD_URL` with HTTPS and API key.
- Adjust `CONTEXT_WINDOW_SIZE` and `DEFAULT_RESULT_LIMIT` based on your needs.

Happy searching!
