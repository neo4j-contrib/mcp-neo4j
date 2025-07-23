DATA_INGEST_PROCESS = """
Follow these steps when ingesting data into Neo4j.
1. Create constraints before loading any data.
2. Load all nodes before relationships.
3. Then load relationships serially to avoid deadlocks.
"""

# General Data Modeling Request Template
DATA_MODELING_TEMPLATE = """
# Neo4j Data Modeling Request Template

## Source Data Description
- **Data Format**: [CSV/JSON/XML/API/Database/Other]
- **Data Volume**: [Small (< 1M records) / Medium (1M-100M) / Large (> 100M)]
- **Update Frequency**: [Static/Real-time/Batch updates]
- **Data Sources**: [List your data sources - files, APIs, databases, etc.]
- **Data Quality**: [Clean/Requires cleaning/Unknown]

## Use Cases & Requirements
- **Primary Queries**: [What questions will you ask of the data?]
- **Performance Requirements**: [Response time needs - sub-second, seconds, minutes]
- **Scale Expectations**: [Expected number of nodes and relationships]
- **Query Patterns**: [Read-heavy/Write-heavy/Balanced]
- **Business Goals**: [What are you trying to achieve?]

## Example Entities (Nodes)
Please provide examples of the main entities in your data:

### Entity 1: [Entity Name]
- **Properties**: 
  - [property1]: [type] - [description]
  - [property2]: [type] - [description]
- **Key Property**: [What uniquely identifies this entity?]
- **Example Data**: [Sample values]

### Entity 2: [Entity Name]
- **Properties**: 
  - [property1]: [type] - [description]
  - [property2]: [type] - [description]
- **Key Property**: [What uniquely identifies this entity?]
- **Example Data**: [Sample values]

## Example Relationships
How do your entities connect to each other?

### Relationship 1: [Entity1] → [Entity2]
- **Type**: [RELATIONSHIP_TYPE]
- **Direction**: [Unidirectional/Bidirectional]
- **Properties**: [Any properties on the relationship?]
- **Cardinality**: [One-to-One/One-to-Many/Many-to-Many]

### Relationship 2: [Entity1] → [Entity2]
- **Type**: [RELATIONSHIP_TYPE]
- **Direction**: [Unidirectional/Bidirectional]
- **Properties**: [Any properties on the relationship?]
- **Cardinality**: [One-to-One/One-to-Many/Many-to-Many]

## Additional Context
- **Domain**: [Business/Technical/Social/Other]
- **Special Requirements**: [Constraints, indexes, specific query patterns]
- **Integration Needs**: [How will this integrate with existing systems?]
- **Compliance**: [Any regulatory or compliance requirements?]
"""

