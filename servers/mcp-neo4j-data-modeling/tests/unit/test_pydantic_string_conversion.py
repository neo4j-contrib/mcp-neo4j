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

        # Expected format: 'name: str = Field(..., description="The name of the property")'
        assert "name:" in result
        assert "str" in result
        assert 'Field(..., description="The name of the property")' in result

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

    def test_node_with_description(self):
        """Test converting a Node with description to Pydantic model string with docstring."""
        node = Node(
            label="Person",
            key_property=Property(
                name="id", type="STRING", description="The ID of the person"
            ),
            properties=[
                Property(
                    name="name", type="STRING", description="The name of the person"
                ),
            ],
            description="Represents a person in the system",
        )
        result = node.to_pydantic_model_str()

        assert "class Person(BaseModel):" in result
        assert '"""Represents a person in the system"""' in result
        assert "id:" in result
        assert "name:" in result

    def test_node_without_description(self):
        """Test converting a Node without description has no docstring."""
        node = Node(
            label="Person",
            key_property=Property(name="id", type="STRING"),
            properties=[],
        )
        result = node.to_pydantic_model_str()

        assert "class Person(BaseModel):" in result
        assert '"""' not in result

    def test_node_with_description_containing_triple_quotes(self):
        """Test converting a Node with description containing triple quotes."""
        node = Node(
            label="Person",
            key_property=Property(name="id", type="STRING"),
            properties=[],
            description='This is a """special""" description',
        )
        result = node.to_pydantic_model_str()

        assert "class Person(BaseModel):" in result
        # Should escape the triple quotes
        assert r"\"\"\"" in result or "special" in result


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
        # Fields should be prefixed with start_node_ and end_node_
        assert "start_node_Person_personId:" in result
        assert "end_node_Person_personId:" in result
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
        assert "start_node_Person_personId:" in result
        assert "end_node_Company_companyId:" in result

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
        assert "start_node_Customer_customerId:" in result
        assert "end_node_Product_productId:" in result

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
        assert "start_node_User_userId:" in result
        assert "end_node_Movie_movieId:" in result

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
        assert "start_node_Person_personId:" in result
        assert "end_node_City_cityId:" in result

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
        assert "start_node_Researcher_researcherId:" in result
        assert "end_node_Project_projectId:" in result

    def test_relationship_with_description(self):
        """Test converting a Relationship with description to Pydantic model string with docstring."""
        relationship = Relationship(
            type="WORKS_FOR",
            start_node_label="Person",
            end_node_label="Company",
            properties=[
                Property(
                    name="startDate", type="DATE", description="Employment start date"
                ),
            ],
            description="Represents an employment relationship between a person and a company",
        )
        start_key_prop = Property(name="personId", type="STRING")
        end_key_prop = Property(name="companyId", type="STRING")
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "class WorksFor(BaseModel):" in result
        assert (
            '"""Represents an employment relationship between a person and a company"""'
            in result
        )
        assert "startDate:" in result

    def test_relationship_without_description(self):
        """Test converting a Relationship without description has no docstring."""
        relationship = Relationship(
            type="KNOWS",
            start_node_label="Person",
            end_node_label="Person",
            properties=[],
        )
        start_key_prop = Property(name="personId", type="STRING")
        end_key_prop = Property(name="personId", type="STRING")
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "class Knows(BaseModel):" in result
        assert '"""' not in result

    def test_relationship_with_description_containing_triple_quotes(self):
        """Test converting a Relationship with description containing triple quotes."""
        relationship = Relationship(
            type="RELATED_TO",
            start_node_label="Node",
            end_node_label="Node",
            properties=[],
            description='A """special""" relationship type',
        )
        start_key_prop = Property(name="id", type="STRING")
        end_key_prop = Property(name="id", type="STRING")
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "class RelatedTo(BaseModel):" in result
        # Should escape the triple quotes
        assert r"\"\"\"" in result or "special" in result


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
        assert "start_node_Person_personId:" in result
        assert "end_node_Person_personId:" in result

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
        assert "start_node_User_userId:" in result
        assert "end_node_Post_postId:" in result


