#!/usr/bin/env python3
"""
Functional test - Test actual tool execution with real API calls
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import server

async def test_tool_1():
    """Test search_filenames_fuzzy"""
    print("\n1️⃣ Testing search_filenames_fuzzy...")
    try:
        # Get the actual function from the tool wrapper
        tool_func = server.search_filenames_fuzzy.fn
        result = await tool_func(query="ecos", limit=3)
        if "filenames" in result or "total_matches" in result:
            print(f"   ✅ PASS - Got response: {len(str(result))} chars")
            return True
        else:
            print(f"   ❌ FAIL - Unexpected response format")
            return False
    except Exception as e:
        print(f"   ❌ FAIL - Error: {e}")
        return False

async def test_tool_2():
    """Test search_with_filename_filter"""
    print("\n2️⃣ Testing search_with_filename_filter...")
    try:
        tool_func = server.search_with_filename_filter.fn
        result = await tool_func(
            query="security",
            filename_filter="ECOS",
            limit=1,
            context_window=2
        )
        if "results" in result:
            print(f"   ✅ PASS - Got response: {len(str(result))} chars")
            return True
        else:
            print(f"   ❌ FAIL - Unexpected response format")
            return False
    except Exception as e:
        print(f"   ❌ FAIL - Error: {e}")
        return False

async def test_tool_3():
    """Test search_multi_query_with_filter"""
    print("\n3️⃣ Testing search_multi_query_with_filter...")
    try:
        tool_func = server.search_multi_query_with_filter.fn
        result = await tool_func(
            queries=["security", "performance"],
            filename_filter="ECOS",
            limit=1,
            context_window=2
        )
        if "results" in result:
            print(f"   ✅ PASS - Got response: {len(str(result))} chars")
            return True
        else:
            print(f"   ❌ FAIL - Unexpected response format")
            return False
    except Exception as e:
        print(f"   ❌ FAIL - Error: {e}")
        return False

async def test_tool_4():
    """Test search_across_multiple_files"""
    print("\n4️⃣ Testing search_across_multiple_files...")
    try:
        tool_func = server.search_across_multiple_files.fn
        result = await tool_func(
            query="security",
            filename_filters=["ECOS_9.3.5", "ECOS_9.3.6"],
            limit=1,
            context_window=2
        )
        if "results_by_file" in result:
            print(f"   ✅ PASS - Got response: {len(str(result))} chars")
            return True
        else:
            print(f"   ❌ FAIL - Unexpected response format")
            return False
    except Exception as e:
        print(f"   ❌ FAIL - Error: {e}")
        return False

async def test_tool_5():
    """Test compare_versions"""
    print("\n5️⃣ Testing compare_versions...")
    try:
        tool_func = server.compare_versions.fn
        result = await tool_func(
            query="security",
            version1_filter="ECOS_9.3.5",
            version2_filter="ECOS_9.3.6",
            limit=1,
            context_window=2
        )
        if "version1" in result and "version2" in result:
            print(f"   ✅ PASS - Got response: {len(str(result))} chars")
            return True
        else:
            print(f"   ❌ FAIL - Unexpected response format")
            return False
    except Exception as e:
        print(f"   ❌ FAIL - Error: {e}")
        return False

async def main():
    """Run all functional tests"""
    print("🧪 FUNCTIONAL TESTING - Actual Tool Execution")
    print("=" * 60)
    print("\n⚠️  Note: These tests require:")
    print("   - Docsplorer API running at http://localhost:8001")
    print("   - Qdrant database with indexed documents")
    print("   - Valid API configuration in .env")
    print()
    
    results = []
    
    # Test all 5 tools
    results.append(await test_tool_1())
    results.append(await test_tool_2())
    results.append(await test_tool_3())
    results.append(await test_tool_4())
    results.append(await test_tool_5())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FUNCTIONAL TEST RESULTS:")
    print(f"   Passed: {sum(results)}/5")
    print(f"   Failed: {5 - sum(results)}/5")
    
    if all(results):
        print("\n🎉 ALL FUNCTIONAL TESTS PASSED!")
        print("✅ All 5 tools are working with real API calls")
        return True
    else:
        print("\n⚠️  Some tests failed")
        print("   This may be due to:")
        print("   - API backend not running")
        print("   - Missing documents in database")
        print("   - Configuration issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
