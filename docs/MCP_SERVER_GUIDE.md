# MCP Server Usage Guide

Complete guide for running and using the **Docsplorer MCP Server** in all modes: stdio (for IDEs) and HTTP (for automation tools).

---

## Table of Contents

1. [What is the MCP Server?](#what-is-the-mcp-server)
2. [Running the MCP Server](#running-the-mcp-server)
3. [Environment Variables](#environment-variables)
4. [MCP Tools Reference](#mcp-tools-reference)
5. [Production Deployment](#production-deployment)
6. [Troubleshooting](#troubleshooting)

---

## What is the MCP Server?

The **Docsplorer MCP Server** is a **Model Context Protocol (MCP)** server that provides 5 specialized tools for searching documentation. It acts as a bridge between:

- **LLM clients** (like Claude Desktop, Windsurf IDE, or custom agents)
- **The Search API** (which does the actual vector search)

Think of it as a smart assistant that knows how to search your documentation and return results to AI tools.

---

## Running the MCP Server

The MCP server supports **two transport modes**:

1. **stdio** – for IDE integration (Windsurf, Claude Desktop, etc.)
2. **HTTP** – for automation tools (n8n, custom scripts, etc.)

### Option 1: stdio Mode (for IDEs)

**When to use**: Integrating with an IDE or MCP-aware client that speaks stdio.

**Run locally** (from `services/mcp-server`):

```bash
cd services/mcp-server
python server.py
```

**Or with explicit transport flag**:

```bash
python server.py --transport stdio
```

**What happens**:

- The server starts in **stdio mode** (reads from stdin, writes to stdout).
- Your IDE configures it in its MCP settings (see IDE Integration below).

---

### Option 2: HTTP Mode (for Automation Tools)

**When to use**: Calling MCP tools from HTTP clients, n8n workflows, or custom scripts.

**Run with Docker Compose** (recommended):

```bash
docker compose up mcp-server
```

The server will be available at:

```
http://localhost:8505/mcp
```

**Run locally without Docker**:

```bash
cd services/mcp-server
python server.py --transport http --host 0.0.0.0 --port 8505
```

**What happens**:

- The server starts an HTTP server on port 8505.
- Clients send MCP requests to `http://localhost:8505/mcp`.

---

### Option 3: Both Services Together (Full Stack)

**Run everything with Docker Compose**:

```bash
docker compose up
```

This starts:

- **Search API** on `http://localhost:8001`
- **MCP Server** (HTTP mode) on `http://localhost:8505`

---

## Environment Variables

The MCP server reads configuration from the `.env` file at the repo root.

### Search API Connection

```bash
# SEARCH_API_URL: Base URL of the Search API.
#   - In Docker: http://search-api:8000 (internal network)
#   - Local dev: http://localhost:8001
SEARCH_API_URL=http://localhost:8001

# SEARCH_API_KEY: API key for Search API (if authentication is enabled).
SEARCH_API_KEY=
```

**When to change**:

- Set `SEARCH_API_URL=http://search-api:8000` when running in Docker (internal network).
- Set `SEARCH_API_KEY` if the Search API has `SEARCH_API_KEY_ENABLED=true`.

---

### Qdrant Collection

```bash
# QDRANT_COLLECTION: Name of the Qdrant collection to search.
QDRANT_COLLECTION=content
```

**When to change**:

- If your Qdrant collection has a different name (e.g., `docs`, `release-notes`).

---

### Embedding Configuration

```bash
# OLLAMA_EMBEDDING_MODEL: Model name used by the Search API.
#   - Must match the model in Search API's .env.
OLLAMA_EMBEDDING_MODEL=bge-m3

# OLLAMA_EMBEDDING_DIMENSIONS: Vector size.
OLLAMA_EMBEDDING_DIMENSIONS=1024
```

**When to change**:

- If you switch embedding models, update both MCP and Search API `.env` files.

---

### Search Defaults

```bash
# CONTEXT_WINDOW_SIZE: Default pages before/after a match.
CONTEXT_WINDOW_SIZE=5

# DEFAULT_RESULT_LIMIT: Default max results per query.
DEFAULT_RESULT_LIMIT=2

# USE_PRODUCTION: Use prod Qdrant by default?
#   - false => use QDRANT_DEV_* settings.
#   - true  => use QDRANT_PROD_* settings.
USE_PRODUCTION=false
```

**When to change**:

- Increase `CONTEXT_WINDOW_SIZE` for more context around matches.
- Increase `DEFAULT_RESULT_LIMIT` for more results.
- Set `USE_PRODUCTION=true` in production deployments.

---

### MCP HTTP Server Settings

```bash
# MCP_TRANSPORT: Transport mode (stdio or http).
MCP_TRANSPORT=http

# MCP_HTTP_HOST: Host to bind to (0.0.0.0 = all interfaces).
MCP_HTTP_HOST=0.0.0.0

# MCP_HTTP_PORT: Port for HTTP mode.
MCP_HTTP_PORT=8505
```

**When to change**:

- Change `MCP_HTTP_PORT` if port 8505 is already in use.
- Set `MCP_TRANSPORT=stdio` if running locally for IDE integration.

---

## MCP Tools Reference

The MCP server provides **5 tools**. Each tool is designed for a specific search workflow.

### 1. `search_filenames_fuzzy`

**Purpose**: Discover documents by partial filename.

**Use when**: You don't know the exact filename.

**Parameters**:

- `query` (string, required): Partial filename (e.g., "ECOS 9.2", "release notes").
- `limit` (integer, optional): Max filenames to return. Default: from `.env`.

**Example**:

```json
{
  "tool": "search_filenames_fuzzy",
  "arguments": {
    "query": "ECOS 9.2",
    "limit": 5
  }
}
```

**Returns**:

```json
{
  "query": "ECOS 9.2",
  "total_matches": 3,
  "filenames": [
    {"filename": "ECOS_9.2.4.0_Release_Notes_RevB", "score": 0.95},
    {"filename": "ECOS_9.2.3.0_Release_Notes_RevA", "score": 0.89}
  ]
}
```

---

### 2. `search_with_filename_filter`

**Purpose**: Search content within ONE document.

**Use when**: You know the filename and want to find specific topics.

**Parameters**:

- `query` (string, required): Search term (e.g., "security vulnerabilities").
- `filename_filter` (string, required): Exact or partial filename.
- `limit` (integer, optional): Max results. Default: from `.env`.
- `context_window` (integer, optional): Pages before/after. Default: from `.env`.

**Example**:

```json
{
  "tool": "search_with_filename_filter",
  "arguments": {
    "query": "security vulnerabilities",
    "filename_filter": "ECOS_9.2.4.0",
    "limit": 2,
    "context_window": 5
  }
}
```

**Returns**:

```json
{
  "results": [[
    {
      "filename": "ECOS_9.2.4.0_Release_Notes_RevB",
      "score": 0.87,
      "center_page": 12,
      "combined_page": "... page content ...",
      "page_numbers": [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    }
  ]]
}
```

---

### 3. `search_multi_query_with_filter`

**Purpose**: Run multiple searches within ONE document (batch processing).

**Use when**: You have multiple topics to search in the same document.

**Parameters**:

- `queries` (array of strings, required): List of search queries.
- `filename_filter` (string, required): Document to search.
- `limit` (integer, optional): Max results per query.
- `context_window` (integer, optional): Pages before/after.

**Example**:

```json
{
  "tool": "search_multi_query_with_filter",
  "arguments": {
    "queries": ["security", "performance", "bugs"],
    "filename_filter": "ECOS_9.2.4.0",
    "limit": 2
  }
}
```

**Returns**:

```json
{
  "results": [
    [/* results for "security" */],
    [/* results for "performance" */],
    [/* results for "bugs" */]
  ]
}
```

---

### 4. `search_across_multiple_files`

**Purpose**: Search ONE topic across MULTIPLE documents.

**Use when**: Tracking a feature across versions or comparing multiple docs.

**Parameters**:

- `query` (string, required): Single search query.
- `filename_filters` (array of strings, required): List of documents to search.
- `limit` (integer, optional): Max results per file.
- `context_window` (integer, optional): Pages before/after.

**Example**:

```json
{
  "tool": "search_across_multiple_files",
  "arguments": {
    "query": "DHCP security",
    "filename_filters": ["ECOS_9.2.4.0", "ECOS_9.2.5.0", "ECOS_9.2.6.0"],
    "limit": 2
  }
}
```

**Returns**:

```json
{
  "query": "DHCP security",
  "results_by_file": {
    "ECOS_9.2.4.0": [/* results */],
    "ECOS_9.2.5.0": [/* results */],
    "ECOS_9.2.6.0": [/* results */]
  }
}
```

---

### 5. `compare_versions`

**Purpose**: Compare a topic in TWO versions side-by-side.

**Use when**: Before/after analysis, regression checking, tracking evolution.

**Parameters**:

- `query` (string, required): Topic to compare.
- `version1_filter` (string, required): First version/baseline.
- `version2_filter` (string, required): Second version/comparison.
- `limit` (integer, optional): Max results per version.
- `context_window` (integer, optional): Pages before/after.

**Example**:

```json
{
  "tool": "compare_versions",
  "arguments": {
    "query": "DHCP improvements",
    "version1_filter": "ECOS_9.2.4.0",
    "version2_filter": "ECOS_9.2.5.0",
    "limit": 2
  }
}
```

**Returns**:

```json
{
  "query": "DHCP improvements",
  "version1": {
    "filename": "ECOS_9.2.4.0",
    "results": [/* results from v9.2.4 */]
  },
  "version2": {
    "filename": "ECOS_9.2.5.0",
    "results": [/* results from v9.2.5 */]
  }
}
```

---

## Production Deployment

### Step 1: Configure `.env` for Production

```bash
# Use production Qdrant
USE_PRODUCTION=true
QDRANT_PROD_URL=https://your-qdrant-prod.com
QDRANT_PROD_API_KEY=your-prod-api-key

# Enable Search API authentication
SEARCH_API_KEY_ENABLED=true
SEARCH_API_KEY=your-strong-random-key

# Set environment mode
ENVIRONMENT=production
```

### Step 2: Build and Push Docker Images

```bash
# Build images
docker build -t ghcr.io/crypto-gi/docsplorer-search-api:v0.1.1 services/search-api
docker build -t ghcr.io/crypto-gi/docsplorer-mcp-server:v0.1.1 services/mcp-server

# Push to registry
docker push ghcr.io/crypto-gi/docsplorer-search-api:v0.1.1
docker push ghcr.io/crypto-gi/docsplorer-mcp-server:v0.1.1
```

> You can also use the `latest` tags instead of versioned tags if you always want the most recent published images:
>
> - `ghcr.io/crypto-gi/docsplorer-search-api:latest`
> - `ghcr.io/crypto-gi/docsplorer-mcp-server:latest`

### Step 3: Deploy with Docker Compose

Update `docker-compose.yml` to use the registry images:

```yaml
services:
  search-api:
    image: ghcr.io/crypto-gi/docsplorer-search-api:v0.1.1
    # ... rest of config

  mcp-server:
    image: ghcr.io/crypto-gi/docsplorer-mcp-server:v0.1.1
    # ... rest of config
```

If you maintain your own fork or want to customize the services, replace `crypto-gi` and the tag (`v0.1.1`) with your own GHCR namespace and version.

Then deploy:

```bash
docker compose pull
docker compose up -d
```

### Step 4: Verify Health

```bash
# Check Search API
curl http://your-server:8001/health

# Check MCP Server
curl http://your-server:8505/health
```

---

## Troubleshooting

### Error: "Connection refused" to Search API

**Cause**: MCP server cannot reach the Search API.

**Fix**:

1. Check `SEARCH_API_URL` in `.env`:
   - In Docker: should be `http://search-api:8000`
   - Local: should be `http://localhost:8001`

2. Verify Search API is running:

   ```bash
   curl http://localhost:8001/health
   ```

---

### Error: "401 Unauthorized" from Search API

**Cause**: Search API has authentication enabled but MCP server didn't send API key.

**Fix**:

Set `SEARCH_API_KEY` in `.env`:

```bash
SEARCH_API_KEY=your-api-key-here
```

Restart MCP server:

```bash
docker compose restart mcp-server
```

---

### Error: "Collection 'content' does not exist"

**Cause**: Qdrant collection name mismatch.

**Fix**:

1. Check collection name in Qdrant:

   ```bash
   curl http://localhost:6333/collections
   ```

2. Update `QDRANT_COLLECTION` in `.env` to match.

---

### MCP Server Not Responding in HTTP Mode

**Cause**: Port conflict or firewall blocking.

**Fix**:

1. Check if port 8505 is in use:

   ```bash
   netstat -tuln | grep 8505
   ```

2. Change `MCP_HTTP_PORT` in `.env` if needed.

3. Restart:

   ```bash
   docker compose restart mcp-server
   ```

---

## Summary

- **stdio mode**: For IDE integration (Windsurf, Claude Desktop).
- **HTTP mode**: For automation tools (n8n, custom scripts).
- **5 tools**: Filename search, single-doc search, multi-query, multi-file, version comparison.
- **Production**: Enable auth, use HTTPS Qdrant, push images to registry.

For complete beginners:

1. Copy `.env.example` to `.env`.
2. Set `QDRANT_DEV_URL` and `OLLAMA_HOST`.
3. Run `docker compose up`.
4. Test with `curl http://localhost:8505/health`.
5. Use MCP tools from your client!
