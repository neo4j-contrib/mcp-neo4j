import json
from collections import Counter
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from .aura_data_import import models as AuraDataImportModels

NODE_COLOR_PALETTE = [
    ("#e3f2fd", "#1976d2"),  # Light Blue / Blue
    ("#f3e5f5", "#7b1fa2"),  # Light Purple / Purple
    ("#e8f5e8", "#388e3c"),  # Light Green / Green
    ("#fff3e0", "#f57c00"),  # Light Orange / Orange
    ("#fce4ec", "#c2185b"),  # Light Pink / Pink
    ("#e0f2f1", "#00695c"),  # Light Teal / Teal
    ("#f1f8e9", "#689f38"),  # Light Lime / Lime
    ("#fff8e1", "#ffa000"),  # Light Amber / Amber
    ("#e8eaf6", "#3f51b5"),  # Light Indigo / Indigo
    ("#efebe9", "#5d4037"),  # Light Brown / Brown
    ("#fafafa", "#424242"),  # Light Grey / Dark Grey
    ("#e1f5fe", "#0277bd"),  # Light Cyan / Cyan
    ("#f9fbe7", "#827717"),  # Light Yellow-Green / Olive
    ("#fff1f0", "#d32f2f"),  # Light Red / Red
    ("#f4e6ff", "#6a1b9a"),  # Light Violet / Violet
    ("#e6f7ff", "#1890ff"),  # Very Light Blue / Bright Blue
]


def _generate_relationship_pattern(
    start_node_label: str, relationship_type: str, end_node_label: str
) -> str:
    "Helper function to generate a pattern for a relationship."
    return f"(:{start_node_label})-[:{relationship_type}]->(:{end_node_label})"


class PropertySource(BaseModel):
    "The source of a property."

    column_name: str | None = Field(
        default=None, description="The column name this property maps to, if known."
    )
    table_name: str | None = Field(
        default=None,
        description="The name of the table this property's column is in, if known. May also be the name of a file.",
    )
    location: str | None = Field(
        default=None,
        description="The location of the property, if known. May be a file path, URL, etc.",
    )
    source_type: Literal["local", "remote"] | None = Field(
        default=None,
        description="The type of the data source: 'local' or 'remote'. 'local' means the data source is a file or database table on the local machine. 'remote' means the data source is a file or database table on a remote machine.",
    )


class Property(BaseModel):
    "A Neo4j Property."

    name: str = Field(description="The name of the property. Should be in camelCase.")
    type: str = Field(
        default="STRING",
        description="The Neo4j type of the property. Should be all caps.",
    )
    source: PropertySource | None = Field(
        default=None,
        description="The source of the property, if known. For example this may be a CSV file or a database table. This should always be provided if possible, especially when exporting data models to the Aura Data Import format.",
    )
    description: str | None = Field(
        default=None, description="The description of the property."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="The metadata of the property. This should only be used when converting data models.",
    )

    @field_validator("type")
    def validate_type(cls, v: str) -> str:
        "Validate the type."

        return v.upper()

    @classmethod
    def from_arrows(cls, arrows_property: dict[str, str]) -> "Property":
        "Convert an Arrows Property in dict format to a Property."

        description = None

        if "|" in list(arrows_property.values())[0]:
            prop_props = [
                x.strip() for x in list(arrows_property.values())[0].split("|")
            ]

            prop_type = prop_props[0]
            description = prop_props[1] if prop_props[1].lower() != "key" else None
        else:
            prop_type = list(arrows_property.values())[0]

        return cls(
            name=list(arrows_property.keys())[0],
            type=prop_type,
            description=description,
        )

    def to_arrows(self, is_key: bool = False) -> dict[str, Any]:
        "Convert a Property to an Arrows property dictionary. Final JSON string formatting is done at the data model level."
        value = f"{self.type}"
        if self.description:
            value += f" | {self.description}"
        if is_key:
            value += " | KEY"
        return {
            self.name: value,
        }

    @classmethod
    def from_aura_data_import(
        cls,
        aura_data_import_property: AuraDataImportModels.Property,
        source_mapping: dict[str, Any],
    ) -> "Property":
        """
        Convert an Aura Data Import Property to a Property.

        Parameters
        ----------
        aura_data_import_property : AuraProperty
            The Aura Data Import property with structure:
            {
                "$id": "p:4",
                "token": "currency",
                "type": "string",
                "nullable": true
            }
        source_mapping : dict[str, Any]
            Source mapping information with structure:
            {
                "tableName": "countries.csv",
                "fieldName": "currency",
                "type": "local",
                "source_type": "local"
            }
        """
        # Map Neo4j Data Importer types to our internal types
        type_mapping = {
            "string": "STRING",
            "integer": "INTEGER",
            "float": "FLOAT",
            "boolean": "BOOLEAN",
        }

        prop_type = aura_data_import_property["type"]["type"]
        mapped_type = type_mapping.get(prop_type, prop_type.upper())

        source = PropertySource(
            column_name=source_mapping.get("fieldName", None),
            table_name=source_mapping.get("tableName", None),
            location=source_mapping.get("type", None),
            source_type=source_mapping.get("source_type", "local"),
        )

        # Create property with nullable and original ID stored in metadata
        return cls(
            name=aura_data_import_property["token"],
            type=mapped_type,
            description=None,  # Aura Data Import doesn't have descriptions
            source=source,
            metadata={
                "aura_data_import": {
                    "nullable": aura_data_import_property.get("nullable", False),
                    "original_id": aura_data_import_property.get("$id"),
                }
            },
        )

    def to_aura_data_import(
        self, property_id: str, is_key: bool = False
    ) -> AuraDataImportModels.Property:
        """
        Convert a Property to Aura Data Import format.
        """
        # Map our internal types to Neo4j Data Importer types
        type_mapping = {
            "STRING": "string",
            "INTEGER": "integer",
            "FLOAT": "float",
            "BOOLEAN": "boolean",
        }

        mapped_type = type_mapping.get(
            self.type, "string"
        )  # Default to string if type is not found

        # Use stored nullable value from metadata, or default based on key property
        nullable = self.metadata.get("aura_data_import", {}).get("nullable", not is_key)

        return {
            "$id": property_id,
            "token": self.name,
            "type": {"type": mapped_type},
            "nullable": nullable,
        }


