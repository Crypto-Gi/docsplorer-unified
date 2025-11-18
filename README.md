# Docsplorer Unified

A production-ready, open source stack for **semantic documentation search**.

Docsplorer Unified combines:

- **Search API** – a FastAPI service backed by Qdrant for vector search over documentation.
- **Docsplorer MCP Server** – a Model Context Protocol (MCP) server that exposes powerful search tools to LLM-based agents, IDEs, and workflow engines.

This repository is designed for teams who want to index their technical documentation (release notes, guides, PDFs, etc.) and query it using modern embeddings and vector search.

---

## Features

- **Vector-powered search API** for rich semantic queries over documentation.
- **MCP server with multiple tools** for filename discovery, single-doc search, multi-doc comparisons, and batch queries.
- **Embeddings via Ollama or Gemini** (configurable via environment variables).
- **Unified configuration** using a single `.env` file at the repo root.
- **Docker Compose setup** to run the full stack with one command.
- **HTTP and stdio transport** for the MCP server, suitable for IDEs and HTTP-based tools.
- **MIT-licensed & public**, ideal as a template or starting point for your own documentation search stack.

---

## Architecture Overview

Docsplorer Unified consists of two services:

1. **Search API (FastAPI + Qdrant)**
   - Exposes endpoints for semantic content search and fuzzy filename search.
   - Uses a vector database (Qdrant) to store and query document embeddings.
   - Supports multiple embedding backends via an abstraction layer (e.g., Ollama, Gemini).

2. **Docsplorer MCP Server (FastMCP)**
   - Implements the Model Context Protocol (MCP) so LLM clients can call tools.
   - Communicates with the Search API over HTTP.
   - Provides tools like:
     - `search_filenames_fuzzy` – discover candidate documents by filename.
     - `search_with_filename_filter` – search within a specific document.
     - `search_multi_query_with_filter` – run multiple queries within one document.
     - `search_across_multiple_files` – search a topic across multiple documents.
     - `compare_versions` – compare how a topic changes between two versions.

Both services are orchestrated via `docker-compose.yml` and share a single `.env` configuration file.

---

## Repository Layout

```text
docsplorer-unified/
├── .env                 # Your environment configuration (not committed)
├── .env.example         # Example env file with all variables and explanations
├── docker-compose.yml   # Orchestrates Search API + MCP server
├── Makefile             # Optional developer convenience commands
├── services/
│   ├── search-api/      # FastAPI-based semantic search API
│   └── mcp-server/      # Docsplorer MCP server
└── docs/                # (Optional) documentation for your deployment
```

> Note: The `.env.example` file documents all configuration variables and is the best place to start when setting up the stack.

---

## Getting Started

### 1. Prerequisites

- **Docker** and **Docker Compose** installed.
- A running **Qdrant** instance (local Docker or managed service).
- An **Ollama** instance (for local embeddings) or a **Gemini** API key.

### 2. Clone the Repository

```bash
git clone https://github.com/Crypto-Gi/docsplorer-unified.git
cd docsplorer-unified
```

### 3. Configure Environment Variables

Copy the example env file:

```bash
cp .env.example .env
```

Open `.env` and adjust values for your environment. At minimum you will want to set:

- `QDRANT_DEV_URL` – URL for your dev Qdrant instance (e.g., `http://localhost:6333` or your lab server).
- `EMBEDDING_PROVIDER` – `ollama` or `gemini`.
- For **Ollama**:
  - `OLLAMA_HOST` – URL of your Ollama server.
  - `OLLAMA_EMBEDDING_MODEL` – embedding model name (e.g., `bge-m3`).
- For **Gemini**:
  - `GEMINI_API_KEY` – your Gemini API key.

The `.env.example` file includes detailed comments explaining each variable.

### 4. Start the Stack with Docker Compose

From the repo root:

```bash
docker compose up --build
```

This will:

- Build and start the **Search API** (FastAPI + Qdrant client).
- Build and start the **Docsplorer MCP server** (HTTP mode on port 8505).

