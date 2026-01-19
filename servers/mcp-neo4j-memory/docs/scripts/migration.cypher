// =============================================================================
// World Model Schema Migration Script for mcp-neo4j-memory
// =============================================================================
// Purpose: Transform existing Entity/Legacy/Memory nodes to specific type labels
//          AND extract structured data from observations into properties
// Version: 2.0.0
// Date: 2026-01-19
//
// IMPORTANT: Create a database backup before running this migration!
//
// Run each section separately and verify results before proceeding.
// =============================================================================

// -----------------------------------------------------------------------------
// SECTION 1: Pre-Migration Audit
// -----------------------------------------------------------------------------
// Run these queries first to understand your current data state.

// 1.1 Count all node labels in the database
CALL db.labels() YIELD label
MATCH (n) WHERE label IN labels(n)
RETURN label, count(n) as count
ORDER BY count DESC;

// 1.2 Count all relationship types
CALL db.relationshipTypes() YIELD relationshipType
MATCH ()-[r]->()
WHERE type(r) = relationshipType
RETURN relationshipType, count(r) as count
ORDER BY count DESC;

// 1.3 Audit Entity nodes with their types
MATCH (e:Entity)
RETURN e.type as entityType, count(e) as count
ORDER BY count DESC;

// 1.4 Audit Memory nodes with their types
MATCH (m:Memory)
RETURN m.type as memoryType, count(m) as count
ORDER BY count DESC;

// 1.5 Find nodes without type property
MATCH (n)
WHERE n.type IS NULL AND (n:Entity OR n:Memory OR n:Legacy)
RETURN labels(n) as labels, count(n) as count;


// -----------------------------------------------------------------------------
// SECTION 2: Add Specific Labels to Memory Nodes
// -----------------------------------------------------------------------------
// This adds the specific type label (e.g., Person, Project) to nodes
// based on their 'type' property, while preserving the Memory label.

// 2.1 Add specific labels to Memory nodes with valid types
MATCH (m:Memory)
WHERE m.type IS NOT NULL
  AND m.type <> ''
  AND m.type =~ '^[A-Za-z][A-Za-z0-9_]*$'
WITH m, m.type as typeName
CALL apoc.create.addLabels(m, [typeName]) YIELD node
RETURN typeName, count(node) as nodesLabeled
ORDER BY nodesLabeled DESC;


// -----------------------------------------------------------------------------
// SECTION 3: Migrate Legacy Nodes
// -----------------------------------------------------------------------------
// If you have Legacy nodes from previous schema versions, migrate them.

// 3.1 Check for Legacy nodes
MATCH (l:Legacy)
RETURN l.type as type, count(l) as count
ORDER BY count DESC;

// 3.2 Add Memory label and specific type labels to Legacy nodes
MATCH (l:Legacy)
WHERE l.type IS NOT NULL
  AND l.type <> ''
  AND l.type =~ '^[A-Za-z][A-Za-z0-9_]*$'
WITH l, l.type as typeName
CALL apoc.create.addLabels(l, ['Memory', typeName]) YIELD node
RETURN typeName, count(node) as nodesLabeled
ORDER BY nodesLabeled DESC;

// 3.3 Remove Legacy label after migration (optional - keeps data lineage if kept)
// MATCH (l:Legacy)
// REMOVE l:Legacy
// RETURN count(l) as legacyLabelsRemoved;


// -----------------------------------------------------------------------------
// SECTION 4: Migrate Entity Nodes (if separate from Memory)
// -----------------------------------------------------------------------------
// Some systems may have Entity nodes separate from Memory nodes.

// 4.1 Check for Entity nodes that don't have Memory label
MATCH (e:Entity)
WHERE NOT e:Memory
RETURN e.type as type, count(e) as count
ORDER BY count DESC;

// 4.2 Add Memory label to Entity nodes that don't have it
MATCH (e:Entity)
WHERE NOT e:Memory AND e.name IS NOT NULL
SET e:Memory
RETURN count(e) as entitiesAddedMemoryLabel;