class Node(BaseModel):
    "A Neo4j Node."

    label: str = Field(
        description="The label of the node. Should be in PascalCase.", min_length=1
    )
    key_property: Property = Field(
        description="The key property of the node. This must exist!"
    )
    properties: list[Property] = Field(
        default_factory=list,
        description="The other properties of the node. The key property is not included here.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="The metadata of the node. This should only be used when converting data models.",
    )

    @field_validator("properties")
    def validate_properties(
        cls, properties: list[Property], info: ValidationInfo
    ) -> list[Property]:
        "Validate the properties."
        properties = [p for p in properties if p.name != info.data["key_property"].name]

        counts = Counter([p.name for p in properties])
        for name, count in counts.items():
            if count > 1:
                raise ValueError(
                    f"Property {name} appears {count} times in node {info.data['label']}"
                )
        return properties

    def add_property(self, prop: Property) -> None:
        "Add a new property to the node."
        if prop.name in [p.name for p in self.properties]:
            raise ValueError(
                f"Property {prop.name} already exists in node {self.label}"
            )
        self.properties.append(prop)

    def remove_property(self, prop: Property) -> None:
        "Remove a property from the node."
        try:
            self.properties.remove(prop)
        except ValueError:
            pass

    @property
    def all_properties_dict(self) -> dict[str, str]:
        "Return a dictionary of all properties of the node. {property_name: property_type}"
        props = {p.name: p.type for p in self.properties} if self.properties else {}
        if self.key_property:
            props.update({self.key_property.name: f"{self.key_property.type} | KEY"})
        return props

    def get_mermaid_config_str(self) -> str:
        "Get the Mermaid configuration string for the node."
        props = [f"<br/>{self.key_property.name}: {self.key_property.type} | KEY"]
        props.extend([f"<br/>{p.name}: {p.type}" for p in self.properties])
        return f'{self.label}["{self.label}{"".join(props)}"]'

    @classmethod
    def from_arrows(cls, arrows_node_dict: dict[str, Any]) -> "Node":
        "Convert an Arrows Node to a Node."
        props = [
            Property.from_arrows({k: v})
            for k, v in arrows_node_dict["properties"].items()
            if "KEY" not in v.upper()
        ]
        keys = [
            {k: v}
            for k, v in arrows_node_dict["properties"].items()
            if "KEY" in v.upper()
        ]
        key_prop = Property.from_arrows(keys[0]) if keys else None
        metadata = {
            "position": arrows_node_dict["position"],
            "caption": arrows_node_dict["caption"],
            "style": arrows_node_dict["style"],
        }
        return cls(
            label=arrows_node_dict["labels"][0],
            key_property=key_prop,
            properties=props,
            metadata=metadata,
        )

    def to_arrows(
        self, default_position: dict[str, float] = {"x": 0.0, "y": 0.0}
    ) -> dict[str, Any]:
        "Convert a Node to an Arrows Node dictionary. Final JSON string formatting is done at the data model level."
        props = dict()
        [props.update(p.to_arrows(is_key=False)) for p in self.properties]
        props.update(self.key_property.to_arrows(is_key=True))
        return {
            "id": self.label,
            "labels": [self.label],
            "properties": props,
            "style": self.metadata.get("style", {}),
            "position": self.metadata.get("position", default_position),
            "caption": self.metadata.get("caption", ""),
        }

    @classmethod
    def from_aura_data_import(
        cls,
        aura_data_import_node_label: AuraDataImportModels.NodeLabel,
        key_property_token: str,
        node_mapping: AuraDataImportModels.NodeMapping,
        source_type: str,
    ) -> "Node":
        """
        Convert an Aura Data Import NodeLabel to a Node.

        Parameters
        ----------
        aura_data_import_node_label: dict[str, Any]
            The Aura Data Import NodeLabel to convert.
                 key_property_token: str
             The token of the key property to use. This is the property name.
         node_mapping: dict[str, Any]
             The node mapping from the graphMappingRepresentation. Should have the following structure:
             ```json
             {
                 "node": {"$ref": "#n:0"},
                 "tableName": "countries.csv",
                 "propertyMappings": [
                     {
                         "property": {"$ref": "#p:0_0"},
                         "fieldName": "id"
                     }
                     ...
                 ]
             }
             ```
        Returns
        -------
        Node
            The converted Node.
        """
        # Find the key property
        key_prop = None
        other_props = []

        def _prepare_source_mapping(
            node_mapping: AuraDataImportModels.NodeMapping,
            property_id: str,
            source_type: str,
        ) -> dict[str, Any]:
            """
            Prepare the source mapping for the node mapping.
            """
            field_name = [
                x["fieldName"]
                for x in node_mapping["propertyMappings"]
                if x["property"]["$ref"] == "#" + property_id
            ]
            if not field_name:
                raise ValueError(f"Property {property_id} not found in node mapping")
            return {
                "tableName": node_mapping["tableName"],
                "fieldName": field_name[0],
                "type": "local",  # This was the original location field
                "source_type": source_type,  # The actual data source type
            }

        for prop in aura_data_import_node_label["properties"]:
            if prop["token"] == key_property_token:
                key_prop = Property.from_aura_data_import(
                    prop,
                    _prepare_source_mapping(node_mapping, prop["$id"], source_type),
                )
            else:
                other_props.append(
                    Property.from_aura_data_import(
                        prop,
                        _prepare_source_mapping(node_mapping, prop["$id"], source_type),
                    )
                )

        if not key_prop:
            # If no key property found, use the first property as key
            key_prop = Property.from_aura_data_import(
                aura_data_import_node_label["properties"][0],
                _prepare_source_mapping(
                    node_mapping,
                    aura_data_import_node_label["properties"][0]["$id"],
                    source_type,
                ),
            )
            other_props = [
                Property.from_aura_data_import(
                    p, _prepare_source_mapping(node_mapping, p["$id"], source_type)
                )
                for p in aura_data_import_node_label["properties"][1:]
            ]

        return cls(
            label=aura_data_import_node_label["token"],
            key_property=key_prop,
            properties=other_props,
        )

    def to_aura_data_import(
        self,
        node_label_id: str,
        node_obj_id: str,
        key_prop_id: str,
        constraint_id: str,
        index_id: str,
        property_id_mapping: dict[str, str] = None,
    ) -> tuple[
        AuraDataImportModels.NodeLabel,
        AuraDataImportModels.NodeKeyProperty,
        AuraDataImportModels.Constraint,
        AuraDataImportModels.Index,
    ]:
        """
        Convert a Node to Aura Data Import NodeLabel format.
        Returns tuple of (NodeLabel, KeyProperty, Constraint, Index)
        """
        # Create property list with key property first
        all_props = [self.key_property] + self.properties
        aura_props = []

        # For the first property (key property), use the provided key_prop_id
        # For additional properties, use the property_id_mapping if provided
        for i, prop in enumerate(all_props):
            if i == 0:
                prop_id = key_prop_id
            else:
                # Use property mapping if available, otherwise generate based on node pattern
                if property_id_mapping and prop.name in property_id_mapping:
                    prop_id = property_id_mapping[prop.name]
                else:
                    prop_id = f"p:{node_label_id.split(':')[1]}_{i}"

            is_key = i == 0  # First property is the key property
            aura_props.append(prop.to_aura_data_import(prop_id, is_key=is_key))

        node_label = {
            "$id": node_label_id,
            "token": self.label,
            "properties": aura_props,
        }

        key_property = {
            "node": {"$ref": f"#{node_obj_id}"},
            "keyProperty": {"$ref": f"#{key_prop_id}"},
        }

        # Create uniqueness constraint on key property
        constraint = {
            "$id": constraint_id,
            "name": f"{self.label}_constraint",
            "constraintType": "uniqueness",
            "entityType": "node",
            "nodeLabel": {"$ref": f"#{node_label_id}"},
            "relationshipType": None,
            "properties": [{"$ref": f"#{key_prop_id}"}],
        }

        # Create default index on key property
        index = {
            "$id": index_id,
            "name": f"{self.label}_index",
            "indexType": "default",
            "entityType": "node",
            "nodeLabel": {"$ref": f"#{node_label_id}"},
            "relationshipType": None,
            "properties": [{"$ref": f"#{key_prop_id}"}],
        }

        return (node_label, key_property, constraint, index)

    def get_cypher_ingest_query_for_many_records(self) -> str:
        """
        Generate a Cypher query to ingest a list of Node records into a Neo4j database.
        This query takes a parameter $records that is a list of dictionaries, each representing a Node record.
        """
        formatted_props = ", ".join(
            [f"{p.name}: record.{p.name}" for p in self.properties]
        )
        return f"""UNWIND $records as record
MERGE (n: {self.label} {{{self.key_property.name}: record.{self.key_property.name}}})
SET n += {{{formatted_props}}}"""

    def get_cypher_constraint_query(self) -> str:
        """
        Generate a Cypher query to create a NODE KEY constraint on the node.
        This creates a range index on the key property of the node and enforces uniqueness and existence of the key property.
        """
        return f"CREATE CONSTRAINT {self.label}_constraint IF NOT EXISTS FOR (n:{self.label}) REQUIRE (n.{self.key_property.name}) IS NODE KEY"


