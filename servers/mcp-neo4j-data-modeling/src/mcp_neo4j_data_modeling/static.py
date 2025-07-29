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
- **Data Sources**: [List your data sources - files, APIs, databases, etc.]

## Use Cases & Requirements
- **Primary Queries**: [What questions will you ask of the data?]
- **Scale Expectations**: [Expected number of nodes and relationships]
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

# Real-World Example: Supply Chain Data Model
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

# Real-World Example: Software Dependency Graph
SOFTWARE_DEPENDENCY_MODEL = {
    "nodes": [
        {
            "label": "Project",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Dependency",
            "key_property": {"name": "artifactId", "type": "STRING"},
            "properties": [
                {"name": "groupId", "type": "STRING"},
                {"name": "version", "type": "STRING"},
            ],
        },
        {
            "label": "CVE",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "description", "type": "STRING"},
                {"name": "severity", "type": "STRING"},
            ],
        },
        {
            "label": "Commit",
            "key_property": {"name": "sha", "type": "STRING"},
            "properties": [{"name": "repository", "type": "STRING"}],
        },
        {
            "label": "Contributor",
            "key_property": {"name": "id", "type": "INTEGER"},
            "properties": [
                {"name": "login", "type": "STRING"},
                {"name": "contributions", "type": "INTEGER"},
            ],
        },
        {
            "label": "BadActor",
            "key_property": {"name": "id", "type": "INTEGER"},
            "properties": [
                {"name": "login", "type": "STRING"},
                {"name": "contributions", "type": "INTEGER"},
            ],
        },
        {
            "label": "Organization",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "SuspectOrg",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Pom",
            "key_property": {"name": "filePath", "type": "STRING"},
            "properties": [{"name": "parentDirectory", "type": "STRING"}],
        },
        {
            "label": "Issue",
            "key_property": {"name": "id", "type": "INTEGER"},
            "properties": [
                {"name": "title", "type": "STRING"},
                {"name": "body", "type": "STRING"},
                {"name": "state", "type": "STRING"},
                {"name": "severity", "type": "STRING"},
                {"name": "comments", "type": "INTEGER"},
                {"name": "createdAt", "type": "STRING"},
                {"name": "updatedAt", "type": "STRING"},
                {"name": "url", "type": "STRING"},
                {"name": "htmlUrl", "type": "STRING"},
            ],
        },
        {
            "label": "User",
            "key_property": {"name": "id", "type": "INTEGER"},
            "properties": [{"name": "login", "type": "STRING"}],
        },
        {
            "label": "Product",
            "key_property": {"name": "serialNumber", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "softwareVersion", "type": "STRING"},
                {"name": "macAddress", "type": "STRING"},
            ],
        },
        {
            "label": "Customer",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "SuspectCommit",
            "key_property": {"name": "sha", "type": "STRING"},
            "properties": [{"name": "repository", "type": "STRING"}],
        },
    ],
    "relationships": [
        {
            "type": "DEPENDS_ON",
            "start_node_label": "Pom",
            "end_node_label": "Dependency",
        },
        {
            "type": "BELONGS_TO_PROJECT",
            "start_node_label": "Pom",
            "end_node_label": "Project",
        },
        {
            "type": "AFFECTED_BY",
            "start_node_label": "Dependency",
            "end_node_label": "CVE",
        },
        {
            "type": "BELONGS_TO",
            "start_node_label": "Project",
            "end_node_label": "Organization",
        },
        {
            "type": "BELONGS_TO",
            "start_node_label": "Project",
            "end_node_label": "SuspectOrg",
        },
        {
            "type": "HAS_HEAD_COMMIT",
            "start_node_label": "Project",
            "end_node_label": "Commit",
        },
        {"type": "HAS_ISSUE", "start_node_label": "Project", "end_node_label": "Issue"},
        {
            "type": "INSTALLED_ON",
            "start_node_label": "Project",
            "end_node_label": "Product",
        },
        {
            "type": "CONTRIBUTED_TO",
            "start_node_label": "Contributor",
            "end_node_label": "Project",
        },
        {
            "type": "CONTRIBUTED_TO",
            "start_node_label": "BadActor",
            "end_node_label": "Project",
        },
        {
            "type": "HAS_COMMIT",
            "start_node_label": "Contributor",
            "end_node_label": "Commit",
        },
        {
            "type": "HAS_COMMIT",
            "start_node_label": "BadActor",
            "end_node_label": "Commit",
        },
        {"type": "CREATED_BY", "start_node_label": "Issue", "end_node_label": "User"},
        {
            "type": "PURCHASED",
            "start_node_label": "Customer",
            "end_node_label": "Product",
            "properties": [{"name": "purchaseDate", "type": "STRING"}],
        },
        {
            "type": "NEXT_COMMIT",
            "start_node_label": "Commit",
            "end_node_label": "Commit",
        },
        {
            "type": "NEXT_COMMIT",
            "start_node_label": "Commit",
            "end_node_label": "SuspectCommit",
        },
        {
            "type": "NEXT_COMMIT",
            "start_node_label": "SuspectCommit",
            "end_node_label": "Commit",
        },
    ],
}

