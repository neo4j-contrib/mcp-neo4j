import pytest
from fastmcp.server import FastMCP


class TestServerTools:
    """Test server tools functionality."""

    @pytest.mark.asyncio
    async def test_list_example_data_models_tool(self, test_mcp_server: FastMCP):
        """Test the list_example_data_models tool."""
        tools = await test_mcp_server.get_tools()
        list_tool = tools.get("list_example_data_models")

        assert list_tool is not None
        result = list_tool.fn()

        assert "available_examples" in result
        assert "total_examples" in result
        assert "usage" in result
        assert result["total_examples"] == 7

        examples = result["available_examples"]
        expected_examples = [
            "patient_journey",
            "supply_chain",
            "software_dependency",
            "oil_gas_monitoring",
            "customer_360",
            "fraud_aml",
            "health_insurance_fraud",
        ]

        for example in expected_examples:
            assert example in examples
            assert "name" in examples[example]
            assert "description" in examples[example]
            assert "nodes" in examples[example]
            assert "relationships" in examples[example]

    @pytest.mark.asyncio
    async def test_get_example_data_model_tool_all_examples(
        self, test_mcp_server: FastMCP
    ):
        """Test the get_example_data_model tool with all available examples."""
        tools = await test_mcp_server.get_tools()
        get_tool = tools.get("get_example_data_model")

        assert get_tool is not None

        # Test all available examples
        examples = [
            "patient_journey",
            "supply_chain",
            "software_dependency",
            "oil_gas_monitoring",
            "customer_360",
            "fraud_aml",
            "health_insurance_fraud",
        ]

        for example in examples:
            result = get_tool.fn(example_name=example)
            data_model = result.data_model
            mermaid_config = result.mermaid_config

            assert data_model is not None
            assert hasattr(data_model, "nodes")
            assert hasattr(data_model, "relationships")
            assert len(data_model.nodes) > 0
            assert len(data_model.relationships) > 0

            assert isinstance(mermaid_config, str)
            assert len(mermaid_config) > 0

    @pytest.mark.asyncio
    async def test_get_example_data_model_tool_invalid_example(
        self, test_mcp_server: FastMCP
    ):
        """Test the get_example_data_model tool with invalid example name."""
        tools = await test_mcp_server.get_tools()
        get_tool = tools.get("get_example_data_model")

        assert get_tool is not None

        with pytest.raises(ValueError, match="Unknown example"):
            get_tool.fn(example_name="invalid_example")


class TestMCPResources:
    """Test MCP resources functionality."""

    @pytest.mark.asyncio
    async def test_mcp_resources_schemas(self, test_mcp_server: FastMCP):
        """Test that schema resources return valid JSON schemas."""
        resources = await test_mcp_server.get_resources()

        schema_resources = [
            "resource://schema/node",
            "resource://schema/relationship",
            "resource://schema/property",
            "resource://schema/data_model",
        ]

        for resource_uri in schema_resources:
            resource = resources.get(resource_uri)
            assert resource is not None
            result = resource.fn()
            assert isinstance(result, dict)
            assert "type" in result or "properties" in result

    @pytest.mark.asyncio
    async def test_mcp_resources_example_models(self, test_mcp_server: FastMCP):
        """Test that example model resources return valid JSON strings."""
        resources = await test_mcp_server.get_resources()

        example_resources = [
            "resource://examples/patient_journey_model",
            "resource://examples/supply_chain_model",
            "resource://examples/software_dependency_model",
            "resource://examples/oil_gas_monitoring_model",
            "resource://examples/customer_360_model",
            "resource://examples/fraud_aml_model",
            "resource://examples/health_insurance_fraud_model",
        ]

        for resource_uri in example_resources:
            resource = resources.get(resource_uri)
            assert resource is not None
            result = resource.fn()
            assert isinstance(result, str)
            # Should be valid JSON
            import json

            parsed = json.loads(result)
            assert "nodes" in parsed
            assert "relationships" in parsed

    @pytest.mark.asyncio
    async def test_mcp_resource_neo4j_data_ingest_process(
        self, test_mcp_server: FastMCP
    ):
        """Test the Neo4j data ingest process resource."""
        resources = await test_mcp_server.get_resources()
        resource = resources.get("resource://static/neo4j_data_ingest_process")

        assert resource is not None
        result = resource.fn()
        assert isinstance(result, str)
        assert "constraints" in result.lower()
        assert "nodes" in result.lower()
        assert "relationships" in result.lower()

    @pytest.mark.asyncio
    async def test_tool_validation_with_example_models(self, test_mcp_server: FastMCP):
        """Test that example models can be validated using the validation tools."""
        tools = await test_mcp_server.get_tools()
        get_tool = tools.get("get_example_data_model")
        validate_tool = tools.get("validate_data_model")

        assert get_tool is not None
        assert validate_tool is not None

        # Test validation with each example model
        examples = ["patient_journey", "supply_chain", "software_dependency"]

        for example in examples:
            data_model = get_tool.fn(example_name=example).data_model
            validation_result = validate_tool.fn(data_model=data_model)
            assert validation_result is True

    @pytest.mark.asyncio
    async def test_consistency_between_resources_and_tools(
        self, test_mcp_server: FastMCP
    ):
        """Test that resources and tools return consistent data for the same models."""
        tools = await test_mcp_server.get_tools()
        resources = await test_mcp_server.get_resources()

        get_tool = tools.get("get_example_data_model")
        patient_journey_resource = resources.get(
            "resource://examples/patient_journey_model"
        )

        assert get_tool is not None
        assert patient_journey_resource is not None

        # Get model via tool
        tool_model = get_tool.fn(example_name="patient_journey").data_model

        # Get model via resource
        import json

        resource_json = patient_journey_resource.fn()
        resource_data = json.loads(resource_json)

        # Both should have the same number of nodes and relationships
        assert len(tool_model.nodes) == len(resource_data["nodes"])
        assert len(tool_model.relationships) == len(resource_data["relationships"])


