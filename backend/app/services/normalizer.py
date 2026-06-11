import json
from typing import Any

_FIELD_ALIASES: dict[str, list[str]] = {
    "line_id": ["line_id", "id", "key", "string_id"],
    "character": ["character", "speaker", "name", "character_name"],
    "source_text_ja": [
        "source_text_ja", "text_ja", "text", "ja", "japanese",
        "source", "source_text",
    ],
    "scene_hint": ["scene_hint", "scene", "context", "scene_context", "location"],
}


def _first_of(raw: dict[str, Any], candidates: list[str]) -> str:
    for name in candidates:
        value = raw.get(name)
        if value is not None and value != "":
            return str(value)
    return ""


class ScriptNormalizer:
    @staticmethod
    def normalize(raw_lines: list[dict[str, Any]]) -> dict[str, Any]:
        lines: list[dict[str, str]] = []
        warnings: list[str] = []
        seen_characters: set[str] = set()
        seen_scene_hints: set[str] = set()

        for idx, raw in enumerate(raw_lines, start=1):
            source_text_ja = _first_of(raw, _FIELD_ALIASES["source_text_ja"]).strip()

            if not source_text_ja:
                orig = raw.get("line_id") or raw.get("id") or f"row {idx}"
                warnings.append(f"Skipped line {orig}: source_text_ja is empty")
                continue

            line_id = _first_of(raw, _FIELD_ALIASES["line_id"]) or str(idx)
            character = _first_of(raw, _FIELD_ALIASES["character"])
            scene_hint = _first_of(raw, _FIELD_ALIASES["scene_hint"]) or "未分類"

            lines.append(
                {
                    "line_id": line_id,
                    "character": character,
                    "source_text_ja": source_text_ja,
                    "scene_hint": scene_hint,
                }
            )

            if character:
                seen_characters.add(character)
            if scene_hint:
                seen_scene_hints.add(scene_hint)

        return {
            "lines": lines,
            "warnings": warnings,
            "detected_characters": sorted(seen_characters),
            "detected_scene_hints": sorted(seen_scene_hints),
        }


class ContextNormalizer:
    @staticmethod
    def normalize(data: dict[str, Any] | str) -> dict[str, Any]:
        warnings: list[str] = []
        result: dict[str, Any] = {
            "project": {},
            "first_environment": {},
            "characters": [],
            "relationships": [],
            "glossary": [],
            "style_rules": [],
            "raw_context": "",
            "warnings": [],
        }

        if isinstance(data, str):
            result["raw_context"] = data
            warnings.append("Context is plain text — no structured sections parsed")
            result["warnings"] = warnings
            return result

        raw = data
        result["raw_context"] = json.dumps(raw, ensure_ascii=False)

        section_map = {
            "project": "project",
            "first_environment": "first_environment",
            "characters": "characters",
            "relationships": "relationships",
            "glossary": "glossary",
            "style_rules": "style_rules",
        }

        for key, section in section_map.items():
            value = raw.get(key) or raw.get(section)
            if value is None or value == {} or value == []:
                warnings.append(f"Missing context section: {section}")
            else:
                result[section] = value

        result["warnings"] = warnings
        return result