# Real-World Example: Patient Journey Healthcare Data Model
PATIENT_JOURNEY_MODEL = {
    "nodes": [
        {
            "label": "Patient",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "first", "type": "STRING"},
                {"name": "last", "type": "STRING"},
                {"name": "birthdate", "type": "DATE"},
                {"name": "gender", "type": "STRING"},
                {"name": "address", "type": "STRING"},
                {"name": "city", "type": "STRING"},
                {"name": "state", "type": "STRING"},
                {"name": "county", "type": "STRING"},
                {"name": "location", "type": "POINT"},
                {"name": "latitude", "type": "FLOAT"},
                {"name": "longitude", "type": "FLOAT"},
                {"name": "ethnicity", "type": "STRING"},
                {"name": "race", "type": "STRING"},
                {"name": "martial", "type": "STRING"},
                {"name": "prefix", "type": "STRING"},
                {"name": "birthplace", "type": "STRING"},
                {"name": "deathdate", "type": "DATE"},
                {"name": "drivers", "type": "STRING"},
                {"name": "healthcare_coverage", "type": "FLOAT"},
                {"name": "healthcare_expenses", "type": "FLOAT"},
            ],
        },
        {
            "label": "Encounter",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "code", "type": "STRING"},
                {"name": "description", "type": "STRING"},
                {"name": "class", "type": "STRING"},
                {"name": "start", "type": "STRING"},
                {"name": "end", "type": "STRING"},
                {"name": "isStart", "type": "BOOLEAN"},
                {"name": "isEnd", "type": "BOOLEAN"},
                {"name": "baseCost", "type": "FLOAT"},
                {"name": "claimCost", "type": "FLOAT"},
                {"name": "coveredAmount", "type": "FLOAT"},
            ],
        },
        {
            "label": "Provider",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "address", "type": "STRING"},
                {"name": "location", "type": "POINT"},
            ],
        },
        {
            "label": "Organization",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "address", "type": "STRING"},
                {"name": "city", "type": "STRING"},
                {"name": "location", "type": "POINT"},
            ],
        },
        {
            "label": "Condition",
            "key_property": {"name": "code", "type": "STRING"},
            "properties": [
                {"name": "description", "type": "STRING"},
                {"name": "start", "type": "STRING"},
                {"name": "stop", "type": "STRING"},
                {"name": "isEnd", "type": "BOOLEAN"},
                {"name": "total_drug_pairings", "type": "INTEGER"},
            ],
        },
        {
            "label": "Drug",
            "key_property": {"name": "code", "type": "STRING"},
            "properties": [
                {"name": "description", "type": "STRING"},
                {"name": "start", "type": "STRING"},
                {"name": "stop", "type": "STRING"},
                {"name": "isEnd", "type": "BOOLEAN"},
                {"name": "basecost", "type": "STRING"},
                {"name": "totalcost", "type": "STRING"},
            ],
        },
        {
            "label": "Procedure",
            "key_property": {"name": "code", "type": "STRING"},
            "properties": [{"name": "description", "type": "STRING"}],
        },
        {
            "label": "Observation",
            "key_property": {"name": "code", "type": "STRING"},
            "properties": [
                {"name": "description", "type": "STRING"},
                {"name": "category", "type": "STRING"},
                {"name": "type", "type": "STRING"},
            ],
        },
        {
            "label": "Device",
            "key_property": {"name": "code", "type": "STRING"},
            "properties": [{"name": "description", "type": "STRING"}],
        },
        {
            "label": "CarePlan",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "code", "type": "STRING"},
                {"name": "description", "type": "STRING"},
                {"name": "start", "type": "STRING"},
                {"name": "end", "type": "STRING"},
                {"name": "isEnd", "type": "BOOLEAN"},
                {"name": "reasoncode", "type": "STRING"},
            ],
        },
        {
            "label": "Allergy",
            "key_property": {"name": "code", "type": "STRING"},
            "properties": [
                {"name": "description", "type": "STRING"},
                {"name": "category", "type": "STRING"},
                {"name": "system", "type": "STRING"},
                {"name": "type", "type": "STRING"},
            ],
        },
        {
            "label": "Reaction",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [{"name": "description", "type": "STRING"}],
        },
        {
            "label": "Payer",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [{"name": "name", "type": "STRING"}],
        },
        {
            "label": "Speciality",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
    ],
    "relationships": [
        {
            "type": "HAS_ENCOUNTER",
            "start_node_label": "Patient",
            "end_node_label": "Encounter",
        },
        {"type": "FIRST", "start_node_label": "Patient", "end_node_label": "Encounter"},
        {"type": "LAST", "start_node_label": "Patient", "end_node_label": "Encounter"},
        {
            "type": "NEXT",
            "start_node_label": "Encounter",
            "end_node_label": "Encounter",
            "properties": [{"name": "amount", "type": "INTEGER"}],
        },
        {
            "type": "HAS_PROVIDER",
            "start_node_label": "Encounter",
            "end_node_label": "Provider",
        },
        {
            "type": "AT_ORGANIZATION",
            "start_node_label": "Encounter",
            "end_node_label": "Organization",
        },
        {
            "type": "BELONGS_TO",
            "start_node_label": "Provider",
            "end_node_label": "Organization",
        },
        {
            "type": "HAS_SPECIALITY",
            "start_node_label": "Provider",
            "end_node_label": "Speciality",
        },
        {
            "type": "HAS_CONDITION",
            "start_node_label": "Encounter",
            "end_node_label": "Condition",
        },
        {"type": "HAS_DRUG", "start_node_label": "Encounter", "end_node_label": "Drug"},
        {
            "type": "HAS_PROCEDURE",
            "start_node_label": "Encounter",
            "end_node_label": "Procedure",
        },
        {
            "type": "HAS_OBSERVATION",
            "start_node_label": "Encounter",
            "end_node_label": "Observation",
            "properties": [
                {"name": "date", "type": "STRING"},
                {"name": "value", "type": "STRING"},
                {"name": "unit", "type": "STRING"},
            ],
        },
        {
            "type": "DEVICE_USED",
            "start_node_label": "Encounter",
            "end_node_label": "Device",
        },
        {
            "type": "HAS_CARE_PLAN",
            "start_node_label": "Encounter",
            "end_node_label": "CarePlan",
        },
        {
            "type": "HAS_ALLERGY",
            "start_node_label": "Patient",
            "end_node_label": "Allergy",
        },
        {
            "type": "ALLERGY_DETECTED",
            "start_node_label": "Encounter",
            "end_node_label": "Allergy",
            "properties": [{"name": "start", "type": "STRING"}],
        },
        {
            "type": "CAUSES_REACTION",
            "start_node_label": "Allergy",
            "end_node_label": "Reaction",
        },
        {
            "type": "HAS_REACTION",
            "start_node_label": "Patient",
            "end_node_label": "Reaction",
            "properties": [{"name": "severity", "type": "STRING"}],
        },
        {
            "type": "HAS_PAYER",
            "start_node_label": "Encounter",
            "end_node_label": "Payer",
        },
        {
            "type": "INSURANCE_START",
            "start_node_label": "Patient",
            "end_node_label": "Payer",
        },
        {
            "type": "INSURANCE_END",
            "start_node_label": "Patient",
            "end_node_label": "Payer",
        },
    ],
}

