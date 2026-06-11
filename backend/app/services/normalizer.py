import json
from typing import Any


class ScriptNormalizer:
    @staticmethod
    def normalize(raw_lines: list[dict[str, Any]]) -> dict[str, Any]:
        lines: list[dict[str, str]] = []
        warnings: list[str] = []

        for idx, raw in enumerate(raw_lines, start=1):
            source_text_ja = (
                raw.get("source_text_ja")
                or raw.get("text_ja")
                or raw.get("text")
                or ""
            ).strip()

            if not source_text_ja:
                orig = raw.get("line_id") or raw.get("id") or f"row {idx}"
                warnings.append(f"Skipped line {orig}: source_text_ja is empty")
                continue

            line_id = str(raw.get("line_id") or raw.get("id") or idx)
            character = str(raw.get("character") or raw.get("speaker") or "")
            scene_hint = str(raw.get("scene_hint") or raw.get("scene") or "未分類")

            lines.append(
                {
                    "line_id": line_id,
                    "character": character,
                    "source_text_ja": source_text_ja,
                    "scene_hint": scene_hint,
                }
            )

        return {"lines": lines, "warnings": warnings}


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

        raw: dict[str, Any]
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
