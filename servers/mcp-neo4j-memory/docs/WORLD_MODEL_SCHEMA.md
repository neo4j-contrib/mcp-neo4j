# World Model Schema for Neo4j Memory

This document defines the comprehensive World Model schema for use with the mcp-neo4j-memory MCP server. It provides guidance for AI agents on entity types, relationship types, and the Event Clock architecture for capturing decisions and temporal facts.

## Overview

The World Model schema extends the flexible mcp-neo4j-memory server with a structured ontology that supports:
- **Organizational entities** (People, Organizations, Projects)
- **Event Clock architecture** (Context, Decision, Event, State)
- **Temporal facts** (validAt, invalidAt for time-bounded knowledge)
- **Causal chaining** (tracking how decisions lead to outcomes)
- **First-class properties** (structured data as node/relationship properties)

---

## Data Model

### Entity Structure

```json
{
  "name": "Alice Johnson",
  "type": "Person",
  "observations": ["Prefers morning meetings"],
  "properties": {
    "email": "alice@acme.com",
    "role": "Senior Architect",
    "validAt": "2026-01-15T10:00:00Z",
    "source": "Onboarding Meeting"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | STRING | Yes | Unique identifier for the entity |
| `type` | STRING | Yes | Entity type (also becomes node label) |
| `observations` | LIST[STRING] | No | Unstructured notes (use sparingly) |
| `properties` | DICT | No | Structured key-value properties |

### Relation Structure

```json
{
  "source": "Alice Johnson",
  "target": "Acme Corp",
  "relationType": "WORKS_AT",
  "properties": {
    "validAt": "2026-01-15T10:00:00Z",
    "role": "Senior Architect",
    "department": "Engineering",
    "source": "HR System"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | STRING | Yes | Source entity name |
| `target` | STRING | Yes | Target entity name |
| `relationType` | STRING | Yes | Relationship type |
| `properties` | DICT | No | Structured key-value properties |

---

## Temporal Properties

All entities and relationships support temporal tracking via properties:

### Core Temporal Fields

| Property | Type | Description |
|----------|------|-------------|
| `createdAt` | DATETIME | Auto-generated when created |
| `validAt` | DATETIME | When this fact became true |
| `invalidAt` | DATETIME | When this fact stopped being true (soft delete) |
| `source` | STRING | Provenance (meeting ID, document, agent) |
| `confidence` | FLOAT | Certainty level (0.0-1.0) |

### Soft Delete Pattern

When a fact becomes invalid, set `invalidAt` rather than deleting:

```json
// Mark relationship as ended
{
  "source": "Alice Johnson",
  "target": "Old Company",
  "relationType": "WORKS_AT",
  "properties": {
    "invalidAt": "2026-01-15T00:00:00Z"
  }
}
```

Query for current facts only:
```cypher
MATCH (p:Person)-[r:WORKS_AT]->(o:Organization)
WHERE r.invalidAt IS NULL OR r.invalidAt > datetime()
RETURN p, r, o
```

---

## Auto-Generated Properties

The MCP server automatically adds these properties:

**Entities:**
| Property | Type | Description |
|----------|------|-------------|
| `title` | STRING | Copy of `name` for Neo4j Bloom display |
| `createdAt` | DATETIME | Timestamp when entity was created |

**Relationships:**
| Property | Type | Description |
|----------|------|-------------|
| `createdAt` | DATETIME | Timestamp when relationship was created |

---

## Property Design Principles

**Use `properties` for structured queryable data:**

| DO | DON'T |
|----|-------|
| `properties: {email: "john@company.com"}` | `observations: ["email: john@company.com"]` |
| `properties: {validAt: "2026-01-06T10:00:00Z"}` | `observations: ["validAt: 2026-01-06"]` |
| `properties: {status: "canonical"}` | `observations: ["status: canonical"]` |

**Use `observations` only for:**
- Unstructured context that doesn't fit standard properties
- Free-form notes and annotations
- Historical commentary

---

## Entity Types Reference

### People & Organizations

| Entity Type | Standard Properties | Description |
|-------------|---------------------|-------------|
| **Person** | `email`, `phone`, `role`, `department`, `validAt`, `invalidAt` | Individual human beings |
| **Organization** | `industry`, `website`, `orgType`, `validAt`, `invalidAt` | Companies, institutions, agencies |
| **Group** | `purpose`, `groupType`, `validAt`, `invalidAt` | Teams, committees, working groups |

### Work Management

| Entity Type | Standard Properties | Description |
|-------------|---------------------|-------------|
| **Project** | `status`, `priority`, `startDate`, `endDate`, `validAt` | Organized work efforts |
| **Task** | `status`, `priority`, `assignee`, `dueDate`, `description` | Individual work items |
| **Meeting** | `datetime`, `duration`, `platform`, `overview`, `location` | Scheduled gatherings |
| **Event** | `timestamp`, `eventType`, `location` | Occurrences in time |

### Intelligence & Decision Making (Event Clock)

| Entity Type | Standard Properties | Description |
|-------------|---------------------|-------------|
| **Context** | `policyVersion`, `marketCondition`, `validAt`, `invalidAt` | Decision environment snapshot |
| **Decision** | `reasoning`, `alternatives`, `confidence`, `decidedBy`, `decidedAt` | Choices made with rationale |
| **Fact** | `text`, `validAt`, `invalidAt`, `status`, `source`, `confidence` | Time-bounded assertions |
| **Action** | `executor`, `executedAt`, `actionType` | Steps taken |
| **State** | `value`, `attribute`, `entityId`, `timestamp` | Point-in-time snapshots |

### Documents & Assets

| Entity Type | Standard Properties | Description |
|-------------|---------------------|-------------|
| **Document** | `url`, `path`, `author`, `documentType`, `version` | Files and documents |
| **Asset** | `assetType`, `location`, `value` | Owned items |

---

## Relationship Types Reference

### Work Relationships

| Relationship | Description | Properties |
|--------------|-------------|------------|
| `WORKS_AT` | Employment | `validAt`, `invalidAt`, `role`, `department` |
| `ASSIGNED_TO` | Task assignment | `validAt`, `assignedDate` |
| `REPORTS_TO` | Hierarchy | `validAt`, `invalidAt` |
| `ATTENDED` | Meeting participation | `validAt` |

### Knowledge Relationships

| Relationship | Description | Properties |
|--------------|-------------|------------|
| `DERIVED_FROM` | Source attribution | `validAt`, `confidence` |
| `SUPERSEDES` | Replacement | `validAt` |
| `MENTIONS` | Reference | `validAt`, `context` |

### Decision & Causality (Event Clock)

| Relationship | Description | Properties |
|--------------|-------------|------------|
| `GOVERNED` | Context control | `validAt` |
| `DETERMINES` | Decision outcome | `validAt`, `confidence` |
| `CAUSED_BY` | Causal chain | `validAt` |
| `RESULTED_IN` | Outcome link | `validAt` |

---

## Event Clock Pattern

The Event Clock captures how decisions are made and their effects over time.

### Subject → Predicate → Object

Every fact in the graph follows this pattern:
```
(Subject:Person {validAt: datetime})
  -[:WORKS_AT {validAt: datetime, invalidAt: datetime, source: "Meeting-123"}]->
(Object:Organization {validAt: datetime})
```

The Predicate (relationship) carries temporal context:
- **When** the relationship became true (`validAt`)
- **When** it stopped being true (`invalidAt`)
- **Why** we believe it (`source`, `confidence`)

### Decision Chain Pattern

```
(Context)-[:GOVERNED {validAt}]->(Decision)-[:DETERMINES {validAt}]->(Action)-[:RESULTED_IN {validAt}]->(State)
```

### Example: Recording a Decision with Properties

```json
// 1. Create Context
{
  "entities": [{
    "name": "Q1 2026 Planning Context",
    "type": "Context",
    "properties": {
      "policyVersion": "planning-guidelines-v2",
      "marketCondition": "competitive",
      "validAt": "2026-01-18T10:00:00Z"
    }
  }]
}

// 2. Create Decision
{
  "entities": [{
    "name": "Prioritize Mobile Development",
    "type": "Decision",
    "properties": {
      "reasoning": "User analytics show 70% mobile traffic",
      "alternatives": ["web-first", "hybrid approach"],
      "confidence": 0.85,
      "decidedBy": "Luc",
      "decidedAt": "2026-01-18T10:30:00Z"
    }
  }]
}

// 3. Link with temporal relationship
{
  "relations": [{
    "source": "Q1 2026 Planning Context",
    "target": "Prioritize Mobile Development",
    "relationType": "GOVERNED",
    "properties": {
      "validAt": "2026-01-18T10:30:00Z"
    }
  }]
}
```

---

## Fact Management

### Fact Status Values

| Status | Description |
|--------|-------------|
| `canonical` | The authoritative, current version |
| `superseded` | Replaced by a newer version |
| `corroborated` | Confirmed by another source |
| `synthesized` | Derived from combining other facts |

### When Facts Change

1. Create new Fact with `validAt` timestamp
2. Create `SUPERSEDES` relationship from new to old
3. Set `invalidAt` on old Fact, change `status` to `superseded`

```json
// New fact supersedes old
{
  "entities": [{
    "name": "Mobile App v3 is Top Priority",
    "type": "Fact",
    "properties": {
      "text": "Mobile App v3 is now #1 priority",
      "validAt": "2026-03-01T10:00:00Z",
      "status": "canonical",
      "source": "Q2 Planning Meeting"
    }
  }],
  "relations": [{
    "source": "Mobile App v3 is Top Priority",
    "target": "Mobile App v2 is Top Priority",
    "relationType": "SUPERSEDES",
    "properties": {
      "validAt": "2026-03-01T10:00:00Z"
    }
  }]
}
```

---

## Querying Temporal Data

### Current Facts Only

```cypher
// Find active employment relationships
MATCH (p:Person)-[r:WORKS_AT]->(o:Organization)
WHERE r.invalidAt IS NULL
RETURN p.name, o.name, r.role, r.validAt

// Find canonical facts
MATCH (f:Fact)
WHERE f.status = 'canonical'
RETURN f.name, f.text, f.validAt
```

### Historical Queries (Point-in-Time)

```cypher
// Who worked where on a specific date?
MATCH (p:Person)-[r:WORKS_AT]->(o:Organization)
WHERE r.validAt <= datetime('2025-06-01T00:00:00Z')
  AND (r.invalidAt IS NULL OR r.invalidAt > datetime('2025-06-01T00:00:00Z'))
RETURN p.name, o.name, r.role
```

### Decision Audit Trail

```cypher
// Trace a decision's context and outcomes
MATCH (ctx:Context)-[:GOVERNED]->(d:Decision)-[:DETERMINES]->(outcome)
WHERE d.name = 'Prioritize Mobile Development'
RETURN ctx, d, outcome
```

---

## Migration from Observations-Based Data

If you have existing data with structured values in observations:

```cypher
// Extract email from observations to property
MATCH (p:Person)
WHERE any(obs IN p.observations WHERE obs STARTS WITH 'email:')
WITH p, [obs IN p.observations WHERE obs STARTS WITH 'email:'][0] AS emailObs
SET p.email = trim(substring(emailObs, 6))
SET p.observations = [obs IN p.observations WHERE NOT obs STARTS WITH 'email:']
RETURN p.name, p.email

// Extract validAt from observations
MATCH (f:Fact)
WHERE any(obs IN f.observations WHERE obs STARTS WITH 'validAt:')
WITH f, [obs IN f.observations WHERE obs STARTS WITH 'validAt:'][0] AS validAtObs
SET f.validAt = datetime(trim(substring(validAtObs, 8)))
SET f.observations = [obs IN f.observations WHERE NOT obs STARTS WITH 'validAt:']
RETURN f.name, f.validAt
```

See `docs/scripts/migration.cypher` for complete migration scripts.

---

## Schema Version

**Version**: 3.0.0
**Last Updated**: 2026-01-19
**Compatible with**: mcp-neo4j-memory v0.5.x+

### Changes from v2.0.0
- Added `properties` dict to Entity and Relation models
- Temporal properties (`validAt`, `invalidAt`) as first-class citizens
- Soft delete pattern documented
- Relationship properties for Event Clock predicates
- Migration guide for observations-based data