# Real-World Example: Oil and Gas Equipment Monitoring
OIL_GAS_MONITORING_MODEL = {
    "nodes": [
        {
            "label": "Producer",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "location", "type": "POINT"},
            ],
        },
        {
            "label": "CollectionPoint",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "location", "type": "POINT"},
            ],
        },
        {
            "label": "Equipment",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [{"name": "type", "type": "STRING"}],
        },
        {
            "label": "Vessel",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [{"name": "type", "type": "STRING"}],
        },
        {
            "label": "Sensor",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [{"name": "type", "type": "STRING"}],
        },
        {
            "label": "Alert",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "type", "type": "STRING"},
                {"name": "status", "type": "STRING"},
            ],
        },
        {
            "label": "MaintenanceRecord",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "date", "type": "STRING"},
                {"name": "description", "type": "STRING"},
                {"name": "type", "type": "STRING"},
                {"name": "downTime", "type": "FLOAT"},
            ],
        },
        {
            "label": "ServiceProvider",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "companyName", "type": "STRING"},
                {"name": "type", "type": "STRING"},
            ],
        },
        {
            "label": "Lease",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "coordinates", "type": "STRING"},
            ],
        },
        {
            "label": "Basin",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Model",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [{"name": "type", "type": "STRING"}],
        },
        {
            "label": "TransmissionRoute",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "start", "type": "POINT"},
                {"name": "end", "type": "POINT"},
            ],
        },
    ],
    "relationships": [
        {
            "type": "COLLECTED_BY",
            "start_node_label": "Producer",
            "end_node_label": "CollectionPoint",
        },
        {
            "type": "MONITORED_BY",
            "start_node_label": "Producer",
            "end_node_label": "Sensor",
        },
        {
            "type": "MONITORED_BY",
            "start_node_label": "CollectionPoint",
            "end_node_label": "Sensor",
        },
        {
            "type": "MONITORED_BY",
            "start_node_label": "Equipment",
            "end_node_label": "Sensor",
        },
        {
            "type": "MONITORED_BY",
            "start_node_label": "Vessel",
            "end_node_label": "Sensor",
        },
        {"type": "RAISED", "start_node_label": "Sensor", "end_node_label": "Alert"},
        {
            "type": "HAS_ALERT",
            "start_node_label": "CollectionPoint",
            "end_node_label": "Alert",
        },
        {
            "type": "HAS_ALERT",
            "start_node_label": "Equipment",
            "end_node_label": "Alert",
        },
        {"type": "HAS_ALERT", "start_node_label": "Vessel", "end_node_label": "Alert"},
        {
            "type": "HAS_MAINTENANCE_RECORD",
            "start_node_label": "Producer",
            "end_node_label": "MaintenanceRecord",
        },
        {
            "type": "HAS_MAINTENANCE_RECORD",
            "start_node_label": "Equipment",
            "end_node_label": "MaintenanceRecord",
        },
        {
            "type": "SERVICED_BY",
            "start_node_label": "Producer",
            "end_node_label": "ServiceProvider",
        },
        {
            "type": "SERVICED_BY",
            "start_node_label": "CollectionPoint",
            "end_node_label": "ServiceProvider",
        },
        {
            "type": "SERVICED_BY",
            "start_node_label": "Equipment",
            "end_node_label": "ServiceProvider",
        },
        {
            "type": "SERVICED_BY",
            "start_node_label": "Lease",
            "end_node_label": "ServiceProvider",
        },
        {
            "type": "LOCATED_ON",
            "start_node_label": "Producer",
            "end_node_label": "Lease",
        },
        {
            "type": "LOCATED_ON",
            "start_node_label": "CollectionPoint",
            "end_node_label": "Lease",
        },
        {
            "type": "LOCATED_IN",
            "start_node_label": "Producer",
            "end_node_label": "Basin",
        },
        {
            "type": "LOCATED_AT",
            "start_node_label": "Equipment",
            "end_node_label": "CollectionPoint",
        },
        {
            "type": "LOCATED_AT",
            "start_node_label": "Vessel",
            "end_node_label": "CollectionPoint",
        },
        {
            "type": "CONNECTED_TO",
            "start_node_label": "Vessel",
            "end_node_label": "Equipment",
        },
        {
            "type": "CONNECTED_TO",
            "start_node_label": "Vessel",
            "end_node_label": "Vessel",
        },
        {
            "type": "HAS_MODEL",
            "start_node_label": "Equipment",
            "end_node_label": "Model",
        },
        {"type": "MODEL_OF", "start_node_label": "Vessel", "end_node_label": "Model"},
        {
            "type": "MODEL_OF",
            "start_node_label": "Equipment",
            "end_node_label": "Model",
        },
        {
            "type": "TRANSMITTED_BY",
            "start_node_label": "CollectionPoint",
            "end_node_label": "TransmissionRoute",
        },
    ],
}

