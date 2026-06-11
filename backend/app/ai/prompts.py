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

    # Project
    proj_name = project_context.get("title") or "Unknown Project"
    proj_genre = project_context.get("genre") or ""
    proj_tone = project_context.get("target_tone") or ""
    proj_line = f"Game: {proj_name}"
    if proj_genre:
        proj_line += f" | Genre: {proj_genre}"
    if proj_tone:
        proj_line += f" | Target tone: {proj_tone}"
    sections.append(proj_line)

    # Raw context
    if raw_context:
        sections.append(f"\n## Raw Context\n{raw_context[:3000]}")

    # Characters
    if characters:
        char_block = "\n".join(
            json.dumps(c, ensure_ascii=False) for c in characters
        )
        sections.append(f"\n## Character Profiles\n{char_block}")

    # Relationships
    if relationships:
        rel_block = "\n".join(
            json.dumps(r, ensure_ascii=False) for r in relationships
        )
        sections.append(f"\n## Relationships\n{rel_block}")

    # Glossary
    if glossary:
        gloss_block = "\n".join(
            json.dumps(g, ensure_ascii=False) for g in glossary
        )
        sections.append(f"\n## Glossary\n{gloss_block}")

    # Style rules
    if style_rules:
        style_block = "\n".join(
            json.dumps(s, ensure_ascii=False) for s in style_rules
        )
        sections.append(f"\n## Style Rules\n{style_block}")

    # Previous memory
    if previous_memory:
        sections.append(
            f"\n## Previous Scene Memory\n{json.dumps(previous_memory, ensure_ascii=False, indent=2)}"
        )

    # Current chunk lines
    lines_block = "\n".join(
        f"  [{l.get('line_id', '')}] {l.get('character', '')}: {l.get('source_text_ja', '')}"
        for l in chunk_lines
    )
    sections.append(f"\n## Current Chunk Lines\n{lines_block}")

    system_prompt = (
        "You are a professional Japanese-to-English game localizer. "
        "Your goal is not direct translation — it is natural English localization "
        "for game scripts. "
        "Preserve the original meaning, emotion, character voice, relationship dynamics, "
        "environment continuity, glossary consistency, story continuity, and natural English dialogue. "
        "Preserve placeholders exactly as-is (e.g. {player}, {item}, %s, %d, \\n, <color>). "
        "Do not add new story information. "
        "Do not remove important meaning. "
        "Avoid stiff translationese. "
        "Avoid overly archaic English unless the uploaded style rules explicitly request it. "
        "Follow glossary terms exactly. "
        "Keep each character's English voice consistent with their uploaded profile. "
        "Use previous scene memory to maintain continuity. "
        "If context is only raw text, infer carefully from it without inventing details. "
        "Return valid JSON only, with no additional text before or after."
    )

    user_prompt = (
        f"Localize the following game chunk into natural English.\n\n"
        + "\n".join(sections)
        + "\n\n"
        + "Return a JSON object with exactly two keys:\n"
        + '"translations": an array of objects with keys '
        + "line_id, character, source_text_ja, literal_meaning, localized_text_en, localization_note\n"
        + '"chunk_memory": an object with keys '
        + "chunk_summary, updated_environment, character_states (dict), "
        + "relationship_updates (list), tone_to_continue, important_terms (dict), unresolved_hooks (list)"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
