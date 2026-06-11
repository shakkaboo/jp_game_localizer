import json
from typing import Any


def build_chunk_localization_prompt(
    project_context: dict[str, Any],
    characters: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    glossary: list[dict[str, Any]],
    style_rules: list[dict[str, Any]],
    raw_context: str,
    previous_memory: dict[str, Any] | None,
    chunk_lines: list[dict[str, str]],
) -> list[dict[str, str]]:
    sections: list[str] = []

    proj_name = project_context.get("title") or "Unknown Project"
    proj_genre = project_context.get("genre") or ""
    proj_tone = project_context.get("target_tone") or ""
    proj_line = f"Game: {proj_name}"
    if proj_genre:
        proj_line += f" | Genre: {proj_genre}"
    if proj_tone:
        proj_line += f" | Target tone: {proj_tone}"
    sections.append(proj_line)

    if raw_context:
        sections.append(f"\n## Raw Context\n{raw_context[:3000]}")

    if characters:
        char_block = "\n".join(
            json.dumps(c, ensure_ascii=False) for c in characters
        )
        sections.append(f"\n## Character Profiles\n{char_block}")

    if relationships:
        rel_block = "\n".join(
            json.dumps(r, ensure_ascii=False) for r in relationships
        )
        sections.append(f"\n## Relationships\n{rel_block}")

    if glossary:
        gloss_block = "\n".join(
            json.dumps(g, ensure_ascii=False) for g in glossary
        )
        sections.append(f"\n## Glossary\n{gloss_block}")

    if style_rules:
        style_block = "\n".join(
            json.dumps(s, ensure_ascii=False) for s in style_rules
        )
        sections.append(f"\n## Style Rules\n{style_block}")

    if previous_memory:
        sections.append(
            f"\n## Previous Scene Memory\n{json.dumps(previous_memory, ensure_ascii=False, indent=2)}"
        )

    lines_block = "\n".join(
        f"  [{l.get('line_id', '')}] {l.get('character', '')}: {l.get('source_text_ja', '')}"
        for l in chunk_lines
    )
    sections.append(f"\n## Current Chunk Lines\n{lines_block}")

    system_prompt = (
        "You are a professional Japanese-to-English game localizer. "
        "Your goal is natural English localization for game scripts, not direct translation. "
        "Preserve meaning, emotion, character voice, relationship dynamics, "
        "environment continuity, glossary consistency, and story continuity. "
        "Preserve placeholders exactly as-is (e.g. {player}, {item}, %s, %d, \\n, <color>). "
        "Do not add new story information. Keep it concise. "
        "Return only the required JSON object — no extra text, no explanations."
    )

    user_prompt = (
        f"Localize these game lines into natural English.\n\n"
        + "\n".join(sections)
        + "\n\n"
        + "Return compact JSON with exactly two keys:\n"
        + '"translations": array, each object has '
        + "line_id, character, source_text_ja, "
        + "literal_meaning (short), "
        + "localized_text_en, "
        + "localization_note (short, omit if empty).\n"
        + '"chunk_memory": object with '
        + "chunk_summary (1 sentence), "
        + "updated_environment (1 phrase), "
        + "character_states (dict, 1-2 words per character), "
        + "relationship_updates (list of brief notes), "
        + "tone_to_continue (short), "
        + "important_terms (dict of term: translation), "
        + "unresolved_hooks (list of short hooks)."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
