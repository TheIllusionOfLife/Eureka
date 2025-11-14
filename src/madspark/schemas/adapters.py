"""
Adapter utilities for converting Pydantic models to Google GenAI schema format.

Google's GenAI SDK expects schemas in a specific dict format based on OpenAPI 3.0.
This module provides conversion from Pydantic's JSON Schema output to GenAI format.
"""

from pydantic import BaseModel
from typing import Dict, Any, Type, List, Optional
import logging
import json

logger = logging.getLogger(__name__)


def pydantic_to_genai_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """
    Convert a Pydantic model to Google GenAI schema format.

    Args:
        model: Pydantic BaseModel class to convert

    Returns:
        Dict in Google GenAI schema format (OpenAPI 3.0 style)

    Example:
        >>> from madspark.schemas.evaluation import EvaluatorResponse
        >>> schema = pydantic_to_genai_schema(EvaluatorResponse)
        >>> schema['type']
        'OBJECT'

    Notes:
        - Preserves minimum/maximum constraints (new Gemini API feature)
        - Handles nested objects and arrays recursively
        - Converts nullable fields appropriately
        - Resolves $ref references from $defs
    """
    json_schema = model.model_json_schema()
    # Extract $defs for reference resolution
    defs = json_schema.get('$defs', {})
    return _convert_json_schema_to_genai(json_schema, defs)


def _convert_json_schema_to_genai(
    json_schema: Dict[str, Any],
    defs: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Recursively convert JSON Schema format to GenAI format.

    Args:
        json_schema: JSON Schema dict to convert
        defs: Optional $defs dict for resolving $ref references

    Type Mapping:
        - string → STRING
        - integer → INTEGER
        - number → NUMBER (floats)
        - boolean → BOOLEAN
        - array → ARRAY
        - object → OBJECT
        - null → nullable flag
    """
    if defs is None:
        defs = {}

    genai_schema = {}

    # Handle $ref resolution
    if '$ref' in json_schema:
        ref_path = json_schema['$ref']
        # Extract definition name from "#/$defs/ModelName"
        if ref_path.startswith('#/$defs/'):
            def_name = ref_path.replace('#/$defs/', '')
            if def_name in defs:
                # Recursively convert the referenced definition
                return _convert_json_schema_to_genai(defs[def_name], defs)
            else:
                logger.warning(f"Referenced definition not found: {def_name}")
                return {}

    # Handle type conversion
    json_type = json_schema.get('type')
    if json_type:
        genai_schema['type'] = _map_type_to_genai(json_type)

    # Handle description
    if 'description' in json_schema:
        genai_schema['description'] = json_schema['description']

    # Handle string constraints
    if 'minLength' in json_schema:
        genai_schema['minLength'] = json_schema['minLength']
    if 'maxLength' in json_schema:
        genai_schema['maxLength'] = json_schema['maxLength']

    # Handle numeric constraints (NEW GEMINI API FEATURE!)
    if 'minimum' in json_schema:
        genai_schema['minimum'] = json_schema['minimum']
    if 'maximum' in json_schema:
        genai_schema['maximum'] = json_schema['maximum']

    # Handle enum values
    if 'enum' in json_schema:
        genai_schema['enum'] = json_schema['enum']

    # Handle object properties
    if json_type == 'object' and 'properties' in json_schema:
        genai_schema['properties'] = {}
        for prop_name, prop_schema in json_schema['properties'].items():
            genai_schema['properties'][prop_name] = _convert_json_schema_to_genai(
                prop_schema, defs
            )

        # Handle required fields
        if 'required' in json_schema:
            genai_schema['required'] = json_schema['required']

    # Handle arrays
    if json_type == 'array' and 'items' in json_schema:
        genai_schema['items'] = _convert_json_schema_to_genai(json_schema['items'], defs)

    # Handle nullable fields (anyOf with null)
    if 'anyOf' in json_schema:
        # Extract non-null type
        non_null_schemas = [s for s in json_schema['anyOf'] if s.get('type') != 'null']
        if len(non_null_schemas) == 1:
            genai_schema = _convert_json_schema_to_genai(non_null_schemas[0], defs)
            genai_schema['nullable'] = True
        elif len(non_null_schemas) > 1:
            # Multiple non-null types - keep as anyOf
            genai_schema['anyOf'] = [
                _convert_json_schema_to_genai(s, defs) for s in non_null_schemas
            ]

    return genai_schema


def _map_type_to_genai(json_type: str) -> str:
    """Map JSON Schema types to GenAI types."""
    type_map = {
        'string': 'STRING',
        'integer': 'INTEGER',
        'number': 'NUMBER',
        'boolean': 'BOOLEAN',
        'array': 'ARRAY',
        'object': 'OBJECT',
    }
    genai_type = type_map.get(json_type)
    if not genai_type:
        logger.warning(f"Unknown JSON Schema type: {json_type}, defaulting to STRING")
        return 'STRING'
    return genai_type


def genai_response_to_pydantic(
    response_text: str,
    model: Type[BaseModel]
) -> BaseModel:
    """
    Parse GenAI JSON response into validated Pydantic model.

    Args:
        response_text: Raw JSON string from GenAI API response
        model: Pydantic model class to validate against

    Returns:
        Validated Pydantic model instance

    Raises:
        ValidationError: If response doesn't match schema
        JSONDecodeError: If response isn't valid JSON

    Example:
        >>> from madspark.schemas.evaluation import EvaluatorResponse
        >>> response_text = '{"score": 8.5, "critique": "Good idea"}'
        >>> result = genai_response_to_pydantic(response_text, EvaluatorResponse)
        >>> result.score
        8.5
    """
    data = json.loads(response_text)
    return model.model_validate(data)