Health checks will verify that both services are running.

---

## Services & Ports

By default:

- **Search API**: `http://localhost:8001`
  - Internal container port: `8000`
  - Exposed via Docker Compose using `SEARCH_API_PORT` in `.env`.
- **MCP HTTP Server**: `http://localhost:8505`
  - Provides the `/mcp` endpoint for MCP clients.
  - Provides `/health` for health checks.

You can customize ports via `.env` (e.g., `SEARCH_API_PORT`, `MCP_HTTP_PORT`).

---

## Using the MCP Server

Docsplorer MCP Server is designed to be consumed by:

- **IDEs and MCP-aware clients** using stdio transport.
- **HTTP clients / workflow engines** (e.g., custom scripts, automation platforms) via HTTP.

### HTTP Mode

When running under Docker Compose, the MCP server starts in HTTP mode and can be reached at:

```text
http://localhost:8505/mcp
```

Your MCP client or integration should be configured to send MCP-compliant HTTP requests to this URL.

### Stdio Mode (Local Development)

For local development without Docker, you can run the MCP server directly (from `services/mcp-server`):

```bash
python server.py  # defaults to stdio transport
```

This is useful when integrating with IDEs that speak MCP over stdio.

---

## Search API Overview

The Search API (FastAPI) is responsible for:

- Generating embeddings for queries.
- Querying Qdrant for nearest neighbors.
- Applying filters (e.g., by filename or metadata).
- Returning ranked results and optional context windows around matched pages.

Typical flows include:

1. Discover relevant documents via fuzzy filename search.
2. Select one or more filenames and perform semantic content search.
3. Retrieve context (pages before/after) for better LLM prompts.

All requests are JSON-based and the MCP server handles payload construction for you.

---

## Configuration Highlights

Key environment groups (see `.env.example` for full details):

- **Global settings**: `ENVIRONMENT`, `DEBUG`, `REQUEST_TIMEOUT`
- **Qdrant dev/prod config**: `QDRANT_DEV_URL`, `QDRANT_PROD_URL`, `QDRANT_DEV_API_KEY`, `QDRANT_PROD_API_KEY`
- **Embedding provider**: `EMBEDDING_PROVIDER`, `OLLAMA_*`, `GEMINI_*`
- **Search defaults**: `CONTEXT_WINDOW_SIZE`, `DEFAULT_RESULT_LIMIT`, `USE_PRODUCTION`
- **MCP server**: `SEARCH_API_URL`, `MCP_TRANSPORT`, `MCP_HTTP_HOST`, `MCP_HTTP_PORT`

The goal is to have a **single source of truth** for configuration that both services consume.

---

## Production Deployment

For production deployments you can:

- Use the provided Dockerfiles to build images and push them to a container registry (e.g., GitHub Container Registry).
- Configure `ENVIRONMENT=production` and use the `QDRANT_PROD_*` variables for your production Qdrant cluster.
- Enable API key authentication between the MCP server and the Search API if desired.

A typical production flow:

1. Build images for `search-api` and `mcp-server`.
2. Push images to your registry.
3. Deploy `docker-compose.yml` or equivalent manifests (Kubernetes, Nomad, etc.) referencing those images.
4. Point your MCP client or workflow engine at the MCP HTTP endpoint.

---

## Contributing

Contributions are welcome. If you’d like to:

- Add support for new embedding providers.
- Integrate additional MCP tools.
- Improve documentation or examples.

Feel free to open an issue or submit a pull request.

Please follow standard best practices:

- Fork the repo and create a feature branch.
- Add or update tests where appropriate.
- Keep changes focused and well-documented.

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](./LICENSE) file for details.

---

## Keywords (SEO)

Semantic search, vector search, Qdrant, Ollama, Gemini, MCP server, Model Context Protocol, documentation search, release notes search, FastAPI, Python, Docker, Docker Compose, LLM tools, IDE integration, HTTP MCP, stdio MCP, AI-powered documentation search, semantic documentation explorer.
