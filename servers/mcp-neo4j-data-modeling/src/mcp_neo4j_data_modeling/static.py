DATA_INGEST_PROCESS = """
Follow these steps when ingesting data into Neo4j.
1. Create constraints before loading any data.
2. Load all nodes before relationships.
3. Then load relationships serially to avoid deadlocks.
"""

# Real-World Example: Patient Journey Healthcare Data Model
PATIENT_JOURNEY_MODEL = {
    "nodes": [
        {
            "label": "Patient",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "first",
                    "type": "STRING",
                    "description": "Patient's first name",
                },
                {
                    "name": "last",
                    "type": "STRING",
                    "description": "Patient's last name",
                },
                {
                    "name": "birthdate",
                    "type": "DATE",
                    "description": "Patient's date of birth",
                },
                {
                    "name": "gender",
                    "type": "STRING",
                    "description": "Patient's gender identity",
                },
                {
                    "name": "address",
                    "type": "STRING",
                    "description": "Patient's street address",
                },
                {
                    "name": "city",
                    "type": "STRING",
                    "description": "City where patient resides",
                },
                {
                    "name": "state",
                    "type": "STRING",
                    "description": "State/province where patient resides",
                },
                {
                    "name": "county",
                    "type": "STRING",
                    "description": "County where patient resides",
                },
                {
                    "name": "location",
                    "type": "POINT",
                    "description": "Geographic coordinates of patient's location",
                },
                {
                    "name": "latitude",
                    "type": "FLOAT",
                    "description": "Latitude coordinate of patient's location",
                },
                {
                    "name": "longitude",
                    "type": "FLOAT",
                    "description": "Longitude coordinate of patient's location",
                },
                {
                    "name": "ethnicity",
                    "type": "STRING",
                    "description": "Patient's ethnic background",
                },
                {
                    "name": "race",
                    "type": "STRING",
                    "description": "Patient's racial background",
                },
                {
                    "name": "martial",
                    "type": "STRING",
                    "description": "Patient's marital status",
                },
                {
                    "name": "prefix",
                    "type": "STRING",
                    "description": "Patient's name prefix (e.g., Dr., Mr., Ms.)",
                },
                {
                    "name": "birthplace",
                    "type": "STRING",
                    "description": "City/country where patient was born",
                },
                {
                    "name": "deathdate",
                    "type": "DATE",
                    "description": "Date of patient's death if deceased",
                },
                {
                    "name": "drivers",
                    "type": "STRING",
                    "description": "Patient's driver's license number",
                },
                {
                    "name": "healthcare_coverage",
                    "type": "FLOAT",
                    "description": "Amount of healthcare coverage in currency",
                },
                {
                    "name": "healthcare_expenses",
                    "type": "FLOAT",
                    "description": "Total healthcare expenses incurred",
                },
            ],
        },
        {
            "label": "Encounter",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "code",
                    "type": "STRING",
                    "description": "Encounter code or identifier",
                },
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Encounter description or reason for visit",
                },
                {
                    "name": "class",
                    "type": "STRING",
                    "description": "Encounter class (emergency, outpatient, inpatient, etc.)",
                },
                {
                    "name": "start",
                    "type": "STRING",
                    "description": "Encounter start date and time",
                },
                {
                    "name": "end",
                    "type": "STRING",
                    "description": "Encounter end date and time",
                },
                {
                    "name": "isStart",
                    "type": "BOOLEAN",
                    "description": "Whether this is the start of the encounter",
                },
                {
                    "name": "isEnd",
                    "type": "BOOLEAN",
                    "description": "Whether this is the end of the encounter",
                },
                {
                    "name": "baseCost",
                    "type": "FLOAT",
                    "description": "Base cost of the encounter",
                },
                {
                    "name": "claimCost",
                    "type": "FLOAT",
                    "description": "Claim cost for the encounter",
                },
                {
                    "name": "coveredAmount",
                    "type": "FLOAT",
                    "description": "Amount covered by insurance",
                },
            ],
        },
        {
            "label": "Provider",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Provider's full name",
                },
                {
                    "name": "address",
                    "type": "STRING",
                    "description": "Provider's practice address",
                },
                {
                    "name": "location",
                    "type": "POINT",
                    "description": "Geographic coordinates of provider's practice location",
                },
            ],
        },
        {
            "label": "Organization",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Healthcare organization name",
                },
                {
                    "name": "address",
                    "type": "STRING",
                    "description": "Organization's address",
                },
                {
                    "name": "city",
                    "type": "STRING",
                    "description": "City where organization is located",
                },
                {
                    "name": "location",
                    "type": "POINT",
                    "description": "Geographic coordinates of organization location",
                },
            ],
        },
        {
            "label": "Condition",
            "key_property": {"name": "code", "type": "STRING"},
            "properties": [
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Medical condition description",
                },
                {
                    "name": "start",
                    "type": "STRING",
                    "description": "Date when condition was diagnosed",
                },
                {
                    "name": "stop",
                    "type": "STRING",
                    "description": "Date when condition was resolved (Optional)",
                },
                {
                    "name": "isEnd",
                    "type": "BOOLEAN",
                    "description": "Indicates if condition is resolved",
                },
                {
                    "name": "total_drug_pairings",
                    "type": "INTEGER",
                    "description": "Number of drug combinations prescribed for this condition",
                },
            ],
        },
        {
            "label": "Drug",
            "key_property": {"name": "code", "type": "STRING"},
            "properties": [
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Drug description",
                },
                {
                    "name": "start",
                    "type": "STRING",
                    "description": "Date when drug was prescribed",
                },
                {
                    "name": "stop",
                    "type": "STRING",
                    "description": "Date when drug prescription ended (Optional), Conditional on isEnd property",
                },
                {
                    "name": "isEnd",
                    "type": "BOOLEAN",
                    "description": "Indicates if drug prescription is discontinued",
                },
                {
                    "name": "basecost",
                    "type": "STRING",
                    "description": "Base cost of the drug before insurance",
                },
                {
                    "name": "totalcost",
                    "type": "STRING",
                    "description": "Total cost of the drug including insurance",
                },
            ],
        },
        {
            "label": "Procedure",
            "key_property": {"name": "code", "type": "STRING"},
            "properties": [
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Medical procedure description",
                }
            ],
        },
        {
            "label": "Observation",
            "key_property": {"name": "code", "type": "STRING"},
            "properties": [
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Observation description",
                },
                {
                    "name": "category",
                    "type": "STRING",
                    "description": "Category of observation",
                },
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Type of observation measurement",
                },
            ],
        },
        {
            "label": "Device",
            "key_property": {"name": "code", "type": "STRING"},
            "properties": [
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Medical device description",
                }
            ],
        },
        {
            "label": "CarePlan",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "code",
                    "type": "STRING",
                    "description": "Care plan code or identifier",
                },
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Care plan description",
                },
                {
                    "name": "start",
                    "type": "STRING",
                    "description": "Date when care plan was initiated",
                },
                {
                    "name": "end",
                    "type": "STRING",
                    "description": "Date when care plan was completed (Optional) and conditional on isEnd property",
                },
                {
                    "name": "isEnd",
                    "type": "BOOLEAN",
                    "description": "Indicates if care plan is completed",
                },
                {
                    "name": "reasoncode",
                    "type": "STRING",
                    "description": "Reason code for care plan creation",
                },
            ],
        },
        {
            "label": "Allergy",
            "key_property": {"name": "code", "type": "STRING"},
            "properties": [
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Allergy description and symptoms",
                },
                {
                    "name": "category",
                    "type": "STRING",
                    "description": "Category of allergy",
                },
                {
                    "name": "system",
                    "type": "STRING",
                    "description": "Body system affected by the allergy",
                },
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Type of allergic reaction",
                },
            ],
        },
        {
            "label": "Reaction",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Description of allergic reaction symptoms",
                }
            ],
        },
        {
            "label": "Payer",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Insurance payer name",
                }
            ],
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
                {
                    "name": "date",
                    "type": "STRING",
                    "description": "Date when observation was recorded",
                },
                {
                    "name": "value",
                    "type": "STRING",
                    "description": "Observation value or result",
                },
                {
                    "name": "unit",
                    "type": "STRING",
                    "description": "Unit of measurement for the observation",
                },
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
            "properties": [
                {
                    "name": "start",
                    "type": "STRING",
                    "description": "Date when allergy was detected during encounter",
                }
            ],
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
            "properties": [
                {
                    "name": "severity",
                    "type": "STRING",
                    "description": "Severity level of the allergic reaction",
                }
            ],
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
            "properties": [
                {"name": "name", "type": "STRING", "description": "Product name"},
                {
                    "name": "category",
                    "type": "STRING",
                    "description": "Product category",
                },
                {
                    "name": "manufacturer",
                    "type": "STRING",
                    "description": "Manufacturer name",
                },
                {"name": "cost", "type": "FLOAT", "description": "Product unit cost"},
                {
                    "name": "weight",
                    "type": "FLOAT",
                    "description": "Product weight in kg",
                },
                {
                    "name": "dimensions",
                    "type": "STRING",
                    "description": "Product dimensions (LxWxH)",
                },
            ],
        },
        {
            "label": "Order",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "order_date",
                    "type": "DATE",
                    "description": "Date when order was placed",
                },
                {
                    "name": "delivery_date",
                    "type": "DATE",
                    "description": "Expected delivery date",
                },
                {
                    "name": "status",
                    "type": "STRING",
                    "description": "Order status (pending, shipped, delivered)",
                },
                {
                    "name": "total_amount",
                    "type": "FLOAT",
                    "description": "Total order value",
                },
                {
                    "name": "priority",
                    "type": "STRING",
                    "description": "Order priority level",
                },
            ],
        },
        {
            "label": "Inventory",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "quantity",
                    "type": "INTEGER",
                    "description": "Available quantity in stock",
                },
                {
                    "name": "min_threshold",
                    "type": "INTEGER",
                    "description": "Minimum stock level for reorder",
                },
                {
                    "name": "max_capacity",
                    "type": "INTEGER",
                    "description": "Maximum storage capacity",
                },
                {
                    "name": "last_updated",
                    "type": "DATETIME",
                    "description": "Last inventory update timestamp",
                },
            ],
        },
        {
            "label": "Location",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Location name (warehouse, store, etc.)",
                },
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Location type (warehouse, retail, distribution center)",
                },
                {
                    "name": "capacity",
                    "type": "INTEGER",
                    "description": "Storage capacity in units",
                },
                {
                    "name": "coordinates",
                    "type": "POINT",
                    "description": "Geographic coordinates of location",
                },
            ],
        },
        {
            "label": "LegalEntity",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Company or organization name",
                },
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Entity type (supplier, customer, manufacturer)",
                },
                {
                    "name": "tax_id",
                    "type": "STRING",
                    "description": "Tax identification number",
                },
                {
                    "name": "country",
                    "type": "STRING",
                    "description": "Country of registration",
                },
            ],
        },
        {
            "label": "Asset",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING", "description": "Asset name"},
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Asset type (equipment, vehicle, building)",
                },
                {
                    "name": "purchase_date",
                    "type": "DATE",
                    "description": "Date when asset was acquired",
                },
                {
                    "name": "value",
                    "type": "FLOAT",
                    "description": "Asset value or cost",
                },
            ],
        },
        {
            "label": "BOM",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Bill of Materials name",
                },
                {
                    "name": "version",
                    "type": "STRING",
                    "description": "BOM version number",
                },
                {
                    "name": "effective_date",
                    "type": "DATE",
                    "description": "Date when BOM becomes effective",
                },
            ],
        },
        {
            "label": "Address",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "street", "type": "STRING", "description": "Street address"},
                {"name": "city", "type": "STRING", "description": "City name"},
                {"name": "state", "type": "STRING", "description": "State or province"},
                {
                    "name": "postal_code",
                    "type": "STRING",
                    "description": "Postal or ZIP code",
                },
                {"name": "country", "type": "STRING", "description": "Country name"},
            ],
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
            "label": "BadActor",
            "key_property": {"name": "id", "type": "INTEGER"},
            "properties": [
                {
                    "name": "contributions",
                    "type": "INTEGER",
                    "description": "Number of contributions made by the bad actor",
                },
                {
                    "name": "login",
                    "type": "STRING",
                    "description": "Bad actor's login username",
                },
            ],
        },
        {
            "label": "CVE",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "CVE vulnerability description",
                },
                {
                    "name": "severity",
                    "type": "STRING",
                    "description": "CVE severity level (low, medium, high, critical)",
                },
            ],
        },
        {
            "label": "Commit",
            "key_property": {"name": "sha", "type": "STRING"},
            "properties": [
                {
                    "name": "repository",
                    "type": "STRING",
                    "description": "Repository name where commit was made",
                },
            ],
        },
        {
            "label": "Contributor",
            "key_property": {"name": "id", "type": "INTEGER"},
            "properties": [
                {
                    "name": "contributions",
                    "type": "INTEGER",
                    "description": "Number of contributions made by the contributor",
                },
                {
                    "name": "login",
                    "type": "STRING",
                    "description": "Contributor's login username",
                },
            ],
        },
        {
            "label": "Customer",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Dependency",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "artifactId",
                    "type": "STRING",
                    "description": "Maven artifact ID",
                },
                {"name": "groupId", "type": "STRING", "description": "Maven group ID"},
                {
                    "name": "version",
                    "type": "STRING",
                    "description": "Dependency version",
                },
            ],
        },
        {
            "label": "Issue",
            "key_property": {"name": "id", "type": "INTEGER"},
            "properties": [
                {"name": "body", "type": "STRING", "description": "Issue body text"},
                {
                    "name": "comments",
                    "type": "INTEGER",
                    "description": "Number of comments on the issue",
                },
                {
                    "name": "createdAt",
                    "type": "STRING",
                    "description": "Issue creation date",
                },
                {
                    "name": "htmlUrl",
                    "type": "STRING",
                    "description": "HTML URL for the issue",
                },
                {
                    "name": "severity",
                    "type": "STRING",
                    "description": "Issue severity level",
                },
                {
                    "name": "state",
                    "type": "STRING",
                    "description": "Issue state (open, closed, etc.)",
                },
                {"name": "title", "type": "STRING", "description": "Issue title"},
                {
                    "name": "updatedAt",
                    "type": "STRING",
                    "description": "Issue last update date",
                },
                {"name": "url", "type": "STRING", "description": "Issue URL"},
            ],
        },
        {
            "label": "Organization",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Pom",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "filePath", "type": "STRING", "description": "POM file path"},
                {
                    "name": "parentDirectory",
                    "type": "STRING",
                    "description": "Parent directory path",
                },
            ],
        },
        {
            "label": "Product",
            "key_property": {"name": "serialNumber", "type": "STRING"},
            "properties": [
                {
                    "name": "macAddress",
                    "type": "STRING",
                    "description": "Product MAC address",
                },
                {"name": "name", "type": "STRING", "description": "Product name"},
                {
                    "name": "softwareVersion",
                    "type": "STRING",
                    "description": "Software version installed on product",
                },
            ],
        },
        {
            "label": "Project",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "SuspectCommit",
            "key_property": {"name": "sha", "type": "STRING"},
            "properties": [
                {
                    "name": "repository",
                    "type": "STRING",
                    "description": "Repository name where suspect commit was made",
                },
            ],
        },
        {
            "label": "SuspectOrg",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "User",
            "key_property": {"name": "id", "type": "INTEGER"},
            "properties": [
                {
                    "name": "login",
                    "type": "STRING",
                    "description": "User's login username",
                },
            ],
        },
    ],
    "relationships": [
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
            "type": "BELONGS_TO_PROJECT",
            "start_node_label": "Pom",
            "end_node_label": "Project",
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
            "type": "CREATED_BY",
            "start_node_label": "Issue",
            "end_node_label": "User",
        },
        {
            "type": "DEPENDS_ON",
            "start_node_label": "Pom",
            "end_node_label": "Dependency",
        },
        {
            "type": "HAS_COMMIT",
            "start_node_label": "BadActor",
            "end_node_label": "Commit",
        },
        {
            "type": "HAS_COMMIT",
            "start_node_label": "Contributor",
            "end_node_label": "Commit",
        },
        {
            "type": "HAS_HEAD_COMMIT",
            "start_node_label": "Project",
            "end_node_label": "Commit",
        },
        {
            "type": "HAS_ISSUE",
            "start_node_label": "Project",
            "end_node_label": "Issue",
        },
        {
            "type": "INSTALLED_ON",
            "start_node_label": "Project",
            "end_node_label": "Product",
        },
        {
            "type": "NEXT_COMMIT",
            "start_node_label": "SuspectCommit",
            "end_node_label": "Commit",
        },
        {
            "type": "NEXT_COMMIT",
            "start_node_label": "Commit",
            "end_node_label": "SuspectCommit",
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
        {
            "type": "NEXT_COMMIT",
            "start_node_label": "Commit",
            "end_node_label": "Commit",
        },
        {
            "type": "NEXT_COMMIT",
            "start_node_label": "Commit",
            "end_node_label": "Commit",
        },
        {
            "type": "PURCHASED",
            "start_node_label": "Customer",
            "end_node_label": "Product",
        },
    ],
}

