#!/usr/bin/env python3

import json
from datetime import datetime
from src.mcp_neo4j_memory.server import Entity, KnowledgeGraph

# Test the JSON serialization issue
def test_json_serialization():
    # Create an entity with datetime fields
    entity = Entity(
        name="TestEntity",
        type="Test",
        observations=["Test observation"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    print("Testing entity.model_dump():")
    try:
        data = entity.model_dump()
        print("model_dump() succeeded")
        json_str = json.dumps(data)
        print("json.dumps(model_dump()) FAILED to reach here")
    except Exception as e:
        print(f"json.dumps(model_dump()) failed: {e}")
    
    print("\nTesting entity.model_dump_json_safe():")
    try:
        data = entity.model_dump_json_safe()
        print("model_dump_json_safe() succeeded")
        json_str = json.dumps(data)
        print("json.dumps(model_dump_json_safe()) succeeded!")
        print(f"JSON: {json_str}")
    except Exception as e:
        print(f"json.dumps(model_dump_json_safe()) failed: {e}")
    
    # Test KnowledgeGraph
    print("\nTesting KnowledgeGraph:")
    kg = KnowledgeGraph(entities=[entity], relations=[])
    try:
        data = kg.model_dump_json_safe()
        json_str = json.dumps(data)
        print("KnowledgeGraph.model_dump_json_safe() + json.dumps() succeeded!")
    except Exception as e:
        print(f"KnowledgeGraph serialization failed: {e}")

if __name__ == "__main__":
    test_json_serialization()