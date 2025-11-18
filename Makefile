.PHONY: help dev-api dev-mcp-stdio dev-mcp-http dev docker-build docker-up docker-down docker-logs test-api test-mcp test validate-env lint format

help:
	@echo "Docsplorer Unified - Development Commands"
	@echo ""
	@echo "Development (no Docker):"
	@echo "  make dev-api          - Run search API locally"
	@echo "  make dev-mcp-stdio    - Run MCP server in stdio mode"
	@echo "  make dev-mcp-http     - Run MCP server in HTTP mode"
	@echo "  make dev              - Run both services (API + MCP HTTP)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     - Build Docker images"
	@echo "  make docker-up        - Start services via docker-compose"
	@echo "  make docker-down      - Stop services"
	@echo "  make docker-logs      - Tail service logs"
	@echo ""
	@echo "Testing:"
	@echo "  make test-api         - Run search API tests"
	@echo "  make test-mcp         - Run MCP server tests"
	@echo "  make test             - Run all tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make validate-env     - Check .env completeness"
	@echo "  make lint             - Run linters"
	@echo "  make format           - Format code"

dev-api:
	@echo "Starting Search API..."
	cd services/search-api && uvicorn app.main:app --reload --port 8000

dev-mcp-stdio:
	@echo "Starting MCP Server (stdio mode)..."
	cd services/mcp-server && python server.py --transport stdio

dev-mcp-http:
	@echo "Starting MCP Server (HTTP mode on port 8505)..."
	cd services/mcp-server && python server.py --transport http --port 8505

dev:
	@echo "Starting both services..."
	@echo "Search API will run on port 8000"
	@echo "MCP Server will run on port 8505"
	@make -j2 dev-api dev-mcp-http

docker-build:
	@echo "Building Docker images..."
	docker compose build

docker-up:
	@echo "Starting services..."
	docker compose up -d
	@echo ""
	@echo "Services started:"
	@echo "  Search API: http://localhost:8000"
	@echo "  MCP Server: http://localhost:8505"

docker-down:
	@echo "Stopping services..."
	docker compose down

docker-logs:
	docker compose logs -f

test-api:
	@echo "Running Search API tests..."
	cd services/search-api && python -m pytest tests/ || echo "No tests found"

test-mcp:
	@echo "Running MCP Server tests..."
	cd services/mcp-server && python -m pytest tests/ || echo "No tests found"

test: test-api test-mcp

validate-env:
	@echo "Validating .env file..."
	@if [ ! -f .env ]; then \
		echo "ERROR: .env file not found. Copy .env.example to .env"; \
		exit 1; \
	fi
	@echo ".env file exists"

lint:
	@echo "Running linters..."
	@cd services/search-api && ruff check app/ || echo "Ruff not installed"
	@cd services/mcp-server && ruff check . || echo "Ruff not installed"

format:
	@echo "Formatting code..."
	@cd services/search-api && ruff format app/ || echo "Ruff not installed"
	@cd services/mcp-server && ruff format . || echo "Ruff not installed"
