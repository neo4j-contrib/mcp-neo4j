"""Integration tests for DataModel Pydantic string generation.

These tests validate that the generated Pydantic model strings are valid Python code
and can be imported and instantiated successfully.
"""

import tempfile
from pathlib import Path

import pytest

from mcp_neo4j_data_modeling.data_model import DataModel, Node, Property, Relationship


def test_generated_node_models_are_valid():
    """Test that generated Node Pydantic models can be imported and instantiated."""
    # Create a data model with multiple nodes
    data_model = DataModel(
        nodes=[
            Node(
                label="User",
                key_property=Property(
                    name="userId", type="STRING", description="User ID"
                ),
                properties=[
                    Property(name="name", type="STRING", description="User name"),
                    Property(name="email", type="STRING", description="Email address"),
                    Property(name="age", type="INTEGER", description="User age"),
                ],
            ),
            Node(
                label="Product",
                key_property=Property(
                    name="productId", type="STRING", description="Product ID"
                ),
                properties=[
                    Property(name="title", type="STRING", description="Product title"),
                    Property(name="price", type="FLOAT", description="Product price"),
                    Property(
                        name="inStock", type="BOOLEAN", description="Stock availability"
                    ),
                ],
            ),
        ],
        relationships=[],
    )

    # Generate Pydantic models string
    pydantic_code = data_model.to_pydantic_model_str()

    # Write to a temporary file and try to import it
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = Path(tmpdir) / "models.py"
        model_file.write_text(pydantic_code)

        # Import the module dynamically
        import importlib.util

        spec = importlib.util.spec_from_file_location("models", model_file)
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)

        # Test User model instantiation
        user = models.User(
            userId="user123", name="John Doe", email="john@example.com", age=30
        )
        assert user.userId == "user123"
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.age == 30

        # Test Product model instantiation
        product = models.Product(
            productId="prod456", title="Widget", price=29.99, inStock=True
        )
        assert product.productId == "prod456"
        assert product.title == "Widget"
        assert product.price == 29.99
        assert product.inStock


def test_generated_relationship_models_are_valid():
    """Test that generated Relationship Pydantic models can be imported and instantiated."""
    # Create a data model with nodes and relationships
    data_model = DataModel(
        nodes=[
            Node(
                label="Person",
                key_property=Property(
                    name="personId", type="STRING", description="Person ID"
                ),
                properties=[],
            ),
            Node(
                label="Company",
                key_property=Property(
                    name="companyId", type="STRING", description="Company ID"
                ),
                properties=[],
            ),
        ],
        relationships=[
            Relationship(
                type="WORKS_FOR",
                start_node_label="Person",
                end_node_label="Company",
                properties=[
                    Property(
                        name="since", type="DATE", description="Employment start date"
                    ),
                    Property(
                        name="position", type="STRING", description="Job position"
                    ),
                ],
            ),
        ],
    )

    # Generate Pydantic models string
    pydantic_code = data_model.to_pydantic_model_str()

    # Write to a temporary file and try to import it
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = Path(tmpdir) / "models.py"
        model_file.write_text(pydantic_code)

        # Import the module dynamically
        import importlib.util
        from datetime import datetime

        spec = importlib.util.spec_from_file_location("models", model_file)
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)

        # Test WorksFor relationship model instantiation
        works_for = models.WorksFor(
            start_node_Person_personId="person123",
            end_node_Company_companyId="company456",
            since=datetime(2020, 1, 15),
            position="Software Engineer",
        )
        assert works_for.start_node_Person_personId == "person123"
        assert works_for.end_node_Company_companyId == "company456"
        assert works_for.since == datetime(2020, 1, 15)
        assert works_for.position == "Software Engineer"

        # Test ClassVar attributes
        assert models.WorksFor.start_node_label == "Person"
        assert models.WorksFor.end_node_label == "Company"


def test_generated_models_with_key_properties():
    """Test that generated models with relationship key properties are valid."""
    data_model = DataModel(
        nodes=[
            Node(
                label="User",
                key_property=Property(
                    name="userId", type="STRING", description="User ID"
                ),
                properties=[],
            ),
            Node(
                label="Post",
                key_property=Property(
                    name="postId", type="STRING", description="Post ID"
                ),
                properties=[],
            ),
        ],
        relationships=[
            Relationship(
                type="AUTHORED",
                start_node_label="User",
                end_node_label="Post",
                key_property=Property(
                    name="authorshipId", type="STRING", description="Authorship ID"
                ),
                properties=[
                    Property(
                        name="publishedAt",
                        type="DATETIME",
                        description="Publish timestamp",
                    ),
                ],
            ),
        ],
    )

    # Generate Pydantic models string
    pydantic_code = data_model.to_pydantic_model_str()

    # Write to a temporary file and try to import it
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = Path(tmpdir) / "models.py"
        model_file.write_text(pydantic_code)

        # Import the module dynamically
        import importlib.util
        from datetime import datetime

        spec = importlib.util.spec_from_file_location("models", model_file)
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)

        # Test Authored relationship model with key property
        authored = models.Authored(
            start_node_User_userId="user123",
            end_node_Post_postId="post456",
            authorshipId="auth789",
            publishedAt=datetime(2024, 1, 1, 12, 0, 0),
        )
        assert authored.start_node_User_userId == "user123"
        assert authored.end_node_Post_postId == "post456"
        assert authored.authorshipId == "auth789"
        assert authored.publishedAt == datetime(2024, 1, 1, 12, 0, 0)


