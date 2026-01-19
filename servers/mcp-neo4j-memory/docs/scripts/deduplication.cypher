// =============================================================================
// Memory Node Deduplication Script for mcp-neo4j-memory
// =============================================================================
// Purpose: Identify and merge duplicate Memory nodes
// Version: 1.0.0
// Date: 2026-01-18
//
// IMPORTANT: Create a database backup before running this script!
// Run queries in order and verify results at each step.
// =============================================================================

// -----------------------------------------------------------------------------
// SECTION 1: Audit Duplicates
// -----------------------------------------------------------------------------

// 1.1 Find all duplicate Memory node names
MATCH (m:Memory)
WITH m.name as name, collect(m) as nodes, count(*) as count
WHERE count > 1
RETURN name, count,
       [n IN nodes | {id: id(n), type: n.type, obsCount: size(coalesce(n.observations, []))}] as duplicates
ORDER BY count DESC;

// 1.2 Count nodes with NULL names
MATCH (m:Memory)
WHERE m.name IS NULL
RETURN m.type as type, count(m) as count
ORDER BY count DESC;

// 1.3 Show nodes with NULL names and their titles (may have title instead of name)
MATCH (m:Memory)
WHERE m.name IS NULL AND m.title IS NOT NULL
RETURN id(m) as nodeId, m.type as type, m.title as title,
       size(coalesce(m.observations, [])) as obsCount
LIMIT 30;


// -----------------------------------------------------------------------------
// SECTION 2: Fix NULL Names
// -----------------------------------------------------------------------------

// 2.1 Copy title to name for nodes that have title but no name
MATCH (m:Memory)
WHERE m.name IS NULL AND m.title IS NOT NULL
SET m.name = m.title
RETURN count(m) as nodesFixed;

// 2.2 Generate names for remaining NULL name nodes using type + id
MATCH (m:Memory)
WHERE m.name IS NULL
SET m.name = coalesce(m.type, 'Unknown') + '_' + toString(id(m))
RETURN count(m) as nodesFixed;

// 2.3 Verify no more NULL names
MATCH (m:Memory)
WHERE m.name IS NULL
RETURN count(m) as remainingNullNames;


// -----------------------------------------------------------------------------
// SECTION 3: Merge Duplicate Persons
// -----------------------------------------------------------------------------
// Strategy: Keep the node with the most observations, merge relationships

// 3.1 Preview Person duplicates that will be merged
MATCH (p:Person:Memory)
WHERE p.name IS NOT NULL
WITH p.name as name, collect(p) as nodes
WHERE size(nodes) > 1
UNWIND nodes as node
RETURN name, id(node) as nodeId, size(coalesce(node.observations, [])) as obsCount,
       labels(node) as labels
ORDER BY name, obsCount DESC;

// 3.2 Merge Person duplicates (keeps node with most observations)
MATCH (p:Person:Memory)
WHERE p.name IS NOT NULL
WITH p.name as name, collect(p) as nodes
WHERE size(nodes) > 1
// Sort by observation count descending to keep the richest node
WITH name, nodes,
     head([n IN nodes | n ORDER BY size(coalesce(n.observations, [])) DESC]) as keeper
WITH name, keeper, [n IN nodes WHERE n <> keeper] as toDelete

// Merge observations from deleted nodes into keeper
UNWIND toDelete as deleteNode
WITH name, keeper, deleteNode,
     [obs IN coalesce(deleteNode.observations, [])
      WHERE NOT obs IN coalesce(keeper.observations, [])] as newObs
SET keeper.observations = coalesce(keeper.observations, []) + newObs

// Transfer incoming relationships
WITH name, keeper, deleteNode
CALL {
    WITH keeper, deleteNode
    MATCH (deleteNode)<-[r]->(other)
    WHERE other <> keeper
    WITH keeper, deleteNode, r, other, type(r) as relType, startNode(r) as start
    CALL apoc.do.when(
        start = deleteNode,
        'MERGE (keeper)-[newR:`' + relType + '`]->(other) RETURN newR',
        'MERGE (other)-[newR:`' + relType + '`]->(keeper) RETURN newR',
        {keeper: keeper, other: other, relType: relType}
    ) YIELD value
    RETURN value
}

// Delete the duplicate node
WITH name, keeper, deleteNode
DETACH DELETE deleteNode
RETURN name, id(keeper) as keptNodeId;


// -----------------------------------------------------------------------------
// SECTION 4: Simplified Merge (if APOC not available)
// -----------------------------------------------------------------------------
// Use this section if APOC procedures are not available

// 4.1 Manual merge: Transfer relationships then delete duplicates
// Run this for each duplicate pair found in Section 1

// Example for "Andrew Immerman" (nodes 148 and 405):
// First, identify which node to keep (the one with more observations)
MATCH (keeper:Memory {name: 'Andrew Immerman'})
RETURN id(keeper) as nodeId, size(coalesce(keeper.observations, [])) as obsCount
ORDER BY obsCount DESC;

