import unittest
from unittest.mock import MagicMock
import uuid
import sys
import os

# Add mcp package root to sys.path for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../servers')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../servers/mcp-neo4j-memory/src')))

from mcp_neo4j_memory.server import Neo4jMemory, Entity, Relation

class FakeNeo4jDriver:
    def __init__(self):
        self.queries = []
        self.params = []
    def execute_query(self, query, params=None):
        self.queries.append(query)
        self.params.append(params)
        # Simulated successful response
        class Result:
            records = [{"entity_id": str(uuid.uuid4()), "name": params.get("name", ""), "type": params.get("type", ""), "relation_id": str(uuid.uuid4()), "relation_type": params.get("relation_type", "")}] if params else []
        return Result()

class TestIssue67Fix(unittest.IsolatedAsyncioTestCase):
    """Test for Issue #67 fix (async support)"""

    def setUp(self):
        self.neo4j_driver = FakeNeo4jDriver()
        self.kg_tool = Neo4jMemory(self.neo4j_driver)

    async def test_create_entities_fixed(self):
        """Test for fixed create_entities function"""
        test_entities = [
            Entity(name='Test Entity 1', type='L1_Knowledge', observations=['Test observation 1'])
        ]
        self.neo4j_driver.queries.clear()  # Clear query history before test
        result = await self.kg_tool.create_entities(test_entities)
        self.assertEqual(len(self.neo4j_driver.queries), 1)
        self.assertEqual(result[0].name, 'Test Entity 1')

    async def test_create_relations_fixed(self):
        """Test for fixed create_relations function"""
        test_relations = [
            Relation(source='Test Entity 1', target='Test Entity 2', relationType='contains')
        ]
        self.neo4j_driver.queries.clear()  # Clear query history before test
        result = await self.kg_tool.create_relations(test_relations)
        self.assertEqual(len(self.neo4j_driver.queries), 1)
        self.assertEqual(result[0].source, 'Test Entity 1')

if __name__ == '__main__':
    unittest.main()
