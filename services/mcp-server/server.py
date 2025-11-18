"""
Docsplorer - Document Explorer MCP Server

Model Context Protocol server for semantic search through documentation and release notes.
Uses Qdrant vector database for intelligent document discovery and content retrieval.
Provides 5 specialized tools for exploring, searching, and comparing documentation.
"""

import httpx
from fastmcp import FastMCP
from config import MCPConfig
from typing import Optional
from starlette.requests import Request
from starlette.responses import PlainTextResponse

# Initialize MCP server and config
mcp = FastMCP("Docsplorer")
config = MCPConfig()


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    """Simple HTTP health endpoint for container orchestration.

    Returns 200 OK with body "OK" when the MCP HTTP server is running.
    """
    return PlainTextResponse("OK")


@mcp.tool()
async def search_filenames_fuzzy(
    query: str,
    limit: Optional[int] = None
) -> dict:
    """
    Discover available documents using fuzzy filename search.
    
    **Use when:** Don't know exact filename, need to discover docs before searching content.
    **Workflow:** Call this first → use returned filename in other tools → get content.
    
    Args:
        query: Filename search (e.g., "ecos 9.3", "release notes", "dhcp docs")
        limit: Max filenames (default: .env DEFAULT_LIMIT). Use 5-10 for broader discovery.
        
    Returns:
        {"query": str, "total_matches": int, "filenames": [{"filename": str, "score": float}]}
        
    Example:
        search_filenames_fuzzy("ecos 9.3", limit=5)
        # Returns: {"total_matches": 3, "filenames": [{"filename": "ECOS_9.3.6.0_Release_Notes_RevB", "score": 0.95}, ...]}
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{config.api_url}/search/filenames",
            json={
                "query": query,
                "collection_name": config.qdrant_collection,
                "limit": limit or config.default_limit,
                "use_production": config.use_production
            },
            headers=config.get_headers()
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def search_with_filename_filter(
    query: str,
    filename_filter: str,
    limit: Optional[int] = None,
    context_window: Optional[int] = None
) -> dict:
    """
    Search content within ONE document using semantic matching.
    
    **Use when:** Know filename, single topic, want context pages.
    **Don't use:** Multiple docs (use search_across_multiple_files), multiple topics (use search_multi_query_with_filter).
    
    Args:
        query: Search term (e.g., "security vulnerabilities", "DHCP config", "performance")
        filename_filter: Document to search (exact: "ECOS_9.3.6.0_Release_Notes_RevB" or partial: "ECOS_9.3.6")
        limit: Max results (default: .env). Use 1-2 for focused, 3-5 for comprehensive.
        context_window: Pages before/after (default: .env, range: 0-11). Use 1-2 for match only, 5-7 for context, 10-11 for max.
        
    Returns:
        {"results": [[{"filename": str, "score": float, "center_page": int, "combined_page": str, "page_numbers": [int]}]]}
        
    Example:
        search_with_filename_filter("security vulnerabilities", "ECOS_9.3.6.0_Release_Notes_RevB", limit=2, context_window=5)
        # Returns passages with 5 pages before/after (11 total)
    """
    payload = config.build_search_payload(
        search_queries=[query],
        limit=limit,
        context_window_size=context_window,
        filter_dict={"metadata.filename": {"match_text": filename_filter}}
    )
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{config.api_url}/search",
            json=payload,
            headers=config.get_headers()
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def search_multi_query_with_filter(
    queries: list[str],
    filename_filter: str,
    limit: Optional[int] = None,
    context_window: Optional[int] = None
) -> dict:
    """
    Run multiple searches within ONE document (batch processing).
    
    **Use when:** Multiple topics in single document. Faster than calling search_with_filename_filter multiple times.
    **Don't use:** Single topic (use search_with_filename_filter), multiple docs (use search_across_multiple_files).
    **Best practice:** Group 3-5 related queries.
    
    Args:
        queries: List of queries (e.g., ["security", "performance", "bugs"], ["DHCP", "DNS", "routing"])
        filename_filter: Document to search (exact or partial)
        limit: Max results per query (default: .env). Each query gets this independently.
        context_window: Pages before/after (default: .env). Applied to all queries.
        
    Returns:
        {"results": [[results_query_1], [results_query_2], ...]}  # Results match queries order
        
    Example:
        search_multi_query_with_filter(["security fixes", "performance", "bugs"], "ECOS_9.3.6.0", limit=2, context_window=5)
        # Returns 3 result sets
    """
    payload = config.build_search_payload(
        search_queries=queries,
        limit=limit,
        context_window_size=context_window,
        filter_dict={"metadata.filename": {"match_text": filename_filter}}
    )
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{config.api_url}/search",
            json=payload,
            headers=config.get_headers()
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def search_across_multiple_files(
    query: str,
    filename_filters: list[str],
    limit: Optional[int] = None,
    context_window: Optional[int] = None
) -> dict:
    """
    Search ONE topic across MULTIPLE documents (cross-file search).
    
    **Use when:** Track feature across versions, compare docs, find topic in multiple files.
    **Don't use:** Single doc (use search_with_filename_filter), multiple topics (use search_multi_query_with_filter), only 2 versions (use compare_versions).
    **Best practice:** Use for 3+ related documents.
    
    Args:
        query: Single query for all docs (e.g., "DHCP security", "performance improvements", "CVE-2023-12345")
        filename_filters: List of docs (exact: ["ECOS_9.3.5.0_Release_Notes_RevB", ...] or partial: ["ECOS_9.3.5", "ECOS_9.3.6"])
        limit: Max results per file (default: .env). Each file gets this independently.
        context_window: Pages before/after (default: .env). Applied to all files.
        
    Returns:
        {"query": str, "results_by_file": {"filename1": [results], "filename2": [results], ...}}
        
    Example:
        search_across_multiple_files("DHCP security", ["ECOS_9.3.5.0", "ECOS_9.3.6.0", "ECOS_9.3.7.0"], limit=2, context_window=5)
        # Returns DHCP info from all 3 versions, grouped by file
    """
    results_by_file = {}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for filename_filter in filename_filters:
            payload = config.build_search_payload(
                search_queries=[query],
                limit=limit,
                context_window_size=context_window,
                filter_dict={"metadata.filename": {"match_text": filename_filter}}
            )
            
            response = await client.post(
                f"{config.api_url}/search",
                json=payload,
                headers=config.get_headers()
            )
            response.raise_for_status()
            data = response.json()
            results_by_file[filename_filter] = data["results"][0] if data["results"] else []
    
    return {
        "query": query,
        "results_by_file": results_by_file
    }


@mcp.tool()
async def compare_versions(
    query: str,
    version1_filter: str,
    version2_filter: str,
    limit: Optional[int] = None,
    context_window: Optional[int] = None
) -> dict:
    """
    Compare topic in TWO versions side-by-side (before/after comparison).
    
    **Use when:** Compare 2 specific versions, track evolution, before/after analysis, regression checking.
    **Don't use:** More than 2 versions (use search_across_multiple_files), single version (use search_with_filename_filter).
    **Best practice:** Use for adjacent versions (e.g., 9.3.6 → 9.3.7).
    
    Args:
        query: Topic to compare (e.g., "DHCP security improvements", "memory leak fix", "routing protocol")
        version1_filter: First version/baseline (e.g., "ECOS_9.3.6.0_Release_Notes", "Product_v1.0")
        version2_filter: Second version/comparison (e.g., "ECOS_9.3.7.0_Release_Notes", "Product_v2.0")
        limit: Max results per version (default: .env). Each version gets this.
        context_window: Pages before/after (default: .env). Applied to both versions.
        
    Returns:
        {"query": str, "version1": {"filename": str, "results": [...]}, "version2": {"filename": str, "results": [...]}}
        
    Example:
        compare_versions("DHCP security", "ECOS_9.3.6.0_Release_Notes", "ECOS_9.3.7.0_Release_Notes", limit=2, context_window=5)
        # Returns side-by-side comparison
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get results for version 1
        payload_v1 = config.build_search_payload(
            search_queries=[query],
            limit=limit,
            context_window_size=context_window,
            filter_dict={"metadata.filename": {"match_text": version1_filter}}
        )
        response_v1 = await client.post(
            f"{config.api_url}/search",
            json=payload_v1,
            headers=config.get_headers()
        )
        response_v1.raise_for_status()
        data_v1 = response_v1.json()
        
        # Get results for version 2
        payload_v2 = config.build_search_payload(
            search_queries=[query],
            limit=limit,
            context_window_size=context_window,
            filter_dict={"metadata.filename": {"match_text": version2_filter}}
        )
        response_v2 = await client.post(
            f"{config.api_url}/search",
            json=payload_v2,
            headers=config.get_headers()
        )
        response_v2.raise_for_status()
        data_v2 = response_v2.json()
    
    return {
        "query": query,
        "version1": {
            "filename": version1_filter,
            "results": data_v1["results"][0] if data_v1["results"] else []
        },
        "version2": {
            "filename": version2_filter,
            "results": data_v2["results"][0] if data_v2["results"] else []
        }
    }


