# JSON Schemas for each tool to validate model output
TOOL_SCHEMAS = {
    'update_file': {
    'type': 'object',
    'properties': {
    'path': {'type': 'string'},
    'content': {'type': 'string'},
    'overwrite': {'type': 'boolean'}
    },
    'required': ['path', 'content']
    },
    'create_user': {
    'type': 'object',
    'properties': {
    'username': {'type': 'string'},
    'roles': {
    'type': 'array',
    'items': {'type': 'string'}
    }
    },
    'required': ['username', 'roles']
    }
    }