def test_generated_models_with_various_types():
    """Test that generated models with various property types are valid."""
    data_model = DataModel(
        nodes=[
            Node(
                label="Event",
                key_property=Property(
                    name="eventId", type="STRING", description="Event ID"
                ),
                properties=[
                    Property(
                        name="attendees",
                        type="INTEGER",
                        description="Number of attendees",
                    ),
                    Property(name="rating", type="FLOAT", description="Event rating"),
                    Property(name="active", type="BOOLEAN", description="Is active"),
                    Property(
                        name="startTime", type="DATETIME", description="Start time"
                    ),
                    Property(name="tags", type="LIST", description="Event tags"),
                ],
            ),
        ],
        relationships=[],
    )

    # Generate Pydantic models string
    pydantic_code = data_model.to_pydantic_model_str()

    # Write to a temporary file and try to import it
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = Path(tmpdir) / "models.py"
        model_file.write_text(pydantic_code)

        # Import the module dynamically
        import importlib.util
        from datetime import datetime

        spec = importlib.util.spec_from_file_location("models", model_file)
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)

        # Test Event model with various types
        event = models.Event(
            eventId="event123",
            attendees=150,
            rating=4.5,
            active=True,
            startTime=datetime(2024, 6, 15, 18, 30),
            tags=["conference", "tech", "networking"],
        )
        assert event.eventId == "event123"
        assert event.attendees == 150
        assert event.rating == 4.5
        assert event.active
        assert event.startTime == datetime(2024, 6, 15, 18, 30)
        assert event.tags == ["conference", "tech", "networking"]


def test_generated_models_validation():
    """Test that generated Pydantic models properly validate data."""
    data_model = DataModel(
        nodes=[
            Node(
                label="Product",
                key_property=Property(
                    name="productId", type="STRING", description="Product ID"
                ),
                properties=[
                    Property(name="price", type="FLOAT", description="Product price"),
                ],
            ),
        ],
        relationships=[],
    )

    # Generate Pydantic models string
    pydantic_code = data_model.to_pydantic_model_str()

    # Write to a temporary file and try to import it
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = Path(tmpdir) / "models.py"
        model_file.write_text(pydantic_code)

        # Import the module dynamically
        import importlib.util

        from pydantic import ValidationError

        spec = importlib.util.spec_from_file_location("models", model_file)
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)

        # Test that validation works - missing required field should raise error
        with pytest.raises(ValidationError):
            models.Product(productId="prod123")  # Missing required 'price' field

        # Test that valid data works
        product = models.Product(productId="prod123", price=29.99)
        assert product.productId == "prod123"
        assert product.price == 29.99


def test_generated_empty_model():
    """Test that an empty data model generates valid (though minimal) code."""
    data_model = DataModel(nodes=[], relationships=[])

    # Generate Pydantic models string
    pydantic_code = data_model.to_pydantic_model_str()

    # Write to a temporary file and try to import it
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = Path(tmpdir) / "models.py"
        model_file.write_text(pydantic_code)

        # Import the module dynamically - should not raise any errors
        import importlib.util

        spec = importlib.util.spec_from_file_location("models", model_file)
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)

        # Verify imports are present
        assert hasattr(models, "BaseModel")
        assert hasattr(models, "Field")
        # Empty model should not import datetime since no datetime types are used
        assert not hasattr(models, "datetime")


def test_generated_models_screaming_snake_case_conversion():
    """Test that SCREAMING_SNAKE_CASE relationship types are properly converted to PascalCase."""
    data_model = DataModel(
        nodes=[
            Node(
                label="User",
                key_property=Property(
                    name="userId", type="STRING", description="User ID"
                ),
                properties=[],
            ),
        ],
        relationships=[
            Relationship(
                type="BELONGS_TO_GROUP",
                start_node_label="User",
                end_node_label="User",
                properties=[],
            ),
        ],
    )

    # Generate Pydantic models string
    pydantic_code = data_model.to_pydantic_model_str()

    # Write to a temporary file and try to import it
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = Path(tmpdir) / "models.py"
        model_file.write_text(pydantic_code)

        # Import the module dynamically
        import importlib.util

        spec = importlib.util.spec_from_file_location("models", model_file)
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)

        # Verify the class name is PascalCase
        assert hasattr(models, "BelongsToGroup")

        # Test instantiation
        belongs_to_group = models.BelongsToGroup(
            start_node_User_userId="user123", end_node_User_userId="user456"
        )
        assert belongs_to_group.start_node_User_userId == "user123"
        assert belongs_to_group.end_node_User_userId == "user456"