class Relationship(BaseModel):
    "A Neo4j Relationship."

    type: str = Field(
        description="The type of the relationship. Should be in SCREAMING_SNAKE_CASE.",
        min_length=1,
    )
    start_node_label: str = Field(description="The label of the start node")
    end_node_label: str = Field(description="The label of the end node")
    key_property: Property | None = Field(
        default=None, description="The key property of the relationship, if it exists."
    )
    properties: list[Property] = Field(
        default_factory=list,
        description="The other properties of the relationship, if any.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="The metadata of the relationship. This should only be used when converting data models.",
    )

    @field_validator("properties")
    def validate_properties(
        cls, properties: list[Property], info: ValidationInfo
    ) -> list[Property]:
        "Validate the properties."
        if info.data.get("key_property"):
            properties = [
                p for p in properties if p.name != info.data["key_property"].name
            ]

        counts = Counter([p.name for p in properties])
        for name, count in counts.items():
            if count > 1:
                raise ValueError(
                    f"Property {name} appears {count} times in relationship {_generate_relationship_pattern(info.data['start_node_label'], info.data['type'], info.data['end_node_label'])}"
                )
        return properties

    def add_property(self, prop: Property) -> None:
        "Add a new property to the relationship."
        if prop.name in [p.name for p in self.properties]:
            raise ValueError(
                f"Property {prop.name} already exists in relationship {self.pattern}"
            )
        self.properties.append(prop)

    def remove_property(self, prop: Property) -> None:
        "Remove a property from the relationship."
        try:
            self.properties.remove(prop)
        except ValueError:
            pass

    @property
    def pattern(self) -> str:
        "Return the pattern of the relationship."
        return _generate_relationship_pattern(
            self.start_node_label, self.type, self.end_node_label
        )

    @property
    def all_properties_dict(self) -> dict[str, str]:
        "Return a dictionary of all properties of the relationship. {property_name: property_type}"

        props = {p.name: p.type for p in self.properties} if self.properties else {}
        if self.key_property:
            props.update({self.key_property.name: f"{self.key_property.type} | KEY"})
        return props

    def get_mermaid_config_str(self) -> str:
        "Get the Mermaid configuration string for the relationship."
        props = (
            [f"<br/>{self.key_property.name}: {self.key_property.type} | KEY"]
            if self.key_property
            else []
        )
        props.extend([f"<br/>{p.name}: {p.type}" for p in self.properties])
        return f"{self.start_node_label} -->|{self.type}{''.join(props)}| {self.end_node_label}"

    @classmethod
    def from_arrows(
        cls,
        arrows_relationship_dict: dict[str, Any],
        node_id_to_label_map: dict[str, str],
    ) -> "Relationship":
        "Convert an Arrows Relationship to a Relationship."
        props = [
            Property.from_arrows({k: v})
            for k, v in arrows_relationship_dict["properties"].items()
            if "KEY" not in v.upper()
        ]
        keys = [
            {k: v}
            for k, v in arrows_relationship_dict["properties"].items()
            if "KEY" in v.upper()
        ]
        key_prop = Property.from_arrows(keys[0]) if keys else None
        metadata = {
            "style": arrows_relationship_dict["style"],
        }
        return cls(
            type=arrows_relationship_dict["type"],
            start_node_label=node_id_to_label_map[arrows_relationship_dict["fromId"]],
            end_node_label=node_id_to_label_map[arrows_relationship_dict["toId"]],
            key_property=key_prop,
            properties=props,
            metadata=metadata,
        )

    def to_arrows(self) -> dict[str, Any]:
        "Convert a Relationship to an Arrows Relationship dictionary. Final JSON string formatting is done at the data model level."
        props = dict()
        [props.update(p.to_arrows(is_key=False)) for p in self.properties]
        if self.key_property:
            props.update(self.key_property.to_arrows(is_key=True))
        return {
            "fromId": self.start_node_label,
            "toId": self.end_node_label,
            "type": self.type,
            "properties": props,
            "style": self.metadata.get("style", {}),
        }

    @classmethod
    def from_aura_data_import(
        cls,
        aura_data_import_relationship_type: AuraDataImportModels.RelationshipType,
        aura_data_import_relationship_object: AuraDataImportModels.RelationshipObjectType,
        node_id_to_label_map: dict[str, str],
        relationship_mapping: AuraDataImportModels.RelationshipMapping,
        source_type: str,
    ) -> "Relationship":
        """Convert Aura Data Import RelationshipType and RelationshipObjectType to a Relationship."""
        # Convert properties
        key_prop = None
        other_props = []

        def _prepare_source_mapping(
            relationship_mapping: AuraDataImportModels.RelationshipMapping,
            property_id: str,
            source_type: str,
        ) -> dict[str, Any]:
            """
            Prepare the source mapping for the relationship mapping.
            """
            field_name = [
                x["fieldName"]
                for x in relationship_mapping["propertyMappings"]
                if x["property"]["$ref"] == "#" + property_id
            ]
            if not field_name:
                raise ValueError(
                    f"Property {property_id} not found in relationship mapping"
                )
            return {
                "tableName": relationship_mapping["tableName"],
                "fieldName": field_name[0],
                "type": "local",  # This was the original location field
                "source_type": source_type,  # The actual data source type
            }

        for prop in aura_data_import_relationship_type["properties"]:
            # Create a default source mapping for relationship properties

            converted_prop = Property.from_aura_data_import(
                prop,
                _prepare_source_mapping(relationship_mapping, prop["$id"], source_type),
            )
            # Add all properties as regular properties (no automatic key property assignment)
            other_props.append(converted_prop)

        # Get start and end node labels from the object type
        start_node_ref = aura_data_import_relationship_object["from"]["$ref"]
        end_node_ref = aura_data_import_relationship_object["to"]["$ref"]

        return cls(
            type=aura_data_import_relationship_type["token"],
            start_node_label=node_id_to_label_map[start_node_ref],
            end_node_label=node_id_to_label_map[end_node_ref],
            key_property=key_prop,
            properties=other_props,
        )

    def to_aura_data_import(
        self,
        rel_type_id: str,
        rel_obj_id: str,
        start_node_id: str,
        end_node_id: str,
        constraint_id: str = None,
        index_id: str = None,
    ) -> tuple[
        AuraDataImportModels.RelationshipType,
        AuraDataImportModels.RelationshipObjectType,
        AuraDataImportModels.Constraint | None,
        AuraDataImportModels.Index | None,
    ]:
        """Convert a Relationship to Aura Data Import format.

        Returns tuple of (RelationshipType, RelationshipObjectType, Constraint, Index)
        Constraint and Index are None if the relationship has no key property.
        """
        # Create relationship type
        all_props = []
        if self.key_property:
            all_props.append(self.key_property)
        all_props.extend(self.properties)

        aura_props = []
        for i, prop in enumerate(all_props):
            prop_id = f"p:{rel_type_id.split(':')[1]}_{i}"
            is_key = (
                i == 0 and self.key_property is not None
            )  # First property is the key property if it exists
            aura_props.append(prop.to_aura_data_import(prop_id, is_key=is_key))

        relationship_type = {
            "$id": rel_type_id,
            "token": self.type,
            "properties": aura_props,
        }

        # Create relationship object type
        relationship_object = {
            "$id": rel_obj_id,
            "type": {"$ref": f"#{rel_type_id}"},
            "from": {"$ref": f"#{start_node_id}"},
            "to": {"$ref": f"#{end_node_id}"},
        }

        # Create constraint and index if relationship has key property
        constraint = None
        index = None
        if self.key_property and constraint_id and index_id:
            key_prop_id = aura_props[0]["$id"]  # First property is the key property

            constraint = {
                "$id": constraint_id,
                "name": f"{self.type}_constraint",
                "constraintType": "uniqueness",
                "entityType": "relationship",
                "nodeLabel": None,
                "relationshipType": {"$ref": f"#{rel_type_id}"},
                "properties": [{"$ref": f"#{key_prop_id}"}],
            }

            index = {
                "$id": index_id,
                "name": f"{self.type}_index",
                "indexType": "default",
                "entityType": "relationship",
                "nodeLabel": None,
                "relationshipType": {"$ref": f"#{rel_type_id}"},
                "properties": [{"$ref": f"#{key_prop_id}"}],
            }

        return relationship_type, relationship_object, constraint, index

    def get_cypher_ingest_query_for_many_records(
        self, start_node_key_property_name: str, end_node_key_property_name: str
    ) -> str:
        """
        Generate a Cypher query to ingest a list of Relationship records into a Neo4j database.
        The sourceId and targetId properties are used to match the start and end nodes.
        This query takes a parameter $records that is a list of dictionaries, each representing a Relationship record.
        """
        formatted_props = ", ".join(
            [f"{p.name}: record.{p.name}" for p in self.properties]
        )
        key_prop = (
            f" {{{self.key_property.name}: record.{self.key_property.name}}}"
            if self.key_property
            else ""
        )
        query = f"""UNWIND $records as record
MATCH (start: {self.start_node_label} {{{start_node_key_property_name}: record.sourceId}})
MATCH (end: {self.end_node_label} {{{end_node_key_property_name}: record.targetId}})
MERGE (start)-[:{self.type}{key_prop}]->(end)"""
        if formatted_props:
            query += f"""
SET end += {{{formatted_props}}}"""
        return query

    def get_cypher_constraint_query(self) -> str | None:
        """
        Generate a Cypher query to create a RELATIONSHIP KEY constraint on the relationship.
        This creates a range index on the key property of the relationship and enforces uniqueness and existence of the key property.
        """
        if self.key_property:
            return f"CREATE CONSTRAINT {self.type}_constraint IF NOT EXISTS FOR ()-[r:{self.type}]->() REQUIRE (r.{self.key_property.name}) IS RELATIONSHIP KEY"
        else:
            return None


