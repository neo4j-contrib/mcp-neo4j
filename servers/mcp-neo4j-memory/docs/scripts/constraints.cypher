// =============================================================================
// World Model Schema Constraints for mcp-neo4j-memory
// =============================================================================
// Purpose: Define database constraints to enforce schema integrity
// Version: 1.0.0
// Date: 2026-01-18
//
// IMPORTANT: These constraints are OPTIONAL. The mcp-neo4j-memory server is
// designed to be flexible. Only apply constraints if you want strict
// schema enforcement.
//
// Note: Some constraints require Neo4j Enterprise Edition.
// Community Edition constraints are marked with [CE].
// Enterprise Edition constraints are marked with [EE].
// =============================================================================

// -----------------------------------------------------------------------------
// SECTION 1: Uniqueness Constraints [CE Compatible]
// -----------------------------------------------------------------------------
// These ensure unique identifiers for key entities.

// 1.1 Memory node name uniqueness (core constraint)
CREATE CONSTRAINT memory_name_unique IF NOT EXISTS
FOR (m:Memory)
REQUIRE m.name IS UNIQUE;

// 1.2 Person uniqueness by name
CREATE CONSTRAINT person_name_unique IF NOT EXISTS
FOR (p:Person)
REQUIRE p.name IS UNIQUE;

// 1.3 Organization uniqueness by name
CREATE CONSTRAINT organization_name_unique IF NOT EXISTS
FOR (o:Organization)
REQUIRE o.name IS UNIQUE;

// 1.4 Project uniqueness by name
CREATE CONSTRAINT project_name_unique IF NOT EXISTS
FOR (p:Project)
REQUIRE p.name IS UNIQUE;

// 1.5 Decision uniqueness by name
CREATE CONSTRAINT decision_name_unique IF NOT EXISTS
FOR (d:Decision)
REQUIRE d.name IS UNIQUE;

// 1.6 Fact uniqueness by name
CREATE CONSTRAINT fact_name_unique IF NOT EXISTS
FOR (f:Fact)
REQUIRE f.name IS UNIQUE;

// 1.7 Context uniqueness by name
CREATE CONSTRAINT context_name_unique IF NOT EXISTS
FOR (c:Context)
REQUIRE c.name IS UNIQUE;


// -----------------------------------------------------------------------------
// SECTION 2: Property Existence Constraints [EE Only]
// -----------------------------------------------------------------------------
// These ensure required properties are always present.
// NOTE: These require Neo4j Enterprise Edition.

// 2.1 Memory nodes must have a name
CREATE CONSTRAINT memory_name_exists IF NOT EXISTS
FOR (m:Memory)
REQUIRE m.name IS NOT NULL;

// 2.2 Memory nodes must have a type
CREATE CONSTRAINT memory_type_exists IF NOT EXISTS
FOR (m:Memory)
REQUIRE m.type IS NOT NULL;

// 2.3 Decision nodes must have reasoning
// CREATE CONSTRAINT decision_reasoning_exists IF NOT EXISTS
// FOR (d:Decision)
// REQUIRE d.reasoning IS NOT NULL;

// 2.4 Fact nodes must have text
// CREATE CONSTRAINT fact_text_exists IF NOT EXISTS
// FOR (f:Fact)
// REQUIRE f.text IS NOT NULL;


// -----------------------------------------------------------------------------
// SECTION 3: Node Key Constraints [EE Only]
// -----------------------------------------------------------------------------
// These create composite keys for entities.
// NOTE: These require Neo4j Enterprise Edition.

// 3.1 Memory node key (name + type combination)
// CREATE CONSTRAINT memory_node_key IF NOT EXISTS
// FOR (m:Memory)
// REQUIRE (m.name, m.type) IS NODE KEY;


// -----------------------------------------------------------------------------
// SECTION 4: Relationship Property Constraints [EE Only]
// -----------------------------------------------------------------------------
// These ensure relationship properties when needed.
// NOTE: These require Neo4j Enterprise Edition.

// 4.1 Example: Ensure ATTENDED relationships have a timestamp
// CREATE CONSTRAINT attended_timestamp IF NOT EXISTS
// FOR ()-[a:ATTENDED]->()
// REQUIRE a.timestamp IS NOT NULL;