class TestNamespacing:
    """Test namespacing functionality."""

    def testformat_namespace(self):
        """Test the format_namespace function behavior."""
        from mcp_neo4j_data_modeling.server import format_namespace

        # Empty namespace
        assert format_namespace("") == ""

        # Namespace without dash
        assert format_namespace("myapp") == "myapp-"

        # Namespace with dash
        assert format_namespace("myapp-") == "myapp-"

        # Complex namespace
        assert format_namespace("company.product") == "company.product-"

    @pytest.mark.asyncio
    async def test_namespace_tool_prefixes(self):
        """Test that tools are correctly prefixed with namespace."""
        from mcp_neo4j_data_modeling.server import create_mcp_server

        # Test with namespace
        namespaced_server = create_mcp_server(namespace="test-ns")
        tools = await namespaced_server.get_tools()

        expected_tools = [
            "test-ns-validate_node",
            "test-ns-validate_relationship",
            "test-ns-validate_data_model",
            "test-ns-load_from_arrows_json",
            "test-ns-export_to_arrows_json",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tools.keys(), (
                f"Expected tool {expected_tool} not found in {list(tools.keys())}"
            )

        # Test without namespace
        default_server = create_mcp_server()
        default_tools = await default_server.get_tools()

        expected_default_tools = [
            "validate_node",
            "validate_relationship",
            "validate_data_model",
            "load_from_arrows_json",
            "export_to_arrows_json",
        ]

        for expected_tool in expected_default_tools:
            assert expected_tool in default_tools.keys(), (
                f"Expected default tool {expected_tool} not found in {list(default_tools.keys())}"
            )

    @pytest.mark.asyncio
    async def test_namespace_tool_functionality(self):
        """Test that namespaced tools function correctly."""
        from mcp_neo4j_data_modeling.data_model import Node, Property
        from mcp_neo4j_data_modeling.server import create_mcp_server

        # Create server with namespace
        namespaced_server = create_mcp_server(namespace="test")
        tools = await namespaced_server.get_tools()

        # Get the namespaced validate_node tool
        validate_tool = tools.get("test-validate_node")
        assert validate_tool is not None

        # Test that the tool works correctly
        test_node = Node(
            label="Person",
            key_property=Property(
                name="id", type="STRING", description="Unique identifier"
            ),
            properties=[
                Property(name="name", type="STRING"),
                Property(name="age", type="INTEGER"),
            ],
        )

        result = validate_tool.fn(node=test_node)
        assert result is True

    @pytest.mark.asyncio
    async def test_multiple_namespace_isolation(self):
        """Test that different namespaces create isolated tool sets."""
        from mcp_neo4j_data_modeling.server import create_mcp_server

        # Create servers with different namespaces
        server_a = create_mcp_server(namespace="app-a")
        server_b = create_mcp_server(namespace="app-b")

        tools_a = await server_a.get_tools()
        tools_b = await server_b.get_tools()

        # Check that each server has its own prefixed tools
        assert "app-a-validate_node" in tools_a.keys()
        assert "app-a-validate_node" not in tools_b.keys()

        assert "app-b-validate_node" in tools_b.keys()
        assert "app-b-validate_node" not in tools_a.keys()

        # Verify they both have the same number of tools (just different prefixes)
        assert len(tools_a) == len(tools_b)
