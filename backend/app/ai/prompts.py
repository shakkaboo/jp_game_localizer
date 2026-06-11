"""Prompt templates for AI localization.

No game-specific content is hardcoded here. All context is injected at
runtime from the uploaded context file.
"""

SYSTEM_PROMPT_TEMPLATE = """You are a professional game localizer specializing in Japanese-to-English translation.

## Game Context

{game_context}

## Character Profiles

{character_profiles}

## Glossary

{glossary}

## Style Rules

{style_rules}
"""

CHUNK_PROMPT_TEMPLATE = """Translate the following Japanese game dialogue chunk into natural English.

## Scene Memory

{scene_memory}

## Lines to translate

{script_lines}

Return your translations as a JSON array of objects with keys:
- "line_id": the original line id
- "final_text_en": the natural English translation
- "localization_note": brief note explaining any key decisions
"""

MEMORY_PROMPT_TEMPLATE = """Given the following scene and its translations, generate scene memory:

{scene_content}

Return a JSON object with:
- "chunk_summary": brief summary of what happened
- "updated_environment": current location/atmosphere details
- "character_emotional_states": dict of character -> emotional state
- "relationship_updates": list of relationship changes
- "tone_to_continue": what tone/style to maintain
- "important_terms": list of important terms introduced
- "unresolved_hooks": list of unresolved plot/character hooks
"""
