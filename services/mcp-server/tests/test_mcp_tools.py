#!/usr/bin/env python3
"""
Test MCP server tools with API key authentication
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import MCPConfig
import httpx

async def test_search_filenames_with_api_key():
    """Test search_filenames tool with API key"""
    print("🧪 Testing MCP Server with API Key Authentication\n")
    
    config = MCPConfig()
    
    print(f"📋 Configuration:")
    print(f"   API URL: {config.api_url}")
    print(f"   API Key: {'✅ Configured' if config.api_key else '❌ Not configured'}")
    print(f"   Collection: {config.qdrant_collection}")
    print(f"   Production: {config.use_production}\n")
    
    # Test 1: search_filenames endpoint
    print("🔍 Test 1: Calling /search/filenames endpoint...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{config.api_url}/search/filenames",
                json={
                    "query": "ecos",
                    "collection_name": config.qdrant_collection,
                    "limit": 2,
                    "use_production": config.use_production
                },
                headers=config.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS! Status: {response.status_code}")
                print(f"   Query: {result['query']}")
                print(f"   Total matches: {result['total_matches']}")
                print(f"   Filenames: {[f['filename'] for f in result['filenames']]}\n")
                return True
            else:
                print(f"❌ FAILED! Status: {response.status_code}")
                print(f"   Response: {response.text}\n")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {str(e)}\n")
        return False

async def test_without_api_key():
    """Test that requests fail without API key when auth is enabled"""
    print("🔒 Test 2: Verifying API key is required...")
    
    config = MCPConfig()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try without Authorization header
            response = await client.post(
                f"{config.api_url}/search/filenames",
                json={
                    "query": "ecos",
                    "collection_name": config.qdrant_collection,
                    "limit": 2,
                    "use_production": config.use_production
                },
                headers={"Content-Type": "application/json"}  # No API key
            )
            
            if response.status_code == 401:
                print(f"✅ CORRECT! Rejected without API key (401)\n")
                return True
            elif response.status_code == 200:
                print(f"⚠️  WARNING: Request succeeded without API key!")
                print(f"   API_KEY_ENABLED might be false\n")
                return True
            else:
                print(f"❌ Unexpected status: {response.status_code}\n")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {str(e)}\n")
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("MCP SERVER API KEY AUTHENTICATION TEST")
    print("=" * 60 + "\n")
    
    # Test with API key
    test1 = await test_search_filenames_with_api_key()
    
    # Test without API key
    test2 = await test_without_api_key()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ With API Key: {'PASSED' if test1 else 'FAILED'}")
    print(f"✅ Without API Key: {'PASSED' if test2 else 'FAILED'}")
    print("=" * 60 + "\n")
    
    if test1 and test2:
        print("🎉 All tests passed! MCP server API key authentication works!\n")
        return 0
    else:
        print("❌ Some tests failed. Check configuration.\n")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