# Real-World Example: Customer 360
CUSTOMER_360_MODEL = {
    "nodes": [
        {
            "label": "Account",
            "key_property": {"name": "account_id", "type": "STRING"},
            "properties": [{"name": "account_name", "type": "STRING"}],
        },
        {
            "label": "Contact",
            "key_property": {"name": "contact_id", "type": "STRING"},
            "properties": [
                {"name": "title", "type": "STRING"},
                {"name": "job_function", "type": "STRING"},
                {"name": "job_role", "type": "STRING"},
            ],
        },
        {
            "label": "Order",
            "key_property": {"name": "order_number", "type": "STRING"},
            "properties": [
                {"name": "order_create_date", "type": "DATE"},
                {"name": "order_complete_date", "type": "DATE"},
                {"name": "source", "type": "STRING"},
            ],
        },
        {
            "label": "Product",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Ticket",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Survey",
            "key_property": {"name": "record_id", "type": "STRING"},
            "properties": [
                {"name": "status", "type": "STRING"},
                {"name": "start_date", "type": "DATE"},
                {"name": "end_date", "type": "DATE"},
                {"name": "start_timestamp", "type": "INTEGER"},
                {"name": "end_timestamp", "type": "INTEGER"},
                {"name": "duration", "type": "INTEGER"},
                {"name": "recorded_date", "type": "DATE"},
                {"name": "survey_response", "type": "STRING"},
                {"name": "sentiment", "type": "STRING"},
                {"name": "nps_group", "type": "STRING"},
                {"name": "qid1", "type": "STRING"},
                {"name": "qid2_1", "type": "STRING"},
                {"name": "qid2_2", "type": "STRING"},
                {"name": "qid2_3", "type": "STRING"},
                {"name": "qid2_4", "type": "STRING"},
                {"name": "qid4", "type": "STRING"},
            ],
        },
        {
            "label": "Address",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "city", "type": "STRING"},
                {"name": "country", "type": "STRING"},
                {"name": "subRegion", "type": "STRING"},
            ],
        },
        {
            "label": "Industry",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Segment",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "ParentAccount",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "SalesProgramType",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Persona",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Service",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "SurveyType",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Question",
            "key_property": {"name": "text", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Theme",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Aspect",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Milestone",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "DataCenter",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Metro",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Country",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Region",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "OrderType",
            "key_property": {"name": "type", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "SubOrderType",
            "key_property": {"name": "type", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "TicketType",
            "key_property": {"name": "type", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "TicketCode",
            "key_property": {"name": "code_name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "EscalationCategory",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "EscalationSubCategory",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "IncidentCategory",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "RootCause",
            "key_property": {"name": "type", "type": "STRING"},
            "properties": [],
        },
    ],
    "relationships": [
        {
            "type": "ACCOUNT_CONTACT",
            "start_node_label": "Account",
            "end_node_label": "Contact",
        },
        {
            "type": "HAS_ADDRESS",
            "start_node_label": "Account",
            "end_node_label": "Address",
        },
        {
            "type": "HAS_INDUSTRY",
            "start_node_label": "Account",
            "end_node_label": "Industry",
        },
        {
            "type": "IN_SEGMENT",
            "start_node_label": "Account",
            "end_node_label": "Segment",
        },
        {
            "type": "PARENT_ACCOUNT",
            "start_node_label": "Account",
            "end_node_label": "ParentAccount",
        },
        {
            "type": "SALES_PROGRAM_TYPE",
            "start_node_label": "Account",
            "end_node_label": "SalesProgramType",
        },
        {
            "type": "PLACES_ORDER",
            "start_node_label": "Account",
            "end_node_label": "Order",
        },
        {
            "type": "CREATED_TICKET",
            "start_node_label": "Account",
            "end_node_label": "Ticket",
        },
        {
            "type": "COMPLETED_SURVEY",
            "start_node_label": "Account",
            "end_node_label": "Survey",
        },
        {
            "type": "HAS_PERSONA",
            "start_node_label": "Contact",
            "end_node_label": "Persona",
        },
        {
            "type": "CONTACT_CREATED_TICKET",
            "start_node_label": "Contact",
            "end_node_label": "Ticket",
        },
        {
            "type": "FOR_PRODUCT",
            "start_node_label": "Order",
            "end_node_label": "Product",
        },
        {
            "type": "SUB_ORDER_TYPE",
            "start_node_label": "Order",
            "end_node_label": "SubOrderType",
        },
        {
            "type": "ORDER_TYPE",
            "start_node_label": "SubOrderType",
            "end_node_label": "OrderType",
        },
        {
            "type": "TICKET_FOR_PRODUCT",
            "start_node_label": "Ticket",
            "end_node_label": "Product",
        },
        {
            "type": "AFFECTED_SERVICE",
            "start_node_label": "Ticket",
            "end_node_label": "Service",
        },
        {
            "type": "HAS_TICKET_TYPE",
            "start_node_label": "Ticket",
            "end_node_label": "TicketType",
        },
        {
            "type": "HAS_PROBLEM_CODE",
            "start_node_label": "Ticket",
            "end_node_label": "TicketCode",
            "properties": [{"name": "code_name", "type": "STRING"}],
        },
        {
            "type": "ESCALATION_CATEGORY",
            "start_node_label": "Ticket",
            "end_node_label": "EscalationCategory",
        },
        {
            "type": "ESCALATION_SUB_CATEGORY",
            "start_node_label": "Ticket",
            "end_node_label": "EscalationSubCategory",
        },
        {
            "type": "INCIDENT_CATEGORY",
            "start_node_label": "Ticket",
            "end_node_label": "IncidentCategory",
        },
        {
            "type": "HAS_ROOT_CAUSE",
            "start_node_label": "Ticket",
            "end_node_label": "RootCause",
        },
        {
            "type": "FILLED_BY",
            "start_node_label": "Survey",
            "end_node_label": "Contact",
        },
        {
            "type": "HAS_SURVEY_TYPE",
            "start_node_label": "Survey",
            "end_node_label": "SurveyType",
        },
        {"type": "HAS_THEME", "start_node_label": "Survey", "end_node_label": "Theme"},
        {
            "type": "HAS_ASPECT",
            "start_node_label": "Survey",
            "end_node_label": "Aspect",
            "properties": [
                {"name": "attributed_sentiment", "type": "STRING"},
                {"name": "pos_sentiment_score", "type": "INTEGER"},
                {"name": "neu_sentiment_score", "type": "INTEGER"},
                {"name": "neg_sentiment_score", "type": "INTEGER"},
            ],
        },
        {
            "type": "RELATED_ORDER",
            "start_node_label": "Survey",
            "end_node_label": "Order",
        },
        {
            "type": "RELATED_TO_DC",
            "start_node_label": "Survey",
            "end_node_label": "DataCenter",
            "properties": [
                {"name": "dcCage", "type": "STRING"},
                {"name": "dc_alias", "type": "STRING"},
            ],
        },
        {
            "type": "RESPONDED_TO",
            "start_node_label": "Survey",
            "end_node_label": "Question",
            "properties": [
                {"name": "nps_group", "type": "STRING"},
                {"name": "nps_score", "type": "INTEGER"},
                {"name": "rating", "type": "STRING"},
                {"name": "rating_score", "type": "STRING"},
            ],
        },
        {
            "type": "HAS_MILESTONE",
            "start_node_label": "SurveyType",
            "end_node_label": "Milestone",
        },
        {
            "type": "HAS_QUESTION",
            "start_node_label": "SurveyType",
            "end_node_label": "Question",
        },
        {
            "type": "THEME_HAS_ASPECT",
            "start_node_label": "Theme",
            "end_node_label": "Aspect",
        },
        {
            "type": "IN_METRO",
            "start_node_label": "DataCenter",
            "end_node_label": "Metro",
        },
        {
            "type": "IN_COUNTRY",
            "start_node_label": "Metro",
            "end_node_label": "Country",
        },
        {
            "type": "IN_REGION",
            "start_node_label": "Country",
            "end_node_label": "Region",
        },
    ],
}

# Real-World Example: Fraud & AML Data Model
FRAUD_AML_MODEL = {
    "nodes": [
        {
            "label": "Customer",
            "key_property": {"name": "customer_id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "date_of_birth", "type": "DATE"},
                {"name": "nationality", "type": "STRING"},
                {"name": "risk_level", "type": "STRING"},
            ],
        },
        {
            "label": "Account",
            "key_property": {"name": "account_number", "type": "STRING"},
            "properties": [
                {"name": "account_type", "type": "STRING"},
                {"name": "balance", "type": "FLOAT"},
                {"name": "opening_date", "type": "DATE"},
                {"name": "status", "type": "STRING"},
            ],
        },
        {
            "label": "Transaction",
            "key_property": {"name": "transaction_id", "type": "STRING"},
            "properties": [
                {"name": "amount", "type": "FLOAT"},
                {"name": "currency", "type": "STRING"},
                {"name": "transaction_date", "type": "DATETIME"},
                {"name": "transaction_type", "type": "STRING"},
                {"name": "description", "type": "STRING"},
            ],
        },
        {
            "label": "Counterparty",
            "key_property": {"name": "counterparty_id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "type", "type": "STRING"},
                {"name": "country", "type": "STRING"},
                {"name": "risk_score", "type": "INTEGER"},
            ],
        },
        {
            "label": "Alert",
            "key_property": {"name": "alert_id", "type": "STRING"},
            "properties": [
                {"name": "alert_type", "type": "STRING"},
                {"name": "severity", "type": "STRING"},
                {"name": "created_date", "type": "DATETIME"},
                {"name": "status", "type": "STRING"},
                {"name": "description", "type": "STRING"},
            ],
        },
        {
            "label": "Case",
            "key_property": {"name": "case_id", "type": "STRING"},
            "properties": [
                {"name": "case_type", "type": "STRING"},
                {"name": "priority", "type": "STRING"},
                {"name": "created_date", "type": "DATETIME"},
                {"name": "status", "type": "STRING"},
                {"name": "assigned_to", "type": "STRING"},
            ],
        },
        {
            "label": "Document",
            "key_property": {"name": "document_id", "type": "STRING"},
            "properties": [
                {"name": "document_type", "type": "STRING"},
                {"name": "upload_date", "type": "DATETIME"},
                {"name": "status", "type": "STRING"},
                {"name": "file_path", "type": "STRING"},
            ],
        },
        {
            "label": "RiskAssessment",
            "key_property": {"name": "assessment_id", "type": "STRING"},
            "properties": [
                {"name": "assessment_date", "type": "DATETIME"},
                {"name": "risk_score", "type": "INTEGER"},
                {"name": "risk_factors", "type": "STRING"},
                {"name": "recommendations", "type": "STRING"},
            ],
        },
        {
            "label": "ComplianceRule",
            "key_property": {"name": "rule_id", "type": "STRING"},
            "properties": [
                {"name": "rule_name", "type": "STRING"},
                {"name": "rule_type", "type": "STRING"},
                {"name": "threshold", "type": "FLOAT"},
                {"name": "description", "type": "STRING"},
            ],
        },
        {
            "label": "SanctionList",
            "key_property": {"name": "list_id", "type": "STRING"},
            "properties": [
                {"name": "list_name", "type": "STRING"},
                {"name": "source", "type": "STRING"},
                {"name": "last_updated", "type": "DATETIME"},
            ],
        },
        {
            "label": "SanctionedEntity",
            "key_property": {"name": "entity_id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "entity_type", "type": "STRING"},
                {"name": "country", "type": "STRING"},
                {"name": "sanction_date", "type": "DATE"},
            ],
        },
        {
            "label": "Device",
            "key_property": {"name": "device_id", "type": "STRING"},
            "properties": [
                {"name": "device_type", "type": "STRING"},
                {"name": "ip_address", "type": "STRING"},
                {"name": "location", "type": "STRING"},
                {"name": "last_used", "type": "DATETIME"},
            ],
        },
        {
            "label": "Location",
            "key_property": {"name": "location_id", "type": "STRING"},
            "properties": [
                {"name": "country", "type": "STRING"},
                {"name": "city", "type": "STRING"},
                {"name": "risk_level", "type": "STRING"},
            ],
        },
        {
            "label": "Product",
            "key_property": {"name": "product_id", "type": "STRING"},
            "properties": [
                {"name": "product_name", "type": "STRING"},
                {"name": "product_type", "type": "STRING"},
                {"name": "risk_category", "type": "STRING"},
            ],
        },
        {
            "label": "Employee",
            "key_property": {"name": "employee_id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "role", "type": "STRING"},
                {"name": "department", "type": "STRING"},
            ],
        },
    ],
    "relationships": [
        {
            "type": "OWNS_ACCOUNT",
            "start_node_label": "Customer",
            "end_node_label": "Account",
        },
        {
            "type": "HAS_TRANSACTION",
            "start_node_label": "Account",
            "end_node_label": "Transaction",
        },
        {
            "type": "INVOLVES_COUNTERPARTY",
            "start_node_label": "Transaction",
            "end_node_label": "Counterparty",
        },
        {
            "type": "TRIGGERS_ALERT",
            "start_node_label": "Transaction",
            "end_node_label": "Alert",
        },
        {
            "type": "ASSOCIATED_WITH_CASE",
            "start_node_label": "Alert",
            "end_node_label": "Case",
        },
        {
            "type": "HAS_DOCUMENT",
            "start_node_label": "Case",
            "end_node_label": "Document",
        },
        {
            "type": "HAS_RISK_ASSESSMENT",
            "start_node_label": "Customer",
            "end_node_label": "RiskAssessment",
        },
        {
            "type": "VIOLATES_RULE",
            "start_node_label": "Transaction",
            "end_node_label": "ComplianceRule",
        },
        {
            "type": "ON_SANCTION_LIST",
            "start_node_label": "SanctionedEntity",
            "end_node_label": "SanctionList",
        },
        {
            "type": "MATCHES_SANCTIONED_ENTITY",
            "start_node_label": "Customer",
            "end_node_label": "SanctionedEntity",
        },
        {
            "type": "MATCHES_SANCTIONED_ENTITY",
            "start_node_label": "Counterparty",
            "end_node_label": "SanctionedEntity",
        },
        {
            "type": "USES_DEVICE",
            "start_node_label": "Customer",
            "end_node_label": "Device",
        },
        {
            "type": "LOCATED_IN",
            "start_node_label": "Customer",
            "end_node_label": "Location",
        },
        {
            "type": "LOCATED_IN",
            "start_node_label": "Counterparty",
            "end_node_label": "Location",
        },
        {
            "type": "INVOLVES_PRODUCT",
            "start_node_label": "Transaction",
            "end_node_label": "Product",
        },
        {
            "type": "ASSIGNED_TO",
            "start_node_label": "Case",
            "end_node_label": "Employee",
        },
        {
            "type": "REVIEWED_BY",
            "start_node_label": "Alert",
            "end_node_label": "Employee",
        },
        {
            "type": "RELATED_TRANSACTION",
            "start_node_label": "Transaction",
            "end_node_label": "Transaction",
        },
        {
            "type": "SAME_DEVICE",
            "start_node_label": "Device",
            "end_node_label": "Device",
        },
        {
            "type": "HIGH_RISK_LOCATION",
            "start_node_label": "Location",
            "end_node_label": "Location",
        },
        {
            "type": "SUSPICIOUS_PATTERN",
            "start_node_label": "Transaction",
            "end_node_label": "Transaction",
        },
        {
            "type": "FREQUENT_COUNTERPARTY",
            "start_node_label": "Customer",
            "end_node_label": "Counterparty",
        },
        {
            "type": "UNUSUAL_AMOUNT",
            "start_node_label": "Transaction",
            "end_node_label": "Transaction",
        },
        {
            "type": "RAPID_MOVEMENT",
            "start_node_label": "Transaction",
            "end_node_label": "Transaction",
        },
    ],
}

# Real-World Example: Health Insurance Fraud Detection
HEALTH_INSURANCE_FRAUD_MODEL = {
    "nodes": [
        {"label": "Person", "key_property": {"name": "id", "type": "STRING"}, "properties": []},
        {"label": "Address", "key_property": {"name": "id", "type": "STRING"}, "properties": []},
        {"label": "Phone", "key_property": {"name": "id", "type": "STRING"}, "properties": []},
        {"label": "IBAN", "key_property": {"name": "id", "type": "STRING"}, "properties": []},
        {"label": "Photo", "key_property": {"name": "id", "type": "STRING"}, "properties": []},
        {"label": "Investigation", "key_property": {"name": "id", "type": "STRING"}, "properties": []},
        {"label": "Beneficiary", "key_property": {"name": "id", "type": "STRING"}, "properties": []},
        {"label": "Prescription", "key_property": {"name": "id", "type": "STRING"}, "properties": []},
        {"label": "Execution", "key_property": {"name": "id", "type": "STRING"}, "properties": []},
        {"label": "Care", "key_property": {"name": "id", "type": "STRING"}, "properties": []},
        {"label": "IP", "key_property": {"name": "id", "type": "STRING"}, "properties": []},
        {"label": "Employee", "key_property": {"name": "id", "type": "STRING"}, "properties": []},
        {"label": "Analyst", "key_property": {"name": "id", "type": "STRING"}, "properties": []},
        {"label": "HealthCarePro", "key_property": {"name": "id", "type": "STRING"}, "properties": []}
    ],
    "relationships": [
        {"type": "HAS", "start_node_label": "Person", "end_node_label": "Address"},
        {"type": "HAS", "start_node_label": "Person", "end_node_label": "Phone"},
        {"type": "HAS", "start_node_label": "Person", "end_node_label": "IBAN"},
        {"type": "HAS", "start_node_label": "Person", "end_node_label": "Photo"},
        {"type": "HAS", "start_node_label": "Person", "end_node_label": "IP"},
        {"type": "HAS_MANAGER", "start_node_label": "Person", "end_node_label": "Person"},
        {"type": "PRESCRIPTION_FOR", "start_node_label": "Person", "end_node_label": "Prescription"},
        {"type": "RESPONSIBLE_FOR", "start_node_label": "Person", "end_node_label": "Prescription"},
        {"type": "BENEFICIARY_FOR", "start_node_label": "Person", "end_node_label": "Execution"},
        {"type": "RESPONSIBLE_FOR", "start_node_label": "Person", "end_node_label": "Execution"},
        {"type": "CONTAINS", "start_node_label": "Prescription", "end_node_label": "Care"},
        {"type": "CONTAINS", "start_node_label": "Execution", "end_node_label": "Care"},
        {"type": "ABOUT", "start_node_label": "Investigation", "end_node_label": "Person"},
        {"type": "HAS_AUTHOR", "start_node_label": "Investigation", "end_node_label": "Person"},
        {"type": "INVOLVES", "start_node_label": "Investigation", "end_node_label": "Person"},
        {"type": "NEXT_STATUS", "start_node_label": "Investigation", "end_node_label": "Investigation"}
    ]
}
