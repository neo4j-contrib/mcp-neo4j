#!/usr/bin/env python3

# %%
"""
Simple script to count nodes in Neo4j database
"""
import os
from contextlib import contextmanager
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables once
load_dotenv()

@contextmanager
def get_neo4j_session():
    """Context manager for Neo4j database connection"""
    url = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE")

    driver = GraphDatabase.driver(url, auth=(username, password))
    try:
        with driver.session(database=database) as session:
            yield session
    finally:
        driver.close()

# %%
def count_nodes():
    """Count total nodes in the database"""
    with get_neo4j_session() as session:
        result = session.run("MATCH (n) RETURN count(n) as node_count")
        record = result.single()
        node_count = record["node_count"]
        print(f"Total nodes in database: {node_count}")
        return node_count

# %%
def reset_database():
    """Reset the database by deleting all nodes and relationships"""
    with get_neo4j_session() as session:
        # Delete all relationships first, then all nodes
        session.run("MATCH ()-[r]->() DELETE r")
        result = session.run("MATCH (n) DELETE n RETURN count(n) as deleted_count")
        record = result.single()
        deleted_count = record["deleted_count"]
        print(f"Deleted {deleted_count} nodes from database")
        return deleted_count

# %%
count_nodes()
reset_database()
count_nodes()
# %%
