# Executive Summary: Docsplorer Stack Unification

**Prepared For**: Docsplorer Stack Owner  
**Prepared By**: AI Architecture Consultant  
**Date**: 2025-11-18  
**Project**: Unifying `qdrant-semantic-search-api` and `docsplorer` MCP server

---

## Overview

This document provides an executive-level summary of the comprehensive architecture analysis and unification plan for the Docsplorer semantic search stack.

---

## Current State

### Two Separate Projects

**1. Qdrant Semantic Search API**
- FastAPI-based vector search service
- Supports Ollama and Gemini embeddings
- 8001 port exposure, 30+ environment variables
- Per-request Qdrant configuration override

**2. Docsplorer MCP Server**
- Model Context Protocol server
- Dual transport: stdio (IDE) + HTTP (n8n)
- 5 specialized search tools
- Client for Search API

### Pain Points

❌ **Configuration fragmentation**: Two separate `.env` files with overlapping variables  
❌ **Deployment complexity**: Must coordinate two separate docker-compose setups  
❌ **Variable naming inconsistencies**: `API_KEY` vs `API_KEY`, `DEV_QDRANT_URL` vs no prefix  
❌ **Documentation split**: Users must consult two separate README files  
❌ **No unified development workflow**: Separate build/test/deploy processes

---

## Recommended Solution

### Two-Image Monorepo Architecture ✅

```
docsplorer-unified/
├── .env                    # Single source of truth
├── docker-compose.yml      # Orchestrates both services
├── Makefile               # Unified developer commands
│
├── services/
│   ├── search-api/        # Image 1: FastAPI search service
│   └── mcp-server/        # Image 2: MCP server (stdio + HTTP)
│
└── docs/                  # Consolidated documentation
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Two separate images** | Preserves flexibility, enables independent scaling, maintains stdio support |
| **Single .env at root** | Eliminates configuration duplication and drift |
| **Consistent variable naming** | `SEARCH_API_*`, `MCP_*`, `QDRANT_*` prefixes |
| **Docker Compose orchestration** | Internal networking, health checks, dependency management |
| **Preserved MCP stdio mode** | Critical for IDE integration (Windsurf, Claude Desktop) |

---

## Benefits

### Operational

✅ **Single deployment unit**: One `docker compose up` starts entire stack  
✅ **Unified configuration**: One `.env` file, no duplication or drift  
✅ **Internal networking**: MCP server → Search API via Docker network  
✅ **Health checks**: Automatic restart and dependency ordering  

### Development

✅ **Simplified workflows**: `make dev`, `make docker-up`, `make test`  
✅ **Consistent naming**: Reduced cognitive load, clearer variable purposes  
✅ **Consolidated docs**: Single source of truth for architecture and setup  
✅ **Flexible deployment**: Run locally or via Docker without code changes  

### Flexibility

✅ **MCP stdio preserved**: No regression for IDE integration  
✅ **Independent scaling**: Two images can scale separately  
✅ **Environment switching**: Dev/prod configuration via single flag  
✅ **Backward compatibility**: Migration script for existing deployments  

---

## Implementation Plan

### Timeline: 1-2 Weeks

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **1. Repository Restructure** | 1-2 days | Move files to `services/`, update imports |
| **2. Environment Consolidation** | 1 day | Unified `.env`, migration script, config loaders |
| **3. Docker Unification** | 1-2 days | Root `docker-compose.yml`, Makefile, networking |
| **4. Testing & Validation** | 1-2 days | End-to-end tests, both transport modes |
| **5. Documentation** | 1 day | Updated READMEs, architecture diagrams |
| **6. Deployment & Rollout** | 1 day | Production deployment, monitoring |

### Risk Level: **Medium**

**Breaking Changes**:
- Environment variable renames (e.g., `API_KEY` → `SEARCH_API_KEY`)
- File path changes (e.g., `app/main.py` → `services/search-api/app/main.py`)
- Docker image names

**Mitigation**:
- Automated migration script provided
- Backward compatibility layer (1-2 releases)
- Comprehensive migration guide
- Rollback plan documented

---

## Technical Highlights

### Environment Variables: 31 (down from 39)

**Consolidations**:
- Removed 8 duplicate/unused variables
- Standardized naming: `QDRANT_DEV_*` instead of `DEV_QDRANT_*`
- Clear prefixes: `SEARCH_API_*`, `MCP_*`, `QDRANT_*`

**Example Mapping**:
```
Old (Search API):  API_KEY, DEV_QDRANT_URL
Old (MCP Server):  API_KEY, API_URL
New (Unified):     SEARCH_API_KEY, QDRANT_DEV_URL, SEARCH_API_URL
```

### Docker Networking

**Internal Communication** (within Docker):
```yaml
mcp-server:
  environment:
    - SEARCH_API_URL=http://search-api:8000
