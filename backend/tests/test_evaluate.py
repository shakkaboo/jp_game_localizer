from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Chunk, Project, SourceFile, SourceLine

_mock_translations = {
    "translations": [
        {
            "line_id": "1",
            "character": "Hero",
            "source_text_ja": "こんにちは",
            "literal_meaning": "Hello",
            "localized_text_en": "Hello!",
            "localization_note": "",
        },
        {
            "line_id": "2",
            "character": "Hero",
            "source_text_ja": "さようなら",
            "literal_meaning": "Goodbye",
            "localized_text_en": "Goodbye!",
            "localization_note": "",
        },
    ],
    "chunk_memory": {
        "chunk_summary": "Hero greets and says farewell.",
        "updated_environment": "village",
        "character_states": {"Hero": "polite"},
        "relationship_updates": [],
        "tone_to_continue": "friendly",
        "important_terms": {},
        "unresolved_hooks": [],
    },
}


@pytest.fixture
def shared_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)

    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    yield session

    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()
    engine.dispose()


def _create_test_chunk(session: Session) -> int:
    project = Project(title="Test Game", genre="RPG")
    session.add(project)
    session.flush()

    src_file = SourceFile(
        project_id=project.id,
        original_filename="script.csv",
        file_type="csv",
        total_lines=2,
    )
    session.add(src_file)
    session.flush()

    chunk = Chunk(
        project_id=project.id,
        source_file_id=src_file.id,
        chunk_number=1,
        chunk_title="Opening",
        status="pending",
    )
    session.add(chunk)
    session.flush()

    for line_id, char, text in [
        ("1", "Hero", "こんにちは"),
        ("2", "Hero", "さようなら"),
    ]:
        session.add(
            SourceLine(
                project_id=project.id,
                source_file_id=src_file.id,
                line_id=line_id,
                character=char,
                source_text_ja=text,
                chunk_id=chunk.id,
            )
        )

    session.commit()
    return chunk.id


def test_evaluate_plain_mode_success(shared_session):
    chunk_id = _create_test_chunk(shared_session)

    with (
        patch("app.routes.evaluate.call_llm_json", return_value=_mock_translations),
        patch("app.routes.evaluate.get_normalized_provider", return_value="test"),
        patch("app.routes.evaluate.get_llm_settings", return_value={"model": "test-model"}),
    ):
        client = TestClient(app)
        response = client.post(f"/evaluate/chunk/{chunk_id}?mode=plain")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["run_id"] > 0
    assert data["chunk_id"] == chunk_id
    assert data["mode"] == "plain"
    assert data["status"] == "completed"
    assert data["translations_count"] == 2
    assert data["generated_memory"] is None

    detail = client.get(f"/evaluate/runs/{data['run_id']}")
    assert detail.status_code == 200
    detail_data = detail.json()
    assert detail_data["status"] == "completed"
    assert detail_data["prompt_version"] == "1.0.0"
    assert len(detail_data["translations"]) == 2
    assert detail_data["translations"][0]["localized_text_en"] == "Hello!"
    assert detail_data["generated_memory"] is None


def test_evaluate_context_mode_success(shared_session):
    chunk_id = _create_test_chunk(shared_session)

    with (
        patch("app.routes.evaluate.call_llm_json", return_value=_mock_translations),
        patch("app.routes.evaluate.get_normalized_provider", return_value="test"),
        patch("app.routes.evaluate.get_llm_settings", return_value={"model": "test-model"}),
    ):
        client = TestClient(app)
        response = client.post(f"/evaluate/chunk/{chunk_id}?mode=context")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["mode"] == "context"
    assert data["status"] == "completed"
    assert data["translations_count"] == 2
    assert data["generated_memory"] is None


