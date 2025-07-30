import json
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
from .models import ExampleDataModelResponse
from .static import (
    DATA_INGEST_PROCESS,
    PATIENT_JOURNEY_MODEL,
    SUPPLY_CHAIN_MODEL,
    SOFTWARE_DEPENDENCY_MODEL,
    OIL_GAS_MONITORING_MODEL,
    CUSTOMER_360_MODEL,
    FRAUD_AML_MODEL,
    HEALTH_INSURANCE_FRAUD_MODEL,
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

    @mcp.resource("resource://examples/patient_journey_model")
    def example_patient_journey_model() -> str:
        """Get a real-world Patient Journey healthcare data model in JSON format."""
        logger.info("Getting the Patient Journey healthcare data model.")
        return json.dumps(PATIENT_JOURNEY_MODEL, indent=2)

    @mcp.resource("resource://examples/supply_chain_model")
    def example_supply_chain_model() -> str:
        """Get a real-world Supply Chain data model in JSON format."""
        logger.info("Getting the Supply Chain data model.")
        return json.dumps(SUPPLY_CHAIN_MODEL, indent=2)

    @mcp.resource("resource://examples/software_dependency_model")
    def example_software_dependency_model() -> str:
        """Get a real-world Software Dependency Graph data model in JSON format."""
        logger.info("Getting the Software Dependency Graph data model.")
        return json.dumps(SOFTWARE_DEPENDENCY_MODEL, indent=2)

    @mcp.resource("resource://examples/oil_gas_monitoring_model")
    def example_oil_gas_monitoring_model() -> str:
        """Get a real-world Oil and Gas Equipment Monitoring data model in JSON format."""
        logger.info("Getting the Oil and Gas Equipment Monitoring data model.")
        return json.dumps(OIL_GAS_MONITORING_MODEL, indent=2)

    @mcp.resource("resource://examples/customer_360_model")
    def example_customer_360_model() -> str:
        """Get a real-world Customer 360 data model in JSON format."""
        logger.info("Getting the Customer 360 data model.")
        return json.dumps(CUSTOMER_360_MODEL, indent=2)

    @mcp.resource("resource://examples/fraud_aml_model")
    def example_fraud_aml_model() -> str:
        """Get a real-world Fraud & AML data model in JSON format."""
        logger.info("Getting the Fraud & AML data model.")
        return json.dumps(FRAUD_AML_MODEL, indent=2)

    @mcp.resource("resource://examples/health_insurance_fraud_model")
    def example_health_insurance_fraud_model() -> str:
        """Get a real-world Health Insurance Fraud Detection data model in JSON format."""
        logger.info("Getting the Health Insurance Fraud Detection data model.")
        return json.dumps(HEALTH_INSURANCE_FRAUD_MODEL, indent=2)

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
    def get_example_data_model(
        example_name: str = Field(
            ...,
            description="Name of the example to load: 'patient_journey', 'supply_chain', 'software_dependency', 'oil_gas_monitoring', 'customer_360', 'fraud_aml', or 'health_insurance_fraud'",
        ),
    ) -> ExampleDataModelResponse:
        """Get an example graph data model from the available templates. Returns a DataModel object and the Mermaid visualization configuration for the example graph data model."""
        logger.info(f"Getting example data model: {example_name}")

        example_map = {
            "patient_journey": PATIENT_JOURNEY_MODEL,
            "supply_chain": SUPPLY_CHAIN_MODEL,
            "software_dependency": SOFTWARE_DEPENDENCY_MODEL,
            "oil_gas_monitoring": OIL_GAS_MONITORING_MODEL,
            "customer_360": CUSTOMER_360_MODEL,
            "fraud_aml": FRAUD_AML_MODEL,
            "health_insurance_fraud": HEALTH_INSURANCE_FRAUD_MODEL,
        }

        if example_name not in example_map:
            raise ValueError(
                f"Unknown example: {example_name}. Available examples: {list(example_map.keys())}"
            )

        example_data = example_map[example_name]

        validated_data_model = DataModel.model_validate(example_data)

        return ExampleDataModelResponse(
            data_model=validated_data_model,
            mermaid_config=validated_data_model.get_mermaid_config_str(),
        )

    @mcp.tool()
    def list_example_data_models() -> dict[str, Any]:
        """List all available example data models with descriptions. Returns a dictionary with example names and their descriptions."""
        logger.info("Listing available example data models.")

        examples = {
            "patient_journey": {
                "name": "Patient Journey",
                "description": "Healthcare data model for tracking patient encounters, conditions, medications, and care plans",
                "nodes": len(PATIENT_JOURNEY_MODEL["nodes"]),
                "relationships": len(PATIENT_JOURNEY_MODEL["relationships"]),
            },
            "supply_chain": {
                "name": "Supply Chain",
                "description": "Supply chain management data model for tracking products, orders, inventory, and locations",
                "nodes": len(SUPPLY_CHAIN_MODEL["nodes"]),
                "relationships": len(SUPPLY_CHAIN_MODEL["relationships"]),
            },
            "software_dependency": {
                "name": "Software Dependency Graph",
                "description": "Software dependency tracking with security vulnerabilities, commits, and contributor analysis",
                "nodes": len(SOFTWARE_DEPENDENCY_MODEL["nodes"]),
                "relationships": len(SOFTWARE_DEPENDENCY_MODEL["relationships"]),
            },
            "oil_gas_monitoring": {
                "name": "Oil & Gas Equipment Monitoring",
                "description": "Industrial monitoring data model for oil and gas equipment, sensors, alerts, and maintenance",
                "nodes": len(OIL_GAS_MONITORING_MODEL["nodes"]),
                "relationships": len(OIL_GAS_MONITORING_MODEL["relationships"]),
            },
            "customer_360": {
                "name": "Customer 360",
                "description": "Customer relationship management data model for accounts, contacts, orders, tickets, and surveys",
                "nodes": len(CUSTOMER_360_MODEL["nodes"]),
                "relationships": len(CUSTOMER_360_MODEL["relationships"]),
            },
            "fraud_aml": {
                "name": "Fraud & AML",
                "description": "Financial fraud detection and anti-money laundering data model for customers, transactions, alerts, and compliance",
                "nodes": len(FRAUD_AML_MODEL["nodes"]),
                "relationships": len(FRAUD_AML_MODEL["relationships"]),
            },
            "health_insurance_fraud": {
                "name": "Health Insurance Fraud Detection",
                "description": "Healthcare fraud detection data model for tracking investigations, prescriptions, executions, and beneficiary relationships",
                "nodes": len(HEALTH_INSURANCE_FRAUD_MODEL["nodes"]),
                "relationships": len(HEALTH_INSURANCE_FRAUD_MODEL["relationships"]),
            },
        }

        return {
            "available_examples": examples,
            "total_examples": len(examples),
            "usage": "Use the get_example_data_model tool with any of the example names above to get a specific data model",
        }

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