class TestPydanticStringConversionReservedKeywords:
    """Test handling of Python reserved keywords in Pydantic string conversion."""

    def test_property_reserved_keyword_class(self):
        """Test Property with reserved keyword 'class'."""
        prop = Property(
            name="class", type="STRING", description="The class of the item"
        )
        result = prop.to_pydantic_model_str()

        assert "class_:" in result
        assert "str" in result
        assert 'alias="class"' in result
        assert "The class of the item" in result

    def test_property_reserved_keyword_global(self):
        """Test Property with reserved keyword 'global'."""
        prop = Property(name="global", type="BOOLEAN", description="Is global")
        result = prop.to_pydantic_model_str()

        assert "global_:" in result
        assert "bool" in result
        assert 'alias="global"' in result
        assert "Is global" in result

    def test_property_reserved_keyword_for(self):
        """Test Property with reserved keyword 'for'."""
        prop = Property(name="for", type="STRING", description="Target purpose")
        result = prop.to_pydantic_model_str()

        assert "for_:" in result
        assert "str" in result
        assert 'alias="for"' in result
        assert "Target purpose" in result

    def test_property_reserved_keyword_from(self):
        """Test Property with reserved keyword 'from'."""
        prop = Property(name="from", type="STRING", description="Source location")
        result = prop.to_pydantic_model_str()

        assert "from_:" in result
        assert "str" in result
        assert 'alias="from"' in result
        assert "Source location" in result

    def test_property_reserved_keyword_without_description(self):
        """Test Property with reserved keyword but no description."""
        prop = Property(name="if", type="STRING")
        result = prop.to_pydantic_model_str()

        assert "if_:" in result
        assert "str" in result
        assert 'alias="if"' in result
        # Should still have Field with alias even without description
        assert "Field(..., alias=" in result

    def test_property_reserved_keyword_with_various_types(self):
        """Test reserved keywords with different property types."""
        # INTEGER type
        prop_int = Property(name="while", type="INTEGER", description="Loop count")
        result_int = prop_int.to_pydantic_model_str()
        assert "while_: int" in result_int
        assert 'alias="while"' in result_int

        # DATETIME type
        prop_dt = Property(name="async", type="DATETIME", description="Async time")
        result_dt = prop_dt.to_pydantic_model_str()
        assert "async_: datetime" in result_dt
        assert 'alias="async"' in result_dt

    def test_node_with_reserved_keywords(self):
        """Test Node with properties that are reserved keywords."""
        node = Node(
            label="Item",
            key_property=Property(name="id", type="STRING", description="Item ID"),
            properties=[
                Property(name="class", type="STRING", description="Item class"),
                Property(
                    name="type", type="STRING", description="Item type"
                ),  # not a keyword
                Property(name="global", type="BOOLEAN", description="Is global"),
            ],
        )
        result = node.to_pydantic_model_str()

        assert "class Item(BaseModel):" in result
        assert "id:" in result
        assert "class_:" in result
        assert 'alias="class"' in result
        assert "type:" in result  # not a keyword, should be normal
        assert 'alias="type"' not in result
        assert "global_:" in result
        assert 'alias="global"' in result

    def test_relationship_with_reserved_keyword_properties(self):
        """Test Relationship with properties that are reserved keywords."""
        relationship = Relationship(
            type="IMPORTS",
            start_node_label="Module",
            end_node_label="Package",
            properties=[
                Property(name="from", type="STRING", description="Import source"),
                Property(name="as", type="STRING", description="Import alias"),
            ],
        )
        start_key_prop = Property(
            name="moduleId", type="STRING", description="Module ID"
        )
        end_key_prop = Property(
            name="packageId", type="STRING", description="Package ID"
        )
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "class Imports(BaseModel):" in result
        assert "from_:" in result
        assert 'alias="from"' in result
        assert "as_:" in result
        assert 'alias="as"' in result

    def test_relationship_key_property_reserved_keyword(self):
        """Test Relationship with key property that is a reserved keyword."""
        relationship = Relationship(
            type="YIELDS",
            start_node_label="Function",
            end_node_label="Result",
            key_property=Property(
                name="yield", type="STRING", description="Yield identifier"
            ),
            properties=[],
        )
        start_key_prop = Property(
            name="functionId", type="STRING", description="Function ID"
        )
        end_key_prop = Property(name="resultId", type="STRING", description="Result ID")
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "class Yields(BaseModel):" in result
        assert "yield_:" in result
        assert 'alias="yield"' in result

    def test_multiple_reserved_keywords_field_order(self):
        """Test that Field parameters are in correct order when both description and alias are present."""
        prop = Property(name="class", type="STRING", description="Object class")
        result = prop.to_pydantic_model_str()

        # Should have: Field(..., description="...", alias="...")
        assert 'Field(..., description="Object class", alias="class")' in result


