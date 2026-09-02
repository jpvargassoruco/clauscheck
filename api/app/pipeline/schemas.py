"""JSON Schemas for the intermediate (non-final) LLM calls of the pipeline.

These are plain JSON Schema dicts (not Pydantic) validated by
`LLMProviderBase.chat_json` via `jsonschema`. The final stage-7 call reuses
`app.schemas.dictamen.dictamen_json_schema()` directly instead of a schema
defined here, since it must match the shared `Dictamen` contract exactly.
"""

CLAUSULAS_SCHEMA: dict = {
    "type": "object",
    "required": ["clausulas"],
    "properties": {
        "clausulas": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "numero", "texto"],
                "properties": {
                    "id": {"type": "string"},
                    "numero": {"type": "string"},
                    "titulo": {"type": ["string", "null"]},
                    "texto": {"type": "string"},
                },
            },
        }
    },
}

PARTES_SCHEMA: dict = {
    "type": "object",
    "required": ["partes"],
    "properties": {
        "partes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "nombre", "rol"],
                "properties": {
                    "id": {"type": "string"},
                    "nombre": {"type": "string"},
                    "rol": {"type": "string"},
                    "redacto": {"type": "boolean"},
                },
            },
        },
        "ficha": {
            "type": "object",
            "properties": {
                "plaza": {"type": ["string", "null"]},
                "fecha": {"type": ["string", "null"]},
                "cuantia": {"type": ["string", "null"]},
                "forma_instrumental": {"type": ["string", "null"]},
                "tipo_contrato": {"type": ["string", "null"]},
                "rubro": {"type": ["string", "null"]},
            },
        },
    },
}

CANDIDATOS_SCHEMA: dict = {
    "type": "object",
    "required": ["candidatos"],
    "properties": {
        "candidatos": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "tipo", "titulo", "problema", "nivel_tentativo"],
                "properties": {
                    "id": {"type": "string"},
                    "tipo": {"type": "string", "enum": ["hallazgo", "omision"]},
                    "clausula_id": {"type": ["string", "null"]},
                    "titulo": {"type": "string"},
                    "problema": {"type": "string"},
                    "nivel_tentativo": {
                        "type": "string",
                        "enum": ["critico", "alto", "medio", "bajo", "informativo"],
                    },
                    "palabras_clave": {"type": "array", "items": {"type": "string"}},
                    "cita_textual": {"type": ["string", "null"]},
                },
            },
        }
    },
}

CONTRASTE_SCHEMA: dict = {
    "type": "object",
    "required": ["resultados"],
    "properties": {
        "resultados": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "applicable"],
                "properties": {
                    "id": {"type": "string"},
                    "applicable": {"type": "boolean"},
                    "nivel": {
                        "type": "string",
                        "enum": ["critico", "alto", "medio", "bajo", "informativo"],
                    },
                    "beneficia": {"type": ["string", "null"]},
                    "perjudica": {"type": ["string", "null"]},
                    "articulo_ids": {"type": "array", "items": {"type": "string"}},
                    "fundamento": {"type": "string"},
                    "redaccion_sustitutiva": {"type": ["string", "null"]},
                    "recomendacion": {"type": ["string", "null"]},
                },
            },
        }
    },
}