// -----------------------------------------------------------------------------
// SECTION 5: Type Property Constraints [EE Only]
// -----------------------------------------------------------------------------
// These restrict property values to specific types.
// NOTE: These require Neo4j Enterprise Edition.

// 5.1 Memory name must be a string
// CREATE CONSTRAINT memory_name_type IF NOT EXISTS
// FOR (m:Memory)
// REQUIRE m.name IS :: STRING;

// 5.2 Memory type must be a string
// CREATE CONSTRAINT memory_type_type IF NOT EXISTS
// FOR (m:Memory)
// REQUIRE m.type IS :: STRING;

// 5.3 Memory observations must be a list of strings
// CREATE CONSTRAINT memory_observations_type IF NOT EXISTS
// FOR (m:Memory)
// REQUIRE m.observations IS :: LIST<STRING>;


// -----------------------------------------------------------------------------
// SECTION 6: Remove Constraints (for rollback)
// -----------------------------------------------------------------------------
// Use these to remove constraints if needed.

// DROP CONSTRAINT memory_name_unique IF EXISTS;
// DROP CONSTRAINT person_name_unique IF EXISTS;
// DROP CONSTRAINT organization_name_unique IF EXISTS;
// DROP CONSTRAINT project_name_unique IF EXISTS;
// DROP CONSTRAINT decision_name_unique IF EXISTS;
// DROP CONSTRAINT fact_name_unique IF EXISTS;
// DROP CONSTRAINT context_name_unique IF EXISTS;
// DROP CONSTRAINT memory_name_exists IF EXISTS;
// DROP CONSTRAINT memory_type_exists IF EXISTS;


// -----------------------------------------------------------------------------
// SECTION 7: Show All Constraints
// -----------------------------------------------------------------------------
// Use this to verify current constraints.

SHOW CONSTRAINTS;


// =============================================================================
// RECOMMENDED MINIMAL CONSTRAINT SET (Community Edition)
// =============================================================================
// If you want basic enforcement without Enterprise features, use only these:
//
// CREATE CONSTRAINT memory_name_unique IF NOT EXISTS
// FOR (m:Memory)
// REQUIRE m.name IS UNIQUE;
//
// This single constraint ensures entity names are unique, which is the most
// critical integrity rule for the mcp-neo4j-memory server.
// =============================================================================


// =============================================================================
// INDEXES FOR PERFORMANCE
// =============================================================================
// These are not constraints but improve query performance.

// Core Memory indexes
CREATE INDEX memory_name IF NOT EXISTS FOR (m:Memory) ON (m.name);
CREATE INDEX memory_type IF NOT EXISTS FOR (m:Memory) ON (m.type);

// Entity type indexes
CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX person_email IF NOT EXISTS FOR (p:Person) ON (p.email);
CREATE INDEX organization_name IF NOT EXISTS FOR (o:Organization) ON (o.name);
CREATE INDEX project_name IF NOT EXISTS FOR (p:Project) ON (p.name);
CREATE INDEX project_status IF NOT EXISTS FOR (p:Project) ON (p.status);

// Event Clock indexes
CREATE INDEX decision_name IF NOT EXISTS FOR (d:Decision) ON (d.name);
CREATE INDEX decision_timestamp IF NOT EXISTS FOR (d:Decision) ON (d.timestamp);
CREATE INDEX context_name IF NOT EXISTS FOR (c:Context) ON (c.name);
CREATE INDEX fact_name IF NOT EXISTS FOR (f:Fact) ON (f.name);
CREATE INDEX fact_validAt IF NOT EXISTS FOR (f:Fact) ON (f.validAt);
CREATE INDEX state_name IF NOT EXISTS FOR (s:State) ON (s.name);
CREATE INDEX action_name IF NOT EXISTS FOR (a:Action) ON (a.name);

// Meeting and Event indexes
CREATE INDEX meeting_name IF NOT EXISTS FOR (m:Meeting) ON (m.name);
CREATE INDEX meeting_datetime IF NOT EXISTS FOR (m:Meeting) ON (m.datetime);
CREATE INDEX event_name IF NOT EXISTS FOR (e:Event) ON (e.name);
CREATE INDEX event_timestamp IF NOT EXISTS FOR (e:Event) ON (e.timestamp);

// Show all indexes
SHOW INDEXES;


// =============================================================================
// END OF CONSTRAINTS SCRIPT
// =============================================================================