// 4.3 Add specific type labels to Entity nodes
MATCH (e:Entity)
WHERE e.type IS NOT NULL
  AND e.type <> ''
  AND e.type =~ '^[A-Za-z][A-Za-z0-9_]*$'
WITH e, e.type as typeName
CALL apoc.create.addLabels(e, [typeName]) YIELD node
RETURN typeName, count(node) as nodesLabeled
ORDER BY nodesLabeled DESC;


// -----------------------------------------------------------------------------
// SECTION 5: Standardize Type Property Values
// -----------------------------------------------------------------------------
// Normalize type values to PascalCase for consistency.

// 5.1 Find type values that need normalization
MATCH (n:Memory)
WHERE n.type IS NOT NULL
  AND NOT n.type =~ '^[A-Z][a-z]*([A-Z][a-z]*)*$'
RETURN n.type as originalType, count(n) as count
ORDER BY count DESC
LIMIT 50;

// 5.2 Common normalization transformations
// Lowercase 'person' to 'Person'
MATCH (n:Memory)
WHERE n.type = 'person'
SET n.type = 'Person'
WITH n
CALL apoc.create.addLabels(n, ['Person']) YIELD node
RETURN count(node) as normalized;

// Lowercase 'organization' to 'Organization'
MATCH (n:Memory)
WHERE n.type = 'organization' OR n.type = 'company'
SET n.type = 'Organization'
WITH n
CALL apoc.create.addLabels(n, ['Organization']) YIELD node
RETURN count(node) as normalized;

// Lowercase 'project' to 'Project'
MATCH (n:Memory)
WHERE n.type = 'project'
SET n.type = 'Project'
WITH n
CALL apoc.create.addLabels(n, ['Project']) YIELD node
RETURN count(node) as normalized;

// Lowercase 'meeting' to 'Meeting'
MATCH (n:Memory)
WHERE n.type = 'meeting'
SET n.type = 'Meeting'
WITH n
CALL apoc.create.addLabels(n, ['Meeting']) YIELD node
RETURN count(node) as normalized;

// Lowercase 'task' to 'Task'
MATCH (n:Memory)
WHERE n.type = 'task'
SET n.type = 'Task'
WITH n
CALL apoc.create.addLabels(n, ['Task']) YIELD node
RETURN count(node) as normalized;

// Lowercase 'event' to 'Event'
MATCH (n:Memory)
WHERE n.type = 'event'
SET n.type = 'Event'
WITH n
CALL apoc.create.addLabels(n, ['Event']) YIELD node
RETURN count(node) as normalized;


// -----------------------------------------------------------------------------
// SECTION 6: Create Event Clock Indexes
// -----------------------------------------------------------------------------
// Add indexes to support Event Clock queries.

// 6.1 Index for Decision timestamp queries
CREATE INDEX decision_timestamp IF NOT EXISTS FOR (d:Decision) ON (d.timestamp);

// 6.2 Index for Fact validity queries
CREATE INDEX fact_validAt IF NOT EXISTS FOR (f:Fact) ON (f.validAt);
CREATE INDEX fact_invalidAt IF NOT EXISTS FOR (f:Fact) ON (f.invalidAt);

// 6.3 Index for Context policy version queries
CREATE INDEX context_policy IF NOT EXISTS FOR (c:Context) ON (c.policyVersion);

// 6.4 Index for State queries
CREATE INDEX state_timestamp IF NOT EXISTS FOR (s:State) ON (s.timestamp);
CREATE INDEX state_entityId IF NOT EXISTS FOR (s:State) ON (s.entityId);

// 6.5 Index for EventTrace queries
CREATE INDEX eventtrace_timestamp IF NOT EXISTS FOR (et:EventTrace) ON (et.timestamp);
CREATE INDEX eventtrace_traceId IF NOT EXISTS FOR (et:EventTrace) ON (et.traceId);


