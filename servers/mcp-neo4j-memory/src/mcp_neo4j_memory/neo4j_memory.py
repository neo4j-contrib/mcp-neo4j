import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from neo4j import AsyncDriver, RoutingControl
from pydantic import BaseModel, Field


# Set up logging
logger = logging.getLogger('mcp_neo4j_memory')
logger.setLevel(logging.INFO)

# Models for our knowledge graph
class Entity(BaseModel):
    """Represents a memory entity in the knowledge graph.

    Example:
    {
        "name": "John Smith",
        "type": "Person",
        "observations": ["Prefers morning meetings"],
        "properties": {
            "email": "john@company.com",
            "role": "Engineer",
            "validAt": "2026-01-15T10:00:00Z"
        }
    }
    """
    name: str = Field(
        description="Unique identifier/name for the entity. Should be descriptive and specific.",
        min_length=1,
        examples=["John Smith", "Neo4j Inc", "San Francisco"]
    )
    type: str = Field(
        description="Category or classification of the entity. Use PascalCase. Common types: 'Person', 'Organization', 'Project', 'Meeting', 'Fact', 'Decision'",
        min_length=1,
        examples=["Person", "Organization", "Project", "Meeting", "Fact", "Decision"],
        pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'
    )
    observations: List[str] = Field(
        default=[],
        description="List of unstructured notes about this entity. Use properties for structured/queryable data.",
        examples=[["Prefers morning meetings"], ["Additional context"]]
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured properties for the entity. Common: validAt, invalidAt, source, confidence, plus type-specific properties like email, role, status.",
        examples=[{"email": "john@company.com", "validAt": "2026-01-15T10:00:00Z"}]
    )

class Relation(BaseModel):
    """Represents a relationship between two entities in the knowledge graph.

    Example:
    {
        "source": "John Smith",
        "target": "Neo4j Inc",
        "relationType": "WORKS_AT",
        "properties": {
            "validAt": "2026-01-15T10:00:00Z",
            "role": "Senior Engineer",
            "source": "HR System"
        }
    }
    """
    source: str = Field(
        description="Name of the source entity (must match an existing entity name exactly)",
        min_length=1,
        examples=["John Smith", "Neo4j Inc"]
    )
    target: str = Field(
        description="Name of the target entity (must match an existing entity name exactly)",
        min_length=1,
        examples=["Neo4j Inc", "San Francisco"]
    )
    relationType: str = Field(
        description="Type of relationship between source and target. Use descriptive, uppercase names with underscores.",
        min_length=1,
        examples=["WORKS_AT", "LIVES_IN", "MANAGES", "COLLABORATES_WITH", "LOCATED_IN"],
        pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured properties for the relationship. Common: validAt, invalidAt, source, confidence. Use for temporal tracking and soft deletes.",
        examples=[{"validAt": "2026-01-15T10:00:00Z", "role": "Senior Engineer"}]
    )

class KnowledgeGraph(BaseModel):
    """Complete knowledge graph containing entities and their relationships."""
    entities: List[Entity] = Field(
        description="List of all entities in the knowledge graph",
        default=[]
    )
    relations: List[Relation] = Field(
        description="List of all relationships between entities",
        default=[]
    )

class ObservationAddition(BaseModel):
    """Request to add new observations to an existing entity.
    
    Example:
    {
        "entityName": "John Smith",
        "observations": ["Recently promoted to Senior Engineer", "Speaks fluent German"]
    }
    """
    entityName: str = Field(
        description="Exact name of the existing entity to add observations to",
        min_length=1,
        examples=["John Smith", "Neo4j Inc"]
    )
    observations: List[str] = Field(
        description="New observations/facts to add to the entity. Each should be unique and informative.",
        min_length=1
    )

class ObservationDeletion(BaseModel):
    """Request to delete specific observations from an existing entity.

    Example:
    {
        "entityName": "John Smith",
        "observations": ["Old job title", "Outdated contact info"]
    }
    """
    entityName: str = Field(
        description="Exact name of the existing entity to remove observations from",
        min_length=1,
        examples=["John Smith", "Neo4j Inc"]
    )
    observations: List[str] = Field(
        description="Exact observation texts to delete from the entity (must match existing observations exactly)",
        min_length=1
    )


class EntityPropertyUpdate(BaseModel):
    """Request to update properties on an existing entity.

    Example:
    {
        "entityName": "John Smith",
        "properties": {
            "invalidAt": "2026-01-15T00:00:00Z",
            "role": "Former Engineer"
        }
    }
    """
    entityName: str = Field(
        description="Exact name of the existing entity to update",
        min_length=1,
        examples=["John Smith", "Neo4j Inc"]
    )
    properties: Dict[str, Any] = Field(
        description="Properties to set or update. Use null to remove a property.",
        examples=[{"invalidAt": "2026-01-15T00:00:00Z", "status": "inactive"}]
    )