```

**External Access** (from host):
- Search API: `http://localhost:8001`
- MCP HTTP: `http://localhost:8505`
- MCP stdio: Direct Python execution (no Docker needed)

### MCP Transport Flexibility Preserved

**stdio Mode** (IDE integration):
```bash
cd services/mcp-server
python server.py --transport stdio
```

**HTTP Mode** (n8n integration):
```bash
docker compose up  # or
python server.py --transport http --port 8505
```

---

## Migration Strategy

### For Existing Deployments

1. **Backup current configurations**
2. **Run migration script** (`migrate-env.sh`)
3. **Update service configs** to use new variable names
4. **Test locally** before production deployment
5. **Deploy to staging** for validation
6. **Production rollout** with rollback plan ready

### Migration Script Provided

Automatically converts:
- Old `.env` files → unified `.env`
- Variable renames
- Path adjustments
- Backups created automatically

---

## Success Metrics

### Post-Migration

- [ ] Single `docker compose up` starts both services
- [ ] MCP stdio mode works with IDE clients
- [ ] MCP HTTP mode accessible from n8n
- [ ] All existing tests passing
- [ ] Configuration drift eliminated
- [ ] Developer onboarding time reduced by 50%

### Long-Term

- Independent service scaling
- Unified monitoring and logging
- Single CI/CD pipeline
- Consistent versioning strategy

---

## Recommendations

### High Priority (Week 1)

1. ✅ **Adopt two-image approach**: Clean separation, preserves flexibility
2. ✅ **Implement unified .env**: Single source of truth
3. ✅ **Create Docker Compose setup**: Orchestrate both services
4. ✅ **Run migration script**: Convert existing deployments

### Medium Priority (Week 2)

5. ⚠️ **Add Makefile**: Streamline developer workflows
6. ⚠️ **Update documentation**: Consolidated guides
7. ⚠️ **Create validation suite**: Ensure correctness

### Low Priority (Future)

8. 🔵 **Shared utilities module**: Common config/types
9. 🔵 **CI/CD updates**: Unified pipeline
10. 🔵 **Monitoring/observability**: Centralized logging

---

## Decision Points

### Question: Single image or two images?

**Answer**: **Two images** ✅

**Justification**:
- Preserves MCP stdio support (critical for IDE integration)
- Enables independent scaling
- Cleaner separation of concerns
- Simpler Dockerfile maintenance
- No degradation of existing capabilities

### Question: How to handle environment variables?

**Answer**: **Single .env at root, prefix-based namespacing** ✅

**Justification**:
- Eliminates duplication
- Clear ownership (SEARCH_API_*, MCP_*)
- Both services read from same file
- Easy to validate completeness
- Migration script handles conversion

### Question: MCP stdio support in Docker?

**Answer**: **Preserved natively by keeping two images** ✅

**Justification**:
- MCP server can run outside Docker (local Python)
- No complex entrypoint logic needed
- IDE clients don't require Docker
- HTTP mode still available via Docker

---

## Next Steps

1. **Review and approve** this architecture proposal
2. **Schedule migration** (1-2 week timeline)
3. **Allocate resources** for implementation and testing
4. **Communicate changes** to users and stakeholders
5. **Execute migration** following provided guide
6. **Monitor and validate** post-migration

---

## Deliverables Provided

📄 **[ARCHITECTURE_ANALYSIS.md](./ARCHITECTURE_ANALYSIS.md)** - Detailed technical analysis  
📄 **[ENV_MAPPING.md](./ENV_MAPPING.md)** - Complete variable mapping and migration script  
📄 **[MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)** - Step-by-step implementation plan  
📄 **[EXECUTIVE_SUMMARY.md](./EXECUTIVE_SUMMARY.md)** - This document

---

## Conclusion

The proposed unified architecture:

✅ **Solves current pain points** (configuration fragmentation, deployment complexity)  
✅ **Preserves all capabilities** (MCP stdio + HTTP, dev/prod switching)  
✅ **Improves developer experience** (single config, unified workflows)  
✅ **Maintains flexibility** (independent images, internal networking)  
✅ **Provides clear migration path** (automated script, rollback plan)  

**Recommendation**: **Proceed with implementation** following the provided migration guide.

---

**Questions or Concerns?**

Contact the architecture team or refer to the detailed documentation for clarification.

**Status**: ✅ Ready for Implementation  
**Risk**: 🟡 Medium (breaking changes, mitigated)  
**Timeline**: 1-2 weeks  
**ROI**: High (improved DX, reduced operational overhead)