// -----------------------------------------------------------------------------
// SECTION 7: Create Property Indexes for Common Queries
// -----------------------------------------------------------------------------
// Add indexes for commonly queried properties.

// 7.1 Person indexes
CREATE INDEX person_email IF NOT EXISTS FOR (p:Person) ON (p.email);
CREATE INDEX person_role IF NOT EXISTS FOR (p:Person) ON (p.role);

// 7.2 Organization indexes
CREATE INDEX org_type IF NOT EXISTS FOR (o:Organization) ON (o.type);

// 7.3 Project indexes
CREATE INDEX project_status IF NOT EXISTS FOR (p:Project) ON (p.status);
CREATE INDEX project_priority IF NOT EXISTS FOR (p:Project) ON (p.priority);

// 7.4 Task indexes
CREATE INDEX task_status IF NOT EXISTS FOR (t:Task) ON (t.status);
CREATE INDEX task_priority IF NOT EXISTS FOR (t:Task) ON (t.priority);

// 7.5 Meeting indexes
CREATE INDEX meeting_datetime IF NOT EXISTS FOR (m:Meeting) ON (m.datetime);


// -----------------------------------------------------------------------------
// SECTION 8: Post-Migration Verification
// -----------------------------------------------------------------------------
// Run these queries to verify the migration was successful.

// 8.1 Verify all Memory nodes have specific type labels
MATCH (m:Memory)
WHERE size(labels(m)) = 1
RETURN m.name as name, m.type as type, labels(m) as labels
LIMIT 20;

// 8.2 Count nodes by their new labels
CALL db.labels() YIELD label
WHERE label <> 'Memory' AND label <> 'Entity' AND label <> 'Legacy'
MATCH (n) WHERE label IN labels(n)
RETURN label, count(n) as count
ORDER BY count DESC;

// 8.3 Verify index creation
SHOW INDEXES;

// 8.4 Check for orphan nodes (nodes without relationships)
MATCH (n:Memory)
WHERE NOT (n)--()
RETURN n.name as name, n.type as type, labels(n) as labels
LIMIT 20;

// 8.5 Summary statistics
MATCH (n:Memory)
RETURN
  count(n) as totalMemoryNodes,
  count(DISTINCT n.type) as uniqueTypes,
  avg(size(coalesce(n.observations, []))) as avgObservations;


// =============================================================================
// SECTION 9: Extract Structured Data from Observations to Properties
// =============================================================================
// This section migrates key-value pairs embedded in observations to proper
// node properties for better queryability.
//
// Pattern: observations containing "key: value" strings become properties

// -----------------------------------------------------------------------------
// 9.1 Audit: Find observations with embedded key-value pairs
// -----------------------------------------------------------------------------
MATCH (n)
WHERE n.observations IS NOT NULL
UNWIND n.observations AS obs
WITH n, obs
WHERE obs CONTAINS ':'
RETURN
  labels(n)[0] as label,
  split(obs, ':')[0] as key,
  count(*) as occurrences
ORDER BY occurrences DESC
LIMIT 50;

// -----------------------------------------------------------------------------
// 9.2 Extract common temporal properties
// -----------------------------------------------------------------------------

// Extract validAt from observations
MATCH (n)
WHERE any(obs IN coalesce(n.observations, []) WHERE obs STARTS WITH 'validAt:')
WITH n, [obs IN n.observations WHERE obs STARTS WITH 'validAt:'][0] AS validAtObs
SET n.validAt = datetime(trim(substring(validAtObs, 8)))
SET n.observations = [obs IN n.observations WHERE NOT obs STARTS WITH 'validAt:']
RETURN count(n) as nodesWithValidAt;