# Real-World Example: Google Supply Chain Data Model
SUPPLY_CHAIN_MODEL = {
    "nodes": [
        {
            "label": "Product",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Order",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Inventory",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Location",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "LegalEntity",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Asset",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "BOM",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Address",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "GeoRef",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Coordinates",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Adm1Location",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Country",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "GGGRecord",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Date",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
    ],
    "relationships": [
        {
            "type": "HAS_PART",
            "start_node_label": "Product",
            "end_node_label": "Product",
            "properties": [{"name": "quantity", "type": "INTEGER"}],
        },
        {
            "type": "MANUFACTURER",
            "start_node_label": "Product",
            "end_node_label": "LegalEntity",
        },
        {"type": "SUB_PARTS", "start_node_label": "Product", "end_node_label": "BOM"},
        {"type": "HAS_PARTS", "start_node_label": "BOM", "end_node_label": "Product"},
        {"type": "PRODUCT", "start_node_label": "Order", "end_node_label": "Product"},
        {
            "type": "PRODUCT",
            "start_node_label": "Inventory",
            "end_node_label": "Product",
        },
        {
            "type": "LEGAL_ENTITY",
            "start_node_label": "Order",
            "end_node_label": "LegalEntity",
        },
        {
            "type": "SUPPLIER",
            "start_node_label": "Inventory",
            "end_node_label": "LegalEntity",
        },
        {"type": "LOCATION", "start_node_label": "Order", "end_node_label": "Location"},
        {
            "type": "LOCATION",
            "start_node_label": "Inventory",
            "end_node_label": "Location",
        },
        {"type": "LOCATION", "start_node_label": "Asset", "end_node_label": "Location"},
        {
            "type": "RECEIVING_LOCATION",
            "start_node_label": "Order",
            "end_node_label": "Location",
        },
        {
            "type": "SHIPPING_LOCATION",
            "start_node_label": "Order",
            "end_node_label": "Location",
        },
        {"type": "ASSET", "start_node_label": "Order", "end_node_label": "Asset"},
        {
            "type": "ADDRESS",
            "start_node_label": "Location",
            "end_node_label": "Address",
        },
        {
            "type": "ADDRESS",
            "start_node_label": "LegalEntity",
            "end_node_label": "Address",
        },
        {"type": "GEOREF", "start_node_label": "GGGRecord", "end_node_label": "GeoRef"},
        {
            "type": "COORDINATES",
            "start_node_label": "GeoRef",
            "end_node_label": "Coordinates",
        },
        {
            "type": "LOCATION",
            "start_node_label": "GeoRef",
            "end_node_label": "Adm1Location",
        },
        {"type": "COUNTRY", "start_node_label": "Address", "end_node_label": "Country"},
        {
            "type": "COUNTRY",
            "start_node_label": "Adm1Location",
            "end_node_label": "Country",
        },
        {
            "type": "WITHIN_50K",
            "start_node_label": "Address",
            "end_node_label": "Coordinates",
        },
        {"type": "DATE", "start_node_label": "GGGRecord", "end_node_label": "Date"},
    ],
}
