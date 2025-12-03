"""Unit tests for Pydantic string conversion methods in Property, Node, and Relationship classes."""

from mcp_neo4j_data_modeling.data_model import Node, Property, Relationship


class TestPropertyToPydanticModelStr:
    """Test Property.to_pydantic_model_str() method."""

    def test_property_with_description(self):
        """Test converting a Property with description to Pydantic model field string."""
        prop = Property(
            name="name", type="STRING", description="The name of the property"
        )
        result = prop.to_pydantic_model_str()

        # Expected format: "name: str = Field(..., description='The name of the property')"
        assert "name:" in result
        assert "str" in result
        assert "Field(..., description='The name of the property')" in result

    def test_property_without_description(self):
        """Test converting a Property without description to Pydantic model field string."""
        prop = Property(name="id", type="STRING")
        result = prop.to_pydantic_model_str()

        # Expected format: "id: str"
        assert "id:" in result
        assert "str" in result
        # Should not have Field when no description
        assert "Field" not in result or result == "id: str"

    def test_property_integer_type(self):
        """Test converting a Property with INTEGER type."""
        prop = Property(name="age", type="INTEGER", description="Age in years")
        result = prop.to_pydantic_model_str()

        assert "age:" in result
        assert "int" in result
        assert "Age in years" in result

    def test_property_float_type(self):
        """Test converting a Property with FLOAT type."""
        prop = Property(name="price", type="FLOAT", description="Price amount")
        result = prop.to_pydantic_model_str()

        assert "price:" in result
        assert "float" in result
        assert "Price amount" in result

    def test_property_boolean_type(self):
        """Test converting a Property with BOOLEAN type."""
        prop = Property(name="isActive", type="BOOLEAN", description="Active status")
        result = prop.to_pydantic_model_str()

        assert "isActive:" in result
        assert "bool" in result
        assert "Active status" in result

    def test_property_date_type(self):
        """Test converting a Property with DATE type."""
        prop = Property(name="birthDate", type="DATE", description="Birth date")
        result = prop.to_pydantic_model_str()

        assert "birthDate:" in result
        assert "datetime" in result
        assert "Birth date" in result

    def test_property_datetime_type(self):
        """Test converting a Property with DATETIME type."""
        prop = Property(name="createdAt", type="DATETIME", description="Creation time")
        result = prop.to_pydantic_model_str()

        assert "createdAt:" in result
        assert "datetime" in result
        assert "Creation time" in result

    def test_property_list_type(self):
        """Test converting a Property with LIST type."""
        prop = Property(name="tags", type="LIST", description="List of tags")
        result = prop.to_pydantic_model_str()

        assert "tags:" in result
        assert "list" in result
        assert "List of tags" in result

    def test_property_unknown_type_defaults_to_str(self):
        """Test converting a Property with unknown type defaults to str."""
        prop = Property(
            name="customField", type="UNKNOWN_TYPE", description="Custom field"
        )
        result = prop.to_pydantic_model_str()

        assert "customField:" in result
        assert "str" in result
        assert "Custom field" in result

    def test_property_special_characters_in_description(self):
        """Test converting a Property with special characters in description."""
        prop = Property(
            name="field",
            type="STRING",
            description="A field with 'quotes' and \"double quotes\"",
        )
        result = prop.to_pydantic_model_str()

        assert "field:" in result
        assert "str" in result
        # The description should be properly handled
        assert "quotes" in result