// Extract invalidAt from observations
MATCH (n)
WHERE any(obs IN coalesce(n.observations, []) WHERE obs STARTS WITH 'invalidAt:')
WITH n, [obs IN n.observations WHERE obs STARTS WITH 'invalidAt:'][0] AS invalidAtObs
SET n.invalidAt = datetime(trim(substring(invalidAtObs, 10)))
SET n.observations = [obs IN n.observations WHERE NOT obs STARTS WITH 'invalidAt:']
RETURN count(n) as nodesWithInvalidAt;

// Extract source from observations
MATCH (n)
WHERE any(obs IN coalesce(n.observations, []) WHERE obs STARTS WITH 'source:')
WITH n, [obs IN n.observations WHERE obs STARTS WITH 'source:'][0] AS sourceObs
SET n.source = trim(substring(sourceObs, 7))
SET n.observations = [obs IN n.observations WHERE NOT obs STARTS WITH 'source:']
RETURN count(n) as nodesWithSource;

// Extract confidence from observations
MATCH (n)
WHERE any(obs IN coalesce(n.observations, []) WHERE obs STARTS WITH 'confidence:')
WITH n, [obs IN n.observations WHERE obs STARTS WITH 'confidence:'][0] AS confObs
SET n.confidence = toFloat(trim(substring(confObs, 11)))
SET n.observations = [obs IN n.observations WHERE NOT obs STARTS WITH 'confidence:']
RETURN count(n) as nodesWithConfidence;

// Extract status from observations (for Facts)
MATCH (n:Fact)
WHERE any(obs IN coalesce(n.observations, []) WHERE obs STARTS WITH 'status:')
WITH n, [obs IN n.observations WHERE obs STARTS WITH 'status:'][0] AS statusObs
SET n.status = trim(substring(statusObs, 7))
SET n.observations = [obs IN n.observations WHERE NOT obs STARTS WITH 'status:']
RETURN count(n) as factsWithStatus;

// -----------------------------------------------------------------------------
// 9.3 Extract Person-specific properties
// -----------------------------------------------------------------------------

// Extract email
MATCH (p:Person)
WHERE any(obs IN coalesce(p.observations, []) WHERE obs STARTS WITH 'email:')
WITH p, [obs IN p.observations WHERE obs STARTS WITH 'email:'][0] AS emailObs
SET p.email = trim(substring(emailObs, 6))
SET p.observations = [obs IN p.observations WHERE NOT obs STARTS WITH 'email:']
RETURN count(p) as personsWithEmail;

// Extract role
MATCH (p:Person)
WHERE any(obs IN coalesce(p.observations, []) WHERE obs STARTS WITH 'role:')
WITH p, [obs IN p.observations WHERE obs STARTS WITH 'role:'][0] AS roleObs
SET p.role = trim(substring(roleObs, 5))
SET p.observations = [obs IN p.observations WHERE NOT obs STARTS WITH 'role:']
RETURN count(p) as personsWithRole;

// Extract department
MATCH (p:Person)
WHERE any(obs IN coalesce(p.observations, []) WHERE obs STARTS WITH 'department:')
WITH p, [obs IN p.observations WHERE obs STARTS WITH 'department:'][0] AS deptObs
SET p.department = trim(substring(deptObs, 11))
SET p.observations = [obs IN p.observations WHERE NOT obs STARTS WITH 'department:']
RETURN count(p) as personsWithDepartment;

// -----------------------------------------------------------------------------
// 9.4 Extract Decision-specific properties
// -----------------------------------------------------------------------------

// Extract reasoning
MATCH (d:Decision)
WHERE any(obs IN coalesce(d.observations, []) WHERE obs STARTS WITH 'reasoning:')
WITH d, [obs IN d.observations WHERE obs STARTS WITH 'reasoning:'][0] AS reasonObs
SET d.reasoning = trim(substring(reasonObs, 10))
SET d.observations = [obs IN d.observations WHERE NOT obs STARTS WITH 'reasoning:']
RETURN count(d) as decisionsWithReasoning;