class RelationPropertyUpdate(BaseModel):
    """Request to update properties on an existing relationship.

    Example:
    {
        "source": "John Smith",
        "target": "Old Company",
        "relationType": "WORKS_AT",
        "properties": {
            "invalidAt": "2026-01-15T00:00:00Z"
        }
    }
    """
    source: str = Field(
        description="Name of the source entity",
        min_length=1
    )
    target: str = Field(
        description="Name of the target entity",
        min_length=1
    )
    relationType: str = Field(
        description="Type of the relationship",
        min_length=1
    )
    properties: Dict[str, Any] = Field(
        description="Properties to set or update. Use null to remove a property.",
        examples=[{"invalidAt": "2026-01-15T00:00:00Z"}]
    )

class Neo4jMemory:
    # Core entity types for the World Model schema
    ENTITY_LABELS = [
        "Person", "Organization", "Group", "Persona",
        "Location", "Facility",
        "Project", "Task", "Job", "Workflow", "Event", "Calendar", "Meeting",
        "Opportunity", "Proposal", "Contract", "Invoice", "Budget", "Transaction",
        "Resource", "Asset", "Component", "Subsystem", "Environment", "Service", "Interface",
        "Product", "Brand", "Offering", "BOM",
        "Intelligence", "Decision", "Action", "Perception", "Signal", "Outcome",
        "State", "EventTrace", "Context", "Fact", "Document"
    ]

    def __init__(self, neo4j_driver: AsyncDriver):
        self.driver = neo4j_driver

    async def create_fulltext_index(self):
        """Create a fulltext search index across all entity types."""
        try:
            # Drop old Memory-based index if it exists
            try:
                await self.driver.execute_query(
                    "DROP INDEX search IF EXISTS",
                    routing_control=RoutingControl.WRITE
                )
            except Exception:
                pass

            # Create multi-label fulltext index
            labels = "|".join(self.ENTITY_LABELS)
            query = f"CREATE FULLTEXT INDEX search IF NOT EXISTS FOR (n:{labels}) ON EACH [n.name, n.title, n.type, n.observations];"
            await self.driver.execute_query(query, routing_control=RoutingControl.WRITE)
            logger.info("Created fulltext search index across all entity types")
        except Exception as e:
            # Index might already exist, which is fine
            logger.debug(f"Fulltext index creation: {e}")

    # Properties to exclude when returning entity properties (managed internally)
    RESERVED_ENTITY_PROPS = {'name', 'type', 'observations', 'title', 'createdAt'}
    RESERVED_RELATION_PROPS = {'createdAt'}

    async def load_graph(self, filter_query: str = "*"):
        """Load the entire knowledge graph from Neo4j."""
        logger.info("Loading knowledge graph from Neo4j")
        query = """
            CALL db.index.fulltext.queryNodes('search', $filter) yield node as entity, score
            OPTIONAL MATCH (entity)-[r]-(other)
            RETURN collect(distinct {
                name: entity.name,
                type: entity.type,
                observations: entity.observations,
                properties: properties(entity)
            }) as nodes,
            collect(distinct {
                source: startNode(r).name,
                target: endNode(r).name,
                relationType: type(r),
                properties: properties(r)
            }) as relations
        """

        result = await self.driver.execute_query(query, {"filter": filter_query}, routing_control=RoutingControl.READ)

        if not result.records:
            return KnowledgeGraph(entities=[], relations=[])

        record = result.records[0]
        nodes = record.get('nodes', list())
        rels = record.get('relations', list())

        entities = []
        for node in nodes:
            if not node.get('name'):
                continue
            # Extract user properties (exclude reserved)
            all_props = node.get('properties', {}) or {}
            user_props = {k: v for k, v in all_props.items() if k not in self.RESERVED_ENTITY_PROPS}
            entities.append(Entity(
                name=node['name'],
                type=node['type'],
                observations=node.get('observations') or [],
                properties=user_props
            ))

        relations = []
        for rel in rels:
            if not rel.get('relationType'):
                continue
            # Extract user properties (exclude reserved)
            all_props = rel.get('properties', {}) or {}
            user_props = {k: v for k, v in all_props.items() if k not in self.RESERVED_RELATION_PROPS}
            relations.append(Relation(
                source=rel['source'],
                target=rel['target'],
                relationType=rel['relationType'],
                properties=user_props
            ))

        logger.debug(f"Loaded entities: {entities}")
        logger.debug(f"Loaded relations: {relations}")

        return KnowledgeGraph(entities=entities, relations=relations)

    async def create_entities(self, entities: List[Entity]) -> List[Entity]:
        """Create multiple new entities in the knowledge graph."""
        logger.info(f"Creating {len(entities)} entities")
        created_at = datetime.now(timezone.utc).isoformat()
        for entity in entities:
            # Create entity with type as primary label
            # Auto-add title and createdAt properties
            # Set user-provided properties (excluding reserved keys)
            query = f"""
            WITH $entity as entity, $createdAt as createdAt, $properties as props
            MERGE (e:`{entity.type}` {{ name: entity.name }})
            SET e += entity {{ .type, .observations }}
            SET e.title = entity.name
            SET e.createdAt = CASE WHEN e.createdAt IS NULL THEN datetime(createdAt) ELSE e.createdAt END
            SET e += props
            """
            # Filter out reserved properties that we manage
            user_props = {k: v for k, v in entity.properties.items() if k not in ['name', 'type', 'observations', 'title', 'createdAt']}
            await self.driver.execute_query(
                query,
                {"entity": entity.model_dump(), "createdAt": created_at, "properties": user_props},
                routing_control=RoutingControl.WRITE
            )

        return entities

    async def create_relations(self, relations: List[Relation]) -> List[Relation]:
        """Create multiple new relations between entities."""
        logger.info(f"Creating {len(relations)} relations")
        created_at = datetime.now(timezone.utc).isoformat()
        for relation in relations:
            # Set createdAt on create, always set user-provided properties
            query = f"""
            WITH $relation as relation, $createdAt as createdAt, $properties as props
            MATCH (from),(to)
            WHERE from.name = relation.source
            AND to.name = relation.target
            MERGE (from)-[r:`{relation.relationType}`]->(to)
            ON CREATE SET r.createdAt = datetime(createdAt)
            SET r += props
            """
            # Filter out reserved properties
            user_props = {k: v for k, v in relation.properties.items() if k not in ['source', 'target', 'relationType', 'createdAt']}
            await self.driver.execute_query(
                query,
                {"relation": relation.model_dump(), "createdAt": created_at, "properties": user_props},
                routing_control=RoutingControl.WRITE
            )

        return relations

    async def add_observations(self, observations: List[ObservationAddition]) -> List[Dict[str, Any]]:
        """Add new observations to existing entities."""
        logger.info(f"Adding observations to {len(observations)} entities")
        query = """
        UNWIND $observations as obs
        MATCH (e { name: obs.entityName })
        WITH e, [o in obs.observations WHERE NOT o IN e.observations] as new
        SET e.observations = coalesce(e.observations,[]) + new
        RETURN e.name as name, new
        """
            
        result = await self.driver.execute_query(
            query, 
            {"observations": [obs.model_dump() for obs in observations]},
            routing_control=RoutingControl.WRITE
        )

        results = [{"entityName": record.get("name"), "addedObservations": record.get("new")} for record in result.records]
        return results

    async def delete_entities(self, entity_names: List[str]) -> None:
        """Delete multiple entities and their associated relations."""
        logger.info(f"Deleting {len(entity_names)} entities")
        query = """
        UNWIND $entities as name
        MATCH (e { name: name })
        DETACH DELETE e
        """
        
        await self.driver.execute_query(query, {"entities": entity_names}, routing_control=RoutingControl.WRITE)
        logger.info(f"Successfully deleted {len(entity_names)} entities")

    async def delete_observations(self, deletions: List[ObservationDeletion]) -> None:
        """Delete specific observations from entities."""
        logger.info(f"Deleting observations from {len(deletions)} entities")
        query = """
        UNWIND $deletions as d
        MATCH (e { name: d.entityName })
        SET e.observations = [o in coalesce(e.observations,[]) WHERE NOT o IN d.observations]
        """
        await self.driver.execute_query(
            query, 
            {"deletions": [deletion.model_dump() for deletion in deletions]},
            routing_control=RoutingControl.WRITE
        )
        logger.info(f"Successfully deleted observations from {len(deletions)} entities")

    async def delete_relations(self, relations: List[Relation]) -> None:
        """Delete multiple relations from the graph."""
        logger.info(f"Deleting {len(relations)} relations")
        for relation in relations:
            query = f"""
            WITH $relation as relation
            MATCH (source)-[r:`{relation.relationType}`]->(target)
            WHERE source.name = relation.source
            AND target.name = relation.target
            DELETE r
            """
            await self.driver.execute_query(
                query, 
                {"relation": relation.model_dump()},
                routing_control=RoutingControl.WRITE
            )
        logger.info(f"Successfully deleted {len(relations)} relations")

    async def read_graph(self) -> KnowledgeGraph:
        """Read the entire knowledge graph."""
        return await self.load_graph()

    async def search_memories(self, query: str) -> KnowledgeGraph:
        """Search for memories based on a query with Fulltext Search."""
        logger.info(f"Searching for memories with query: '{query}'")
        return await self.load_graph(query)

    async def find_memories_by_name(self, names: List[str]) -> KnowledgeGraph:
        """Find specific memories by their names. This does not use fulltext search."""
        logger.info(f"Finding {len(names)} memories by name")
        query = """
        MATCH (e)
        WHERE e.name IN $names
        RETURN  e.name as name,
                e.type as type,
                e.observations as observations,
                properties(e) as properties
        """
        result_nodes = await self.driver.execute_query(query, {"names": names}, routing_control=RoutingControl.READ)
        entities: list[Entity] = list()
        for record in result_nodes.records:
            # Extract user properties (exclude reserved)
            all_props = record.get('properties', {}) or {}
            user_props = {k: v for k, v in all_props.items() if k not in self.RESERVED_ENTITY_PROPS}
            entities.append(Entity(
                name=record['name'],
                type=record['type'],
                observations=record.get('observations') or [],
                properties=user_props
            ))

        # Get relations for found entities
        relations: list[Relation] = list()
        if entities:
            query = """
            MATCH (source)-[r]->(target)
            WHERE source.name IN $names OR target.name IN $names
            RETURN  source.name as source,
                    target.name as target,
                    type(r) as relationType,
                    properties(r) as properties
            """
            result_relations = await self.driver.execute_query(query, {"names": names}, routing_control=RoutingControl.READ)
            for record in result_relations.records:
                # Extract user properties (exclude reserved)
                all_props = record.get('properties', {}) or {}
                user_props = {k: v for k, v in all_props.items() if k not in self.RESERVED_RELATION_PROPS}
                relations.append(Relation(
                    source=record["source"],
                    target=record["target"],
                    relationType=record["relationType"],
                    properties=user_props
                ))

        logger.info(f"Found {len(entities)} entities and {len(relations)} relations")
        return KnowledgeGraph(entities=entities, relations=relations)

    async def update_entity_properties(self, updates: List[EntityPropertyUpdate]) -> List[Dict[str, Any]]:
        """Update properties on existing entities. Use for soft deletes (set invalidAt)."""
        logger.info(f"Updating properties on {len(updates)} entities")
        results = []
        for update in updates:
            # Filter out reserved properties
            user_props = {k: v for k, v in update.properties.items() if k not in self.RESERVED_ENTITY_PROPS}

            # Handle null values (remove property) separately
            props_to_set = {k: v for k, v in user_props.items() if v is not None}
            props_to_remove = [k for k, v in user_props.items() if v is None]

            query = """
            MATCH (e { name: $entityName })
            SET e += $properties
            """
            # Add REMOVE clauses for null properties
            for prop in props_to_remove:
                query += f"\nREMOVE e.{prop}"
            query += "\nRETURN e.name as name, properties(e) as properties"

            result = await self.driver.execute_query(
                query,
                {"entityName": update.entityName, "properties": props_to_set},
                routing_control=RoutingControl.WRITE
            )

            if result.records:
                record = result.records[0]
                all_props = record.get('properties', {}) or {}
                user_props_result = {k: v for k, v in all_props.items() if k not in self.RESERVED_ENTITY_PROPS}
                results.append({"entityName": record['name'], "properties": user_props_result})

        logger.info(f"Successfully updated properties on {len(results)} entities")
        return results

    async def update_relation_properties(self, updates: List[RelationPropertyUpdate]) -> List[Dict[str, Any]]:
        """Update properties on existing relationships. Use for soft deletes (set invalidAt)."""
        logger.info(f"Updating properties on {len(updates)} relations")
        results = []
        for update in updates:
            # Filter out reserved properties
            user_props = {k: v for k, v in update.properties.items() if k not in self.RESERVED_RELATION_PROPS}

            # Handle null values (remove property) separately
            props_to_set = {k: v for k, v in user_props.items() if v is not None}
            props_to_remove = [k for k, v in user_props.items() if v is None]

            query = f"""
            MATCH (source {{ name: $source }})-[r:`{update.relationType}`]->(target {{ name: $target }})
            SET r += $properties
            """
            # Add REMOVE clauses for null properties
            for prop in props_to_remove:
                query += f"\nREMOVE r.{prop}"
            query += "\nRETURN source.name as source, target.name as target, type(r) as relationType, properties(r) as properties"

            result = await self.driver.execute_query(
                query,
                {"source": update.source, "target": update.target, "properties": props_to_set},
                routing_control=RoutingControl.WRITE
            )

            if result.records:
                record = result.records[0]
                all_props = record.get('properties', {}) or {}
                user_props_result = {k: v for k, v in all_props.items() if k not in self.RESERVED_RELATION_PROPS}
                results.append({
                    "source": record['source'],
                    "target": record['target'],
                    "relationType": record['relationType'],
                    "properties": user_props_result
                })

        logger.info(f"Successfully updated properties on {len(results)} relations")
        return results