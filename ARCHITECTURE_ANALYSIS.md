# Docsplorer Unified Architecture Analysis

**Executive Summary**: This document provides a comprehensive analysis of the `qdrant-semantic-search-api` and `docsplorer` MCP server projects, with recommendations for unifying them into a single, production-ready stack.

---

## Table of Contents

1. [Project Analysis](#1-project-analysis)
2. [Environment Variable Mapping](#2-environment-variable-mapping)
3. [Unified Architecture Proposal](#3-unified-architecture-proposal)
4. [Docker Strategy Recommendation](#4-docker-strategy-recommendation)
5. [Migration & Implementation Plan](#5-migration--implementation-plan)
6. [Developer Workflows](#6-developer-workflows)
7. [Risks & Validation](#7-risks--validation)

---

## 1. Project Analysis

### 1.1 Qdrant Semantic Search API

**Repository**: `qdrant-semantic-search-api`
**Technology**: FastAPI + Qdrant + Ollama/Gemini embeddings
**Port**: 8000 (internal), 8001 (exposed)

#### Architecture

```
FastAPI App (main.py)
├── Endpoints
│   ├── POST /search - Semantic search with filters
│   ├── POST /search/filenames - Fuzzy filename discovery
│   └── GET /health - Service health check
├── Components
│   ├── SearchSystem - Core search orchestration
│   ├── EmbeddingProviderFactory - Ollama/Gemini abstraction
│   ├── QdrantClient - Connection pooling (dev/prod)
│   └── Content cleaning - Token optimization
└── Configuration
    ├── Dev/Prod environment switching
    ├── Per-request Qdrant overrides
    └── API key authentication (Bearer token)
```

#### Key Features

- **Multi-tenant**: Per-request Qdrant URL/API key override
- **Dual environments**: DEV_* and PROD_* variable sets
- **Connection pooling**: Separate clients for dev/prod
- **Flexible embedding**: Ollama (local) or Gemini (API)
- **Content optimization**: Automatic whitespace cleaning (98.8% token reduction)
- **Security**: Optional API key authentication

#### Current Environment Variables (30+)

**Global**:
- `ENVIRONMENT` (development|production)
- `DEBUG`, `REQUEST_TIMEOUT`
- `API_KEY_ENABLED`, `API_KEY`

**Qdrant Configuration**:
- `DEV_QDRANT_URL`, `DEV_QDRANT_API_KEY`, `DEV_QDRANT_VERIFY_SSL`
- `PROD_QDRANT_URL`, `PROD_QDRANT_API_KEY`, `PROD_QDRANT_VERIFY_SSL`
- `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_VERIFY_SSL` (fallback)
- `QDRANT_HOST` (legacy)
- `QDRANT_FORCE_IGNORE_SSL`

**Embedding Configuration**:
- `EMBEDDING_PROVIDER` (ollama|gemini)
- `DEFAULT_EMBEDDING_MODEL`, `DEFAULT_VECTOR_SIZE`
- `OLLAMA_HOST`
- `GEMINI_API_KEY`, `GEMINI_EMBEDDING_MODEL`, `GEMINI_EMBEDDING_TASK_TYPE`, `GEMINI_EMBEDDING_DIM`

**Other**:
- `CONTEXT_WINDOW_SIZE`

---

### 1.2 Docsplorer MCP Server

**Repository**: `docsplorer`
**Technology**: FastMCP + httpx
**Port**: 8505 (HTTP mode)
**Transports**: stdio (IDE) | HTTP (n8n)

#### Architecture

```
FastMCP Server (server.py)
├── MCP Tools (5)
│   ├── search_filenames_fuzzy
│   ├── search_with_filename_filter
│   ├── search_multi_query_with_filter
│   ├── search_across_multiple_files
│   └── compare_versions
├── Configuration (config.py)
│   ├── MCPConfig - Environment variable loading
│   ├── get_headers() - API key injection
│   └── build_search_payload() - Request construction
└── Transport Modes
    ├── stdio - For IDE integration (Windsurf, Claude Desktop)
    └── HTTP - For n8n workflows (uvicorn server)
```

#### Key Features

- **Dual transport**: stdio (IDE) + HTTP (n8n)
- **5 specialized tools**: Optimized for documentation search workflows
- **Client-side orchestration**: Builds requests for search API
- **Environment-driven**: All config from .env
- **Zero embedding logic**: Pure API client

#### Current Environment Variables (9)

- `API_URL` - Search API endpoint
- `API_KEY` - Search API authentication
- `QDRANT_COLLECTION` - Collection name
- `QDRANT_HOST`, `QDRANT_API_KEY` - Optional overrides
- `OLLAMA_URL`, `OLLAMA_API_KEY` - Optional overrides
- `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`
- `USE_PRODUCTION` - Dev/prod switch
- `DEFAULT_CONTEXT_WINDOW`, `DEFAULT_LIMIT`
- `TRANSPORT`, `HOST`, `PORT` (HTTP mode)

---

### 1.3 Service Communication

**Current Flow**:
```
MCP Client (IDE/n8n)
    ↓ stdio or HTTP
Docsplorer MCP Server (8505)
    ↓ HTTP (API_URL)
Search API (8001)
    ↓
Qdrant Vector DB
    ↓
Ollama/Gemini Embeddings
```

**Request Path**:
1. MCP client calls tool (e.g., `search_with_filename_filter`)
2. MCP server builds search payload using `config.py`
3. MCP server sends HTTP POST to `API_URL/search`
4. Search API generates embeddings, queries Qdrant
5. Search API returns results
6. MCP server forwards results to MCP client

**Authentication**: Single API key shared between MCP server and Search API

---

## 2. Environment Variable Mapping

See [ENV_MAPPING.md](./ENV_MAPPING.md) for detailed mapping.

### Key Consolidations

| Concept | Search API | MCP Server | Unified Name | Notes |
|---------|------------|------------|--------------|-------|
| **Environment** | `ENVIRONMENT` | N/A | `ENVIRONMENT` | Keep as-is |
| **API Key** | `API_KEY` | `API_KEY` | `SEARCH_API_KEY` | Rename for clarity |
| **Qdrant Dev URL** | `DEV_QDRANT_URL` | N/A | `QDRANT_DEV_URL` | Consistent prefix |
| **Qdrant Prod URL** | `PROD_QDRANT_URL` | N/A | `QDRANT_PROD_URL` | Consistent prefix |
| **Collection** | Passed in request | `QDRANT_COLLECTION` | `QDRANT_COLLECTION` | Keep as-is |
| **Embedding Provider** | `EMBEDDING_PROVIDER` | N/A | `EMBEDDING_PROVIDER` | Keep as-is |
| **MCP Port** | N/A | `PORT` | `MCP_HTTP_PORT` | Explicit naming |
| **Search API Port** | Hardcoded 8000 | N/A | `SEARCH_API_PORT` | Add for flexibility |

**Total Variables**: 31 (reduced from 39 through consolidation)

---

## 3. Unified Architecture Proposal

### 3.1 Recommended Repo Structure

```
docsplorer-unified/
├── .env                          # Single source of truth
├── .env.example                  # Template with all variables
├── docker-compose.yml            # Orchestrates both services
├── Makefile                      # Developer commands
├── README.md                     # Unified documentation
│
├── services/
│   ├── search-api/               # Qdrant Semantic Search API
│   │   ├── Dockerfile
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── embeddings/
│   │   │   └── requirements.txt
│   │   └── tests/
│   │
│   └── mcp-server/               # Docsplorer MCP Server
│       ├── Dockerfile
│       ├── config.py
│       ├── server.py
│       ├── requirements.txt
│       └── tests/
│
├── shared/                       # Common utilities (future)
│   ├── config/                   # Shared config validation
│   └── types/                    # Common type definitions
│
└── docs/
    ├── ARCHITECTURE.md           # This document
    ├── DEPLOYMENT.md            # Deployment guide
    ├── ENV_MAPPING.md           # Environment variable reference
    └── MIGRATION_GUIDE.md       # Migration instructions
```

### 3.2 Service Communication Model

**Internal Docker Network** (docker-compose):
```
mcp-server:
  API_URL: http://search-api:8000
  
search-api:
  container_name: search-api
  expose: [8000]
```

**External Access**:
- MCP HTTP: `http://localhost:8505` (for n8n)
- Search API: `http://localhost:8001` (optional, for direct access)

**MCP stdio Mode** (local dev):
```bash
# MCP server uses configured API_URL
API_URL=http://localhost:8001 python services/mcp-server/server.py
```

### 3.3 Configuration Flow

```
Root .env file
    ├── Loaded by docker-compose.yml (env_file: .env)
    ├── Passed to search-api container
    └── Passed to mcp-server container
        ├── stdio mode: Reads .env directly
        └── HTTP mode: Reads from Docker environment
```

**Key Principle**: One .env file, consumed by both services with prefix-based namespacing (e.g., `SEARCH_API_*`, `MCP_*`)

---

## 4. Docker Strategy Recommendation

### Recommendation: **Two-Image Approach** ✅

#### Rationale

| Criterion | Two Images | Single Image |
|-----------|------------|--------------|
| **Separation of concerns** | ✅ Clean | ❌ Coupled |
| **Independent scaling** | ✅ Yes | ❌ Limited |
| **MCP stdio support** | ✅ Native | ⚠️ Complex |
| **Development flexibility** | ✅ Run either service | ❌ All or nothing |
| **Build caching** | ✅ Independent | ❌ Shared |
| **Maintenance** | ✅ Simple | ❌ Complex entrypoint |

#### Implementation

**Image 1: Search API**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY services/search-api/ .
RUN pip install -r requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Image 2: MCP Server**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY services/mcp-server/ .
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "server.py"]
CMD ["--transport", "http", "--port", "8505"]
```

#### MCP Transport Flexibility

**stdio Mode** (IDE integration):
```bash
# Local Python (recommended for dev)
cd services/mcp-server
python server.py  # Defaults to stdio

# Or via Docker (less common)
docker run -it --env-file .env docsplorer-mcp --transport stdio
```

**HTTP Mode** (n8n integration):
```bash
# Docker Compose (recommended for prod)
docker compose up

# Or standalone
docker run -p 8505:8505 --env-file .env docsplorer-mcp --transport http
```

**Key Insight**: Two images preserve stdio support naturally—just run `server.py` locally without Docker for IDE integration.

---

## 5. Migration & Implementation Plan

See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for step-by-step instructions.

### Phase 1: Repository Restructure (Non-Breaking)

1. Create new directory structure
2. Move files to `services/*`
3. Update import paths in search-api (`app.*` → relative)
4. Test both services independently

### Phase 2: Environment Consolidation

1. Create unified `.env.example`
2. Map old→new variable names
3. Update config loaders in both services
4. Provide migration script for existing .env files

### Phase 3: Docker Unification

1. Create root `docker-compose.yml`
2. Update Dockerfiles with new paths
3. Configure internal networking
4. Add health checks and dependencies

### Phase 4: Documentation & Testing

1. Update all README files
2. Create architecture diagrams
3. Test end-to-end workflows
4. Validate MCP stdio and HTTP modes

### Migration Script Example

```bash
#!/bin/bash
# migrate-env.sh - Convert old .env to new format

cp search-api/.env .env.tmp
echo "# MCP Server Configuration" >> .env.tmp
grep "API_URL\|API_KEY" mcp-server/.env >> .env.tmp

# Rename variables
sed -i 's/^API_KEY=/SEARCH_API_KEY=/' .env.tmp
sed -i 's/^DEV_QDRANT_URL=/QDRANT_DEV_URL=/' .env.tmp
# ... more transformations

mv .env.tmp .env
```

---

## 6. Developer Workflows

### Makefile Targets

```makefile
# Development
dev-api:          # Run search API locally
dev-mcp-stdio:    # Run MCP server in stdio mode
dev-mcp-http:     # Run MCP server in HTTP mode
dev:              # Run both services (API + MCP HTTP)

# Docker
docker-build:     # Build both images
docker-up:        # Start services via docker-compose
docker-down:      # Stop services
docker-logs:      # Tail logs

# Testing
test-api:         # Run search API tests
test-mcp:         # Run MCP server tests
test:             # Run all tests

# Utilities
validate-env:     # Check .env completeness
lint:             # Run linters
format:           # Format code
```

### Common Workflows

**Local Development (No Docker)**:
```bash
# Terminal 1: Start search API
make dev-api

# Terminal 2: Start MCP server (stdio)
make dev-mcp-stdio

# IDE: Configure MCP client to use stdio
```

**Docker Development**:
```bash
make docker-up       # Starts both services
make docker-logs     # Watch output
curl http://localhost:8505/  # Test MCP HTTP
```

**MCP stdio in IDE** (Windsurf/Claude):
```json
{
  "mcpServers": {
    "docsplorer": {
      "command": "python",
      "args": ["/path/to/services/mcp-server/server.py"],
      "env": {
        "API_URL": "http://localhost:8001",
        "API_KEY": "your-key"
      }
    }
  }
}
```

---

## 7. Risks & Validation

### Breaking Changes

1. **Environment variable renames**: Existing deployments must update .env
2. **File paths**: Any hardcoded paths will break
3. **Docker image names**: CI/CD pipelines need updates

### Mitigation

- Provide automated migration script
- Maintain backward compatibility layer (1-2 releases)
- Comprehensive migration guide with examples
- Version bump to v2.0.0 (semantic versioning)

### Validation Checklist

#### Functional Tests
- [ ] Search API endpoints respond correctly
- [ ] MCP stdio mode works with IDE
- [ ] MCP HTTP mode accessible from n8n
- [ ] Docker Compose starts both services
- [ ] Health checks pass
- [ ] API authentication works

#### End-to-End Workflows
- [ ] Fuzzy filename search → content search
- [ ] Multi-query batch search
- [ ] Cross-file comparison
- [ ] Context window retrieval
- [ ] Gemini embedding provider
- [ ] Ollama embedding provider

#### Configuration Tests
- [ ] Dev environment configuration
- [ ] Prod environment configuration
- [ ] Per-request Qdrant override
- [ ] SSL verification modes
- [ ] API key authentication on/off

#### Integration Tests
- [ ] Qdrant connectivity (dev)
- [ ] Qdrant connectivity (prod)
- [ ] Ollama service integration
- [ ] Gemini API integration
- [ ] Docker internal networking
- [ ] External port exposure

---

## Summary & Next Steps

### Key Recommendations

1. **Adopt two-image approach**: Preserves flexibility, clean separation
2. **Unified .env at root**: Single source of truth for config
3. **Keep MCP stdio support**: Critical for IDE integration
4. **Use Docker Compose for prod**: Orchestrate both services cleanly
5. **Namespace variables**: `SEARCH_API_*`, `MCP_*`, `QDRANT_*`, etc.

### Implementation Priority

**High Priority**:
- Repository restructure
- Unified .env schema
- Docker Compose setup

**Medium Priority**:
- Makefile developer commands
- Migration guide and scripts
- Updated documentation

**Low Priority**:
- Shared utilities module
- CI/CD updates
- Monitoring/observability

### Timeline Estimate

- **Week 1**: Repo restructure + env consolidation
- **Week 2**: Docker unification + testing
- **Week 3**: Documentation + migration guide
- **Week 4**: Buffer for issues + final validation

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-18  
**Prepared By**: AI Architecture Consultant