// Extract decidedBy
MATCH (d:Decision)
WHERE any(obs IN coalesce(d.observations, []) WHERE obs STARTS WITH 'decidedBy:')
WITH d, [obs IN d.observations WHERE obs STARTS WITH 'decidedBy:'][0] AS decidedByObs
SET d.decidedBy = trim(substring(decidedByObs, 10))
SET d.observations = [obs IN d.observations WHERE NOT obs STARTS WITH 'decidedBy:']
RETURN count(d) as decisionsWithDecidedBy;

// Extract alternatives (as string - can be parsed to array later)
MATCH (d:Decision)
WHERE any(obs IN coalesce(d.observations, []) WHERE obs STARTS WITH 'alternatives:')
WITH d, [obs IN d.observations WHERE obs STARTS WITH 'alternatives:'][0] AS altObs
SET d.alternativesRaw = trim(substring(altObs, 13))
SET d.observations = [obs IN d.observations WHERE NOT obs STARTS WITH 'alternatives:']
RETURN count(d) as decisionsWithAlternatives;

// -----------------------------------------------------------------------------
// 9.5 Extract Fact-specific properties
// -----------------------------------------------------------------------------

// Extract text
MATCH (f:Fact)
WHERE any(obs IN coalesce(f.observations, []) WHERE obs STARTS WITH 'text:')
WITH f, [obs IN f.observations WHERE obs STARTS WITH 'text:'][0] AS textObs
SET f.text = trim(substring(textObs, 5))
SET f.observations = [obs IN f.observations WHERE NOT obs STARTS WITH 'text:']
RETURN count(f) as factsWithText;

// -----------------------------------------------------------------------------
// 9.6 Extract Context-specific properties
// -----------------------------------------------------------------------------

// Extract policyVersion
MATCH (c:Context)
WHERE any(obs IN coalesce(c.observations, []) WHERE obs STARTS WITH 'policyVersion:')
WITH c, [obs IN c.observations WHERE obs STARTS WITH 'policyVersion:'][0] AS pvObs
SET c.policyVersion = trim(substring(pvObs, 14))
SET c.observations = [obs IN c.observations WHERE NOT obs STARTS WITH 'policyVersion:']
RETURN count(c) as contextsWithPolicyVersion;

// Extract marketCondition
MATCH (c:Context)
WHERE any(obs IN coalesce(c.observations, []) WHERE obs STARTS WITH 'marketCondition:')
WITH c, [obs IN c.observations WHERE obs STARTS WITH 'marketCondition:'][0] AS mcObs
SET c.marketCondition = trim(substring(mcObs, 16))
SET c.observations = [obs IN c.observations WHERE NOT obs STARTS WITH 'marketCondition:']
RETURN count(c) as contextsWithMarketCondition;

// -----------------------------------------------------------------------------
// 9.7 Extract Meeting-specific properties
// -----------------------------------------------------------------------------

// Extract datetime
MATCH (m:Meeting)
WHERE any(obs IN coalesce(m.observations, []) WHERE obs STARTS WITH 'datetime:')
WITH m, [obs IN m.observations WHERE obs STARTS WITH 'datetime:'][0] AS dtObs
SET m.datetime = datetime(trim(substring(dtObs, 9)))
SET m.observations = [obs IN m.observations WHERE NOT obs STARTS WITH 'datetime:']
RETURN count(m) as meetingsWithDatetime;

// Extract platform
MATCH (m:Meeting)
WHERE any(obs IN coalesce(m.observations, []) WHERE obs STARTS WITH 'platform:')
WITH m, [obs IN m.observations WHERE obs STARTS WITH 'platform:'][0] AS platObs
SET m.platform = trim(substring(platObs, 9))
SET m.observations = [obs IN m.observations WHERE NOT obs STARTS WITH 'platform:']
RETURN count(m) as meetingsWithPlatform;

// -----------------------------------------------------------------------------
// 9.8 Extract Project/Task-specific properties
// -----------------------------------------------------------------------------

