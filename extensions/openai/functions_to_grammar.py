import json

from extensions.openai.json_schema_to_grammar import SchemaConverter

class Function:
    def __init__(self, name, description, parameters):
        self.name: str = name
        self.description: str = description
        self.parameters: dict = parameters

class JSONFunctionStructure:
    def __init__(self):
        self.oneOf = []

def to_json_structure(functions: Function):
    js = JSONFunctionStructure()
    for function in functions:
        properties = function.parameters.get("properties", {})
        js.oneOf.append({
            "type": "object",
            "properties": {
                "function": {"const": function.name},
                "arguments": {
                    "type": "object",
                    "properties": properties
                },
            },
        })
    return js.__dict__

# Parse the JSON or dictionary to create Function objects.
def parse_functions(function_list):
    # function_list = json.loads(json_data)
    functions = [Function(f['name'], f['description'], f['parameters']) for f in function_list]
    json_structure = to_json_structure(functions)
    prop_order = {name: idx for idx, name in enumerate(["function","name","arguments"])}
    converter = SchemaConverter(prop_order)
    converter.visit(json_structure, '')
    return converter.format_grammar()