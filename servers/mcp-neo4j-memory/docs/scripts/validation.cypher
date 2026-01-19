// =============================================================================
// World Model Schema Validation Queries for mcp-neo4j-memory
// =============================================================================
// Purpose: Validate schema compliance and data quality
// Version: 1.0.0
// Date: 2026-01-18
//
// Run these queries periodically to ensure data quality and schema compliance.
// =============================================================================

// -----------------------------------------------------------------------------
// SECTION 1: Entity Validation
// -----------------------------------------------------------------------------

// 1.1 Find entities missing required 'name' property
MATCH (n:Memory)
WHERE n.name IS NULL OR n.name = ''
RETURN labels(n) as labels, id(n) as nodeId, n.type as type
LIMIT 50;

// 1.2 Find entities missing 'type' property
MATCH (n:Memory)
WHERE n.type IS NULL OR n.type = ''
RETURN n.name as name, labels(n) as labels, id(n) as nodeId
LIMIT 50;

// 1.3 Find entities with invalid type format (should be PascalCase)
MATCH (n:Memory)
WHERE n.type IS NOT NULL
  AND NOT n.type =~ '^[A-Z][a-zA-Z0-9]*$'
RETURN n.name as name, n.type as invalidType
LIMIT 50;

// 1.4 Find entities without observations
MATCH (n:Memory)
WHERE n.observations IS NULL OR size(n.observations) = 0
RETURN n.name as name, n.type as type, labels(n) as labels
LIMIT 50;

// 1.5 Find duplicate entity names (name should be unique per type)
MATCH (n:Memory)
WITH n.name as name, n.type as type, count(*) as count
WHERE count > 1
RETURN name, type, count
ORDER BY count DESC
LIMIT 20;


// -----------------------------------------------------------------------------
// SECTION 2: Relationship Validation
// -----------------------------------------------------------------------------

// 2.1 Find invalid relationship types (should be SCREAMING_SNAKE_CASE)
MATCH ()-[r]->()
WHERE NOT type(r) =~ '^[A-Z][A-Z0-9_]*$'
WITH type(r) as relType, count(r) as count
RETURN relType, count
ORDER BY count DESC;

// 2.2 Find relationships with non-Memory endpoints
MATCH (a)-[r]->(b)
WHERE (NOT a:Memory OR NOT b:Memory)
RETURN type(r) as relationType,
       labels(a) as sourceLabels,
       labels(b) as targetLabels,
       count(r) as count
ORDER BY count DESC
LIMIT 20;

// 2.3 Find self-referential relationships (may be valid, but worth reviewing)
MATCH (n)-[r]->(n)
RETURN n.name as entity, type(r) as relationType, count(r) as count
ORDER BY count DESC;

// 2.4 Relationship type distribution
MATCH ()-[r]->()
RETURN type(r) as relationType, count(r) as count
ORDER BY count DESC;


// -----------------------------------------------------------------------------
// SECTION 3: Event Clock Validation
// -----------------------------------------------------------------------------

// 3.1 Find Decision nodes without Context (orphan decisions)
MATCH (d:Decision)
WHERE NOT (d)<-[:GOVERNED]-(:Context)
RETURN d.name as decision, d.reasoning as reasoning
LIMIT 20;

// 3.2 Find Decision nodes missing 'reasoning' property
MATCH (d:Decision)
WHERE d.reasoning IS NULL
  AND NOT any(obs IN coalesce(d.observations, []) WHERE obs STARTS WITH 'reasoning:')
RETURN d.name as decision, d.observations as observations
LIMIT 20;

// 3.3 Find Context nodes missing temporal properties
MATCH (c:Context)
WHERE NOT any(obs IN coalesce(c.observations, []) WHERE obs STARTS WITH 'validAt:')
RETURN c.name as context, c.observations as observations
LIMIT 20;

// 3.4 Find incomplete Event Clock chains
// A complete chain should be: Context -> Decision -> Action -> Event -> State
MATCH (d:Decision)
WHERE NOT (d)-[:DETERMINES]->(:Action)
  AND NOT (d)-[:DETERMINES]->(:State)
RETURN d.name as orphanDecision, d.reasoning as reasoning
LIMIT 20;