// Extract status from Projects
MATCH (p:Project)
WHERE any(obs IN coalesce(p.observations, []) WHERE obs STARTS WITH 'status:')
WITH p, [obs IN p.observations WHERE obs STARTS WITH 'status:'][0] AS statusObs
SET p.status = trim(substring(statusObs, 7))
SET p.observations = [obs IN p.observations WHERE NOT obs STARTS WITH 'status:']
RETURN count(p) as projectsWithStatus;

// Extract priority from Projects
MATCH (p:Project)
WHERE any(obs IN coalesce(p.observations, []) WHERE obs STARTS WITH 'priority:')
WITH p, [obs IN p.observations WHERE obs STARTS WITH 'priority:'][0] AS prioObs
SET p.priority = trim(substring(prioObs, 9))
SET p.observations = [obs IN p.observations WHERE NOT obs STARTS WITH 'priority:']
RETURN count(p) as projectsWithPriority;

// Extract status from Tasks
MATCH (t:Task)
WHERE any(obs IN coalesce(t.observations, []) WHERE obs STARTS WITH 'status:')
WITH t, [obs IN t.observations WHERE obs STARTS WITH 'status:'][0] AS statusObs
SET t.status = trim(substring(statusObs, 7))
SET t.observations = [obs IN t.observations WHERE NOT obs STARTS WITH 'status:']
RETURN count(t) as tasksWithStatus;

// Extract priority from Tasks
MATCH (t:Task)
WHERE any(obs IN coalesce(t.observations, []) WHERE obs STARTS WITH 'priority:')
WITH t, [obs IN t.observations WHERE obs STARTS WITH 'priority:'][0] AS prioObs
SET t.priority = trim(substring(prioObs, 9))
SET t.observations = [obs IN t.observations WHERE NOT obs STARTS WITH 'priority:']
RETURN count(t) as tasksWithPriority;

// -----------------------------------------------------------------------------
// 9.9 Post-extraction verification
// -----------------------------------------------------------------------------

// Count nodes with remaining key-value observations (may need manual review)
MATCH (n)
WHERE n.observations IS NOT NULL
UNWIND n.observations AS obs
WITH n, obs
WHERE obs CONTAINS ':' AND NOT obs CONTAINS 'http'
RETURN DISTINCT
  labels(n)[0] as label,
  split(obs, ':')[0] as remainingKey,
  count(*) as count
ORDER BY count DESC
LIMIT 30;

// Summary: nodes with clean observations vs still having embedded properties
MATCH (n)
WHERE n.observations IS NOT NULL
WITH n,
  size([obs IN n.observations WHERE obs CONTAINS ':' AND NOT obs CONTAINS 'http']) as embeddedProps
RETURN
  CASE WHEN embeddedProps = 0 THEN 'clean' ELSE 'needs_review' END as status,
  count(n) as nodeCount
ORDER BY status;


// =============================================================================
// SECTION 10: Add validAt to Existing Relationships
// =============================================================================
// For existing relationships without temporal properties, add default validAt

// 10.1 Add validAt to relationships that don't have it (use createdAt as default)
MATCH ()-[r]->()
WHERE r.validAt IS NULL AND r.createdAt IS NOT NULL
SET r.validAt = r.createdAt
RETURN type(r) as relType, count(r) as updated;

// 10.2 For relationships without any timestamps, set validAt to now
MATCH ()-[r]->()
WHERE r.validAt IS NULL AND r.createdAt IS NULL
SET r.validAt = datetime()
SET r.createdAt = datetime()
RETURN type(r) as relType, count(r) as updated;

// 10.3 Verify all relationships have temporal properties
MATCH ()-[r]->()
RETURN
  type(r) as relType,
  count(r) as total,
  count(r.validAt) as hasValidAt,
  count(r.invalidAt) as hasInvalidAt
ORDER BY total DESC;


// =============================================================================
// END OF MIGRATION SCRIPT
// =============================================================================
