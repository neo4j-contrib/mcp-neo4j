import logging
from typing import Any, Literal

from fastmcp.server import FastMCP
from pydantic import Field, ValidationError

from .data_model import (
    DataModel,
    Node,
    Property,
    Relationship,
)
from .static import (
    DATA_INGEST_PROCESS,
    DATA_MODELING_TEMPLATE,
    PATIENT_JOURNEY_MODEL,
    SUPPLY_CHAIN_MODEL,
)

logger = logging.getLogger("mcp_neo4j_data_modeling")


def create_mcp_server() -> FastMCP:
    """Create an MCP server instance for data modeling."""

    mcp: FastMCP = FastMCP(
        "mcp-neo4j-data-modeling", dependencies=["pydantic"], stateless_http=True
    )

    @mcp.resource("resource://schema/node")
    def node_schema() -> dict[str, Any]:
        """Get the schema for a node."""
        logger.info("Getting the schema for a node.")
        return Node.model_json_schema()

    @mcp.resource("resource://schema/relationship")
    def relationship_schema() -> dict[str, Any]:
        """Get the schema for a relationship."""
        logger.info("Getting the schema for a relationship.")
        return Relationship.model_json_schema()

    @mcp.resource("resource://schema/property")
    def property_schema() -> dict[str, Any]:
        """Get the schema for a property."""
        logger.info("Getting the schema for a property.")
        return Property.model_json_schema()

    @mcp.resource("resource://schema/data_model")
    def data_model_schema() -> dict[str, Any]:
        """Get the schema for a data model."""
        logger.info("Getting the schema for a data model.")
        return DataModel.model_json_schema()

    @mcp.resource("resource://static/neo4j_data_ingest_process")
    def neo4j_data_ingest_process() -> str:
        """Get the process for ingesting data into a Neo4j database."""
        logger.info("Getting the process for ingesting data into a Neo4j database.")
        return DATA_INGEST_PROCESS

    # Data Modeling Template
    @mcp.resource("resource://templates/data_modeling_request")
    def data_modeling_template() -> str:
        """Get a comprehensive template for requesting data model creation."""
        logger.info("Getting the data modeling request template.")
        return DATA_MODELING_TEMPLATE

    # Real-World Example: Patient Journey Healthcare Data Model
    @mcp.resource("resource://examples/patient_journey_model")
    def example_patient_journey_model() -> dict[str, Any]:
        """Get a real-world Patient Journey healthcare data model in JSON format."""
        logger.info("Getting the Patient Journey healthcare data model.")
        return PATIENT_JOURNEY_MODEL

    # Real-World Example: Google Supply Chain Data Model
    @mcp.resource("resource://examples/supply_chain_model")
    def example_supply_chain_model() -> dict[str, Any]:
        """Get a real-world Google Supply Chain data model in JSON format."""
        logger.info("Getting the Google Supply Chain data model.")
        return SUPPLY_CHAIN_MODEL

    @mcp.tool()
    def generate_data_modeling_prompt(
        domain: str = Field(
            ...,
            description="Domain of your data (e.g., 'healthcare', 'supply_chain', 'ecommerce', 'fraud', 'infosec')",
        ),
        data_samples: list[dict] = Field(
            ...,
            description="Sample data records (2-5 records is sufficient for analysis)",
        ),
        use_cases: list[str] = Field(
            ...,
            description="Main use cases or questions you want to answer with this data model",
        ),
        additional_context: str = Field(
            "",
            description="Any additional context, constraints, or special requirements",
        ),
    ) -> str:
        """Generate a customized data modeling prompt template based on your actual data samples and context."""
        logger.info(
            f"Generating customized data modeling prompt for domain: {domain} with {len(data_samples)} data samples"
        )

        if not data_samples:
            raise ValueError("At least one data sample is required for analysis")

        # Analyze the data samples
        sample_analysis = _analyze_data_samples(data_samples)

        # Get relevant example model based on domain using resources
        example_details = ""

        # Create available examples data directly instead of calling the tool
        available_examples = {
            "available_models": {
                "patient_journey": {
                    "name": "Patient Journey Healthcare",
                    "domain": "Healthcare/Medical",
                    "description": "Complete healthcare data model with patients, encounters, providers, conditions, drugs, and medical procedures",
                    "nodes": len(PATIENT_JOURNEY_MODEL["nodes"]),
                    "relationships": len(PATIENT_JOURNEY_MODEL["relationships"]),
                    "key_entities": [
                        "Patient",
                        "Encounter",
                        "Provider",
                        "Condition",
                        "Drug",
                        "Procedure",
                    ],
                    "use_cases": [
                        "Patient journey tracking",
                        "Medical analytics",
                        "Care coordination",
                        "Clinical decision support",
                    ],
                    "resource_uri": "resource://examples/patient_journey_model",
                    "tool_command": "load_example_data_model('patient_journey')",
                },
                "supply_chain": {
                    "name": "Google Supply Chain",
                    "domain": "Supply Chain/Logistics",
                    "description": "Comprehensive supply chain data model with products, orders, inventory, locations, and legal entities",
                    "nodes": len(SUPPLY_CHAIN_MODEL["nodes"]),
                    "relationships": len(SUPPLY_CHAIN_MODEL["relationships"]),
                    "key_entities": [
                        "Product",
                        "Order",
                        "Inventory",
                        "Location",
                        "LegalEntity",
                        "Asset",
                    ],
                    "use_cases": [
                        "Supply chain optimization",
                        "Inventory management",
                        "Order tracking",
                        "Supplier management",
                    ],
                    "resource_uri": "resource://examples/supply_chain_model",
                    "tool_command": "load_example_data_model('supply_chain')",
                },
            }
        }

        # Find the best matching example based on domain and use cases
        best_match = _find_best_example_match(domain, use_cases, available_examples)

        if best_match:
            example_name = best_match["name"]
            example_details = f"""
**Relevant Example Model**: {example_name}
- **Domain**: {best_match["domain"]}
- **Description**: {best_match["description"]}
- **Nodes**: {best_match["nodes"]} | **Relationships**: {best_match["relationships"]}
- **Key Entities**: {", ".join(best_match["key_entities"])}
- **Use Cases**: {", ".join(best_match["use_cases"])}

You can load this example using: `load_example_data_model('{best_match["key"]}')`
"""
        else:
            example_details = """
**Available Examples**: No specific example matches your domain, but you can explore:
- **Patient Journey Healthcare**: Medical/clinical data modeling
- **Google Supply Chain**: Logistics and supply chain management

Use `list_available_example_models()` to see all available examples.
"""

        # Build the customized template
        template = f"""# Customized Data Modeling Request Template for {domain.title()} Domain

## Your Context
- **Domain**: {domain}
- **Use Cases**: {", ".join(use_cases)}
- **Data Samples Analyzed**: {len(data_samples)} records
{f"- **Additional Context**: {additional_context}" if additional_context else ""}

## Data Analysis Results
Based on your data samples, here's what I found:

### Detected Fields
{sample_analysis["field_analysis"]}

### Potential Entities
{sample_analysis["entity_suggestions"]}

### Data Type Recommendations
{sample_analysis["type_recommendations"]}

### Relationship Suggestions
{sample_analysis["relationship_suggestions"]}

## Source Data Description
Please provide detailed information about your data:

- **Data Format**: [CSV/JSON/XML/API/Database/Other]
- **Data Volume**: [Small (< 1M records) / Medium (1M-100M) / Large (> 100M)]
- **Data Sources**: [List your specific data sources - files, APIs, databases, etc.]
- **Data Quality**: [Clean/Requires cleaning/Unknown]

## Use Cases & Requirements
Based on your stated use cases: {", ".join(use_cases)}

- **Specific Questions**: [What exact questions will you ask of the data?]
- **Performance Requirements**: [Response time needs - sub-second, seconds, minutes]
- **Scale Expectations**: [Expected number of nodes and relationships]
- **Query Patterns**: [Read-heavy/Write-heavy/Balanced]
- **Business Goals**: [What are you trying to achieve?]

## Example Entities (Nodes)
Based on the data analysis above, here are suggested entities:

{sample_analysis["detailed_entities"]}

## Example Relationships
Based on the data analysis, here are suggested relationships:

{sample_analysis["detailed_relationships"]}

## Additional Context
- **Domain**: {domain}
- **Special Requirements**: [Constraints, indexes, specific query patterns]
- **Integration Needs**: [How will this integrate with existing systems?]
- **Compliance**: [Any regulatory or compliance requirements?]

## Reference Example
{example_details}

## Next Steps
1. Review and refine the suggested entities and relationships above
2. Use `list_available_example_models()` to explore all available examples
3. Use `load_example_data_model('example_name')` to load a specific example
4. Use `validate_data_model()` to validate your model
5. Use `export_to_arrows_json()` to export for visualization
6. Use `get_mermaid_config_str()` to generate Mermaid diagrams
"""

        return template

    @mcp.tool()
    def list_available_example_models() -> dict[str, Any]:
        """List all available example data models with their details and domains. Uses the example resources to provide comprehensive information."""
        logger.info("Listing available example data models")

        examples = {
            "patient_journey": {
                "name": "Patient Journey Healthcare",
                "domain": "Healthcare/Medical",
                "description": "Complete healthcare data model with patients, encounters, providers, conditions, drugs, and medical procedures",
                "nodes": len(PATIENT_JOURNEY_MODEL["nodes"]),
                "relationships": len(PATIENT_JOURNEY_MODEL["relationships"]),
                "key_entities": [
                    "Patient",
                    "Encounter",
                    "Provider",
                    "Condition",
                    "Drug",
                    "Procedure",
                ],
                "use_cases": [
                    "Patient journey tracking",
                    "Medical analytics",
                    "Care coordination",
                    "Clinical decision support",
                ],
                "resource_uri": "resource://examples/patient_journey_model",
                "tool_command": "load_example_data_model('patient_journey')",
            },
            "supply_chain": {
                "name": "Google Supply Chain",
                "domain": "Supply Chain/Logistics",
                "description": "Comprehensive supply chain data model with products, orders, inventory, locations, and legal entities",
                "nodes": len(SUPPLY_CHAIN_MODEL["nodes"]),
                "relationships": len(SUPPLY_CHAIN_MODEL["relationships"]),
                "key_entities": [
                    "Product",
                    "Order",
                    "Inventory",
                    "Location",
                    "LegalEntity",
                    "Asset",
                ],
                "use_cases": [
                    "Supply chain optimization",
                    "Inventory management",
                    "Order tracking",
                    "Supplier management",
                ],
                "resource_uri": "resource://examples/supply_chain_model",
                "tool_command": "load_example_data_model('supply_chain')",
            },
        }

        # Add schema information
        schema_info = {
            "node_schema": "resource://schema/node",
            "relationship_schema": "resource://schema/relationship",
            "property_schema": "resource://schema/property",
            "data_model_schema": "resource://schema/data_model",
        }

        return {
            "available_models": examples,
            "schema_resources": schema_info,
            "usage": {
                "load_example": "Use load_example_data_model('model_name') to load a specific model",
                "get_schema": "Use get_schema_guidance('schema_type') to get schema information",
                "get_data_types": "Use get_neo4j_data_types_guide() for comprehensive data type information",
                "compare_models": "Use compare_with_example_model() to compare your model with examples",
                "validate": "Use validate_data_model() to validate your model",
                "export": "Use export_to_arrows_json() to export for visualization",
            },
            "total_models": len(examples),
            "domains_covered": list(
                set(example["domain"] for example in examples.values())
            ),
        }

    @mcp.tool()
    def validate_node(
        node: Node, return_validated: bool = False
    ) -> bool | dict[str, Any]:
        "Validate a single node. Returns True if the node is valid, otherwise raises a ValueError. If return_validated is True, returns the validated node."
        logger.info("Validating a single node.")
        try:
            validated_node = Node.model_validate(node, strict=True)
            logger.info("Node validated successfully")
            if return_validated:
                return validated_node
            else:
                return True
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            raise ValueError(f"Validation error: {e}")

    @mcp.tool()
    def validate_relationship(
        relationship: Relationship, return_validated: bool = False
    ) -> bool | dict[str, Any]:
        "Validate a single relationship. Returns True if the relationship is valid, otherwise raises a ValueError. If return_validated is True, returns the validated relationship."
        logger.info("Validating a single relationship.")
        try:
            validated_relationship = Relationship.model_validate(
                relationship, strict=True
            )
            logger.info("Relationship validated successfully")
            if return_validated:
                return validated_relationship
            else:
                return True
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            raise ValueError(f"Validation error: {e}")

    @mcp.tool()
    def validate_data_model(
        data_model: DataModel, return_validated: bool = False
    ) -> bool | dict[str, Any]:
        "Validate the entire data model. Returns True if the data model is valid, otherwise raises a ValueError. If return_validated is True, returns the validated data model."
        logger.info("Validating the entire data model.")
        try:
            DataModel.model_validate(data_model, strict=True)
            logger.info("Data model validated successfully")
            if return_validated:
                return data_model
            else:
                return True
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            raise ValueError(f"Validation error: {e}")

    @mcp.tool()
    def load_from_arrows_json(arrows_data_model_dict: dict[str, Any]) -> DataModel:
        "Load a data model from the Arrows web application format. Returns a data model as a JSON string."
        logger.info("Loading a data model from the Arrows web application format.")
        return DataModel.from_arrows(arrows_data_model_dict)

    @mcp.tool()
    def export_to_arrows_json(data_model: DataModel) -> str:
        "Export the data model to the Arrows web application format. Returns a JSON string. This should be presented to the user as an artifact if possible."
        logger.info("Exporting the data model to the Arrows web application format.")
        return data_model.to_arrows_json_str()

    @mcp.tool()
    def get_mermaid_config_str(data_model: DataModel) -> str:
        "Get the Mermaid configuration string for the data model. This may be visualized in Claude Desktop and other applications with Mermaid support."
        logger.info("Getting the Mermaid configuration string for the data model.")
        try:
            dm_validated = DataModel.model_validate(data_model, strict=True)
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            raise ValueError(f"Validation error: {e}")
        return dm_validated.get_mermaid_config_str()

    @mcp.tool()
    def get_node_cypher_ingest_query(
        node: Node = Field(description="The node to get the Cypher query for."),
    ) -> str:
        """
        Get the Cypher query to ingest a list of Node records into a Neo4j database.
        This should be used to ingest data into a Neo4j database.
        This is a parameterized Cypher query that takes a list of records as input to the $records parameter.
        """
        logger.info(
            f"Getting the Cypher query to ingest a list of Node records into a Neo4j database for node {node.label}."
        )
        return node.get_cypher_ingest_query_for_many_records()

    @mcp.tool()
    def get_relationship_cypher_ingest_query(
        data_model: DataModel = Field(
            description="The data model snippet that contains the relationship, start node and end node."
        ),
        relationship_type: str = Field(
            description="The type of the relationship to get the Cypher query for."
        ),
        relationship_start_node_label: str = Field(
            description="The label of the relationship start node."
        ),
        relationship_end_node_label: str = Field(
            description="The label of the relationship end node."
        ),
    ) -> str:
        """
        Get the Cypher query to ingest a list of Relationship records into a Neo4j database.
        This should be used to ingest data into a Neo4j database.
        This is a parameterized Cypher query that takes a list of records as input to the $records parameter.
        The records must contain the Relationship properties, if any, as well as the sourceId and targetId properties of the start and end nodes respectively.
        """
        logger.info(
            "Getting the Cypher query to ingest a list of Relationship records into a Neo4j database."
        )
        return data_model.get_relationship_cypher_ingest_query_for_many_records(
            relationship_type,
            relationship_start_node_label,
            relationship_end_node_label,
        )

    @mcp.tool()
    def get_constraints_cypher_queries(data_model: DataModel) -> list[str]:
        "Get the Cypher queries to create constraints on the data model. This creates range indexes on the key properties of the nodes and relationships and enforces uniqueness and existence of the key properties."
        logger.info(
            "Getting the Cypher queries to create constraints on the data model."
        )
        return data_model.get_cypher_constraints_query()

    @mcp.tool()
    def load_example_data_model(
        example_name: str = Field(
            ...,
            description="Name of the example to load: 'patient_journey' or 'supply_chain'",
        ),
    ) -> DataModel:
        """Load an example data model from the available templates. Returns a DataModel object that can be used with validation and export tools."""
        logger.info(f"Loading example data model: {example_name}")

        example_map = {
            "patient_journey": PATIENT_JOURNEY_MODEL,
            "supply_chain": SUPPLY_CHAIN_MODEL,
        }

        if example_name not in example_map:
            raise ValueError(
                f"Unknown example: {example_name}. Available examples: {list(example_map.keys())}"
            )

        example_data = example_map[example_name]

        # Convert the example JSON to DataModel objects
        nodes = []
        for node_data in example_data["nodes"]:
            # Create key property
            key_prop = Property(
                name=node_data["key_property"]["name"],
                type=node_data["key_property"]["type"],
            )

            # Create other properties
            properties = []
            for prop_data in node_data.get("properties", []):
                prop = Property(name=prop_data["name"], type=prop_data["type"])
                properties.append(prop)

            # Create node
            node = Node(
                label=node_data["label"], key_property=key_prop, properties=properties
            )
            nodes.append(node)

        # Create relationships
        relationships = []
        for rel_data in example_data["relationships"]:
            # Create key property if it exists
            key_property = None
            if "key_property" in rel_data:
                key_property = Property(
                    name=rel_data["key_property"]["name"],
                    type=rel_data["key_property"]["type"],
                )

            # Create other properties
            properties = []
            for prop_data in rel_data.get("properties", []):
                prop = Property(name=prop_data["name"], type=prop_data["type"])
                properties.append(prop)

            # Create relationship
            relationship = Relationship(
                type=rel_data["type"],
                start_node_label=rel_data["start_node_label"],
                end_node_label=rel_data["end_node_label"],
                key_property=key_property,
                properties=properties,
            )
            relationships.append(relationship)

        # Create and return the data model
        data_model = DataModel(nodes=nodes, relationships=relationships)
        return data_model

    @mcp.tool()
    def get_schema_guidance(
        schema_type: str = Field(
            ...,
            description="Type of schema to get guidance for: 'node', 'relationship', 'property', or 'data_model'",
        ),
    ) -> dict[str, Any]:
        """Get schema guidance and validation rules for data modeling components. Uses the schema resources to provide detailed information."""
        logger.info(f"Getting schema guidance for: {schema_type}")

        schema_map = {
            "node": node_schema,
            "relationship": relationship_schema,
            "property": property_schema,
            "data_model": data_model_schema,
        }

        if schema_type not in schema_map:
            raise ValueError(
                f"Unknown schema type: {schema_type}. Available types: {list(schema_map.keys())}"
            )

        schema = schema_map[schema_type]()

        # Add helpful guidance based on schema type
        guidance = {
            "schema": schema,
            "usage_tips": _get_schema_usage_tips(schema_type),
            "validation_rules": _get_validation_rules(schema_type),
            "best_practices": _get_best_practices(schema_type),
            "related_tools": {
                "data_types_guide": "Use get_neo4j_data_types_guide() for comprehensive Neo4j data type information",
                "type_detection": "Use generate_data_modeling_prompt() with data samples for automatic type detection",
                "validation": "Use validate_data_model() to validate your complete model",
            },
        }

        return guidance

    @mcp.tool()
    def compare_with_example_model(
        domain: str = Field(
            ...,
            description="Domain to compare with (e.g., 'healthcare', 'supply_chain')",
        ),
        your_entities: list[str] = Field(
            ..., description="List of your proposed entities/nodes"
        ),
        your_relationships: list[str] = Field(
            ..., description="List of your proposed relationships"
        ),
    ) -> dict[str, Any]:
        """Compare your proposed data model with available example models to identify overlaps and gaps. Uses the example resources for comparison."""
        logger.info(f"Comparing proposed model with examples for domain: {domain}")

        # Get available examples
        available_examples = list_available_example_models()

        # Find the best matching example
        best_match = _find_best_example_match(domain, [], available_examples)

        if not best_match:
            return {
                "message": f"No specific example found for domain '{domain}'",
                "available_examples": list(available_examples.keys()),
                "suggestions": "Consider using list_available_example_models() to see all available examples",
            }

        # Load the example model for detailed comparison
        example_model = load_example_data_model(best_match["key"])

        # Compare entities
        example_entities = [node.label for node in example_model.nodes]
        entity_overlap = [
            entity for entity in your_entities if entity in example_entities
        ]
        entity_gaps = [
            entity for entity in example_entities if entity not in your_entities
        ]
        your_unique = [
            entity for entity in your_entities if entity not in example_entities
        ]

        # Compare relationships
        example_relationships = [rel.type for rel in example_model.relationships]
        relationship_overlap = [
            rel for rel in your_relationships if rel in example_relationships
        ]
        relationship_gaps = [
            rel for rel in example_relationships if rel not in your_relationships
        ]
        your_unique_rels = [
            rel for rel in your_relationships if rel not in example_relationships
        ]

        return {
            "comparison_with": best_match["name"],
            "domain": best_match["domain"],
            "entities": {
                "overlap": entity_overlap,
                "gaps_in_your_model": entity_gaps,
                "your_unique_entities": your_unique,
                "example_entities": example_entities,
            },
            "relationships": {
                "overlap": relationship_overlap,
                "gaps_in_your_model": relationship_gaps,
                "your_unique_relationships": your_unique_rels,
                "example_relationships": example_relationships,
            },
            "recommendations": _generate_comparison_recommendations(
                entity_overlap, entity_gaps, relationship_overlap, relationship_gaps
            ),
            "next_steps": [
                f"Load the {best_match['name']} example: load_example_data_model('{best_match['key']}')",
                "Review the example model structure and properties",
                "Consider incorporating missing entities/relationships",
                "Validate your model: validate_data_model()",
            ],
        }

    @mcp.tool()
    def get_data_modeling_process_guide() -> dict[str, Any]:
        """Get a comprehensive guide for the data modeling process using the static resources."""
        logger.info("Getting data modeling process guide")

        # Use the static resources
        ingest_process = neo4j_data_ingest_process()
        template = data_modeling_template()

        return {
            "process_overview": "Complete Neo4j data modeling workflow",
            "ingest_process": ingest_process,
            "request_template": template,
            "step_by_step_guide": [
                "1. **Analyze Your Data**: Use generate_data_modeling_prompt() with your data samples",
                "2. **Explore Examples**: Use list_available_example_models() to see available examples",
                "3. **Compare Models**: Use compare_with_example_model() to identify gaps",
                "4. **Get Schema Info**: Use get_schema_guidance() for validation rules",
                "5. **Understand Data Types**: Use get_neo4j_data_types_guide() for type information",
                "6. **Load Examples**: Use load_example_data_model() to study examples",
                "7. **Validate Your Model**: Use validate_data_model() to check your model",
                "8. **Export for Visualization**: Use export_to_arrows_json() for Arrows",
                "9. **Generate Cypher**: Use get_node_cypher_ingest_query() and get_relationship_cypher_ingest_query()",
                "10. **Create Constraints**: Use get_constraints_cypher_queries() for optimization",
            ],
            "available_resources": {
                "schemas": [
                    "resource://schema/node",
                    "resource://schema/relationship",
                    "resource://schema/property",
                    "resource://schema/data_model",
                ],
                "examples": [
                    "resource://examples/patient_journey_model",
                    "resource://examples/supply_chain_model",
                ],
                "templates": [
                    "resource://templates/data_modeling_request",
                    "resource://static/neo4j_data_ingest_process",
                ],
            },
            "key_tools": {
                "analysis": "generate_data_modeling_prompt()",
                "exploration": "list_available_example_models()",
                "comparison": "compare_with_example_model()",
                "validation": "validate_data_model()",
                "data_types": "get_neo4j_data_types_guide()",
                "export": "export_to_arrows_json()",
                "cypher": "get_node_cypher_ingest_query()",
            },
        }

    @mcp.tool()
    def get_neo4j_data_types_guide() -> dict[str, Any]:
        """Get comprehensive information about Neo4j data types, their usage, and examples."""
        logger.info("Getting Neo4j data types guide")

        return {
            "neo4j_data_types": {
                "basic_types": {
                    "NULL": {
                        "description": "Represents the absence of a value",
                        "example": "null",
                        "usage": "Use when a property has no value",
                    },
                    "INTEGER": {
                        "description": "64-bit integer values",
                        "example": "42, -17, 1000000",
                        "usage": "Counts, IDs, ages, quantities",
                    },
                    "FLOAT": {
                        "description": "64-bit floating point numbers",
                        "example": "3.14, -0.001, 1.23e-10",
                        "usage": "Prices, measurements, calculations",
                    },
                    "BOOLEAN": {
                        "description": "True or false values",
                        "example": "true, false",
                        "usage": "Flags, status indicators, conditions",
                    },
                    "STRING": {
                        "description": "Text values",
                        "example": "'Hello World', 'user@example.com'",
                        "usage": "Names, emails, descriptions, labels",
                    },
                },
                "temporal_types": {
                    "DATE": {
                        "description": "Date without time",
                        "example": "date('2024-01-15')",
                        "usage": "Birth dates, event dates, deadlines",
                    },
                    "TIME": {
                        "description": "Time without date",
                        "example": "time('14:30:00')",
                        "usage": "Meeting times, opening hours",
                    },
                    "LOCAL_TIME": {
                        "description": "Time without timezone",
                        "example": "localtime('14:30:00')",
                        "usage": "Local business hours, schedules",
                    },
                    "ZONED_TIME": {
                        "description": "Time with timezone",
                        "example": "time('14:30:00+01:00')",
                        "usage": "Global events, travel schedules",
                    },
                    "LOCAL_DATETIME": {
                        "description": "Date and time without timezone",
                        "example": "datetime('2024-01-15T14:30:00')",
                        "usage": "Local events, appointments",
                    },
                    "ZONED_DATETIME": {
                        "description": "Date and time with timezone",
                        "example": "datetime('2024-01-15T14:30:00+01:00')",
                        "usage": "Global events, timestamps",
                    },
                    "DURATION": {
                        "description": "Time periods",
                        "example": "duration('P1Y2M3DT4H5M6S')",
                        "usage": "Project durations, time intervals",
                    },
                },
                "spatial_types": {
                    "POINT_2D_CARTESIAN": {
                        "description": "2D point in Cartesian coordinates",
                        "example": "point({x: 1, y: 2})",
                        "usage": "Simple 2D coordinates, screen positions",
                    },
                    "POINT_2D_WGS84": {
                        "description": "2D point in WGS84 coordinates (latitude/longitude)",
                        "example": "point({longitude: 2.3, latitude: 48.9})",
                        "usage": "Geographic locations, GPS coordinates",
                    },
                    "POINT_3D_CARTESIAN": {
                        "description": "3D point in Cartesian coordinates",
                        "example": "point({x: 1, y: 2, z: 3})",
                        "usage": "3D modeling, scientific data",
                    },
                    "POINT_3D_WGS84": {
                        "description": "3D point in WGS84 coordinates with altitude",
                        "example": "point({longitude: 2.3, latitude: 48.9, height: 100})",
                        "usage": "3D geographic data, elevation",
                    },
                },
                "collection_types": {
                    "LIST": {
                        "description": "Ordered collection of values",
                        "example": "[1, 2, 3], ['a', 'b', 'c']",
                        "usage": "Tags, categories, ordered data",
                    },
                    "MAP": {
                        "description": "Key-value pairs",
                        "example": "{name: 'John', age: 30}",
                        "usage": "Flexible properties, metadata",
                    },
                },
                "binary_types": {
                    "BYTE_ARRAY": {
                        "description": "Binary data",
                        "example": "bytes('Hello World')",
                        "usage": "File content, images, binary data",
                    }
                },
            },
            "type_detection_tips": [
                "Use generate_data_modeling_prompt() with your data samples for automatic type detection",
                "Consider the semantic meaning of your data when choosing types",
                "Use appropriate temporal types for dates and times",
                "Use spatial types for geographic data",
                "Use LIST for ordered collections and MAP for key-value data",
            ],
            "validation_rules": {
                "INTEGER": "Must be a whole number between -9223372036854775808 and 9223372036854775807",
                "FLOAT": "Must be a valid floating point number",
                "BOOLEAN": "Must be true or false",
                "STRING": "Must be a valid string",
                "DATE": "Must be in YYYY-MM-DD format",
                "TIME": "Must be in HH:MM:SS format",
                "POINT": "Must have valid coordinate values",
            },
            "performance_considerations": [
                "Use INTEGER for IDs and counts for better performance",
                "Index frequently queried properties",
                "Use appropriate types to avoid type coercion",
                "Consider using LIST for small collections, MAP for flexible schemas",
            ],
        }

    def _analyze_data_samples(data_samples: list[dict]) -> dict[str, str]:
        """Analyze data samples to extract insights for data modeling."""
        if not data_samples:
            return {}

        # Get all unique fields across samples
        all_fields = set()
        for sample in data_samples:
            all_fields.update(sample.keys())

        # Analyze data types
        field_types = {}
        for field in all_fields:
            values = [
                sample.get(field)
                for sample in data_samples
                if sample.get(field) is not None
            ]
            if values:
                field_types[field] = _infer_data_type(values)

        # Suggest entities based on field patterns
        entities = _suggest_entities(all_fields, field_types)

        # Suggest relationships
        relationships = _suggest_relationships(all_fields, field_types)

        # Build analysis results
        field_analysis = "\n".join(
            [
                f"- **{field}**: {field_types.get(field, 'UNKNOWN')}"
                for field in sorted(all_fields)
            ]
        )

        entity_suggestions = "\n".join(
            [
                f"- **{entity}**: {', '.join(fields)}"
                for entity, fields in entities.items()
            ]
        )

        type_recommendations = "\n".join(
            [
                f"- **{field}**: {field_types.get(field, 'UNKNOWN')} → Neo4j {_neo4j_type_mapping(field_types.get(field, 'UNKNOWN'))}"
                for field in sorted(all_fields)
            ]
        )

        relationship_suggestions = "\n".join(
            [
                f"- **{rel}**: {start} → {end}"
                for rel, (start, end) in relationships.items()
            ]
        )

        # Build detailed entities section
        detailed_entities_parts = []
        for entity, fields in entities.items():
            properties_list = []
            for field in fields:
                field_type = field_types.get(field, "UNKNOWN")
                properties_list.append(f"{field} ({field_type})")

            properties_str = ", ".join(properties_list)
            sample_data = _get_sample_values(data_samples, fields)

            entity_section = f"""### {entity}
- **Properties**: {properties_str}
- **Key Property**: [Suggest a unique identifier]
- **Example Data**: {sample_data}"""
            detailed_entities_parts.append(entity_section)

        detailed_entities = "\n".join(detailed_entities_parts)

        # Build detailed relationships section
        detailed_relationships_parts = []
        for rel, (start, end) in relationships.items():
            rel_section = f"""### {rel}
- **Type**: {rel.upper()}
- **Direction**: {start} → {end}
- **Properties**: [Any properties on the relationship?]
- **Cardinality**: [One-to-One/One-to-Many/Many-to-Many]"""
            detailed_relationships_parts.append(rel_section)

        detailed_relationships = "\n".join(detailed_relationships_parts)

        return {
            "field_analysis": field_analysis,
            "entity_suggestions": entity_suggestions,
            "type_recommendations": type_recommendations,
            "relationship_suggestions": relationship_suggestions,
            "detailed_entities": detailed_entities,
            "detailed_relationships": detailed_relationships,
        }

    def _infer_data_type(values: list) -> str:
        """Infer the data type from a list of values."""
        if not values:
            return "UNKNOWN"

        # Check for None/null values
        if all(v is None for v in values):
            return "NULL"

        # Check if all are lists
        if all(isinstance(v, list) for v in values if v is not None):
            return "LIST"

        # Check if all are dictionaries/maps
        if all(isinstance(v, dict) for v in values if v is not None):
            return "MAP"

        # Check if all are integers
        try:
            [int(v) for v in values if v is not None]
            return "INTEGER"
        except (ValueError, TypeError):
            pass

        # Check if all are floats
        try:
            [float(v) for v in values if v is not None]
            return "FLOAT"
        except (ValueError, TypeError):
            pass

        # Check if all are booleans
        if all(
            str(v).lower() in ["true", "false", "1", "0"]
            for v in values
            if v is not None
        ):
            return "BOOLEAN"

        # Check for temporal types
        temporal_patterns = {
            "TIME": [r"\d{1,2}:\d{2}(:\d{2})?(\.\d+)?$"],  # HH:MM:SS or HH:MM
            "LOCAL_TIME": [r"\d{1,2}:\d{2}:\d{2}(\.\d+)?$"],  # HH:MM:SS
            "ZONED_TIME": [
                r"\d{1,2}:\d{2}:\d{2}(\.\d+)?[+-]\d{2}:\d{2}$"
            ],  # HH:MM:SS+/-TZ
            "DATE": [r"\d{4}-\d{2}-\d{2}$"],  # YYYY-MM-DD
            "LOCAL_DATETIME": [
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$"
            ],  # YYYY-MM-DDTHH:MM:SS
            "ZONED_DATETIME": [
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?[+-]\d{2}:\d{2}$"
            ],  # YYYY-MM-DDTHH:MM:SS+/-TZ
            "DURATION": [r"P\d+[YMWD]", r"PT\d+[HMS]"],  # ISO 8601 duration format
        }

        import re

        for temp_type, patterns in temporal_patterns.items():
            if all(
                any(re.match(pattern, str(v)) for pattern in patterns)
                for v in values
                if v is not None
            ):
                return temp_type

        # Check for spatial types (Point)
        point_patterns = [
            r"point\(\s*\{[^}]*\}\s*\)",  # point({x: 1, y: 2})
            r"point\(\s*\d+,\s*\d+(?:,\s*\d+)?\s*\)",  # point(4326, 1, 2) or point(4326, 1, 2, 3)
            r"POINT\s*\(\s*\d+\.\d+\s+\d+\.\d+(?:\s+\d+\.\d+)?\s*\)",  # POINT(1.5 2.5) or POINT(1.5 2.5 3.5)
        ]

        if any(
            any(re.search(pattern, str(v), re.IGNORECASE) for pattern in point_patterns)
            for v in values
            if v is not None
        ):
            # Try to determine if it's 2D or 3D and Cartesian or WGS84
            for v in values:
                if v is not None:
                    v_str = str(v).lower()
                    if "z" in v_str or "3d" in v_str:
                        if "wgs" in v_str or "4326" in v_str or "4979" in v_str:
                            return "POINT_3D_WGS84"
                        else:
                            return "POINT_3D_CARTESIAN"
                    else:
                        if "wgs" in v_str or "4326" in v_str:
                            return "POINT_2D_WGS84"
                        else:
                            return "POINT_2D_CARTESIAN"

        # Check for byte arrays (base64 encoded or hex strings)
        byte_patterns = [
            r"^[A-Za-z0-9+/]*={0,2}$",  # Base64
            r"^[0-9A-Fa-f]+$",  # Hex string
        ]

        if all(
            any(re.match(pattern, str(v)) for pattern in byte_patterns)
            and len(str(v)) > 8
            for v in values
            if v is not None
        ):
            return "BYTE_ARRAY"

        # Default to string
        return "STRING"

    def _neo4j_type_mapping(python_type: str) -> str:
        """Map Python types to Neo4j types."""
        mapping = {
            # Basic types
            "NULL": "NULL",
            "INTEGER": "INTEGER",
            "FLOAT": "FLOAT",
            "BOOLEAN": "BOOLEAN",
            "STRING": "STRING",
            "DATE": "DATE",
            # List and Map types
            "LIST": "LIST",
            "MAP": "MAP",
            # Temporal types
            "TIME": "TIME",
            "LOCAL_TIME": "LOCAL TIME",
            "ZONED_TIME": "ZONED TIME",
            "DATETIME": "DATETIME",
            "LOCAL_DATETIME": "LOCAL DATETIME",
            "ZONED_DATETIME": "ZONED DATETIME",
            "DURATION": "DURATION",
            # Spatial types
            "POINT_2D_CARTESIAN": "POINT (2D Cartesian)",
            "POINT_2D_WGS84": "POINT (2D WGS-84)",
            "POINT_3D_CARTESIAN": "POINT (3D Cartesian)",
            "POINT_3D_WGS84": "POINT (3D WGS-84)",
            # Binary types
            "BYTE_ARRAY": "ByteArray",
            # Graph types (for reference, not typically used as properties)
            "NODE": "NODE",
            "RELATIONSHIP": "RELATIONSHIP",
            "PATH": "PATH",
        }
        return mapping.get(python_type, "STRING")

    def _suggest_entities(fields: set, field_types: dict) -> dict[str, list[str]]:
        """Suggest entities based on field patterns."""
        entities = {}

        # Look for common entity patterns
        entity_patterns = {
            "id": ["id", "_id", "Id", "ID"],
            "name": ["name", "Name", "NAME"],
            "type": ["type", "Type", "TYPE"],
            "code": ["code", "Code", "CODE"],
        }

        # Group fields by potential entities
        for field in fields:
            field_lower = field.lower()

            # Check for ID fields (potential entities)
            if any(pattern in field_lower for pattern in entity_patterns["id"]):
                entity_name = (
                    field.replace("_id", "").replace("Id", "").replace("ID", "").title()
                )
                if entity_name:
                    if entity_name not in entities:
                        entities[entity_name] = []
                    entities[entity_name].append(field)

            # Check for name fields
            elif any(pattern in field_lower for pattern in entity_patterns["name"]):
                entity_name = field.replace("name", "").replace("Name", "").title()
                if entity_name:
                    if entity_name not in entities:
                        entities[entity_name] = []
                    entities[entity_name].append(field)

        # Add remaining fields to a general entity
        used_fields = set()
        for entity_fields in entities.values():
            used_fields.update(entity_fields)

        remaining_fields = fields - used_fields
        if remaining_fields:
            entities["Entity"] = list(remaining_fields)

        return entities

    def _suggest_relationships(
        fields: set, field_types: dict
    ) -> dict[str, tuple[str, str]]:
        """Suggest relationships based on field patterns."""
        relationships = {}

        # Look for foreign key patterns
        for field in fields:
            if "_id" in field.lower() or field.lower().endswith("id"):
                # This might be a foreign key
                source_entity = field.replace("_id", "").replace("Id", "").title()
                target_entity = field.replace("_id", "").replace("Id", "").title()

                if source_entity and target_entity:
                    rel_name = f"HAS_{target_entity.upper()}"
                    relationships[rel_name] = (source_entity, target_entity)

        return relationships

    def _get_sample_values(data_samples: list[dict], fields: list[str]) -> str:
        """Get sample values for the given fields."""
        if not data_samples:
            return "No data available"

        sample = data_samples[0]
        values = []
        for field in fields:
            value = sample.get(field, "N/A")
            values.append(f"{field}: {value}")

        return ", ".join(values)

    def _find_best_example_match(
        domain: str, use_cases: list[str], available_examples: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Find the best matching example based on domain and use cases using dynamic pattern matching from resources."""
        import re

        # Create a combined search string from domain and use cases
        search_text = f"{domain} {' '.join(use_cases)}".lower()

        # Dynamic mapping from resource URI to function
        def get_resource_function(resource_uri: str):
            """Dynamically map resource URI to the appropriate function."""
            uri_to_function = {
                "resource://examples/patient_journey_model": example_patient_journey_model,
                "resource://examples/supply_chain_model": example_supply_chain_model,
            }
            return uri_to_function.get(resource_uri)

        # Dynamically generate patterns from example data
        for example_key, example_data in available_examples["available_models"].items():
            # Get the actual resource data by calling the appropriate resource function
            resource_uri = example_data.get("resource_uri", "")
            resource_function = get_resource_function(resource_uri)

            if not resource_function:
                # Skip if we don't have a resource function for this example
                continue

            resource_data = resource_function()

            # Create patterns from domain, description, key entities, and use cases
            pattern_parts = []

            # Add domain keywords
            pattern_parts.append(
                example_data["domain"].lower().replace("/", "|").replace(" ", "|")
            )

            # Add description keywords (extract meaningful words)
            description_words = re.findall(
                r"\b\w+\b", example_data["description"].lower()
            )
            # Filter out common words and keep domain-specific terms
            stop_words = {
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
                "being",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "will",
                "would",
                "could",
                "should",
                "may",
                "might",
                "can",
                "this",
                "that",
                "these",
                "those",
                "i",
                "you",
                "he",
                "she",
                "it",
                "we",
                "they",
                "me",
                "him",
                "her",
                "us",
                "them",
                "my",
                "your",
                "his",
                "her",
                "its",
                "our",
                "their",
                "mine",
                "yours",
                "his",
                "hers",
                "ours",
                "theirs",
            }
            meaningful_words = [
                word
                for word in description_words
                if word not in stop_words and len(word) > 2
            ]
            pattern_parts.extend(meaningful_words)

            # Add key entities from the actual resource data
            resource_entities = [node["label"] for node in resource_data["nodes"]]
            pattern_parts.extend([entity.lower() for entity in resource_entities])

            # Add use cases
            pattern_parts.extend(
                [uc.lower().replace(" ", "|") for uc in example_data["use_cases"]]
            )

            # Create a comprehensive pattern
            pattern = "|".join(set(pattern_parts))  # Remove duplicates

            # Check if the search text matches this pattern
            if re.search(pattern, search_text, re.IGNORECASE):
                example_data_copy = example_data.copy()
                example_data_copy["key"] = example_key  # Add the key for reference
                return example_data_copy

        return None

    def _get_schema_usage_tips(schema_type: str) -> list[str]:
        """Provide usage tips for a given schema type."""
        if schema_type == "node":
            return [
                "Use the `node_schema` resource to get the JSON schema for a node.",
                "Nodes are the fundamental building blocks of your data model.",
                "Each node has a unique label and can have multiple properties.",
                "The `key_property` is crucial for identifying nodes and enforcing uniqueness.",
            ]
        elif schema_type == "relationship":
            return [
                "Use the `relationship_schema` resource to get the JSON schema for a relationship.",
                "Relationships define connections between nodes.",
                "They have a type, start node label, end node label, and can have properties.",
                "The `key_property` is used to enforce uniqueness and enforce existence.",
            ]
        elif schema_type == "property":
            return [
                "Use the `property_schema` resource to get the JSON schema for a property.",
                "Properties are attributes of nodes and relationships.",
                "They have a name and a type (e.g., string, integer, boolean, date).",
                "The `key_property` is a special property that can be used for indexing.",
            ]
        elif schema_type == "data_model":
            return [
                "Use the `data_model_schema` resource to get the JSON schema for the entire data model.",
                "This schema defines the structure of your data, including nodes and relationships.",
                "It's used for validation and export to the Arrows web application.",
            ]
        return []

    def _get_validation_rules(schema_type: str) -> dict[str, Any]:
        """Provide validation rules for a given schema type."""
        if schema_type == "node":
            return {
                "required_fields": ["label"],
                "key_property_required": True,
                "properties_optional": True,
                "property_types": {
                    "label": "string",
                    "key_property": {"name": "string", "type": "string"},
                    "properties": {"name": "string", "type": "string"},
                },
            }
        elif schema_type == "relationship":
            return {
                "required_fields": ["type", "start_node_label", "end_node_label"],
                "key_property_optional": True,
                "properties_optional": True,
                "property_types": {
                    "type": "string",
                    "start_node_label": "string",
                    "end_node_label": "string",
                    "key_property": {"name": "string", "type": "string"},
                    "properties": {"name": "string", "type": "string"},
                },
            }
        elif schema_type == "property":
            return {
                "required_fields": ["name", "type"],
                "key_property_optional": True,
                "property_types": {"name": "string", "type": "string"},
            }
        elif schema_type == "data_model":
            return {
                "required_fields": ["nodes", "relationships"],
                "nodes_required": True,
                "relationships_required": True,
                "node_schema_required": True,
                "relationship_schema_required": True,
                "property_schema_required": True,
                "model_types": {
                    "nodes": [
                        {
                            "label": "string",
                            "key_property": {"name": "string", "type": "string"},
                            "properties": [{"name": "string", "type": "string"}],
                        }
                    ],
                    "relationships": [
                        {
                            "type": "string",
                            "start_node_label": "string",
                            "end_node_label": "string",
                            "key_property": {"name": "string", "type": "string"},
                            "properties": [{"name": "string", "type": "string"}],
                        }
                    ],
                },
            }
        return {}

    def _get_best_practices(schema_type: str) -> list[str]:
        """Provide best practices for a given schema type."""
        if schema_type == "node":
            return [
                "Use meaningful and consistent labels for nodes.",
                "Choose a clear key property for each node to ensure uniqueness.",
                "Avoid overly complex node structures unless absolutely necessary.",
                "Consider adding properties to nodes to enhance data modeling.",
            ]
        elif schema_type == "relationship":
            return [
                "Define clear and concise relationship types.",
                "Use meaningful names for relationships.",
                "Consider adding properties to relationships to capture more context.",
                "Ensure relationships are bidirectional if applicable.",
            ]
        elif schema_type == "property":
            return [
                "Use descriptive names for properties.",
                "Choose appropriate types for properties (string, integer, boolean, date).",
                "Avoid adding too many properties to nodes/relationships.",
                "Consider adding `key_property` if it's a critical identifier.",
            ]
        elif schema_type == "data_model":
            return [
                "Start with a clear domain and use cases.",
                "Model the data in a way that supports your intended queries.",
                "Consider adding constraints (e.g., unique, range indexes) to optimize performance.",
                "Export the model to the Arrows web application for visualization and further refinement.",
            ]
        return []

    def _generate_comparison_recommendations(
        entity_overlap: list[str],
        entity_gaps: list[str],
        relationship_overlap: list[str],
        relationship_gaps: list[str],
    ) -> list[str]:
        """Generate recommendations based on comparison results."""
        recommendations = []

        if entity_gaps:
            recommendations.append(
                f"Consider adding the following entities to your model: {', '.join(entity_gaps)}"
            )

        if relationship_gaps:
            recommendations.append(
                f"Consider adding the following relationships to your model: {', '.join(relationship_gaps)}"
            )

        if not entity_overlap and not relationship_overlap:
            recommendations.append(
                "Your proposed data model is significantly different from the example model. This might indicate a need for a more tailored approach or a different example model."
            )

        return recommendations

    return mcp


async def main(
    transport: Literal["stdio", "sse", "http"] = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp/",
) -> None:
    logger.info("Starting MCP Neo4j Data Modeling Server")

    mcp = create_mcp_server()

    match transport:
        case "http":
            await mcp.run_http_async(host=host, port=port, path=path)
        case "stdio":
            await mcp.run_stdio_async()
        case "sse":
            await mcp.run_sse_async(host=host, port=port, path=path)


if __name__ == "__main__":
    main()