# Real-World Example: Oil & Gas Equipment Monitoring
OIL_GAS_MONITORING_MODEL = {
    "nodes": [
        {
            "label": "Alert",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "status",
                    "type": "STRING",
                    "description": "Alert status (active, resolved, acknowledged)",
                },
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Alert type (pressure, temperature, flow, level)",
                },
            ],
        },
        {
            "label": "Basin",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Battery",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "location",
                    "type": "POINT",
                    "description": "Battery location coordinates",
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Battery name or identifier",
                },
            ],
        },
        {
            "label": "CollectionPoint",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "location",
                    "type": "POINT",
                    "description": "Collection point location coordinates",
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Collection point name or identifier",
                },
            ],
        },
        {
            "label": "Equipment",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Equipment type (compressor, pump, valve, etc.)",
                },
            ],
        },
        {
            "label": "EquipmentServiceProvider",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "companyName",
                    "type": "STRING",
                    "description": "Service provider company name",
                },
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Service provider type",
                },
            ],
        },
        {
            "label": "FlowSensor",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "type", "type": "STRING", "description": "Flow sensor type"},
            ],
        },
        {
            "label": "FreeWaterKnockOut",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Free water knock out type",
                },
            ],
        },
        {
            "label": "GasCompressor",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Gas compressor type",
                },
            ],
        },
        {
            "label": "HeaterTreater",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Heater treater type",
                },
            ],
        },
        {
            "label": "HighLevel",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "status",
                    "type": "STRING",
                    "description": "High level status",
                },
                {"name": "type", "type": "STRING", "description": "High level type"},
            ],
        },
        {
            "label": "LACT",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "LACT (Lease Automatic Custody Transfer) type",
                },
            ],
        },
        {
            "label": "Lease",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "coordinates",
                    "type": "STRING",
                    "description": "Lease coordinates",
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Lease name or identifier",
                },
            ],
        },
        {
            "label": "LeaseOperator",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Lease operator name",
                },
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Lease operator type",
                },
            ],
        },
        {
            "label": "Level",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "type", "type": "STRING", "description": "Level sensor type"},
            ],
        },
        {
            "label": "MaintenanceRecord",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "date",
                    "type": "STRING",
                    "description": "Maintenance record date",
                },
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Maintenance description",
                },
                {
                    "name": "downTime",
                    "type": "FLOAT",
                    "description": "Downtime in hours",
                },
                {"name": "type", "type": "STRING", "description": "Maintenance type"},
            ],
        },
        {
            "label": "Model",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Equipment model type",
                },
            ],
        },
        {
            "label": "OilLease",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "coordinates",
                    "type": "STRING",
                    "description": "Oil lease coordinates",
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Oil lease name or identifier",
                },
            ],
        },
        {
            "label": "OilPipeline",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "end",
                    "type": "POINT",
                    "description": "Pipeline end point coordinates",
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Pipeline name or identifier",
                },
                {
                    "name": "start",
                    "type": "POINT",
                    "description": "Pipeline start point coordinates",
                },
            ],
        },
        {
            "label": "OilTank",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "type", "type": "STRING", "description": "Oil tank type"},
            ],
        },
        {
            "label": "OilWell",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "location",
                    "type": "POINT",
                    "description": "Oil well location coordinates",
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Oil well name or identifier",
                },
            ],
        },
        {
            "label": "PipelineStation",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "location",
                    "type": "POINT",
                    "description": "Pipeline station location coordinates",
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Pipeline station name or identifier",
                },
            ],
        },
        {
            "label": "PressureSensor",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Pressure sensor type",
                },
            ],
        },
        {
            "label": "Producer",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "location",
                    "type": "POINT",
                    "description": "Producer location coordinates",
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Producer name or identifier",
                },
            ],
        },
        {
            "label": "PumpOffControl",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Pump off control type",
                },
            ],
        },
        {
            "label": "SWD",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Sensor",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Sensor type (flow, pressure, temperature, level)",
                },
            ],
        },
        {
            "label": "ServiceProvider",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "companyName",
                    "type": "STRING",
                    "description": "Service provider company name",
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Service provider name",
                },
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Service provider type",
                },
            ],
        },
        {
            "label": "Temperature",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Temperature sensor type",
                },
            ],
        },
        {
            "label": "TransmissionRoute",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "end",
                    "type": "POINT",
                    "description": "Transmission route end point coordinates",
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Transmission route name or identifier",
                },
                {
                    "name": "start",
                    "type": "POINT",
                    "description": "Transmission route start point coordinates",
                },
            ],
        },
        {
            "label": "Vessel",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Vessel type (tank, separator, etc.)",
                },
            ],
        },
        {
            "label": "WaterTank",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "type", "type": "STRING", "description": "Water tank type"},
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
            "type": "COLLECTED_BY",
            "start_node_label": "CollectionPoint",
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
            "type": "HAS_ALERT",
            "start_node_label": "CollectionPoint",
            "end_node_label": "Alert",
        },
        {
            "type": "HAS_ALERT",
            "start_node_label": "Equipment",
            "end_node_label": "Alert",
        },
        {
            "type": "HAS_ALERT",
            "start_node_label": "Vessel",
            "end_node_label": "Alert",
        },
        {
            "type": "HAS_MAINTENANCE_RECORD",
            "start_node_label": "Equipment",
            "end_node_label": "MaintenanceRecord",
        },
        {
            "type": "HAS_MAINTENANCE_RECORD",
            "start_node_label": "Producer",
            "end_node_label": "MaintenanceRecord",
        },
        {
            "type": "HAS_MODEL",
            "start_node_label": "Equipment",
            "end_node_label": "Model",
        },
        {
            "type": "LOCATED_AT",
            "start_node_label": "Vessel",
            "end_node_label": "CollectionPoint",
        },
        {
            "type": "LOCATED_AT",
            "start_node_label": "Equipment",
            "end_node_label": "CollectionPoint",
        },
        {
            "type": "LOCATED_IN",
            "start_node_label": "Producer",
            "end_node_label": "Basin",
        },
        {
            "type": "LOCATED_ON",
            "start_node_label": "CollectionPoint",
            "end_node_label": "Lease",
        },
        {
            "type": "LOCATED_ON",
            "start_node_label": "Producer",
            "end_node_label": "Lease",
        },
        {
            "type": "MODEL_OF",
            "start_node_label": "Vessel",
            "end_node_label": "Model",
        },
        {
            "type": "MODEL_OF",
            "start_node_label": "Equipment",
            "end_node_label": "Model",
        },
        {
            "type": "MONITORED_BY",
            "start_node_label": "CollectionPoint",
            "end_node_label": "Sensor",
        },
        {
            "type": "MONITORED_BY",
            "start_node_label": "Producer",
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
        {
            "type": "RAISED",
            "start_node_label": "Sensor",
            "end_node_label": "Alert",
        },
        {
            "type": "SERVICED_BY",
            "start_node_label": "Lease",
            "end_node_label": "ServiceProvider",
        },
        {
            "type": "SERVICED_BY",
            "start_node_label": "Producer",
            "end_node_label": "ServiceProvider",
        },
        {
            "type": "SERVICED_BY",
            "start_node_label": "Equipment",
            "end_node_label": "ServiceProvider",
        },
        {
            "type": "SERVICED_BY",
            "start_node_label": "CollectionPoint",
            "end_node_label": "ServiceProvider",
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
            "properties": [
                {
                    "name": "account_name",
                    "type": "STRING",
                    "description": "Account or company name",
                },
            ],
        },
        {
            "label": "Address",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "city", "type": "STRING", "description": "City name"},
                {"name": "country", "type": "STRING", "description": "Country name"},
                {
                    "name": "subRegion",
                    "type": "STRING",
                    "description": "State or province",
                },
            ],
        },
        {
            "label": "Aspect",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Aspect description - aspects are extracted from surveys using NLP techniques",
                },
            ],
        },
        {
            "label": "Contact",
            "key_property": {"name": "contact_id", "type": "STRING"},
            "properties": [
                {
                    "name": "job_function",
                    "type": "STRING",
                    "description": "Job function or department",
                },
                {
                    "name": "job_role",
                    "type": "STRING",
                    "description": "Specific job role",
                },
                {"name": "title", "type": "STRING", "description": "Job title"},
            ],
        },
        {
            "label": "Country",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "DataCenter",
            "key_property": {"name": "name", "type": "STRING"},
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
            "label": "EscalationTicket",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "receipt_date",
                    "type": "DATE",
                    "description": "Date when escalation was received",
                },
                {
                    "name": "response_id",
                    "type": "STRING",
                    "description": "Response identifier",
                },
                {
                    "name": "status",
                    "type": "STRING",
                    "description": "Escalation status",
                },
            ],
        },
        {
            "label": "IncidentCategory",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "IncidentTicket",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "declared_date",
                    "type": "DATE",
                    "description": "Date when incident was declared",
                },
                {
                    "name": "highest_color",
                    "type": "STRING",
                    "description": "Highest severity color",
                },
                {
                    "name": "incident_number",
                    "type": "STRING",
                    "description": "Incident number",
                },
                {"name": "status", "type": "STRING", "description": "Incident status"},
            ],
        },
        {
            "label": "Industry",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Metro",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Milestone",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Order",
            "key_property": {"name": "order_number", "type": "STRING"},
            "properties": [
                {
                    "name": "order_complete_date",
                    "type": "DATE",
                    "description": "Date when order was completed",
                },
                {
                    "name": "order_create_date",
                    "type": "DATE",
                    "description": "Date when order was created",
                },
                {
                    "name": "source",
                    "type": "STRING",
                    "description": "Order source (web, phone, sales rep)",
                },
            ],
        },
        {
            "label": "OrderType",
            "key_property": {"name": "type", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "ParentAccount",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Persona",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Product",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Question",
            "key_property": {"name": "text", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Region",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "RootCause",
            "key_property": {"name": "type", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "SalesProgramType",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Segment",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Service",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "SubOrderType",
            "key_property": {"name": "type", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Survey",
            "key_property": {"name": "record_id", "type": "STRING"},
            "properties": [
                {
                    "name": "duration",
                    "type": "INTEGER",
                    "description": "Survey duration in seconds",
                },
                {"name": "end_date", "type": "DATE", "description": "Survey end date"},
                {
                    "name": "end_timestamp",
                    "type": "INTEGER",
                    "description": "Survey end timestamp",
                },
                {
                    "name": "nps_group",
                    "type": "STRING",
                    "description": "Net Promoter Score group",
                },
                {
                    "name": "qid1",
                    "type": "STRING",
                    "description": "Question 1 response",
                },
                {
                    "name": "qid2_1",
                    "type": "STRING",
                    "description": "Question 2.1 response",
                },
                {
                    "name": "qid2_2",
                    "type": "STRING",
                    "description": "Question 2.2 response",
                },
                {
                    "name": "qid2_3",
                    "type": "STRING",
                    "description": "Question 2.3 response",
                },
                {
                    "name": "qid2_4",
                    "type": "STRING",
                    "description": "Question 2.4 response",
                },
                {
                    "name": "qid4",
                    "type": "STRING",
                    "description": "Question 4 response",
                },
                {
                    "name": "recorded_date",
                    "type": "DATE",
                    "description": "Date when survey was recorded",
                },
                {
                    "name": "sentiment",
                    "type": "STRING",
                    "description": "Sentiment analysis result",
                },
                {
                    "name": "start_date",
                    "type": "DATE",
                    "description": "Survey start date",
                },
                {
                    "name": "start_timestamp",
                    "type": "INTEGER",
                    "description": "Survey start timestamp",
                },
                {
                    "name": "status",
                    "type": "STRING",
                    "description": "Survey completion status",
                },
                {
                    "name": "survey_response",
                    "type": "STRING",
                    "description": "Survey response text",
                },
            ],
        },
        {
            "label": "SurveyType",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "Theme",
            "key_property": {"name": "name", "type": "STRING"},
            "properties": [
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Theme description - themes are extracted from surveys using NLP techniques",
                },
            ],
        },
        {
            "label": "Ticket",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "TicketCode",
            "key_property": {"name": "code_name", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "TicketType",
            "key_property": {"name": "type", "type": "STRING"},
            "properties": [],
        },
        {
            "label": "TroubleTicket",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "created_date",
                    "type": "STRING",
                    "description": "Ticket creation date",
                },
                {
                    "name": "days_difference",
                    "type": "STRING",
                    "description": "Days between creation and resolution",
                },
                {
                    "name": "resolution_date",
                    "type": "STRING",
                    "description": "Ticket resolution date",
                },
                {
                    "name": "severity",
                    "type": "STRING",
                    "description": "Ticket severity level",
                },
                {"name": "status", "type": "STRING", "description": "Ticket status"},
                {
                    "name": "ticket_number",
                    "type": "STRING",
                    "description": "Ticket number",
                },
            ],
        },
    ],
    "relationships": [
        {
            "type": "ACCOUNT_CONTACT",
            "start_node_label": "Account",
            "end_node_label": "Contact",
        },
        {
            "type": "AFFECTED_SERVICE",
            "start_node_label": "Ticket",
            "end_node_label": "Service",
        },
        {
            "type": "COMPLETED_SURVEY",
            "start_node_label": "Account",
            "end_node_label": "Survey",
        },
        {
            "type": "CONTACT_CREATED_TICKET",
            "start_node_label": "Contact",
            "end_node_label": "Ticket",
        },
        {
            "type": "CREATED_TICKET",
            "start_node_label": "Account",
            "end_node_label": "Ticket",
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
            "type": "FILLED_BY",
            "start_node_label": "Survey",
            "end_node_label": "Contact",
        },
        {
            "type": "FOR_PRODUCT",
            "start_node_label": "Order",
            "end_node_label": "Product",
        },
        {
            "type": "HAS_ADDRESS",
            "start_node_label": "Account",
            "end_node_label": "Address",
        },
        {
            "type": "HAS_ASPECT",
            "start_node_label": "Survey",
            "end_node_label": "Aspect",
        },
        {
            "type": "HAS_ESCALATION_SUB_CATEGORY",
            "start_node_label": "EscalationCategory",
            "end_node_label": "EscalationSubCategory",
        },
        {
            "type": "HAS_INDUSTRY",
            "start_node_label": "Account",
            "end_node_label": "Industry",
        },
        {
            "type": "HAS_MILESTONE",
            "start_node_label": "SurveyType",
            "end_node_label": "Milestone",
        },
        {
            "type": "HAS_PERSONA",
            "start_node_label": "Contact",
            "end_node_label": "Persona",
        },
        {
            "type": "HAS_PROBLEM_CODE",
            "start_node_label": "Ticket",
            "end_node_label": "TicketCode",
        },
        {
            "type": "HAS_QUESTION",
            "start_node_label": "SurveyType",
            "end_node_label": "Question",
        },
        {
            "type": "HAS_ROOT_CAUSE",
            "start_node_label": "Ticket",
            "end_node_label": "RootCause",
        },
        {
            "type": "HAS_SURVEY_TYPE",
            "start_node_label": "Survey",
            "end_node_label": "SurveyType",
        },
        {
            "type": "HAS_THEME",
            "start_node_label": "Survey",
            "end_node_label": "Theme",
        },
        {
            "type": "HAS_TICKET_TYPE",
            "start_node_label": "Ticket",
            "end_node_label": "TicketType",
        },
        {
            "type": "INCIDENT_CATEGORY",
            "start_node_label": "Ticket",
            "end_node_label": "IncidentCategory",
        },
        {
            "type": "IN_COUNTRY",
            "start_node_label": "Metro",
            "end_node_label": "Country",
        },
        {
            "type": "IN_METRO",
            "start_node_label": "DataCenter",
            "end_node_label": "Metro",
        },
        {
            "type": "IN_REGION",
            "start_node_label": "Country",
            "end_node_label": "Region",
        },
        {
            "type": "IN_SEGMENT",
            "start_node_label": "Account",
            "end_node_label": "Segment",
        },
        {
            "type": "ORDER_TYPE",
            "start_node_label": "SubOrderType",
            "end_node_label": "OrderType",
        },
        {
            "type": "PARENT_ACCOUNT",
            "start_node_label": "Account",
            "end_node_label": "ParentAccount",
        },
        {
            "type": "PLACES_ORDER",
            "start_node_label": "Account",
            "end_node_label": "Order",
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
        },
        {
            "type": "RESPONDED_TO",
            "start_node_label": "Survey",
            "end_node_label": "Question",
        },
        {
            "type": "SALES_PROGRAM_TYPE",
            "start_node_label": "Account",
            "end_node_label": "SalesProgramType",
        },
        {
            "type": "SUB_ORDER_TYPE",
            "start_node_label": "Order",
            "end_node_label": "SubOrderType",
        },
        {
            "type": "THEME_HAS_ASPECT",
            "start_node_label": "Theme",
            "end_node_label": "Aspect",
        },
        {
            "type": "TICKET_FOR_PRODUCT",
            "start_node_label": "Ticket",
            "end_node_label": "Product",
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
                {"name": "name", "type": "STRING", "description": "Customer full name"},
                {
                    "name": "date_of_birth",
                    "type": "DATE",
                    "description": "Customer date of birth",
                },
                {
                    "name": "nationality",
                    "type": "STRING",
                    "description": "Customer nationality",
                },
                {
                    "name": "risk_level",
                    "type": "STRING",
                    "description": "Customer risk level (low, medium, high)",
                },
            ],
        },
        {
            "label": "Account",
            "key_property": {"name": "account_number", "type": "STRING"},
            "properties": [
                {
                    "name": "account_type",
                    "type": "STRING",
                    "description": "Account type (checking, savings, business)",
                },
                {
                    "name": "balance",
                    "type": "FLOAT",
                    "description": "Current account balance",
                },
                {
                    "name": "opening_date",
                    "type": "DATE",
                    "description": "Account opening date",
                },
                {
                    "name": "status",
                    "type": "STRING",
                    "description": "Account status (active, frozen, closed)",
                },
            ],
        },
        {
            "label": "Transaction",
            "key_property": {"name": "transaction_id", "type": "STRING"},
            "properties": [
                {
                    "name": "amount",
                    "type": "FLOAT",
                    "description": "Transaction amount",
                },
                {
                    "name": "currency",
                    "type": "STRING",
                    "description": "Transaction currency",
                },
                {
                    "name": "transaction_date",
                    "type": "DATETIME",
                    "description": "Transaction timestamp",
                },
                {
                    "name": "transaction_type",
                    "type": "STRING",
                    "description": "Transaction type (transfer, deposit, withdrawal)",
                },
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Transaction description",
                },
            ],
        },
        {
            "label": "Counterparty",
            "key_property": {"name": "counterparty_id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING", "description": "Counterparty name"},
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Counterparty type (individual, business, bank)",
                },
                {
                    "name": "country",
                    "type": "STRING",
                    "description": "Counterparty country",
                },
                {
                    "name": "risk_score",
                    "type": "INTEGER",
                    "description": "Counterparty risk score",
                },
            ],
        },
        {
            "label": "Alert",
            "key_property": {"name": "alert_id", "type": "STRING"},
            "properties": [
                {
                    "name": "alert_type",
                    "type": "STRING",
                    "description": "Alert type (suspicious activity, large transaction, etc.)",
                },
                {
                    "name": "severity",
                    "type": "STRING",
                    "description": "Alert severity (low, medium, high, critical)",
                },
                {
                    "name": "created_date",
                    "type": "DATETIME",
                    "description": "Alert creation timestamp",
                },
                {
                    "name": "status",
                    "type": "STRING",
                    "description": "Alert status (new, reviewed, closed)",
                },
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Alert description and details",
                },
            ],
        },
        {
            "label": "Case",
            "key_property": {"name": "case_id", "type": "STRING"},
            "properties": [
                {
                    "name": "case_type",
                    "type": "STRING",
                    "description": "Case type (fraud investigation, aml review)",
                },
                {
                    "name": "priority",
                    "type": "STRING",
                    "description": "Case priority (low, medium, high, urgent)",
                },
                {
                    "name": "created_date",
                    "type": "DATETIME",
                    "description": "Case creation timestamp",
                },
                {
                    "name": "status",
                    "type": "STRING",
                    "description": "Case status (open, in progress, closed)",
                },
                {
                    "name": "assigned_to",
                    "type": "STRING",
                    "description": "Case assigned investigator",
                },
            ],
        },
        {
            "label": "Document",
            "key_property": {"name": "document_id", "type": "STRING"},
            "properties": [
                {
                    "name": "document_type",
                    "type": "STRING",
                    "description": "Document type (id, proof of address, bank statement)",
                },
                {
                    "name": "upload_date",
                    "type": "DATETIME",
                    "description": "Document upload timestamp",
                },
                {
                    "name": "status",
                    "type": "STRING",
                    "description": "Document status (pending, verified, rejected)",
                },
                {
                    "name": "file_path",
                    "type": "STRING",
                    "description": "Document file path",
                },
            ],
        },
        {
            "label": "RiskAssessment",
            "key_property": {"name": "assessment_id", "type": "STRING"},
            "properties": [
                {
                    "name": "assessment_date",
                    "type": "DATETIME",
                    "description": "Risk assessment date",
                },
                {
                    "name": "risk_score",
                    "type": "INTEGER",
                    "description": "Risk score (1-100)",
                },
                {
                    "name": "risk_factors",
                    "type": "STRING",
                    "description": "Identified risk factors",
                },
                {
                    "name": "recommendations",
                    "type": "STRING",
                    "description": "Risk mitigation recommendations",
                },
            ],
        },
        {
            "label": "ComplianceRule",
            "key_property": {"name": "rule_id", "type": "STRING"},
            "properties": [
                {
                    "name": "rule_name",
                    "type": "STRING",
                    "description": "Compliance rule name",
                },
                {
                    "name": "rule_type",
                    "type": "STRING",
                    "description": "Rule type (transaction limit, frequency, pattern)",
                },
                {
                    "name": "threshold",
                    "type": "FLOAT",
                    "description": "Rule threshold value",
                },
                {
                    "name": "description",
                    "type": "STRING",
                    "description": "Rule description and criteria",
                },
            ],
        },
        {
            "label": "SanctionList",
            "key_property": {"name": "list_id", "type": "STRING"},
            "properties": [
                {
                    "name": "list_name",
                    "type": "STRING",
                    "description": "Sanction list name",
                },
                {
                    "name": "source",
                    "type": "STRING",
                    "description": "List source (OFAC, UN, EU)",
                },
                {
                    "name": "last_updated",
                    "type": "DATETIME",
                    "description": "Last update timestamp",
                },
            ],
        },
        {
            "label": "SanctionedEntity",
            "key_property": {"name": "entity_id", "type": "STRING"},
            "properties": [
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Sanctioned entity name",
                },
                {
                    "name": "entity_type",
                    "type": "STRING",
                    "description": "Entity type (individual, organization, vessel)",
                },
                {
                    "name": "country",
                    "type": "STRING",
                    "description": "Entity's country of origin",
                },
                {
                    "name": "sanction_date",
                    "type": "DATE",
                    "description": "Date when entity was sanctioned",
                },
            ],
        },
        {
            "label": "Device",
            "key_property": {"name": "device_id", "type": "STRING"},
            "properties": [
                {
                    "name": "device_type",
                    "type": "STRING",
                    "description": "Device type (mobile, desktop, tablet)",
                },
                {
                    "name": "ip_address",
                    "type": "STRING",
                    "description": "Device IP address",
                },
                {
                    "name": "location",
                    "type": "STRING",
                    "description": "Device location",
                },
                {
                    "name": "last_used",
                    "type": "DATETIME",
                    "description": "Last time device was used",
                },
            ],
        },
        {
            "label": "Location",
            "key_property": {"name": "location_id", "type": "STRING"},
            "properties": [
                {"name": "country", "type": "STRING", "description": "Country name"},
                {"name": "city", "type": "STRING", "description": "City name"},
                {
                    "name": "risk_level",
                    "type": "STRING",
                    "description": "Location risk level (low, medium, high)",
                },
            ],
        },
        {
            "label": "Product",
            "key_property": {"name": "product_id", "type": "STRING"},
            "properties": [
                {
                    "name": "product_name",
                    "type": "STRING",
                    "description": "Product name",
                },
                {
                    "name": "product_type",
                    "type": "STRING",
                    "description": "Product type",
                },
                {
                    "name": "risk_category",
                    "type": "STRING",
                    "description": "Product risk category",
                },
            ],
        },
        {
            "label": "Employee",
            "key_property": {"name": "employee_id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING", "description": "Employee name"},
                {"name": "role", "type": "STRING", "description": "Employee role"},
                {
                    "name": "department",
                    "type": "STRING",
                    "description": "Employee department",
                },
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
        {
            "label": "Person",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING", "description": "Person's full name"},
                {
                    "name": "date_of_birth",
                    "type": "DATE",
                    "description": "Person's date of birth",
                },
                {
                    "name": "nationality",
                    "type": "STRING",
                    "description": "Person's nationality",
                },
                {
                    "name": "role",
                    "type": "STRING",
                    "description": "Person's role (patient, provider, beneficiary)",
                },
            ],
        },
        {
            "label": "Address",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "street", "type": "STRING", "description": "Street address"},
                {"name": "city", "type": "STRING", "description": "City name"},
                {"name": "postal_code", "type": "STRING", "description": "Postal code"},
                {"name": "country", "type": "STRING", "description": "Country name"},
            ],
        },
        {
            "label": "Phone",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "number", "type": "STRING", "description": "Phone number"},
                {
                    "name": "type",
                    "type": "STRING",
                    "description": "Phone type (mobile, landline)",
                },
                {
                    "name": "country_code",
                    "type": "STRING",
                    "description": "Country calling code",
                },
            ],
        },
        {
            "label": "IBAN",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "account_number",
                    "type": "STRING",
                    "description": "IBAN account number",
                },
                {"name": "bank_name", "type": "STRING", "description": "Bank name"},
                {"name": "country", "type": "STRING", "description": "Bank country"},
            ],
        },
        {
            "label": "Photo",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "file_path",
                    "type": "STRING",
                    "description": "Photo file path",
                },
                {
                    "name": "upload_date",
                    "type": "DATETIME",
                    "description": "Photo upload date",
                },
                {
                    "name": "verification_status",
                    "type": "STRING",
                    "description": "Photo verification status",
                },
            ],
        },
        {
            "label": "Investigation",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "case_number",
                    "type": "STRING",
                    "description": "Investigation case number",
                },
                {
                    "name": "status",
                    "type": "STRING",
                    "description": "Investigation status",
                },
                {
                    "name": "priority",
                    "type": "STRING",
                    "description": "Investigation priority level",
                },
                {
                    "name": "created_date",
                    "type": "DATETIME",
                    "description": "Investigation creation date",
                },
                {
                    "name": "fraud_type",
                    "type": "STRING",
                    "description": "Type of fraud being investigated",
                },
            ],
        },
        {
            "label": "Beneficiary",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING", "description": "Beneficiary name"},
                {
                    "name": "relationship",
                    "type": "STRING",
                    "description": "Relationship to policyholder",
                },
                {
                    "name": "coverage_type",
                    "type": "STRING",
                    "description": "Type of coverage",
                },
            ],
        },
        {
            "label": "Prescription",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "medication_name",
                    "type": "STRING",
                    "description": "Prescribed medication name",
                },
                {
                    "name": "dosage",
                    "type": "STRING",
                    "description": "Prescribed dosage",
                },
                {
                    "name": "quantity",
                    "type": "INTEGER",
                    "description": "Prescribed quantity",
                },
                {
                    "name": "prescription_date",
                    "type": "DATE",
                    "description": "Date prescription was written",
                },
                {
                    "name": "refills",
                    "type": "INTEGER",
                    "description": "Number of refills allowed",
                },
            ],
        },
        {
            "label": "Execution",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "execution_date",
                    "type": "DATE",
                    "description": "Date prescription was filled",
                },
                {
                    "name": "pharmacy_name",
                    "type": "STRING",
                    "description": "Pharmacy where filled",
                },
                {"name": "cost", "type": "FLOAT", "description": "Cost of medication"},
                {
                    "name": "insurance_coverage",
                    "type": "FLOAT",
                    "description": "Amount covered by insurance",
                },
            ],
        },
        {
            "label": "Care",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "care_type",
                    "type": "STRING",
                    "description": "Type of care provided",
                },
                {
                    "name": "diagnosis",
                    "type": "STRING",
                    "description": "Medical diagnosis",
                },
                {
                    "name": "treatment_date",
                    "type": "DATE",
                    "description": "Date of treatment",
                },
                {"name": "cost", "type": "FLOAT", "description": "Cost of care"},
            ],
        },
        {
            "label": "IP",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "ip_address", "type": "STRING", "description": "IP address"},
                {
                    "name": "location",
                    "type": "STRING",
                    "description": "Geographic location",
                },
                {
                    "name": "isp",
                    "type": "STRING",
                    "description": "Internet service provider",
                },
                {
                    "name": "last_used",
                    "type": "DATETIME",
                    "description": "Last time IP was used",
                },
            ],
        },
        {
            "label": "Employee",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING", "description": "Employee name"},
                {
                    "name": "department",
                    "type": "STRING",
                    "description": "Employee department",
                },
                {"name": "role", "type": "STRING", "description": "Employee role"},
                {
                    "name": "employee_id",
                    "type": "STRING",
                    "description": "Employee ID number",
                },
            ],
        },
        {
            "label": "Analyst",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {"name": "name", "type": "STRING", "description": "Analyst name"},
                {
                    "name": "specialization",
                    "type": "STRING",
                    "description": "Analyst specialization",
                },
                {
                    "name": "experience_years",
                    "type": "INTEGER",
                    "description": "Years of experience",
                },
            ],
        },
        {
            "label": "HealthCarePro",
            "key_property": {"name": "id", "type": "STRING"},
            "properties": [
                {
                    "name": "name",
                    "type": "STRING",
                    "description": "Healthcare professional name",
                },
                {
                    "name": "license_number",
                    "type": "STRING",
                    "description": "Professional license number",
                },
                {
                    "name": "specialty",
                    "type": "STRING",
                    "description": "Medical specialty",
                },
                {
                    "name": "practice_name",
                    "type": "STRING",
                    "description": "Practice or hospital name",
                },
            ],
        },
    ],
    "relationships": [
        {"type": "HAS", "start_node_label": "Person", "end_node_label": "Address"},
        {"type": "HAS", "start_node_label": "Person", "end_node_label": "Phone"},
        {"type": "HAS", "start_node_label": "Person", "end_node_label": "IBAN"},
        {"type": "HAS", "start_node_label": "Person", "end_node_label": "Photo"},
        {"type": "HAS", "start_node_label": "Person", "end_node_label": "IP"},
        {
            "type": "HAS_MANAGER",
            "start_node_label": "Person",
            "end_node_label": "Person",
        },
        {
            "type": "PRESCRIPTION_FOR",
            "start_node_label": "Person",
            "end_node_label": "Prescription",
        },
        {
            "type": "RESPONSIBLE_FOR",
            "start_node_label": "Person",
            "end_node_label": "Prescription",
        },
        {
            "type": "BENEFICIARY_FOR",
            "start_node_label": "Person",
            "end_node_label": "Execution",
        },
        {
            "type": "RESPONSIBLE_FOR",
            "start_node_label": "Person",
            "end_node_label": "Execution",
        },
        {
            "type": "CONTAINS",
            "start_node_label": "Prescription",
            "end_node_label": "Care",
        },
        {"type": "CONTAINS", "start_node_label": "Execution", "end_node_label": "Care"},
        {
            "type": "ABOUT",
            "start_node_label": "Investigation",
            "end_node_label": "Person",
        },
        {
            "type": "HAS_AUTHOR",
            "start_node_label": "Investigation",
            "end_node_label": "Person",
        },
        {
            "type": "INVOLVES",
            "start_node_label": "Investigation",
            "end_node_label": "Person",
        },
        {
            "type": "NEXT_STATUS",
            "start_node_label": "Investigation",
            "end_node_label": "Investigation",
        },
    ],
}
