from typing import List, Literal, Optional, TypedDict


class Position(TypedDict):
    x: float
    y: float


class AuraDataImportVisualisationNode(TypedDict):
    id: str
    position: Position


# Property and Type Definitions
class PropertyType(TypedDict):
    type: Literal["string", "integer", "float", "boolean"]


class Property(TypedDict):
    """Property definition with $id, token, type, and nullable fields."""

    __dollar_id: str  # Represents "$id" field
    token: str
    type: PropertyType
    nullable: bool


# Node and Relationship Schema Types
class NodeLabel(TypedDict):
    """Node label definition with properties."""

    __dollar_id: str  # Represents "$id" field
    token: str
    properties: List[Property]


class RelationshipType(TypedDict):
    """Relationship type definition."""

    __dollar_id: str  # Represents "$id" field
    token: str
    properties: List[Property]


class LabelRef(TypedDict):
    """Reference to a node label."""

    __dollar_ref: str  # Represents "$ref" field


class NodeObjectType(TypedDict):
    """Node object type with labels."""

    __dollar_id: str  # Represents "$id" field
    labels: List[LabelRef]


class TypeRef(TypedDict):
    """Reference to a relationship type."""

    __dollar_ref: str  # Represents "$ref" field


class NodeRef(TypedDict):
    """Reference to a node."""

    __dollar_ref: str  # Represents "$ref" field


class RelationshipObjectType(TypedDict):
    """Relationship object type definition."""

    __dollar_id: str  # Represents "$id" field
    type: TypeRef
    __from: NodeRef  # Represents "from" field (Python keyword)
    to: NodeRef


class PropertyRef(TypedDict):
    """Reference to a property."""

    __dollar_ref: str  # Represents "$ref" field


# Constraint and Index Types
class Constraint(TypedDict):
    """Database constraint definition."""

    __dollar_id: str  # Represents "$id" field
    name: str
    constraintType: Literal["uniqueness", "existence", "node_key"]
    entityType: Literal["node", "relationship"]
    nodeLabel: Optional[LabelRef]
    relationshipType: Optional[TypeRef]
    properties: List[PropertyRef]


class Index(TypedDict):
    """Database index definition."""

    __dollar_id: str  # Represents "$id" field
    name: str
    indexType: str
    entityType: Literal["node", "relationship"]
    nodeLabel: Optional[LabelRef]
    relationshipType: Optional[TypeRef]
    properties: List[PropertyRef]


# Graph Schema Types
class GraphSchema(TypedDict):
    """Complete graph schema definition."""

    nodeLabels: List[NodeLabel]
    relationshipTypes: List[RelationshipType]
    nodeObjectTypes: List[NodeObjectType]
    relationshipObjectTypes: List[RelationshipObjectType]
    constraints: List[Constraint]
    indexes: List[Index]


class GraphSchemaRepresentation(TypedDict):
    """Graph schema representation with version."""

    version: str
    graphSchema: GraphSchema


# Graph Schema Extensions
class NodeKeyProperty(TypedDict):
    """Node key property mapping."""

    node: NodeRef
    keyProperty: PropertyRef


class GraphSchemaExtensionsRepresentation(TypedDict):
    """Graph schema extensions."""

    nodeKeyProperties: List[NodeKeyProperty]


# Data Source Schema Types
class RecommendedType(TypedDict):
    """Recommended data type for a field."""

    type: Literal["string", "integer", "float", "boolean"]


class Field(TypedDict):
    """Field definition in a table schema."""

    name: str
    sample: str
    recommendedType: RecommendedType


class TableSchema(TypedDict):
    """Table schema definition."""

    name: str
    fields: List[Field]


class DataSourceSchema(TypedDict):
    """Data source schema definition."""

    type: Literal["local", "remote"]
    tableSchemas: List[TableSchema]


# Mapping Types
class PropertyMapping(TypedDict):
    """Property to field mapping."""

    property: PropertyRef
    fieldName: str


class NodeMapping(TypedDict):
    """Node mapping to table."""

    node: NodeRef
    tableName: str
    propertyMappings: List[PropertyMapping]


class FieldMapping(TypedDict):
    """Field mapping for relationships."""

    fieldName: str


class RelationshipMapping(TypedDict):
    """Relationship mapping to table."""

    relationship: NodeRef
    tableName: str
    propertyMappings: List[PropertyMapping]
    fromMapping: FieldMapping
    toMapping: FieldMapping


class GraphMappingRepresentation(TypedDict):
    """Graph mapping representation."""

    dataSourceSchema: DataSourceSchema
    nodeMappings: List[NodeMapping]
    relationshipMappings: List[RelationshipMapping]


# Configuration Types
class Configurations(TypedDict):
    """Configuration settings."""

    idsToIgnore: List[str]


# Main Data Model Types
class DataModelContent(TypedDict):
    """Data model content structure."""

    version: str
    graphSchemaRepresentation: GraphSchemaRepresentation
    graphSchemaExtensionsRepresentation: GraphSchemaExtensionsRepresentation
    graphMappingRepresentation: GraphMappingRepresentation
    configurations: Configurations


class AuraDataImportDataModel(TypedDict):
    """Complete Aura Data Import model structure."""

    version: str
    visualisation: List[AuraDataImportVisualisationNode]
    dataModel: DataModelContent
