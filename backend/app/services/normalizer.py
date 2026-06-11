import json
from typing import Any

from app.schemas import ContextNormalized, ScriptLineNormalized, ScriptNormalized


class ScriptNormalizer:
    """Normalize parsed script data into ScriptNormalized."""

    @staticmethod
    def normalize(raw_lines: list[dict[str, Any]]) -> ScriptNormalized:
        normalized = ScriptNormalized()
        for raw in raw_lines:
            line = ScriptLineNormalized(
                line_id=str(raw.get("line_id", raw.get("id", ""))),
                character=str(raw.get("character", raw.get("speaker", ""))),
                source_text_ja=str(
                    raw.get("source_text_ja", raw.get("text_ja", raw.get("text", "")))
                ),
                scene_hint=str(raw.get("scene_hint", raw.get("scene", ""))),
            )
            normalized.lines.append(line)
        return normalized


class ContextNormalizer:
    """Normalize parsed context data into ContextNormalized."""

    @staticmethod
    def normalize(data: dict | str) -> ContextNormalized:
        if isinstance(data, str):
            return ContextNormalized(raw_context=data)

        result = ContextNormalized()

        if isinstance(data, dict):
            result.project = data.get("project", {})
            result.first_environment = data.get("first_environment", {})
            result.characters = data.get("characters", [])
            result.relationships = data.get("relationships", [])
            result.glossary = data.get("glossary", [])
            result.style_rules = data.get("style_rules", [])
            result.raw_context = data.get("raw_context", json.dumps(data, ensure_ascii=False))

        return result