// 4.2 Merge observations from duplicate to keeper
// Replace NODE_ID_TO_DELETE and NODE_ID_TO_KEEP with actual IDs
// MATCH (keeper:Memory), (dup:Memory)
// WHERE id(keeper) = NODE_ID_TO_KEEP AND id(dup) = NODE_ID_TO_DELETE
// WITH keeper, dup, [obs IN coalesce(dup.observations, []) WHERE NOT obs IN coalesce(keeper.observations, [])] as newObs
// SET keeper.observations = coalesce(keeper.observations, []) + newObs
// RETURN keeper.name, size(keeper.observations) as totalObs;

// 4.3 Transfer outgoing relationships (example)
// MATCH (dup:Memory)-[r]->(target)
// WHERE id(dup) = NODE_ID_TO_DELETE
// MATCH (keeper:Memory)
// WHERE id(keeper) = NODE_ID_TO_KEEP
// MERGE (keeper)-[newR:SAME_TYPE_AS_R]->(target)
// DELETE r;

// 4.4 Transfer incoming relationships (example)
// MATCH (source)-[r]->(dup:Memory)
// WHERE id(dup) = NODE_ID_TO_DELETE
// MATCH (keeper:Memory)
// WHERE id(keeper) = NODE_ID_TO_KEEP
// MERGE (source)-[newR:SAME_TYPE_AS_R]->(keeper)
// DELETE r;

// 4.5 Delete duplicate after relationship transfer
// MATCH (dup:Memory)
// WHERE id(dup) = NODE_ID_TO_DELETE
// DETACH DELETE dup;


// -----------------------------------------------------------------------------
// SECTION 5: Batch Deduplication (Without APOC)
// -----------------------------------------------------------------------------
// This approach identifies duplicates and handles them one at a time

// 5.1 Get list of duplicate names to process
MATCH (m:Memory)
WHERE m.name IS NOT NULL
WITH m.name as name, collect(id(m)) as nodeIds, count(*) as count
WHERE count > 1
RETURN name, nodeIds, count
ORDER BY count DESC;

// 5.2 For each duplicate name, run this to merge (replace NAME_VALUE):
// Step A: Identify keeper (most observations)
MATCH (m:Memory {name: 'REPLACE_WITH_NAME'})
WITH m ORDER BY size(coalesce(m.observations, [])) DESC
WITH collect(m) as nodes
WITH nodes[0] as keeper, nodes[1..] as duplicates
RETURN id(keeper) as keeperId, [d IN duplicates | id(d)] as duplicateIds;

// Step B: Merge observations
MATCH (m:Memory {name: 'REPLACE_WITH_NAME'})
WITH m ORDER BY size(coalesce(m.observations, [])) DESC
WITH collect(m) as nodes
WITH nodes[0] as keeper, nodes[1..] as duplicates
UNWIND duplicates as dup
WITH keeper, dup, [obs IN coalesce(dup.observations, []) WHERE NOT obs IN coalesce(keeper.observations, [])] as newObs
SET keeper.observations = coalesce(keeper.observations, []) + newObs
RETURN keeper.name, size(keeper.observations) as totalObservations;

// Step C: Delete duplicates (after manually transferring important relationships)
MATCH (m:Memory {name: 'REPLACE_WITH_NAME'})
WITH m ORDER BY size(coalesce(m.observations, [])) DESC
WITH collect(m) as nodes
WITH nodes[0] as keeper, nodes[1..] as duplicates
UNWIND duplicates as dup
DETACH DELETE dup
RETURN keeper.name as kept, count(*) as deleted;


// -----------------------------------------------------------------------------
// SECTION 6: Automated Batch Deduplication
// -----------------------------------------------------------------------------
// This merges all duplicates automatically, keeping the node with most observations

// 6.1 Merge all Memory node duplicates (WARNING: Reviews relationships are lost!)
// Only use if relationships are not critical or can be recreated
MATCH (m:Memory)
WHERE m.name IS NOT NULL
WITH m.name as name, collect(m) as nodes
WHERE size(nodes) > 1
WITH name, nodes,
     head(apoc.coll.sortNodes(nodes, '^observations')) as keeper
WITH name, keeper, [n IN nodes WHERE n <> keeper] as toDelete
UNWIND toDelete as dup
// Merge observations
WITH name, keeper, dup,
     [obs IN coalesce(dup.observations, []) WHERE NOT obs IN coalesce(keeper.observations, [])] as newObs
SET keeper.observations = coalesce(keeper.observations, []) + newObs
WITH name, keeper, dup
DETACH DELETE dup
RETURN name, id(keeper) as keptId;


// -----------------------------------------------------------------------------
// SECTION 7: Post-Deduplication Verification
// -----------------------------------------------------------------------------

// 7.1 Verify no more duplicates
MATCH (m:Memory)
WHERE m.name IS NOT NULL
WITH m.name as name, count(*) as count
WHERE count > 1
RETURN name, count;

// 7.2 Verify no NULL names remain
MATCH (m:Memory)
WHERE m.name IS NULL
RETURN count(m) as nullNames;

// 7.3 Now apply the uniqueness constraint
CREATE CONSTRAINT memory_name_unique IF NOT EXISTS
FOR (m:Memory)
REQUIRE m.name IS UNIQUE;

// 7.4 Verify constraint was created
SHOW CONSTRAINTS;


// =============================================================================
// END OF DEDUPLICATION SCRIPT
// =============================================================================