// 3.5 Find State nodes without causal connections
MATCH (s:State)
WHERE NOT (s)<-[:CHANGED]-()
  AND NOT (s)<-[:RESULTED_IN]-()
RETURN s.name as orphanState, s.value as value
LIMIT 20;


// -----------------------------------------------------------------------------
// SECTION 4: Fact Validation (Temporal Knowledge)
// -----------------------------------------------------------------------------

// 4.1 Find Fact nodes missing 'text' property
MATCH (f:Fact)
WHERE f.text IS NULL
  AND NOT any(obs IN coalesce(f.observations, []) WHERE obs STARTS WITH 'text:')
RETURN f.name as fact, f.observations as observations
LIMIT 20;

// 4.2 Find Fact nodes without validity timestamps
MATCH (f:Fact)
WHERE NOT any(obs IN coalesce(f.observations, []) WHERE obs STARTS WITH 'validAt:')
RETURN f.name as fact, f.observations as observations
LIMIT 20;

// 4.3 Find Fact nodes with invalid status values
MATCH (f:Fact)
UNWIND coalesce(f.observations, []) as obs
WITH f, obs
WHERE obs STARTS WITH 'status:'
WITH f, substring(obs, 8) as status
WHERE NOT status IN ['canonical', 'superseded', 'corroborated', 'synthesized']
RETURN f.name as fact, status as invalidStatus;

// 4.4 Find superseded Facts that are still marked canonical
MATCH (newer:Fact)-[:SUPERSEDES]->(older:Fact)
WHERE any(obs IN coalesce(older.observations, []) WHERE obs CONTAINS 'status: canonical')
RETURN older.name as supersededFact, newer.name as newerFact
LIMIT 20;

// 4.5 Count Facts by status
MATCH (f:Fact)
UNWIND coalesce(f.observations, []) as obs
WITH obs
WHERE obs STARTS WITH 'status:'
WITH substring(obs, 8) as status
RETURN trim(status) as factStatus, count(*) as count
ORDER BY count DESC;


// -----------------------------------------------------------------------------
// SECTION 5: Type-Specific Validations
// -----------------------------------------------------------------------------

// 5.1 Person nodes validation
MATCH (p:Person)
WHERE NOT p:Memory
RETURN p.name as personWithoutMemoryLabel
LIMIT 20;

// 5.2 Organization nodes validation
MATCH (o:Organization)
OPTIONAL MATCH (o)<-[:WORKS_AT]-(person:Person)
WITH o, count(person) as employeeCount
WHERE employeeCount = 0
RETURN o.name as orgWithNoEmployees
LIMIT 20;

// 5.3 Project nodes without assignments
MATCH (p:Project)
WHERE NOT (p)<-[:ASSIGNED_TO|WORKS_ON]-(:Person)
RETURN p.name as unassignedProject, p.status as status
LIMIT 20;

// 5.4 Meeting nodes validation
MATCH (m:Meeting)
WHERE NOT (m)<-[:ATTENDED]-(:Person)
RETURN m.name as meetingWithNoAttendees
LIMIT 20;


// -----------------------------------------------------------------------------
// SECTION 6: Data Quality Metrics
// -----------------------------------------------------------------------------

// 6.1 Overall schema compliance score
MATCH (n:Memory)
WITH n,
     CASE WHEN n.name IS NOT NULL AND n.name <> '' THEN 1 ELSE 0 END as hasName,
     CASE WHEN n.type IS NOT NULL AND n.type <> '' THEN 1 ELSE 0 END as hasType,
     CASE WHEN n.observations IS NOT NULL AND size(n.observations) > 0 THEN 1 ELSE 0 END as hasObservations
WITH count(n) as total,
     sum(hasName) as withName,
     sum(hasType) as withType,
     sum(hasObservations) as withObservations
RETURN total,
       withName,
       withType,
       withObservations,
       round(100.0 * withName / total, 2) as nameCompliancePct,
       round(100.0 * withType / total, 2) as typeCompliancePct,
       round(100.0 * withObservations / total, 2) as observationsCompliancePct;

// 6.2 Entity type distribution
MATCH (n:Memory)
RETURN n.type as entityType, count(n) as count
ORDER BY count DESC;