class TestNodeToPydanticModelStr:
    """Test Node.to_pydantic_model_str() method."""

    def test_node_with_key_property_only(self):
        """Test converting a Node with only key property to Pydantic model string."""
        node = Node(
            label="Person",
            key_property=Property(
                name="id", type="STRING", description="Unique identifier"
            ),
            properties=[],
        )
        result = node.to_pydantic_model_str()

        assert "class Person(BaseModel):" in result
        assert "id:" in result
        assert "str" in result
        assert "Unique identifier" in result

    def test_node_with_multiple_properties(self):
        """Test converting a Node with multiple properties to Pydantic model string."""
        node = Node(
            label="Person",
            key_property=Property(
                name="id", type="STRING", description="The ID of the person"
            ),
            properties=[
                Property(
                    name="name", type="STRING", description="The name of the person"
                ),
                Property(name="age", type="INTEGER", description="Age in years"),
            ],
        )
        result = node.to_pydantic_model_str()

        assert "class Person(BaseModel):" in result
        assert "id:" in result
        assert "name:" in result
        assert "age:" in result
        assert "str" in result
        assert "int" in result
        assert "The ID of the person" in result
        assert "The name of the person" in result
        assert "Age in years" in result

    def test_node_with_various_property_types(self):
        """Test converting a Node with various property types."""
        node = Node(
            label="Product",
            key_property=Property(
                name="productId", type="STRING", description="Product ID"
            ),
            properties=[
                Property(name="price", type="FLOAT", description="Product price"),
                Property(
                    name="inStock", type="BOOLEAN", description="Stock availability"
                ),
                Property(name="tags", type="LIST", description="Product tags"),
                Property(
                    name="createdAt", type="DATETIME", description="Creation timestamp"
                ),
            ],
        )
        result = node.to_pydantic_model_str()

        assert "class Product(BaseModel):" in result
        assert "productId:" in result
        assert "price:" in result
        assert "inStock:" in result
        assert "tags:" in result
        assert "createdAt:" in result

    def test_node_camel_case_label(self):
        """Test converting a Node with PascalCase label."""
        node = Node(
            label="UserAccount",
            key_property=Property(
                name="accountId", type="STRING", description="Account ID"
            ),
            properties=[],
        )
        result = node.to_pydantic_model_str()

        assert "class UserAccount(BaseModel):" in result

    def test_node_properties_without_descriptions(self):
        """Test converting a Node with properties that don't have descriptions."""
        node = Node(
            label="SimpleNode",
            key_property=Property(name="id", type="STRING"),
            properties=[
                Property(name="field1", type="STRING"),
                Property(name="field2", type="INTEGER"),
            ],
        )
        result = node.to_pydantic_model_str()

        assert "class SimpleNode(BaseModel):" in result
        assert "id:" in result
        assert "field1:" in result
        assert "field2:" in result


class TestRelationshipToPydanticModelStr:
    """Test Relationship.to_pydantic_model_str() method."""

    def test_relationship_without_key_property_or_properties(self):
        """Test converting a basic Relationship to Pydantic model string."""
        relationship = Relationship(
            type="KNOWS",
            start_node_label="Person",
            end_node_label="Person",
            properties=[],
        )
        start_key_prop = Property(
            name="personId", type="STRING", description="Person ID"
        )
        end_key_prop = Property(name="personId", type="STRING", description="Person ID")
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        # Class name should be PascalCase version of SCREAMING_SNAKE_CASE
        assert "class Knows(BaseModel):" in result
        # Fields should be prefixed with source_ and target_
        assert "source_personId:" in result
        assert "target_personId:" in result
        # Should include description from properties
        assert "Person ID" in result

    def test_relationship_with_key_property(self):
        """Test converting a Relationship with key property to Pydantic model string."""
        relationship = Relationship(
            type="WORKS_FOR",
            start_node_label="Person",
            end_node_label="Company",
            key_property=Property(
                name="employmentId", type="STRING", description="Employment ID"
            ),
            properties=[],
        )
        start_key_prop = Property(
            name="personId", type="STRING", description="Person ID"
        )
        end_key_prop = Property(
            name="companyId", type="STRING", description="Company ID"
        )
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "class WorksFor(BaseModel):" in result
        assert "employmentId:" in result
        assert "Employment ID" in result
        assert "source_personId:" in result
        assert "target_companyId:" in result

    def test_relationship_with_properties(self):
        """Test converting a Relationship with properties to Pydantic model string."""
        relationship = Relationship(
            type="PURCHASED",
            start_node_label="Customer",
            end_node_label="Product",
            properties=[
                Property(
                    name="purchaseDate", type="DATETIME", description="Date of purchase"
                ),
                Property(
                    name="quantity", type="INTEGER", description="Quantity purchased"
                ),
                Property(name="price", type="FLOAT", description="Purchase price"),
            ],
        )
        start_key_prop = Property(
            name="customerId", type="STRING", description="Customer ID"
        )
        end_key_prop = Property(
            name="productId", type="STRING", description="Product ID"
        )
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "class Purchased(BaseModel):" in result
        assert "purchaseDate:" in result
        assert "quantity:" in result
        assert "price:" in result
        assert "Date of purchase" in result
        assert "Quantity purchased" in result
        assert "Purchase price" in result
        assert "source_customerId:" in result
        assert "target_productId:" in result

    def test_relationship_with_key_property_and_properties(self):
        """Test converting a Relationship with both key property and other properties."""
        relationship = Relationship(
            type="RATED",
            start_node_label="User",
            end_node_label="Movie",
            key_property=Property(
                name="ratingId", type="STRING", description="Rating ID"
            ),
            properties=[
                Property(name="score", type="INTEGER", description="Rating score"),
                Property(name="comment", type="STRING", description="Review comment"),
            ],
        )
        start_key_prop = Property(name="userId", type="STRING", description="User ID")
        end_key_prop = Property(name="movieId", type="STRING", description="Movie ID")
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "class Rated(BaseModel):" in result
        assert "ratingId:" in result
        assert "score:" in result
        assert "comment:" in result
        assert "source_userId:" in result
        assert "target_movieId:" in result

    def test_relationship_screaming_snake_case_to_pascal_case(self):
        """Test that relationship type is converted from SCREAMING_SNAKE_CASE to PascalCase."""
        relationship = Relationship(
            type="HAS_MANY_ITEMS",
            start_node_label="Cart",
            end_node_label="Item",
            properties=[],
        )
        start_key_prop = Property(name="cartId", type="STRING", description="Cart ID")
        end_key_prop = Property(name="itemId", type="STRING", description="Item ID")
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "class HasManyItems(BaseModel):" in result

    def test_relationship_includes_node_references(self):
        """Test that relationship includes start and end node references."""
        relationship = Relationship(
            type="LIVES_IN",
            start_node_label="Person",
            end_node_label="City",
            properties=[],
        )
        start_key_prop = Property(
            name="personId", type="STRING", description="Person ID"
        )
        end_key_prop = Property(name="cityId", type="STRING", description="City ID")
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        # Should include references to start and end node key properties
        assert "source_personId:" in result
        assert "target_cityId:" in result

    def test_relationship_complex_scenario(self):
        """Test a complex relationship with multiple properties and types."""
        relationship = Relationship(
            type="COLLABORATED_ON",
            start_node_label="Researcher",
            end_node_label="Project",
            key_property=Property(
                name="collaborationId", type="STRING", description="Collaboration ID"
            ),
            properties=[
                Property(name="startDate", type="DATE", description="Start date"),
                Property(name="endDate", type="DATE", description="End date"),
                Property(name="role", type="STRING", description="Role in project"),
                Property(
                    name="hoursContributed",
                    type="INTEGER",
                    description="Hours contributed",
                ),
                Property(
                    name="isActive",
                    type="BOOLEAN",
                    description="Is collaboration active",
                ),
            ],
        )
        start_key_prop = Property(
            name="researcherId", type="STRING", description="Researcher ID"
        )
        end_key_prop = Property(
            name="projectId", type="STRING", description="Project ID"
        )
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "class CollaboratedOn(BaseModel):" in result
        assert "collaborationId:" in result
        assert "startDate:" in result
        assert "endDate:" in result
        assert "role:" in result
        assert "hoursContributed:" in result
        assert "isActive:" in result
        assert "source_researcherId:" in result
        assert "target_projectId:" in result


