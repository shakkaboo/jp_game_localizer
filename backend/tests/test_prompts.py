from app.ai.prompts import PROMPT_VERSION, build_chunk_localization_prompt


def test_prompt_version():
    assert PROMPT_VERSION == "1.0.0"


def test_plain_mode_omits_context_and_memory():
    lines = [{"line_id": "1", "character": "Hero", "source_text_ja": "こんにちは"}]
    messages = build_chunk_localization_prompt(
        chunk_lines=lines,
        project_context={"title": "Test Game"},
        characters=[{"name": "Hero"}],
        previous_memory={"chunk_summary": "previous scene"},
        mode="plain",
    )
    user_content = messages[1]["content"]
    assert "Character Profiles" not in user_content
    assert "Previous Scene Memory" not in user_content
    assert "Test Game" not in user_content
    assert "Current Chunk Lines" in user_content
    assert "こんにちは" in user_content


def test_context_mode_includes_context_but_not_memory():
    lines = [{"line_id": "1", "character": "Hero", "source_text_ja": "こんにちは"}]
    messages = build_chunk_localization_prompt(
        chunk_lines=lines,
        project_context={"title": "RPG World"},
        characters=[{"name": "Hero", "role": "protagonist"}],
        previous_memory={"chunk_summary": "previous scene"},
        mode="context",
    )
    user_content = messages[1]["content"]
    assert "RPG World" in user_content
    assert "Character Profiles" in user_content
    assert "Previous Scene Memory" not in user_content
    assert "Current Chunk Lines" in user_content


def test_context_memory_mode_includes_everything():
    lines = [{"line_id": "1", "character": "Hero", "source_text_ja": "こんにちは"}]
    messages = build_chunk_localization_prompt(
        chunk_lines=lines,
        project_context={"title": "RPG World"},
        characters=[{"name": "Hero", "role": "protagonist"}],
        previous_memory={"chunk_summary": "previous scene"},
        mode="context_memory",
    )
    user_content = messages[1]["content"]
    assert "RPG World" in user_content
    assert "Character Profiles" in user_content
    assert "Previous Scene Memory" in user_content
    assert "Current Chunk Lines" in user_content


def test_default_mode_is_context_memory():
    lines = [{"line_id": "1", "character": "Hero", "source_text_ja": "こんにちは"}]
    messages = build_chunk_localization_prompt(
        chunk_lines=lines,
        project_context={"title": "RPG World"},
        previous_memory={"chunk_summary": "scene"},
    )
    user_content = messages[1]["content"]
    assert "Previous Scene Memory" in user_content
    assert "RPG World" in user_content


def test_no_context_when_args_are_none():
    lines = [{"line_id": "1", "character": "Hero", "source_text_ja": "こんにちは"}]
    messages = build_chunk_localization_prompt(
        chunk_lines=lines,
        mode="context",
    )
    user_content = messages[1]["content"]
    assert "Unknown Project" in user_content
    assert "Current Chunk Lines" in user_content


def test_plain_mode_no_context_at_all():
    lines = [{"line_id": "1", "character": "Hero", "source_text_ja": "こんにちは"}]
    messages = build_chunk_localization_prompt(
        chunk_lines=lines,
        mode="plain",
    )
    user_content = messages[1]["content"]
    assert "Unknown Project" not in user_content
    assert "Current Chunk Lines" in user_content
    assert "こんにちは" in user_content


def test_messages_have_system_and_user():
    lines = [{"line_id": "1", "character": "Hero", "source_text_ja": "test"}]
    messages = build_chunk_localization_prompt(chunk_lines=lines)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
