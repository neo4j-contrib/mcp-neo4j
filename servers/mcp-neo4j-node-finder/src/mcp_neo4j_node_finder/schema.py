from neo4j import AsyncDriver
    
MAX_STRING_LENGTH = 50
EXCLUDED_LABELS = ["_Bloom_Perspective_", "_Bloom_Scene_"]
NODE_PROPERTIES_QUERY = (
"CALL apoc.meta.data() "
"YIELD label, other, elementType, type, property "
"WHERE NOT type = 'RELATIONSHIP' AND elementType = 'node' "
"AND NOT label IN $EXCLUDED_LABELS "
"WITH label AS nodeLabel, collect({property:property, type:type}) AS properties "
"RETURN nodeLabel, properties"
)

def filter_string_properties(data):
   filtered_data = []
   
   for node in data:
       string_props = [prop for prop in node['properties'] if prop['type'] == 'STRING']
       
       if string_props:  # Only include nodes that have string properties
           filtered_data.append({
               'nodeLabel': node['nodeLabel'],
               'properties': string_props
           })
   
   return filtered_data

def attributes_to_json(attributes):
    pairs = []
    
    for attr in attributes:
        pairs.append(f'{attr}: n.`{attr}`')
    
    return "{" + ", ".join(pairs) + "} AS output"

async def get_schema_definition(driver: AsyncDriver, database: str):
    response, _, _ = await driver.execute_query(NODE_PROPERTIES_QUERY, EXCLUDED_LABELS=EXCLUDED_LABELS, database_=database)
    props = [el.data() for el in response]
    string_props = filter_string_properties(props)
    for row in string_props:
        #print(row)
        cypher = f"MATCH (n:`{row['nodeLabel']}`) "
        node_props = [el['property'] for el in row['properties']]
        cypher += f"RETURN {attributes_to_json(node_props)} LIMIT 25"
        response, _, _ = await driver.execute_query(cypher, database_=database)
        response = [el.data() for el in response]
        
        # Process each property to add examples and filter by length
        valid_properties = []
        
        for prop_info in row['properties']:
            property_name = prop_info['property']
            
            # Collect valid examples (length <= 50 chars)
            valid_examples = []
            seen_values = set()
            
            for record in response:
                value = record['output'].get(property_name)
                if (value is not None and 
                    isinstance(value, str) and 
                    len(value) <= MAX_STRING_LENGTH and 
                    value not in seen_values):
                    valid_examples.append(value)
                    seen_values.add(value)
                    if len(valid_examples) >= 2:
                        break
            
            # Only include properties with valid examples
            if valid_examples:
                prop_info['examples'] = valid_examples
                valid_properties.append(prop_info)
        
        # Update the row with only valid properties
        row['properties'] = valid_properties
    return string_props