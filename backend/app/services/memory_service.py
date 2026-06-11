import json
from typing import Any


class MemoryService:
    @staticmethod
    def build_initial_memory(context: dict[str, Any] | None) -> dict[str, Any]:
        if not context:
            return {}

        memory: dict[str, Any] = {}

        first_env = context.get("first_environment") or {}
        if first_env:
            memory["environment"] = first_env

        project_info = context.get("project") or {}
        if project_info:
            memory["project"] = project_info

        characters = context.get("characters") or []
        if characters:
            memory["characters"] = characters

        relationships = context.get("relationships") or []
        if relationships:
            memory["relationships"] = relationships

        glossary = context.get("glossary") or []
        if glossary:
            memory["glossary"] = glossary

        raw = context.get("raw_context", "")
        if raw and not (first_env or project_info or characters):
            memory["raw_context_fallback"] = raw[:2000]

        return memory

    @staticmethod
    def format_for_prompt(memory: dict[str, Any] | None) -> str:
        if not memory:
            return "No prior context."
        return json.dumps(memory, ensure_ascii=False, indent=2)
