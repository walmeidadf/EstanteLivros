"""Validador mínimo de JSON Schema 2020-12 (só o subconjunto usado no catálogo).

Palavras-chave fora do subconjunto fazem `load_schema` falhar, para que um
schema nunca prometa uma regra que não é conferida.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

VALIDATION_KEYWORDS = {
    "type", "properties", "required", "additionalProperties", "items", "enum",
    "const", "pattern", "minimum", "maximum", "minLength", "maxLength",
    "minItems", "uniqueItems", "$ref", "oneOf",
}
ANNOTATION_KEYWORDS = {"$schema", "$id", "$defs", "title", "description", "$comment"}
SUPPORTED = VALIDATION_KEYWORDS | ANNOTATION_KEYWORDS

Error = Tuple[str, str]


class SchemaError(Exception):
    """Schema malformado ou com palavra-chave não suportada."""


def _check_keywords(node: Any, where: str) -> None:
    if isinstance(node, bool):
        return
    if not isinstance(node, dict):
        raise SchemaError(f"{where}: schema deve ser objeto")
    unknown = set(node) - SUPPORTED
    if unknown:
        raise SchemaError(f"{where}: palavra-chave não suportada: {sorted(unknown)}")
    for name, sub in node.get("properties", {}).items():
        _check_keywords(sub, f"{where}/properties/{name}")
    for name, sub in node.get("$defs", {}).items():
        _check_keywords(sub, f"{where}/$defs/{name}")
    if "items" in node:
        _check_keywords(node["items"], f"{where}/items")
    if isinstance(node.get("additionalProperties"), dict):
        _check_keywords(node["additionalProperties"], f"{where}/additionalProperties")
    for i, sub in enumerate(node.get("oneOf", [])):
        _check_keywords(sub, f"{where}/oneOf/{i}")


def check_schema(schema: Dict[str, Any], name: str = "schema") -> Dict[str, Any]:
    _check_keywords(schema, name)
    return schema


def load_schema(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        schema = json.load(fh)
    return check_schema(schema, str(path))


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    raise SchemaError(f"tipo desconhecido: {expected}")


def _resolve(ref: str, root: Dict[str, Any]) -> Dict[str, Any]:
    if not ref.startswith("#/"):
        raise SchemaError(f"só $ref local é suportado: {ref}")
    node: Any = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def validate(instance: Any, schema: Dict[str, Any]) -> List[Error]:
    """Lista de (caminho, mensagem). Caminho no estilo `edition.isbn13`, `themes[2]`."""
    errors: List[Error] = []
    _validate(instance, schema, schema, "", errors)
    return errors


def _join(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key


def _validate(value: Any, node: Any, root: Dict[str, Any], path: str,
              errors: List[Error]) -> None:
    here = path or "(raiz)"
    if node is True:
        return
    if node is False:
        errors.append((here, "nenhum valor é permitido"))
        return
    if "$ref" in node:
        _validate(value, _resolve(node["$ref"], root), root, path, errors)

    if "oneOf" in node:
        matches = 0
        for option in node["oneOf"]:
            sub: List[Error] = []
            _validate(value, option, root, path, sub)
            if not sub:
                matches += 1
        if matches != 1:
            errors.append((here, f"deve casar com exatamente uma opção de oneOf (casou {matches})"))

    if "type" in node:
        types = node["type"] if isinstance(node["type"], list) else [node["type"]]
        if not any(_type_ok(value, t) for t in types):
            errors.append((here, f"tipo inválido: esperado {'|'.join(types)}, recebido {type(value).__name__}"))
            return

    if "const" in node and value != node["const"]:
        errors.append((here, f"deve ser {node['const']!r}"))
    if "enum" in node and value not in node["enum"]:
        errors.append((here, f"valor {value!r} fora de {node['enum']}"))

    if isinstance(value, str):
        if "minLength" in node and len(value) < node["minLength"]:
            errors.append((here, f"texto menor que {node['minLength']}"))
        if "maxLength" in node and len(value) > node["maxLength"]:
            errors.append((here, f"texto maior que {node['maxLength']}"))
        if "pattern" in node and not re.search(node["pattern"], value):
            errors.append((here, f"{value!r} não casa com {node['pattern']}"))

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in node and value < node["minimum"]:
            errors.append((here, f"{value} < {node['minimum']}"))
        if "maximum" in node and value > node["maximum"]:
            errors.append((here, f"{value} > {node['maximum']}"))

    if isinstance(value, list):
        if "minItems" in node and len(value) < node["minItems"]:
            errors.append((here, f"precisa de ao menos {node['minItems']} itens"))
        if node.get("uniqueItems"):
            seen = []
            for item in value:
                if item in seen:
                    errors.append((here, f"item repetido: {item!r}"))
                    break
                seen.append(item)
        if "items" in node:
            for i, item in enumerate(value):
                _validate(item, node["items"], root, f"{path}[{i}]", errors)

    if isinstance(value, dict):
        props = node.get("properties", {})
        for key in node.get("required", []):
            if key not in value:
                errors.append((_join(path, key), "campo obrigatório ausente"))
        for key, item in value.items():
            if key in props:
                _validate(item, props[key], root, _join(path, key), errors)
            elif node.get("additionalProperties") is False:
                errors.append((_join(path, key), "campo não permitido"))
            elif isinstance(node.get("additionalProperties"), dict):
                _validate(item, node["additionalProperties"], root, _join(path, key), errors)
