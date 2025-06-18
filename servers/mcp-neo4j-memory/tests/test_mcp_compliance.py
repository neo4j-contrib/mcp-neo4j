#!/usr/bin/env python3
"""
MCP Compliance Test Runner

This script specifically tests MCP protocol compliance for all transport protocols.
It can be run independently or as part of the full test suite.
"""

import subprocess
import sys
import os
import time
from pathlib import Path


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")


def run_test_command(command: list, description: str) -> bool:
    """Run a test command and return success status."""
    print(f"\nRunning: {description}")
    print(f"Command: {' '.join(command)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            command,
            cwd=Path(__file__).parent.parent,
            capture_output=False,  # Show output in real-time
            text=True
        )
        
        success = result.returncode == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status}: {description}")
        
        return success
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def check_dependencies():
    """Check that required dependencies are available."""
    print_header("Checking Dependencies")
    
    missing_deps = []
    
    try:
        import pytest
        print("✅ pytest available")
    except ImportError:
        missing_deps.append("pytest")
    
    try:
        import aiohttp
        print("✅ aiohttp available")
    except ImportError:
        missing_deps.append("aiohttp")
    
    try:
        import neo4j
        print("✅ neo4j driver available")
    except ImportError:
        missing_deps.append("neo4j")
    
    try:
        from mcp_neo4j_memory.core import Neo4jMemory
        print("✅ MCP Neo4j Memory core available")
    except ImportError:
        missing_deps.append("mcp_neo4j_memory")
    
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("💡 Install missing dependencies and try again")
        return False
    
    print("✅ All dependencies available")
    return True


def check_neo4j():
    """Check Neo4j connectivity."""
    print_header("Checking Neo4j Connection")
    
    try:
        from neo4j import GraphDatabase
        
        uri = os.environ.get("NEO4J_URI", "neo4j://localhost:7687")
        user = os.environ.get("NEO4J_USERNAME", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "password")
        
        print(f"Connecting to: {uri}")
        print(f"Username: {user}")
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        driver.close()
        
        print("✅ Neo4j connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("\n💡 Environment variables:")
        print(f"   NEO4J_URI={os.environ.get('NEO4J_URI', 'neo4j://localhost:7687')}")
        print(f"   NEO4J_USERNAME={os.environ.get('NEO4J_USERNAME', 'neo4j')}")
        print(f"   NEO4J_PASSWORD={'***' if os.environ.get('NEO4J_PASSWORD') else 'password'}")
        return False


def run_mcp_compliance_tests():
    """Run MCP protocol compliance tests."""
    print_header("MCP Protocol Compliance Tests")
    
    tests = [
        # Unit tests for MCP tools and protocol handling
        {
            "command": ["python", "-m", "pytest", "tests/test_unit.py", "-v", "-k", "mcp"],
            "description": "MCP Tools Definition Tests"
        },
        
        # SSE MCP compliance tests
        {
            "command": ["python", "-m", "pytest", "tests/test_sse_mcp_compliance.py", "-v"],
            "description": "SSE MCP Protocol Compliance"
        },
        
        # Transport integration with focus on MCP compliance
        {
            "command": ["python", "-m", "pytest", "tests/test_transport_integration.py", "-v", "-k", "mcp or tools"],
            "description": "Transport Protocol MCP Integration"
        }
    ]
    
    results = []
    
    for test in tests:
        success = run_test_command(test["command"], test["description"])
        results.append((test["description"], success))
    
    return results


def run_live_server_tests():
    """Run tests against a live SSE server if available."""
    print_header("Live Server Integration Tests")
    
    # Check if a server is running
    server_url = os.environ.get("MCP_SSE_SERVER_URL", "http://localhost:3001")
    
    print(f"Checking for live server at: {server_url}")
    
    try:
        import requests
        response = requests.get(f"{server_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Live SSE server detected")
            
            # Run live integration tests
            success = run_test_command(
                ["python", "-m", "pytest", "tests/test_sse_mcp_compliance.py", "-v", "-m", "integration"],
                "Live SSE Server Integration Tests"
            )
            
            return [("Live Server Integration", success)]
        else:
            print(f"❌ Server responded with status {response.status_code}")
            
    except Exception as e:
        print(f"⏭️ No live server available: {e}")
        print("💡 To test against a live server:")
        print("   1. Start the SSE server: docker run -p 3001:3001 ... --mode sse")
        print("   2. Set MCP_SSE_SERVER_URL=http://localhost:3001")
        print("   3. Run this script again")
    
    return []


def main():
    """Main test runner function."""
    print("🚀 MCP Protocol Compliance Test Suite")
    print("Testing MCP specification compliance across all transport protocols")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check Neo4j
    neo4j_available = check_neo4j()
    if not neo4j_available:
        print("⚠️ Some tests will be skipped without Neo4j")
        print("💡 For complete testing, ensure Neo4j is running and accessible")
    
    # Run MCP compliance tests
    compliance_results = run_mcp_compliance_tests() if neo4j_available else []
    
    # Run live server tests
    live_results = run_live_server_tests()
    
    # Combine results
    all_results = compliance_results + live_results
    
    # Print summary
    print_header("Test Results Summary")
    
    passed = 0
    failed = 0
    
    for test_name, success in all_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {test_name}")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Results: {passed} passed, {failed} failed")
    
    # Overall assessment
    if failed == 0 and passed > 0:
        print("\n🎉 ALL MCP COMPLIANCE TESTS PASSED!")
        print("✅ Your SSE server is fully MCP-compliant")
        print("✅ Ready for use with Claude Desktop, MCP Inspector, and other MCP clients")
        return 0
    elif failed == 0 and passed == 0:
        print("\n⚠️ NO TESTS RUN")
        print("💡 Check Neo4j connection and dependencies")
        return 1
    else:
        print(f"\n❌ {failed} MCP COMPLIANCE TEST(S) FAILED")
        print("💡 Review the errors above to fix MCP protocol issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
