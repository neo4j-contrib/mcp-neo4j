from pydantic import BaseModel, Field

from .data_model import DataModel


class ExampleDataModelResponse(BaseModel):
    """Response model for the `get_example_data_model` tool."""

    data_model: DataModel = Field(description="The example graph data model.")
    mermaid_config: str = Field(
        description="The Mermaid visualization configuration for the example graph data model."
    )
