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

    @staticmethod
    def ensure_chunk_memory(
        chunk_memory: dict[str, Any],
        previous_memory: dict[str, Any] | None,
        chunk_lines: list[dict[str, str]],
        translations: list[dict[str, str]],
    ) -> dict[str, Any]:
        if not isinstance(chunk_memory, dict):
            chunk_memory = {}

        REQUIRED_KEYS = [
            "chunk_summary",
            "updated_environment",
            "character_states",
            "relationship_updates",
            "tone_to_continue",
            "important_terms",
            "unresolved_hooks",
        ]

        has_content = any(
            chunk_memory.get(k) for k in REQUIRED_KEYS
        )
        if has_content:
            for k in REQUIRED_KEYS:
                if k not in chunk_memory:
                    chunk_memory[k] = MemoryService._fallback_for(k, previous_memory, chunk_lines, translations)
            return chunk_memory

        # Entirely empty/missing — build full fallback
        return MemoryService._build_fallback_memory(previous_memory, chunk_lines, translations)

    @staticmethod
    def _build_fallback_memory(
        previous_memory: dict[str, Any] | None,
        chunk_lines: list[dict[str, str]],
        translations: list[dict[str, str]],
    ) -> dict[str, Any]:
        characters: list[str] = []
        dialogue_preview: list[str] = []
        for line in chunk_lines:
            c = (line.get("character") or "").strip()
            if c and c not in characters:
                characters.append(c)

        for t in translations:
            src = t.get("source_text_ja", "")[:60]
            loc = t.get("localized_text_en", "")[:60]
            if src or loc:
                dialogue_preview.append(f"{src} → {loc}")

        char_states: dict[str, str] = {c: "neutral" for c in characters}

        prev_summary = ""
        prev_env = ""
        prev_terms: dict[str, str] = {}
        prev_hooks: list[str] = []
        if previous_memory:
            prev_summary = previous_memory.get("chunk_summary", "")
            prev_env = previous_memory.get("updated_environment", "")
            prev_terms = previous_memory.get("important_terms", {}) or {}
            prev_hooks = previous_memory.get("unresolved_hooks", []) or []

        summary = f"Scene with {', '.join(characters) if characters else 'unknown characters'}"
        if dialogue_preview:
            summary += ". " + dialogue_preview[0]
        if prev_summary:
            summary = f"Continuing from: {prev_summary[:120]}. " + summary

        if prev_env:
            updated_env = prev_env
        elif chunk_lines:
            first_hint = (chunk_lines[0].get("scene_hint") or "").strip()
            updated_env = first_hint if first_hint else "unspecified location"
        else:
            updated_env = "unspecified location"

        tone = previous_memory.get("tone_to_continue", "") if previous_memory else ""
        if not tone:
            tone = "neutral"

        return {
            "chunk_summary": summary[:200],
            "updated_environment": updated_env[:100],
            "character_states": char_states,
            "relationship_updates": [],
            "tone_to_continue": tone[:100],
            "important_terms": prev_terms,
            "unresolved_hooks": prev_hooks,
        }

    @staticmethod
    def _fallback_for(
        key: str,
        previous_memory: dict[str, Any] | None,
        chunk_lines: list[dict[str, str]],
        translations: list[dict[str, str]],
    ) -> Any:
        if key == "chunk_summary":
            characters = list({
                line.get("character", "").strip()
                for line in chunk_lines if line.get("character", "").strip()
            })
            preview = ""
            for t in translations[:1]:
                loc = t.get("localized_text_en", "")
                if loc:
                    preview = loc[:80]
            prev = (previous_memory or {}).get("chunk_summary", "")
            base = f"Scene with {', '.join(characters)}" if characters else "Untitled scene"
            if preview:
                base += f": {preview}"
            if prev:
                base = f"Continuing from: {prev[:80]}. {base}"
            return base[:200]

        if key == "updated_environment":
            env = (previous_memory or {}).get("updated_environment", "")
            if env:
                return env[:100]
            hint = (chunk_lines[0].get("scene_hint") or "").strip() if chunk_lines else ""
            return (hint or "unspecified location")[:100]

        if key == "character_states":
            result: dict[str, str] = {}
            prev_states = (previous_memory or {}).get("character_states", {}) or {}
            for line in chunk_lines:
                c = (line.get("character") or "").strip()
                if c:
                    result[c] = prev_states.get(c, "neutral")
            return result

        if key == "relationship_updates":
            return []

        if key == "tone_to_continue":
            prev_tone = (previous_memory or {}).get("tone_to_continue", "")
            return (prev_tone or "neutral")[:100]

        if key == "important_terms":
            prev_terms = (previous_memory or {}).get("important_terms", {}) or {}
            return prev_terms

        if key == "unresolved_hooks":
            prev_hooks = (previous_memory or {}).get("unresolved_hooks", []) or []
            return prev_hooks

        return ""
