#!/usr/bin/env python3
"""
Test script for Docsplorer MCP Server HTTP mode
Tests all 5 tools and generates a report
"""

import httpx
import json
import sys
from typing import Dict, Any

# Test configuration
BASE_URL = "http://127.0.0.1:8505"
TIMEOUT = 30.0

# Test results
test_results = []

def log_test(test_name: str, status: str, details: str = ""):
    """Log test result"""
    result = {
        "test": test_name,
        "status": status,
        "details": details
    }
    test_results.append(result)
    
    emoji = "✅" if status == "PASS" else "❌"
    print(f"\n{emoji} {test_name}: {status}")
    if details:
        print(f"   {details}")

async def test_tools_list():
    """Test 1: List all available tools"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # MCP HTTP transport uses streamable HTTP
            # We need to make a proper MCP request
            response = await client.post(
                f"{BASE_URL}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {}
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "tools" in data["result"]:
                    tools = data["result"]["tools"]
                    tool_names = [t["name"] for t in tools]
                    log_test("Test 1: List Tools", "PASS", f"Found {len(tools)} tools: {', '.join(tool_names)}")
                    return True
                else:
                    log_test("Test 1: List Tools", "FAIL", f"Unexpected response: {data}")
                    return False
            else:
                log_test("Test 1: List Tools", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        log_test("Test 1: List Tools", "FAIL", f"Exception: {str(e)}")
        return False

async def test_search_filenames_fuzzy():
    """Test 2: search_filenames_fuzzy tool"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{BASE_URL}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "search_filenames_fuzzy",
                        "arguments": {
                            "query": "release notes",
                            "limit": 5
                        }
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    result = data["result"]
                    if isinstance(result, dict) and "content" in result:
                        content = result["content"][0]["text"] if result["content"] else ""
                        log_test("Test 2: search_filenames_fuzzy", "PASS", f"Returned results")
                        return True
                    else:
                        log_test("Test 2: search_filenames_fuzzy", "PASS", f"Got result: {str(result)[:100]}")
                        return True
                else:
                    log_test("Test 2: search_filenames_fuzzy", "FAIL", f"No result in response: {data}")
                    return False
            else:
                log_test("Test 2: search_filenames_fuzzy", "FAIL", f"HTTP {response.status_code}: {response.text[:200]}")
                return False
                
    except Exception as e:
        log_test("Test 2: search_filenames_fuzzy", "FAIL", f"Exception: {str(e)}")
        return False

async def test_search_with_filename_filter():
    """Test 3: search_with_filename_filter tool"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{BASE_URL}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "search_with_filename_filter",
                        "arguments": {
                            "query": "security",
                            "filename_filter": "release",
                            "limit": 2,
                            "context_window": 3
                        }
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    log_test("Test 3: search_with_filename_filter", "PASS", "Tool executed successfully")
                    return True
                else:
                    log_test("Test 3: search_with_filename_filter", "FAIL", f"No result: {data}")
                    return False
            else:
                log_test("Test 3: search_with_filename_filter", "FAIL", f"HTTP {response.status_code}")
                return False
                
    except Exception as e:
        log_test("Test 3: search_with_filename_filter", "FAIL", f"Exception: {str(e)}")
        return False

async def test_search_multi_query():
    """Test 4: search_multi_query_with_filter tool"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{BASE_URL}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "search_multi_query_with_filter",
                        "arguments": {
                            "queries": ["security", "performance"],
                            "filename_filter": "release",
                            "limit": 2
                        }
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    log_test("Test 4: search_multi_query_with_filter", "PASS", "Tool executed successfully")
                    return True
                else:
                    log_test("Test 4: search_multi_query_with_filter", "FAIL", f"No result: {data}")
                    return False
            else:
                log_test("Test 4: search_multi_query_with_filter", "FAIL", f"HTTP {response.status_code}")
                return False
                
    except Exception as e:
        log_test("Test 4: search_multi_query_with_filter", "FAIL", f"Exception: {str(e)}")
        return False

async def test_search_across_files():
    """Test 5: search_across_multiple_files tool"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{BASE_URL}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {
                        "name": "search_across_multiple_files",
                        "arguments": {
                            "query": "security",
                            "filename_filters": ["release", "notes"],
                            "limit": 2
                        }
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    log_test("Test 5: search_across_multiple_files", "PASS", "Tool executed successfully")
                    return True
                else:
                    log_test("Test 5: search_across_multiple_files", "FAIL", f"No result: {data}")
                    return False
            else:
                log_test("Test 5: search_across_multiple_files", "FAIL", f"HTTP {response.status_code}")
                return False
                
    except Exception as e:
        log_test("Test 5: search_across_multiple_files", "FAIL", f"Exception: {str(e)}")
        return False

async def test_compare_versions():
    """Test 6: compare_versions tool"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{BASE_URL}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "tools/call",
                    "params": {
                        "name": "compare_versions",
                        "arguments": {
                            "query": "security",
                            "version1_filter": "9.3",
                            "version2_filter": "9.6",
                            "limit": 2
                        }
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    log_test("Test 6: compare_versions", "PASS", "Tool executed successfully")
                    return True
                else:
                    log_test("Test 6: compare_versions", "FAIL", f"No result: {data}")
                    return False
            else:
                log_test("Test 6: compare_versions", "FAIL", f"HTTP {response.status_code}")
                return False
                
    except Exception as e:
        log_test("Test 6: compare_versions", "FAIL", f"Exception: {str(e)}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🧪 DOCSPLORER MCP SERVER - HTTP MODE TEST SUITE")
    print("=" * 60)
    print(f"\nTesting server at: {BASE_URL}")
    print(f"Timeout: {TIMEOUT}s\n")
    
    # Run all tests
    await test_tools_list()
    await test_search_filenames_fuzzy()
    await test_search_with_filename_filter()
    await test_search_multi_query()
    await test_search_across_files()
    await test_compare_versions()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    total = len(test_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")
    
    if failed > 0:
        print("Failed Tests:")
        for r in test_results:
            if r["status"] == "FAIL":
                print(f"  - {r['test']}: {r['details']}")
    
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