def test_evaluate_context_memory_mode_success(shared_session):
    chunk_id = _create_test_chunk(shared_session)

    with (
        patch("app.routes.evaluate.call_llm_json", return_value=_mock_translations),
        patch("app.routes.evaluate.get_normalized_provider", return_value="test"),
        patch("app.routes.evaluate.get_llm_settings", return_value={"model": "test-model"}),
    ):
        client = TestClient(app)
        response = client.post(f"/evaluate/chunk/{chunk_id}?mode=context_memory")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["mode"] == "context_memory"
    assert data["status"] == "completed"
    assert data["generated_memory"] is not None


def test_evaluate_invalid_mode_returns_422(shared_session):
    chunk_id = _create_test_chunk(shared_session)
    client = TestClient(app)
    response = client.post(f"/evaluate/chunk/{chunk_id}?mode=invalid_mode")
    assert response.status_code == 422


def test_evaluate_missing_mode_returns_422(shared_session):
    chunk_id = _create_test_chunk(shared_session)
    client = TestClient(app)
    response = client.post(f"/evaluate/chunk/{chunk_id}")
    assert response.status_code == 422


def test_evaluate_chunk_not_found_returns_404(shared_session):
    client = TestClient(app)
    response = client.post("/evaluate/chunk/99999?mode=plain")
    assert response.status_code == 404


def test_evaluate_llm_error_sets_run_to_failed(shared_session):
    chunk_id = _create_test_chunk(shared_session)

    with (
        patch("app.routes.evaluate.call_llm_json", side_effect=ValueError("API error")),
        patch("app.routes.evaluate.get_normalized_provider", return_value="test"),
        patch("app.routes.evaluate.get_llm_settings", return_value={"model": "test-model"}),
    ):
        client = TestClient(app)
        response = client.post(f"/evaluate/chunk/{chunk_id}?mode=plain")

    assert response.status_code == 502

    runs = client.get("/evaluate/runs")
    assert runs.status_code == 200
    runs_data = runs.json()
    assert len(runs_data) >= 1
    latest = runs_data[0]
    assert latest["status"] == "failed"
    assert latest["error_message"] == "llm_request_failed"