def test_generated_models_with_reserved_keywords():
    """Test that generated models with Python reserved keywords work correctly."""
    data_model = DataModel(
        nodes=[
            Node(
                label="Item",
                key_property=Property(name="id", type="STRING", description="Item ID"),
                properties=[
                    Property(name="class", type="STRING", description="Item class"),
                    Property(name="global", type="BOOLEAN", description="Is global"),
                    Property(name="from", type="STRING", description="Source location"),
                    Property(
                        name="for", type="STRING", description="Intended recipient"
                    ),
                ],
            ),
            Node(
                label="Resource",
                key_property=Property(
                    name="resourceId", type="STRING", description="Resource ID"
                ),
                properties=[],
            ),
        ],
        relationships=[
            Relationship(
                type="RESERVED_FOR",
                start_node_label="Item",
                end_node_label="Resource",
                properties=[
                    Property(name="if", type="BOOLEAN", description="Conditional flag"),
                    Property(name="while", type="INTEGER", description="Duration"),
                ],
            ),
        ],
    )

    # Generate Pydantic models string
    pydantic_code = data_model.to_pydantic_model_str()

    # Write to a temporary file and try to import it
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = Path(tmpdir) / "models.py"
        model_file.write_text(pydantic_code)

        # Import the module dynamically
        import importlib.util

        spec = importlib.util.spec_from_file_location("models", model_file)
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)

        # Test Item model instantiation with reserved keywords using aliases
        item = models.Item(
            id="item123",
            **{
                "class": "premium",
                "global": True,
                "from": "warehouse",
                "for": "customer",
            },
        )

        # Verify the model has underscore-suffixed attributes internally
        assert item.class_ == "premium"
        assert item.global_
        assert item.from_ == "warehouse"
        assert item.for_ == "customer"

        # Verify aliases work correctly in serialization
        dumped = item.model_dump(by_alias=True)
        assert dumped["class"] == "premium"
        assert dumped["global"]
        assert dumped["from"] == "warehouse"
        assert dumped["for"] == "customer"

        # Test ReservedFor relationship model with reserved keywords
        reserved_for = models.ReservedFor(
            start_node_Item_id="item123",
            end_node_Resource_resourceId="resource456",
            **{"if": True, "while": 30},
        )

        # Verify underscore-suffixed attributes
        assert reserved_for.if_
        assert reserved_for.while_ == 30

        # Verify aliases in serialization
        dumped_rel = reserved_for.model_dump(by_alias=True)
        assert dumped_rel["if"]
        assert dumped_rel["while"] == 30


def test_generated_relationship_pattern_class_method():
    """Test that generated relationship models have working pattern() class method."""
    data_model = DataModel(
        nodes=[
            Node(
                label="Person",
                key_property=Property(
                    name="personId", type="STRING", description="Person ID"
                ),
                properties=[],
            ),
            Node(
                label="Company",
                key_property=Property(
                    name="companyId", type="STRING", description="Company ID"
                ),
                properties=[],
            ),
        ],
        relationships=[
            Relationship(
                type="WORKS_FOR",
                start_node_label="Person",
                end_node_label="Company",
                properties=[
                    Property(
                        name="since", type="DATE", description="Employment start date"
                    ),
                ],
            ),
            Relationship(
                type="MANAGES",
                start_node_label="Person",
                end_node_label="Person",
                properties=[],
            ),
        ],
    )

    # Generate Pydantic models string
    pydantic_code = data_model.to_pydantic_model_str()

    # Write to a temporary file and try to import it
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = Path(tmpdir) / "models.py"
        model_file.write_text(pydantic_code)

        # Import the module dynamically
        import importlib.util
        from datetime import datetime

        spec = importlib.util.spec_from_file_location("models", model_file)
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)

        # Test WorksFor relationship pattern ClassVar attribute
        assert hasattr(models.WorksFor, "pattern")
        pattern = models.WorksFor.pattern
        assert pattern == "(:Person)-[:WORKS_FOR]->(:Company)"

        # Test Manages relationship pattern ClassVar attribute (self-referential)
        assert hasattr(models.Manages, "pattern")
        pattern = models.Manages.pattern
        assert pattern == "(:Person)-[:MANAGES]->(:Person)"

        # Verify pattern is consistent with start_node_label and end_node_label
        works_for_start = models.WorksFor.start_node_label
        works_for_end = models.WorksFor.end_node_label
        works_for_pattern = models.WorksFor.pattern
        assert f"(:{works_for_start})" in works_for_pattern
        assert f"(:{works_for_end})" in works_for_pattern
        assert "[:WORKS_FOR]" in works_for_pattern

        # Verify ClassVar attributes are NOT exported in model_dump()
        works_for = models.WorksFor(
            start_node_Person_personId="person123",
            end_node_Company_companyId="company456",
            since=datetime(2020, 1, 15),
        )
        dumped = works_for.model_dump()
        # ClassVar attributes should not be in the dump
        assert "start_node_label" not in dumped
        assert "end_node_label" not in dumped
        assert "pattern" not in dumped
        # Only instance fields should be in the dump
        assert "start_node_Person_personId" in dumped
        assert "end_node_Company_companyId" in dumped
        assert "since" in dumped