class TestPydanticStringConversionEdgeCases:
    """Test edge cases and error scenarios for Pydantic string conversion."""

    def test_property_with_empty_description(self):
        """Test Property with empty string as description."""
        prop = Property(name="field", type="STRING", description="")
        result = prop.to_pydantic_model_str()

        assert "field:" in result
        assert "str" in result

    def test_node_with_empty_properties_list(self):
        """Test Node with explicitly empty properties list."""
        node = Node(
            label="EmptyNode",
            key_property=Property(name="id", type="STRING"),
            properties=[],
        )
        result = node.to_pydantic_model_str()

        assert "class EmptyNode(BaseModel):" in result
        assert "id:" in result

    def test_relationship_same_start_and_end_nodes(self):
        """Test Relationship where start and end nodes are the same (self-referential)."""
        relationship = Relationship(
            type="FRIENDS_WITH",
            start_node_label="Person",
            end_node_label="Person",
            properties=[
                Property(name="since", type="DATE", description="Friends since")
            ],
        )
        start_key_prop = Property(
            name="personId", type="STRING", description="Person ID"
        )
        end_key_prop = Property(name="personId", type="STRING", description="Person ID")
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "class FriendsWith(BaseModel):" in result
        assert "since:" in result
        assert "source_personId:" in result
        assert "target_personId:" in result

    def test_property_type_case_insensitive(self):
        """Test that property type is case-insensitive (validator uppercases it)."""
        prop = Property(name="field", type="string", description="Test field")
        result = prop.to_pydantic_model_str()

        # Type should be converted to uppercase internally
        assert "field:" in result
        assert "str" in result

    def test_node_single_word_label(self):
        """Test Node with single word label."""
        node = Node(
            label="User",
            key_property=Property(name="userId", type="STRING"),
            properties=[],
        )
        result = node.to_pydantic_model_str()

        assert "class User(BaseModel):" in result

    def test_relationship_single_word_type(self):
        """Test Relationship with single word type."""
        relationship = Relationship(
            type="LIKES", start_node_label="User", end_node_label="Post", properties=[]
        )
        start_key_prop = Property(name="userId", type="STRING", description="User ID")
        end_key_prop = Property(name="postId", type="STRING", description="Post ID")
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "class Likes(BaseModel):" in result
        assert "source_userId:" in result
        assert "target_postId:" in result