def test_evaluate_list_runs(shared_session):
    chunk_id = _create_test_chunk(shared_session)

    with (
        patch("app.routes.evaluate.call_llm_json", return_value=_mock_translations),
        patch("app.routes.evaluate.get_normalized_provider", return_value="test"),
        patch("app.routes.evaluate.get_llm_settings", return_value={"model": "test-model"}),
    ):
        client = TestClient(app)
        client.post(f"/evaluate/chunk/{chunk_id}?mode=plain")
        client.post(f"/evaluate/chunk/{chunk_id}?mode=context")
        client.post(f"/evaluate/chunk/{chunk_id}?mode=context_memory")

    response = client.get("/evaluate/runs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["mode"] == "context_memory"
    assert data[1]["mode"] == "context"
    assert data[2]["mode"] == "plain"


def test_evaluate_run_not_found(shared_session):
    client = TestClient(app)
    response = client.get("/evaluate/runs/99999")
    assert response.status_code == 404


def test_generated_memory_only_in_context_memory(shared_session):
    chunk_id = _create_test_chunk(shared_session)

    with (
        patch("app.routes.evaluate.call_llm_json", return_value=_mock_translations),
        patch("app.routes.evaluate.get_normalized_provider", return_value="test"),
        patch("app.routes.evaluate.get_llm_settings", return_value={"model": "test-model"}),
    ):
        client = TestClient(app)
        plain_resp = client.post(f"/evaluate/chunk/{chunk_id}?mode=plain")
        context_resp = client.post(f"/evaluate/chunk/{chunk_id}?mode=context")
        mem_resp = client.post(f"/evaluate/chunk/{chunk_id}?mode=context_memory")

    plain_detail = client.get(f"/evaluate/runs/{plain_resp.json()['run_id']}").json()
    context_detail = client.get(f"/evaluate/runs/{context_resp.json()['run_id']}").json()
    mem_detail = client.get(f"/evaluate/runs/{mem_resp.json()['run_id']}").json()

    assert plain_detail["generated_memory"] is None
    assert context_detail["generated_memory"] is None
    assert mem_detail["generated_memory"] is not None
    assert mem_detail["generated_memory"]["chunk_summary"] == "Hero greets and says farewell."


def _create_test_chunk_with_project(session: Session, project: Project) -> int:
    src_file = SourceFile(
        project_id=project.id,
        original_filename="script.csv",
        file_type="csv",
        total_lines=2,
    )
    session.add(src_file)
    session.flush()

    chunk = Chunk(
        project_id=project.id,
        source_file_id=src_file.id,
        chunk_number=1,
        chunk_title="Test",
        status="pending",
    )
    session.add(chunk)
    session.flush()

    for line_id, char, text in [
        ("1", "Hero", "Test line 1"),
        ("2", "Hero", "Test line 2"),
    ]:
        session.add(
            SourceLine(
                project_id=project.id,
                source_file_id=src_file.id,
                line_id=line_id,
                character=char,
                source_text_ja=text,
                chunk_id=chunk.id,
            )
        )

    session.commit()
    return chunk.id


def test_evaluate_list_runs_filtered(shared_session):
    project_a = Project(title="Project A", genre="RPG")
    shared_session.add(project_a)
    shared_session.flush()
    chunk_a_id = _create_test_chunk_with_project(shared_session, project_a)

    project_b = Project(title="Project B", genre="RPG")
    shared_session.add(project_b)
    shared_session.flush()
    chunk_b_id = _create_test_chunk_with_project(shared_session, project_b)

    with (
        patch("app.routes.evaluate.call_llm_json", return_value=_mock_translations),
        patch("app.routes.evaluate.get_normalized_provider", return_value="test"),
        patch("app.routes.evaluate.get_llm_settings", return_value={"model": "test-model"}),
    ):
        client = TestClient(app)
        client.post(f"/evaluate/chunk/{chunk_a_id}?mode=plain")
        client.post(f"/evaluate/chunk/{chunk_a_id}?mode=context")
        client.post(f"/evaluate/chunk/{chunk_b_id}?mode=plain")

    all_runs = client.get("/evaluate/runs")
    assert all_runs.status_code == 200
    assert len(all_runs.json()) == 3

    filtered_a = client.get(f"/evaluate/runs?chunk_id={chunk_a_id}")
    assert filtered_a.status_code == 200
    filtered_a_data = filtered_a.json()
    assert len(filtered_a_data) == 2
    for r in filtered_a_data:
        assert r["chunk_id"] == chunk_a_id

    filtered_b = client.get(f"/evaluate/runs?chunk_id={chunk_b_id}")
    assert filtered_b.status_code == 200
    filtered_b_data = filtered_b.json()
    assert len(filtered_b_data) == 1
    assert filtered_b_data[0]["chunk_id"] == chunk_b_id


def test_evaluate_chunk_state_isolation(shared_session):
    chunk_id = _create_test_chunk(shared_session)

    chunk_before = shared_session.query(Chunk).filter(Chunk.id == chunk_id).first()
    assert chunk_before.status == "pending"
    assert chunk_before.chunk_memory_json is None
    assert chunk_before.previous_memory_json is None

    with (
        patch("app.routes.evaluate.call_llm_json", return_value=_mock_translations),
        patch("app.routes.evaluate.get_normalized_provider", return_value="test"),
        patch("app.routes.evaluate.get_llm_settings", return_value={"model": "test-model"}),
    ):
        client = TestClient(app)
        for mode in ("plain", "context", "context_memory"):
            resp = client.post(f"/evaluate/chunk/{chunk_id}?mode={mode}")
            assert resp.status_code == 200, f"{mode}: {resp.text}"

    chunk_after = shared_session.query(Chunk).filter(Chunk.id == chunk_id).first()
    assert chunk_after.status == "pending"
    assert chunk_after.chunk_memory_json is None
    assert chunk_after.previous_memory_json is None