// 6.3 Average observations per entity type
MATCH (n:Memory)
WHERE n.observations IS NOT NULL
RETURN n.type as entityType,
       count(n) as entityCount,
       round(avg(size(n.observations)), 2) as avgObservations,
       min(size(n.observations)) as minObservations,
       max(size(n.observations)) as maxObservations
ORDER BY entityCount DESC;

// 6.4 Relationship connectivity analysis
MATCH (n:Memory)
OPTIONAL MATCH (n)-[r]-()
WITH n, count(r) as relationshipCount
RETURN n.type as entityType,
       count(n) as entityCount,
       round(avg(relationshipCount), 2) as avgRelationships,
       sum(CASE WHEN relationshipCount = 0 THEN 1 ELSE 0 END) as orphanNodes
ORDER BY entityCount DESC;

// 6.5 Event Clock coverage
MATCH (d:Decision)
OPTIONAL MATCH (c:Context)-[:GOVERNED]->(d)
OPTIONAL MATCH (d)-[:DETERMINES]->(a:Action)
OPTIONAL MATCH (a)-[:CAUSED|CHANGED]->(s:State)
WITH count(d) as totalDecisions,
     sum(CASE WHEN c IS NOT NULL THEN 1 ELSE 0 END) as withContext,
     sum(CASE WHEN a IS NOT NULL THEN 1 ELSE 0 END) as withAction,
     sum(CASE WHEN s IS NOT NULL THEN 1 ELSE 0 END) as withState
RETURN totalDecisions,
       withContext,
       withAction,
       withState,
       round(100.0 * withContext / CASE WHEN totalDecisions = 0 THEN 1 ELSE totalDecisions END, 2) as contextCoveragePct,
       round(100.0 * withAction / CASE WHEN totalDecisions = 0 THEN 1 ELSE totalDecisions END, 2) as actionCoveragePct;


// -----------------------------------------------------------------------------
// SECTION 7: Orphan Detection
// -----------------------------------------------------------------------------

// 7.1 Find completely isolated nodes (no relationships at all)
MATCH (n:Memory)
WHERE NOT (n)--()
RETURN n.name as isolatedEntity, n.type as type, labels(n) as labels
ORDER BY n.type
LIMIT 50;

// 7.2 Find entities only connected to one other entity
MATCH (n:Memory)
WHERE size([(n)--() | 1]) = 1
RETURN n.name as sparselyConnected, n.type as type
LIMIT 50;

// 7.3 Find relationship endpoints referencing non-existent entities
// (This shouldn't happen with proper constraints, but good to check)
MATCH (a:Memory)-[r]->(b)
WHERE NOT b:Memory
RETURN a.name as source, type(r) as relationship, labels(b) as targetLabels
LIMIT 20;


// -----------------------------------------------------------------------------
// SECTION 8: Summary Report Query
// -----------------------------------------------------------------------------

// 8.1 Generate a comprehensive validation summary
CALL {
  MATCH (n:Memory) RETURN count(n) as totalEntities
}
CALL {
  MATCH ()-[r]->() RETURN count(r) as totalRelationships
}
CALL {
  MATCH (n:Memory) WHERE n.name IS NULL OR n.name = '' RETURN count(n) as missingName
}
CALL {
  MATCH (n:Memory) WHERE n.type IS NULL OR n.type = '' RETURN count(n) as missingType
}
CALL {
  MATCH (n:Memory) WHERE NOT (n)--() RETURN count(n) as orphanNodes
}
CALL {
  MATCH (d:Decision) WHERE NOT (d)<-[:GOVERNED]-(:Context) RETURN count(d) as decisionsWithoutContext
}
CALL {
  MATCH (n:Memory) RETURN count(DISTINCT n.type) as uniqueTypes
}
RETURN
  totalEntities,
  totalRelationships,
  uniqueTypes,
  missingName as entitiesMissingName,
  missingType as entitiesMissingType,
  orphanNodes,
  decisionsWithoutContext,
  CASE
    WHEN missingName = 0 AND missingType = 0 AND orphanNodes < totalEntities * 0.1
    THEN 'HEALTHY'
    WHEN missingName < 10 AND missingType < 10
    THEN 'MINOR_ISSUES'
    ELSE 'NEEDS_ATTENTION'
  END as overallStatus;


// =============================================================================
// END OF VALIDATION QUERIES
// =============================================================================
