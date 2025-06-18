#!/usr/bin/env python3
"""
Comprehensive test runner for MCP Neo4j Memory refactored architecture.

This script runs all tests and provides a summary of the test results.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command: list, description: str) -> bool:
    """Run a command and return whether it succeeded."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        success = result.returncode == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\nResult: {status}")

        return success

    except Exception as e:
        print(f"❌ ERROR: Failed to run command: {e}")
        return False


def check_neo4j_connection() -> bool:
    """Check if Neo4j is available for testing."""
    print("🔍 Checking Neo4j connection...")

    try:
        from neo4j import GraphDatabase

        uri = os.environ.get("NEO4J_URI", "neo4j://localhost:7687")
        user = os.environ.get("NEO4J_USERNAME", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "password")

        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        driver.close()

        print("✅ Neo4j connection successful")
        return True

    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("💡 Make sure Neo4j is running and environment variables are set:")
        print("   - NEO4J_URI (default: neo4j://localhost:7687)")
        print("   - NEO4J_USERNAME (default: neo4j)")
        print("   - NEO4J_PASSWORD (default: password)")
        return False


def run_import_test() -> bool:
    """Test that all imports work correctly."""
    print("🔍 Testing imports...")

    try:
        # Test core imports
        from mcp_neo4j_memory.core import Neo4jMemory, Entity, Relation, KnowledgeGraph
        from mcp_neo4j_memory.core import ObservationAddition, ObservationDeletion
        from mcp_neo4j_memory.core import get_mcp_tools, execute_tool

        # Test protocol imports
        from mcp_neo4j_memory.protocols import run_stdio_server, run_sse_server

        # Test CLI import
        from mcp_neo4j_memory.cli import main

        # Test main package import
        from mcp_neo4j_memory import main as package_main

        print("✅ All imports successful")
        return True

    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


def main():
    """Run all tests and provide summary."""
    print("🚀 MCP Neo4j Memory - Comprehensive Test Suite")
    print("Testing refactored architecture with new modular structure")

    # Track test results
    results = {}

    # Check imports first
    results["imports"] = run_import_test()

    # Check Neo4j connection
    results["neo4j_connection"] = check_neo4j_connection()

    # Run unit tests for core models and basic functionality
    results["unit_tests"] = run_command(
        ["python", "-m", "pytest", "tests/test_unit.py", "tests/test_core_models.py", "tests/test_json_string_parsing.py", "-v"],
        "Unit Tests (No External Dependencies)"
    )

    # Run integration tests (only if Neo4j is available)
    if results["neo4j_connection"]:
        results["core_integration"] = run_command(
            ["python", "-m", "pytest", "tests/test_neo4j_memory_integration.py", "-v"],
            "Core Neo4j Integration Tests"
        )

        results["transport_integration"] = run_command(
            ["python", "-m", "pytest", "tests/test_transport_integration.py", "-v"],
            "Transport Protocol Integration Tests"
        )

        results["sse_mcp_compliance"] = run_command(
            ["python", "-m", "pytest", "tests/test_sse_mcp_compliance.py", "-v"],
            "SSE MCP Protocol Compliance Tests"
        )
    else:
        print("\n⚠️ Skipping integration tests - Neo4j not available")
        results["core_integration"] = None
        results["transport_integration"] = None
        results["sse_mcp_compliance"] = None

    # Run all tests together
    if results["neo4j_connection"]:
        results["all_tests"] = run_command(
            ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
            "All Tests Combined"
        )
    else:
        results["all_tests"] = run_command(
            ["python", "-m", "pytest", "tests/test_unit.py", "tests/test_core_models.py", "tests/test_json_string_parsing.py", "-v"],
            "Available Unit Tests Only"
        )

    # Test CLI functionality
    results["cli_help"] = run_command(
        ["python", "-m", "mcp_neo4j_memory", "--help"],
        "CLI Help Command"
    )

    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")

    passed = 0
    failed = 0
    skipped = 0

    for test_name, result in results.items():
        if result is True:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        elif result is False:
            print(f"❌ {test_name}: FAILED")
            failed += 1
        else:
            print(f"⏭️ {test_name}: SKIPPED")
            skipped += 1

    print(f"\n📈 Results: {passed} passed, {failed} failed, {skipped} skipped")

    # Overall assessment
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Refactoring appears successful.")

        if skipped > 0:
            print("💡 Some tests were skipped due to missing dependencies (likely Neo4j).")
            print("   Set up Neo4j and run again for complete testing.")

        return 0
    else:
        print(f"\n❌ {failed} TEST(S) FAILED. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