if __name__ == "__main__":
    import argparse
    import sys
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Docsplorer MCP Server - Semantic documentation search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with stdio (default - for IDE integration)
  python server.py
  
  # Run with HTTP (for n8n integration) - default port 8505
  python server.py --transport http
  
  # Run with HTTP on custom port
  python server.py --transport http --port 8080
  
  # Run with HTTP on specific host and port
  python server.py --transport http --host 127.0.0.1 --port 8505
        """
    )
    
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol (default: stdio for IDE integration)"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to for HTTP transport (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8505,
        help="Port to bind to for HTTP transport (default: 8505)"
    )
    
    args = parser.parse_args()
    
    print(f"Starting Docsplorer MCP Server with config: {config}")
    print(f"Transport: {args.transport}")
    
    if args.transport == "stdio":
        # Run with stdio transport (default for IDE integration)
        print("Mode: stdio (for IDE integration - Windsurf, Claude Desktop)")
        mcp.run()
    
    elif args.transport == "http":
        # Run with HTTP transport (for n8n integration)
        print(f"Mode: HTTP server on {args.host}:{args.port}")
        print(f"Access at: http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}")
        print("\nHTTP MCP endpoint (for tools like n8n, HTTP clients, etc.):")
        print(f'  URL: http://localhost:{args.port}/mcp')
        print("\nPress Ctrl+C to stop the server")
        
        try:
            import uvicorn
            app = mcp.http_app()
            uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("\nError: uvicorn is required for HTTP transport")
            print("Install it with: pip install uvicorn[standard]")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            sys.exit(0)