class DataModel(BaseModel):
    "A Neo4j Graph Data Model."

    nodes: list[Node] = Field(
        default_factory=list, description="The nodes of the data model"
    )
    relationships: list[Relationship] = Field(
        default_factory=list, description="The relationships of the data model"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="The metadata of the data model. This should only be used when converting data models.",
    )

    @field_validator("nodes")
    def validate_nodes(cls, nodes: list[Node]) -> list[Node]:
        "Validate the nodes."

        counts = Counter([n.label for n in nodes])
        for label, count in counts.items():
            if count > 1:
                raise ValueError(
                    f"Node with label {label} appears {count} times in data model"
                )
        return nodes

    @field_validator("relationships")
    def validate_relationships(
        cls, relationships: list[Relationship], info: ValidationInfo
    ) -> list[Relationship]:
        "Validate the relationships."

        # check for duplicate relationships
        counts = Counter([r.pattern for r in relationships])
        for pattern, count in counts.items():
            if count > 1:
                raise ValueError(
                    f"Relationship with pattern {pattern} appears {count} times in data model"
                )

        # ensure source and target nodes exist
        for relationship in relationships:
            if relationship.start_node_label not in [
                n.label for n in info.data["nodes"]
            ]:
                raise ValueError(
                    f"Relationship {relationship.pattern} has a start node that does not exist in data model"
                )
            if relationship.end_node_label not in [n.label for n in info.data["nodes"]]:
                raise ValueError(
                    f"Relationship {relationship.pattern} has an end node that does not exist in data model"
                )

        return relationships

    @property
    def nodes_dict(self) -> dict[str, Node]:
        "Return a dictionary of the nodes of the data model. {node_label: node_dict}"
        return {n.label: n for n in self.nodes}

    @property
    def relationships_dict(self) -> dict[str, Relationship]:
        "Return a dictionary of the relationships of the data model. {relationship_pattern: relationship_dict}"
        return {r.pattern: r for r in self.relationships}

    def add_node(self, node: Node) -> None:
        "Add a new node to the data model."
        if node.label in [n.label for n in self.nodes]:
            raise ValueError(
                f"Node with label {node.label} already exists in data model"
            )
        self.nodes.append(node)

    def add_relationship(self, relationship: Relationship) -> None:
        "Add a new relationship to the data model."
        if relationship.pattern in [r.pattern for r in self.relationships]:
            raise ValueError(
                f"Relationship {relationship.pattern} already exists in data model"
            )
        self.relationships.append(relationship)

    def remove_node(self, node_label: str) -> None:
        "Remove a node from the data model."
        try:
            [self.nodes.remove(x) for x in self.nodes if x.label == node_label]
        except ValueError:
            pass

    def remove_relationship(
        self,
        relationship_type: str,
        relationship_start_node_label: str,
        relationship_end_node_label: str,
    ) -> None:
        "Remove a relationship from the data model."
        pattern = _generate_relationship_pattern(
            relationship_start_node_label,
            relationship_type,
            relationship_end_node_label,
        )
        try:
            [
                self.relationships.remove(x)
                for x in self.relationships
                if x.pattern == pattern
            ]
        except ValueError:
            pass

    def _generate_mermaid_config_styling_str(self) -> str:
        "Generate the Mermaid configuration string for the data model."
        node_color_config = ""

        for idx, node in enumerate(self.nodes):
            node_color_config += f"classDef node_{idx}_color fill:{NODE_COLOR_PALETTE[idx % len(NODE_COLOR_PALETTE)][0]},stroke:{NODE_COLOR_PALETTE[idx % len(NODE_COLOR_PALETTE)][1]},stroke-width:3px,color:#000,font-size:12px\nclass {node.label} node_{idx}_color\n\n"

        return f"""
%% Styling 
{node_color_config}
        """

    def get_mermaid_config_str(self) -> str:
        "Get the Mermaid configuration string for the data model."
        mermaid_nodes = [n.get_mermaid_config_str() for n in self.nodes]
        mermaid_relationships = [r.get_mermaid_config_str() for r in self.relationships]
        mermaid_styling = self._generate_mermaid_config_styling_str()
        return f"""graph TD
%% Nodes
{"\n".join(mermaid_nodes)}

%% Relationships
{"\n".join(mermaid_relationships)}

{mermaid_styling}
"""

    @classmethod
    def from_arrows(cls, arrows_data_model_dict: dict[str, Any]) -> "DataModel":
        "Convert an Arrows Data Model to a Data Model."
        nodes = [Node.from_arrows(n) for n in arrows_data_model_dict["nodes"]]
        node_id_to_label_map = {
            n["id"]: n["labels"][0] for n in arrows_data_model_dict["nodes"]
        }
        relationships = [
            Relationship.from_arrows(r, node_id_to_label_map)
            for r in arrows_data_model_dict["relationships"]
        ]
        metadata = {
            "style": arrows_data_model_dict["style"],
        }
        return cls(nodes=nodes, relationships=relationships, metadata=metadata)

    def to_arrows_dict(self) -> dict[str, Any]:
        "Convert the data model to an Arrows Data Model Python dictionary."
        node_spacing: int = 200
        y_current = 0
        arrows_nodes = []
        for idx, n in enumerate(self.nodes):
            if (idx + 1) % 5 == 0:
                y_current -= 200
            arrows_nodes.append(
                n.to_arrows(
                    default_position={"x": node_spacing * (idx % 5), "y": y_current}
                )
            )
        arrows_relationships = [r.to_arrows() for r in self.relationships]
        return {
            "nodes": arrows_nodes,
            "relationships": arrows_relationships,
            "style": self.metadata.get("style", {}),
        }

    def to_arrows_json_str(self) -> str:
        "Convert the data model to an Arrows Data Model JSON string."
        return json.dumps(self.to_arrows_dict(), indent=2)

    @classmethod
    def from_aura_data_import(
        cls, aura_data_import_data_model: AuraDataImportModels.AuraDataImportDataModel
    ) -> "DataModel":
        """Convert an Aura Data Import DataModel to a DataModel."""
        graph_schema = aura_data_import_data_model["dataModel"][
            "graphSchemaRepresentation"
        ]["graphSchema"]
        key_properties = aura_data_import_data_model["dataModel"][
            "graphSchemaExtensionsRepresentation"
        ]["nodeKeyProperties"]
        node_mappings = aura_data_import_data_model["dataModel"][
            "graphMappingRepresentation"
        ]["nodeMappings"]

        # Get the data source schema to determine source type
        data_source_schema = aura_data_import_data_model["dataModel"][
            "graphMappingRepresentation"
        ]["dataSourceSchema"]
        source_type = data_source_schema.get("type", "local")

        # Create mapping from node object ID to key property token
        node_key_map = {}
        for key_prop in key_properties:
            node_ref = key_prop["node"]["$ref"]
            prop_ref = key_prop["keyProperty"]["$ref"]
            # Find the property token by ID
            for node_label in graph_schema["nodeLabels"]:
                for prop in node_label["properties"]:
                    if prop["$id"] == prop_ref.replace("#", ""):
                        node_key_map[node_ref] = prop["token"]
                        break

        # Create node ID to label mapping
        node_id_to_label_map = {}
        for node_obj in graph_schema["nodeObjectTypes"]:
            node_id = node_obj["$id"]
            # Find the label from nodeLabels
            for label_ref in node_obj["labels"]:
                label_id = label_ref["$ref"].replace("#", "")
                for node_label in graph_schema["nodeLabels"]:
                    if node_label["$id"] == label_id:
                        node_id_to_label_map[f"#{node_id}"] = node_label["token"]
                        break

        # Get relationship mappings
        relationship_mappings = aura_data_import_data_model["dataModel"][
            "graphMappingRepresentation"
        ]["relationshipMappings"]

        # Create mapping from relationship object ID to relationship mapping
        rel_obj_to_mapping = {}
        for rel_mapping in relationship_mappings:
            rel_ref = rel_mapping["relationship"]["$ref"]
            rel_obj_to_mapping[rel_ref] = rel_mapping

        # Create mapping from node object ID to node mapping
        node_obj_to_mapping = {}
        for node_mapping in node_mappings:
            node_ref = node_mapping["node"]["$ref"]
            node_obj_to_mapping[node_ref] = node_mapping

        # Convert nodes
        nodes = []
        for node_label in graph_schema["nodeLabels"]:
            # Find corresponding node object type
            node_obj_id = None
            for node_obj in graph_schema["nodeObjectTypes"]:
                for label_ref in node_obj["labels"]:
                    if label_ref["$ref"] == f"#{node_label['$id']}":
                        node_obj_id = f"#{node_obj['$id']}"
                        break

            key_property_token = node_key_map.get(
                node_obj_id,
                node_label["properties"][0]["token"]
                if node_label["properties"]
                else "id",
            )

            # Get the corresponding node mapping
            node_mapping = node_obj_to_mapping.get(
                node_obj_id,
                {
                    "node": {"$ref": node_obj_id},
                    "tableName": "unknown",
                    "propertyMappings": [],
                },
            )

            node = Node.from_aura_data_import(
                node_label, key_property_token, node_mapping, source_type
            )
            nodes.append(node)

        # Convert relationships
        relationships = []
        for rel_obj in graph_schema["relationshipObjectTypes"]:
            # Find corresponding relationship type
            rel_type_id = rel_obj["type"]["$ref"].replace("#", "")
            rel_type = None
            for rt in graph_schema["relationshipTypes"]:
                if rt["$id"] == rel_type_id:
                    rel_type = rt
                    break

            if rel_type:
                # Get the corresponding relationship mapping
                rel_obj_id = f"#{rel_obj['$id']}"
                rel_mapping = rel_obj_to_mapping.get(
                    rel_obj_id,
                    {
                        "relationship": {"$ref": rel_obj_id},
                        "tableName": "unknown",
                        "propertyMappings": [],
                    },
                )

                relationship = Relationship.from_aura_data_import(
                    rel_type, rel_obj, node_id_to_label_map, rel_mapping, source_type
                )
                relationships.append(relationship)

        # Store visualization coordinates in node metadata
        visualization_data = aura_data_import_data_model.get("visualisation", {})
        vis_nodes = visualization_data.get("nodes", [])
        vis_node_positions = {
            vis_node["id"]: vis_node["position"] for vis_node in vis_nodes
        }

        # Update node metadata with visualization coordinates
        for i, node in enumerate(nodes):
            node_id = f"n:{i}"
            if node_id in vis_node_positions:
                node.metadata["visualization"] = {
                    "position": vis_node_positions[node_id]
                }

        # Store Aura Data Import metadata (excluding visualization since it's now in nodes)
        metadata = {
            "aura_data_import": {
                "version": aura_data_import_data_model.get("version"),
                "dataModel_version": aura_data_import_data_model["dataModel"].get(
                    "version"
                ),
                "constraints": graph_schema.get("constraints", []),
                "indexes": graph_schema.get("indexes", []),
                "configurations": aura_data_import_data_model["dataModel"].get(
                    "configurations", {}
                ),
                "dataSourceSchema": aura_data_import_data_model["dataModel"][
                    "graphMappingRepresentation"
                ].get("dataSourceSchema", {}),
            }
        }

        return cls(nodes=nodes, relationships=relationships, metadata=metadata)

    def to_aura_data_import_dict(self) -> AuraDataImportModels.AuraDataImportDataModel:
        """Convert the data model to an Aura Data Import dictionary."""
        # Check if we have stored Aura Data Import metadata
        aura_metadata = self.metadata.get("aura_data_import", {})

        # Generate IDs following the original schema patterns
        node_labels = []
        node_object_types = []
        node_key_properties = []
        constraints = []
        indexes = []

        # Track property IDs to match original schema
        node_to_key_prop_id = {}

        # Generate property IDs dynamically
        global_property_counter = 0

        for i, node in enumerate(self.nodes):
            node_label_id = f"nl:{i}"
            node_obj_id = f"n:{i}"
            constraint_id = f"c:{i}"
            index_id = f"i:{i}"

            # Use stored original property ID if available, otherwise generate new one
            key_prop_id = node.key_property.metadata.get("aura_data_import", {}).get(
                "original_id", f"p:{global_property_counter}"
            )
            if not node.key_property.metadata.get("aura_data_import", {}).get(
                "original_id"
            ):
                global_property_counter += 1

            # Build property mapping for additional properties
            node_prop_mapping = {}
            for prop in node.properties:
                stored_id = prop.metadata.get("aura_data_import", {}).get("original_id")
                if stored_id:
                    node_prop_mapping[prop.name] = stored_id
                else:
                    node_prop_mapping[prop.name] = f"p:{global_property_counter}"
                    global_property_counter += 1

            node_to_key_prop_id[node_obj_id] = key_prop_id

            # Use the updated Node.to_aura_data_import method
            node_label, key_property, constraint, index = node.to_aura_data_import(
                node_label_id,
                node_obj_id,
                key_prop_id,
                constraint_id,
                index_id,
                node_prop_mapping,
            )

            node_labels.append(node_label)
            node_key_properties.append(key_property)
            constraints.append(constraint)
            indexes.append(index)

            # Create node object type
            node_object_type = {
                "$id": node_obj_id,
                "labels": [{"$ref": f"#{node_label_id}"}],
            }
            node_object_types.append(node_object_type)

        # Handle relationships - start from rt:1, r:1 (not rt:0, r:0)
        relationship_types = []
        relationship_object_types = []

        for i, rel in enumerate(self.relationships):
            rel_type_id = f"rt:{i + 1}"  # Start from 1
            rel_obj_id = f"r:{i + 1}"  # Start from 1

            # Find start and end node IDs
            start_node_id = None
            end_node_id = None
            for j, node in enumerate(self.nodes):
                if node.label == rel.start_node_label:
                    start_node_id = f"n:{j}"
                if node.label == rel.end_node_label:
                    end_node_id = f"n:{j}"

            # Generate constraint and index IDs if relationship has key property
            constraint_id = None
            index_id = None
            if rel.key_property:
                # Continue constraint and index numbering after nodes
                constraint_id = f"c:{len(self.nodes) + i}"
                index_id = f"i:{len(self.nodes) + i}"

            rel_type, rel_obj, rel_constraint, rel_index = rel.to_aura_data_import(
                rel_type_id,
                rel_obj_id,
                start_node_id,
                end_node_id,
                constraint_id,
                index_id,
            )
            relationship_types.append(rel_type)
            relationship_object_types.append(rel_obj)

            # Add relationship constraints and indexes if they exist
            if rel_constraint:
                constraints.append(rel_constraint)
            if rel_index:
                indexes.append(rel_index)

        # Create node mappings with property mappings for round-trip conversion
        # We need to extract the property IDs from the already created node_labels
        node_mappings = []

        for i, node in enumerate(self.nodes):
            node_obj_id = f"n:{i}"

            # Get the property IDs from the corresponding node label that was just created
            node_label = node_labels[i]  # This corresponds to the current node

            # Create property mappings using the exact property IDs from the node label
            property_mappings = []

            for prop_def in node_label["properties"]:
                prop_id = prop_def["$id"]
                prop_token = prop_def["token"]

                # Find the corresponding property in our node to get the field name
                field_name = prop_token  # default to token name

                # Check key property first
                if node.key_property.name == prop_token:
                    field_name = (
                        node.key_property.source.column_name
                        if node.key_property.source
                        and node.key_property.source.column_name
                        else prop_token
                    )
                else:
                    # Check other properties
                    for prop in node.properties:
                        if prop.name == prop_token:
                            field_name = (
                                prop.source.column_name
                                if prop.source and prop.source.column_name
                                else prop_token
                            )
                            break

                property_mappings.append(
                    {"property": {"$ref": f"#{prop_id}"}, "fieldName": field_name}
                )

            # Use the property source information if available, otherwise use default
            table_name = (
                node.key_property.source.table_name
                if node.key_property.source and node.key_property.source.table_name
                else f"{node.label.lower()}.csv"
            )

            node_mapping = {
                "node": {"$ref": f"#{node_obj_id}"},
                "tableName": table_name,
                "propertyMappings": property_mappings,
            }
            node_mappings.append(node_mapping)

        # Create relationship mappings
        relationship_mappings = []
        for i, rel in enumerate(self.relationships):
            rel_obj_id = f"r:{i + 1}"  # Start from 1

            # Find source and target nodes
            source_node = None
            target_node = None
            for node in self.nodes:
                if node.label == rel.start_node_label:
                    source_node = node
                if node.label == rel.end_node_label:
                    target_node = node

            # Determine table name from relationship properties first, then fall back to source node
            table_name = None

            # Check if any relationship property has source information with table name
            if (
                rel.key_property
                and rel.key_property.source
                and rel.key_property.source.table_name
            ):
                table_name = rel.key_property.source.table_name
            else:
                for prop in rel.properties:
                    if prop.source and prop.source.table_name:
                        table_name = prop.source.table_name
                        break

            # If no relationship property has table info, use source node's table or default
            if not table_name:
                table_name = (
                    source_node.key_property.source.table_name
                    if source_node
                    and source_node.key_property.source
                    and source_node.key_property.source.table_name
                    else f"{source_node.label.lower()}_{rel.type.lower()}_{target_node.label.lower()}.csv"
                )

            # Generate field mappings based on node key properties
            from_field = (
                source_node.key_property.source.column_name
                if source_node
                and source_node.key_property.source
                and source_node.key_property.source.column_name
                else source_node.key_property.name.lower()
            )
            to_field = (
                target_node.key_property.source.column_name
                if target_node
                and target_node.key_property.source
                and target_node.key_property.source.column_name
                else target_node.key_property.name.lower()
            )

            # Create property mappings for relationship properties
            property_mappings = []

            # Find the corresponding relationship type to get property IDs
            rel_type_id = f"rt:{i + 1}"
            rel_type = None
            for rt in relationship_types:
                if rt["$id"] == rel_type_id:
                    rel_type = rt
                    break

            if rel_type and rel_type["properties"]:
                for prop_def in rel_type["properties"]:
                    prop_id = prop_def["$id"]
                    prop_token = prop_def["token"]

                    # Find the corresponding property in our relationship to get the field name
                    field_name = prop_token  # default to token name

                    # Check key property first
                    if rel.key_property and rel.key_property.name == prop_token:
                        field_name = (
                            rel.key_property.source.column_name
                            if rel.key_property.source
                            and rel.key_property.source.column_name
                            else prop_token
                        )
                    else:
                        # Check other properties
                        for prop in rel.properties:
                            if prop.name == prop_token:
                                field_name = (
                                    prop.source.column_name
                                    if prop.source and prop.source.column_name
                                    else prop_token
                                )
                                break

                    property_mappings.append(
                        {"property": {"$ref": f"#{prop_id}"}, "fieldName": field_name}
                    )

            rel_mapping = {
                "relationship": {"$ref": f"#{rel_obj_id}"},
                "tableName": table_name,
                "propertyMappings": property_mappings,
                "fromMapping": {"fieldName": from_field},
                "toMapping": {"fieldName": to_field},
            }
            relationship_mappings.append(rel_mapping)

        # Use stored metadata if available, otherwise create defaults
        version = aura_metadata.get("version", "2.3.1-beta.0")
        datamodel_version = aura_metadata.get("dataModel_version", "2.3.1-beta.0")
        stored_constraints = aura_metadata.get("constraints")
        stored_indexes = aura_metadata.get("indexes")
        stored_configurations = aura_metadata.get("configurations", {"idsToIgnore": []})

        # Generate table schemas for all referenced tables
        table_names = set()
        for node_mapping in node_mappings:
            table_names.add(node_mapping["tableName"])
        for rel_mapping in relationship_mappings:
            table_names.add(rel_mapping["tableName"])

        # Create table schemas if not stored in metadata
        stored_data_source_schema = aura_metadata.get("dataSourceSchema")
        if not stored_data_source_schema or not stored_data_source_schema.get(
            "tableSchemas"
        ):
            # Determine the source type based on the properties in the data model
            # Check all properties to see if any have a different source type
            source_types = set()
            for node in self.nodes:
                if node.key_property.source and node.key_property.source.source_type:
                    source_types.add(node.key_property.source.source_type)
                for prop in node.properties:
                    if prop.source and prop.source.source_type:
                        source_types.add(prop.source.source_type)

            for rel in self.relationships:
                if (
                    rel.key_property
                    and rel.key_property.source
                    and rel.key_property.source.source_type
                ):
                    source_types.add(rel.key_property.source.source_type)
                for prop in rel.properties:
                    if prop.source and prop.source.source_type:
                        source_types.add(prop.source.source_type)

            # Default to "local" if no source types found, or use the first one found
            # In practice, all properties should have the same source type for a given data model
            data_source_type = source_types.pop() if source_types else "local"

            table_schemas = []
            for table_name in sorted(table_names):  # Sort for consistent output
                # Generate field schemas based on node/relationship mappings
                fields = []

                # Collect fields from node mappings
                for node_mapping in node_mappings:
                    if node_mapping["tableName"] == table_name:
                        for prop_mapping in node_mapping["propertyMappings"]:
                            field_name = prop_mapping["fieldName"]
                            # Find the property to get its type
                            prop_ref = prop_mapping["property"]["$ref"].replace("#", "")
                            prop_type = "string"  # default

                            # Search for the property in node labels
                            for node_label in node_labels:
                                for prop in node_label["properties"]:
                                    if prop["$id"] == prop_ref:
                                        prop_type = prop["type"]["type"]
                                        break

                            fields.append(
                                {
                                    "name": field_name,
                                    "sample": f"sample_{field_name}",
                                    "recommendedType": {"type": prop_type},
                                }
                            )

                # Collect fields from relationship mappings
                for rel_mapping in relationship_mappings:
                    if rel_mapping["tableName"] == table_name:
                        # Add from/to fields
                        from_field = rel_mapping["fromMapping"]["fieldName"]
                        to_field = rel_mapping["toMapping"]["fieldName"]

                        # Add from field if not already present
                        if not any(f["name"] == from_field for f in fields):
                            fields.append(
                                {
                                    "name": from_field,
                                    "sample": f"sample_{from_field}",
                                    "recommendedType": {"type": "string"},
                                }
                            )

                        # Add to field if not already present
                        if not any(f["name"] == to_field for f in fields):
                            fields.append(
                                {
                                    "name": to_field,
                                    "sample": f"sample_{to_field}",
                                    "recommendedType": {"type": "string"},
                                }
                            )

                        # Add relationship property fields
                        for prop_mapping in rel_mapping["propertyMappings"]:
                            field_name = prop_mapping["fieldName"]
                            # Find the property to get its type
                            prop_ref = prop_mapping["property"]["$ref"].replace("#", "")
                            prop_type = "string"  # default

                            # Search for the property in relationship types
                            for rel_type in relationship_types:
                                for prop in rel_type["properties"]:
                                    if prop["$id"] == prop_ref:
                                        prop_type = prop["type"]["type"]
                                        break

                            # Add field if not already present
                            if not any(f["name"] == field_name for f in fields):
                                fields.append(
                                    {
                                        "name": field_name,
                                        "sample": f"sample_{field_name}",
                                        "recommendedType": {"type": prop_type},
                                    }
                                )

                table_schemas.append({"name": table_name, "fields": fields})

            stored_data_source_schema = {
                "type": data_source_type,
                "tableSchemas": table_schemas,
            }
        else:
            stored_data_source_schema = aura_metadata.get(
                "dataSourceSchema", {"type": "local", "tableSchemas": []}
            )

        # Reconstruct visualization nodes from node metadata and generate for new nodes
        visualization_nodes = []
        for i, node in enumerate(self.nodes):
            node_id = f"n:{i}"

            # Check if node has stored visualization position
            if (
                "visualization" in node.metadata
                and "position" in node.metadata["visualization"]
            ):
                position = node.metadata["visualization"]["position"]
            else:
                # Generate default position for new nodes
                # Use a grid layout: 5 nodes per row, 200px spacing
                row = i // 5
                col = i % 5
                position = {"x": col * 200.0, "y": row * 200.0}

            vis_node = {"id": node_id, "position": position}
            visualization_nodes.append(vis_node)

        # Build complete structure
        result = {
            "version": version,
            "visualisation": {"nodes": visualization_nodes},
            "dataModel": {
                "version": datamodel_version,
                "graphSchemaRepresentation": {
                    "version": "1.0.0",
                    "graphSchema": {
                        "nodeLabels": node_labels,
                        "relationshipTypes": relationship_types,
                        "nodeObjectTypes": node_object_types,
                        "relationshipObjectTypes": relationship_object_types,
                        "constraints": stored_constraints
                        if stored_constraints is not None
                        else constraints,
                        "indexes": stored_indexes
                        if stored_indexes is not None
                        else indexes,
                    },
                },
                "graphSchemaExtensionsRepresentation": {
                    "nodeKeyProperties": node_key_properties
                },
                "graphMappingRepresentation": {
                    "dataSourceSchema": stored_data_source_schema,
                    "nodeMappings": node_mappings,
                    "relationshipMappings": relationship_mappings,
                },
                "configurations": stored_configurations,
            },
        }

        return result

    def to_aura_data_import_json_str(self) -> str:
        """Convert the data model to an Aura Data Import JSON string."""
        return json.dumps(self.to_aura_data_import_dict(), indent=2)

    def get_node_cypher_ingest_query_for_many_records(self, node_label: str) -> str:
        "Generate a Cypher query to ingest a list of Node records into a Neo4j database."
        node = self.nodes_dict[node_label]
        return node.get_cypher_ingest_query_for_many_records()

    def get_relationship_cypher_ingest_query_for_many_records(
        self,
        relationship_type: str,
        relationship_start_node_label: str,
        relationship_end_node_label: str,
    ) -> str:
        "Generate a Cypher query to ingest a list of Relationship records into a Neo4j database."
        pattern = _generate_relationship_pattern(
            relationship_start_node_label,
            relationship_type,
            relationship_end_node_label,
        )
        relationship = self.relationships_dict[pattern]
        start_node = self.nodes_dict[relationship.start_node_label]
        end_node = self.nodes_dict[relationship.end_node_label]
        return relationship.get_cypher_ingest_query_for_many_records(
            start_node.key_property.name, end_node.key_property.name
        )

    def get_cypher_constraints_query(self) -> list[str]:
        """
        Generate a list of Cypher queries to create constraints on the data model.
        This creates range indexes on the key properties of the nodes and relationships and enforces uniqueness and existence of the key properties.
        """
        node_queries = [n.get_cypher_constraint_query() + ";" for n in self.nodes]
        relationship_queries = [
            r.get_cypher_constraint_query() + ";"
            for r in self.relationships
            if r.key_property is not None
        ]
        return node_queries + relationship_queries
