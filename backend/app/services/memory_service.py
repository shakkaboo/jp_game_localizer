import json
from typing import Any


class MemoryService:
    """Manage rolling memory across chunks.

    ``build_memory`` is a stub for future AI integration.
    ``format_for_prompt`` serialises memory for inclusion in LLM prompts.
    """

    @staticmethod
    def build_memory(
        chunk_data: dict[str, Any],
        context: dict[str, Any],
        previous_memory: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build chunk memory — currently a stub."""
        return {
            "chunk_summary": "",
            "updated_environment": {},
            "character_emotional_states": {},
            "relationship_updates": [],
            "tone_to_continue": "",
            "important_terms": [],
            "unresolved_hooks": [],
        }

    @staticmethod
    def format_for_prompt(memory: dict[str, Any] | None) -> str:
        if not memory:
            return "No prior context."
        return json.dumps(memory, ensure_ascii=False, indent=2)