class TestRelationshipPatternClassMethod:
    """Test the pattern() class method in generated Relationship Pydantic models."""

    def test_relationship_includes_pattern_method(self):
        """Test that generated relationship includes pattern ClassVar attribute."""
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

        assert "pattern: ClassVar[str]" in result
        assert 'pattern: ClassVar[str] = "(:Person)-[:KNOWS]->(:Person)"' in result

    def test_relationship_pattern_different_nodes(self):
        """Test pattern ClassVar with different start and end nodes."""
        relationship = Relationship(
            type="WORKS_FOR",
            start_node_label="Employee",
            end_node_label="Company",
            properties=[],
        )
        start_key_prop = Property(
            name="employeeId", type="STRING", description="Employee ID"
        )
        end_key_prop = Property(
            name="companyId", type="STRING", description="Company ID"
        )
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "pattern: ClassVar[str]" in result
        assert (
            'pattern: ClassVar[str] = "(:Employee)-[:WORKS_FOR]->(:Company)"' in result
        )

    def test_relationship_pattern_screaming_snake_case(self):
        """Test pattern ClassVar preserves SCREAMING_SNAKE_CASE in pattern."""
        relationship = Relationship(
            type="HAS_MANY_ITEMS",
            start_node_label="Cart",
            end_node_label="Item",
            properties=[],
        )
        start_key_prop = Property(name="cartId", type="STRING", description="Cart ID")
        end_key_prop = Property(name="itemId", type="STRING", description="Item ID")
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        # Pattern should preserve original SCREAMING_SNAKE_CASE
        assert 'pattern: ClassVar[str] = "(:Cart)-[:HAS_MANY_ITEMS]->(:Item)"' in result

    def test_relationship_pattern_with_properties(self):
        """Test that pattern ClassVar is included even when relationship has properties."""
        relationship = Relationship(
            type="REVIEWED",
            start_node_label="User",
            end_node_label="Product",
            properties=[
                Property(name="rating", type="INTEGER", description="Rating"),
                Property(name="comment", type="STRING", description="Comment"),
            ],
        )
        start_key_prop = Property(name="userId", type="STRING", description="User ID")
        end_key_prop = Property(
            name="productId", type="STRING", description="Product ID"
        )
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "pattern: ClassVar[str]" in result
        assert 'pattern: ClassVar[str] = "(:User)-[:REVIEWED]->(:Product)"' in result

    def test_relationship_pattern_with_key_property(self):
        """Test that pattern ClassVar is included when relationship has a key property."""
        relationship = Relationship(
            type="PURCHASED",
            start_node_label="Customer",
            end_node_label="Item",
            key_property=Property(
                name="transactionId", type="STRING", description="Transaction ID"
            ),
            properties=[],
        )
        start_key_prop = Property(
            name="customerId", type="STRING", description="Customer ID"
        )
        end_key_prop = Property(name="itemId", type="STRING", description="Item ID")
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        assert "pattern: ClassVar[str]" in result
        assert 'pattern: ClassVar[str] = "(:Customer)-[:PURCHASED]->(:Item)"' in result

    def test_relationship_all_class_methods_present(self):
        """Test that all three ClassVar attributes are present: start_node_label, end_node_label, pattern."""
        relationship = Relationship(
            type="FOLLOWS",
            start_node_label="User",
            end_node_label="User",
            properties=[],
        )
        start_key_prop = Property(name="userId", type="STRING", description="User ID")
        end_key_prop = Property(name="userId", type="STRING", description="User ID")
        result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

        # Check all three ClassVar attributes are present
        assert 'start_node_label: ClassVar[str] = "User"' in result
        assert 'end_node_label: ClassVar[str] = "User"' in result
        assert 'pattern: ClassVar[str] = "(:User)-[:FOLLOWS]->(:User)"' in result
