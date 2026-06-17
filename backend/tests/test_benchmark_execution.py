import json
from unittest.mock import patch

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import (
    BenchmarkAutomaticScore,
    BenchmarkDataset,
    BenchmarkItem,
    BenchmarkOutput,
    BenchmarkRun,
    BenchmarkScene,
    BenchmarkSceneMemory,
    Chunk,
    ContextData,
    EvaluationRun,
    EvaluationTranslation,
    Project,
    SourceFile,
    SourceLine,
    Translation,
)


def _load_yaml():
    with open("benchmark/dataset_v1.yaml", "r") as f:
        return f.read()


def _make_translations(items, memory):
    translations = []
    for it in items:
        translations.append({
            "line_id": str(it["sequence_number"]),
            "character": it.get("speaker", "") or "",
            "source_text_ja": it["source_text_ja"],
            "literal_meaning": "Fake: " + it["reference_en"][:40],
            "localized_text_en": it["reference_en"],
            "localization_note": "",
        })
    return {
        "translations": translations,
        "chunk_memory": {
            "chunk_summary": memory.get("summary", f"Scene complete"),
            "updated_environment": memory.get("env", "test_location"),
            "character_states": memory.get("states", {}),
            "relationship_updates": memory.get("relationships", []),
            "tone_to_continue": memory.get("tone", "neutral"),
            "important_terms": memory.get("terms", {}),
            "unresolved_hooks": memory.get("hooks", []),
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


def _seed_dataset(shared_session, db: Session):
    yaml_text = _load_yaml()
    raw = yaml.safe_load(yaml_text)
    ds_data = raw["dataset"]
    dataset = BenchmarkDataset(
        name=ds_data["name"],
        version=ds_data["version"],
        source_or_author=ds_data["source_or_author"],
        license_or_usage_status=ds_data["license_or_usage_status"],
        reference_translation_method=ds_data["reference_translation_method"],
        review_status=ds_data["review_status"],
        description=ds_data.get("description", ""),
    )
    db.add(dataset)
    db.flush()

    all_items = []
    for scene_data in ds_data["scenes"]:
        items_list = scene_data.pop("items")
        scene = BenchmarkScene(
            dataset_id=dataset.id,
            scene_number=scene_data["scene_number"],
            title=scene_data.get("title", ""),
            genre=scene_data["genre"],
            content_type=scene_data["content_type"],
            setting_or_location=scene_data.get("setting_or_location"),
            tone=scene_data.get("tone"),
            context_json=json.dumps(scene_data.get("context", {}), ensure_ascii=False),
        )
        db.add(scene)
        db.flush()
        for item_data in items_list:
            item = BenchmarkItem(
                scene_id=scene.id,
                sequence_number=item_data["sequence_number"],
                source_text_ja=item_data["source_text_ja"],
                reference_en=item_data["reference_en"],
                speaker=item_data.get("speaker"),
                character_voice_context=item_data.get("character_voice_context"),
                relationship_context=item_data.get("relationship_context"),
                glossary_expectations=json.dumps(item_data.get("glossary_expectations", []), ensure_ascii=False)
                if item_data.get("glossary_expectations") else None,
                placeholder_expectations=json.dumps(item_data.get("placeholder_expectations", []), ensure_ascii=False)
                if item_data.get("placeholder_expectations") else None,
                requires_previous_memory=item_data.get("requires_previous_memory", False),
            )
            db.add(item)
            all_items.append(item)
        db.flush()

    db.commit()
    return dataset.id


memory_counter = {"call": 0}


def _fake_llm(messages):
    memory_counter["call"] += 1
    call_idx = memory_counter["call"]
    memory = {
        "summary": f"Scene {call_idx} complete with key events",
        "env": f"location_{call_idx}",
        "states": {"Kaelen": "determined"},
        "relationships": [],
        "tone": "neutral",
        "terms": {"聖剣": "Sacred Sword"},
        "hooks": [],
    }

    user_content = messages[1]["content"] if len(messages) > 1 else ""
    has_prev_memory = "Previous Scene Memory" in user_content

    scene_items = []
    for line in user_content.split("\n"):
        if line.strip().startswith("[") and "]: " in line:
            scene_items.append(True)

    items = _get_scene_items_from_messages(messages)
    if items is None:
        items = []

    return _make_translations(
        [{"sequence_number": i + 1, "reference_en": f"Fake translation {i+1}", "speaker": ""} for i in range(len(scene_items))],
        memory,
    )


def _fake_llm_with_items(items_by_scene):
    def _fake(messages):
        user_content = messages[1]["content"] if len(messages) > 1 else ""
        has_prev = "Previous Scene Memory" in user_content

        line_ids = []
        for line in user_content.split("\n"):
            line = line.strip()
            if line.startswith("[") and "]: " in line:
                lid = line[1:].split("]")[0]
                if lid.isdigit():
                    line_ids.append(int(lid))

        scene_found = None
        for scene_num, scene_items in items_by_scene.items():
            item_seqs = {it["sequence_number"] for it in scene_items}
            matching = item_seqs & set(line_ids)
            if matching and len(matching) > 0:
                scene_found = scene_num
                break

        if scene_found is None:
            scene_found = 1

        sid = str(scene_found)
        scene_items = items_by_scene.get(scene_found, [])
        memory = {
            "summary": f"Scene {sid} complete",
            "updated_environment": f"loc_{sid}",
            "character_states": {},
            "relationship_updates": [],
            "tone_to_continue": "neutral",
            "important_terms": {},
            "unresolved_hooks": [],
        }

        translations = []
        for it in scene_items:
            translations.append({
                "line_id": str(it["sequence_number"]),
                "character": it.get("speaker", "") or "",
                "source_text_ja": it["source_text_ja"],
                "literal_meaning": "Fake meaning",
                "localized_text_en": it["reference_en"],
                "localization_note": "",
            })

        return {"translations": translations, "chunk_memory": memory}

    return _fake


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------


def test_plain_mode_execution(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        items = db.query(BenchmarkItem).order_by(BenchmarkItem.sequence_number).all()
        by_scene = {}
        for it in items:
            by_scene.setdefault(it.scene_id, []).append({
                "sequence_number": it.sequence_number,
                "speaker": it.speaker or "",
                "source_text_ja": it.source_text_ja,
                "reference_en": it.reference_en,
            })

        mock_llm.side_effect = _fake_llm_with_items(by_scene)

        client = TestClient(app)
        response = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "plain"})
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "completed"
        assert data["total_scenes"] == 6
        assert data["completed_scenes"] == 6
        assert data["mode"] == "plain"
        assert data["memory_gap"] is False

        memories = db.query(BenchmarkSceneMemory).filter(BenchmarkSceneMemory.run_id == data["run_id"]).all()
        assert len(memories) == 0

        outputs = db.query(BenchmarkOutput).filter(BenchmarkOutput.run_id == data["run_id"]).all()
        assert len(outputs) == 60
        for out in outputs:
            assert out.status == "completed"

        metrics_resp = client.get(f"/benchmark/runs/{data['run_id']}/metrics")
        assert metrics_resp.status_code == 200
        m = metrics_resp.json()
        assert m["total_items"] == 60
        assert m["completed_items"] == 60


def test_plain_mode_no_context(shared_session):
    prompts_captured = []

    def _capture_llm(messages):
        prompts_captured.append(messages[1]["content"])
        return _fake_llm_with_items({})(messages)

    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        items = db.query(BenchmarkItem).order_by(BenchmarkItem.sequence_number).all()
        by_scene = {}
        for it in items:
            by_scene.setdefault(it.scene_id, []).append({
                "sequence_number": it.sequence_number,
                "speaker": it.speaker or "",
                "source_text_ja": it.source_text_ja,
                "reference_en": it.reference_en,
            })

        mock_llm.side_effect = _fake_llm_with_items(by_scene)

        client = TestClient(app)
        response = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "plain"})
        assert response.status_code == 200

        call_args_list = mock_llm.call_args_list
        for call_args in call_args_list:
            messages = call_args[0][0]
            user_content = messages[1]["content"]
            assert "Character Profiles" not in user_content
            assert "Glossary" not in user_content
            assert "Previous Scene Memory" not in user_content
            assert "Game:" not in user_content
            assert "Current Chunk Lines" in user_content


def test_context_mode_execution(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        items = db.query(BenchmarkItem).order_by(BenchmarkItem.sequence_number).all()
        by_scene = {}
        for it in items:
            by_scene.setdefault(it.scene_id, []).append({
                "sequence_number": it.sequence_number,
                "speaker": it.speaker or "",
                "source_text_ja": it.source_text_ja,
                "reference_en": it.reference_en,
            })

        mock_llm.side_effect = _fake_llm_with_items(by_scene)

        client = TestClient(app)
        response = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "context"})
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "completed"
        assert data["total_scenes"] == 6

        memories = db.query(BenchmarkSceneMemory).filter(BenchmarkSceneMemory.run_id == data["run_id"]).all()
        assert len(memories) == 0


def test_context_mode_contains_context(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        items = db.query(BenchmarkItem).order_by(BenchmarkItem.sequence_number).all()
        by_scene = {}
        for it in items:
            by_scene.setdefault(it.scene_id, []).append({
                "sequence_number": it.sequence_number,
                "speaker": it.speaker or "",
                "source_text_ja": it.source_text_ja,
                "reference_en": it.reference_en,
            })

        mock_llm.side_effect = _fake_llm_with_items(by_scene)

        client = TestClient(app)
        client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "context"})

        for call_args in mock_llm.call_args_list:
            messages = call_args[0][0]
            user_content = messages[1]["content"]
            assert "Previous Scene Memory" not in user_content
            assert "Game:" in user_content


def test_context_memory_mode_execution(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        items = db.query(BenchmarkItem).order_by(BenchmarkItem.sequence_number).all()
        by_scene = {}
        for it in items:
            by_scene.setdefault(it.scene_id, []).append({
                "sequence_number": it.sequence_number,
                "speaker": it.speaker or "",
                "source_text_ja": it.source_text_ja,
                "reference_en": it.reference_en,
            })

        mock_llm.side_effect = _fake_llm_with_items(by_scene)

        client = TestClient(app)
        response = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "context_memory"})
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "completed"
        assert data["memory_gap"] is False

        memories = db.query(BenchmarkSceneMemory).filter(BenchmarkSceneMemory.run_id == data["run_id"]).all()
        assert len(memories) == 6


def test_context_memory_cross_scene_propagation(shared_session):
    scene_prompts = []

    def _capture_llm(messages):
        scene_prompts.append(messages[1]["content"])
        call_idx = len(scene_prompts)
        memory = {
            "chunk_summary": f"Scene {call_idx} complete with key events",
            "updated_environment": f"loc_{call_idx}",
            "character_states": {"Kaelen": "determined"},
            "relationship_updates": [],
            "tone_to_continue": "hopeful",
            "important_terms": {"聖剣": "Sacred Sword"},
            "unresolved_hooks": [],
        }
        items = _get_scene_items_from_messages(messages)
        if items is None:
            items = []
        translations = [
            {
                "line_id": str(i + 1),
                "character": "",
                "source_text_ja": f"source_{i+1}",
                "literal_meaning": "meaning",
                "localized_text_en": f"trans_{i+1}",
                "localization_note": "",
            }
            for i in range(len(items))
        ]
        return {"translations": translations, "chunk_memory": memory}

    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        items = db.query(BenchmarkItem).order_by(BenchmarkItem.sequence_number).all()
        by_scene = {}
        for it in items:
            by_scene.setdefault(it.scene_id, []).append({
                "sequence_number": it.sequence_number,
                "speaker": it.speaker or "",
                "source_text_ja": it.source_text_ja,
                "reference_en": it.reference_en,
            })

        mock_llm.side_effect = _capture_llm

        client = TestClient(app)
        response = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "context_memory"})
        assert response.status_code == 200

        for i, prompt in enumerate(scene_prompts):
            if i == 0:
                assert "Previous Scene Memory" not in prompt, f"Scene {i+1} should not have previous memory"
            else:
                assert "Previous Scene Memory" in prompt, f"Scene {i+1} should have previous memory"


def _get_scene_items_from_messages(messages):
    import re
    user_content = messages[1]["content"] if len(messages) > 1 else ""
    line_ids = []
    for line in user_content.split("\n"):
        line = line.strip()
        m = re.match(r'^\s*\[(\d+)\]', line)
        if m:
            line_ids.append(int(m.group(1)))
    if not line_ids:
        return None
    return line_ids


def test_append_only_runs(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        items = db.query(BenchmarkItem).order_by(BenchmarkItem.sequence_number).all()
        by_scene = {}
        for it in items:
            by_scene.setdefault(it.scene_id, []).append({
                "sequence_number": it.sequence_number,
                "speaker": it.speaker or "",
                "source_text_ja": it.source_text_ja,
                "reference_en": it.reference_en,
            })
        mock_llm.side_effect = _fake_llm_with_items(by_scene)

        client = TestClient(app)
        r1 = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "plain"})
        r2 = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "context"})
        r3 = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "context_memory"})

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r3.status_code == 200

        runs_resp = client.get("/benchmark/runs")
        assert len(runs_resp.json()) == 3
        run_ids = [r["id"] for r in runs_resp.json()]
        assert len(set(run_ids)) == 3


def test_partial_failure_preserves_prior(shared_session):
    call_count = [0]

    def _failing_llm(messages):
        call_count[0] += 1
        if call_count[0] == 3:
            raise ValueError("Simulated scene 3 failure")
        return {
            "translations": [
                {"line_id": "1", "character": "", "source_text_ja": "test", "literal_meaning": "m", "localized_text_en": "t", "localization_note": ""},
            ],
            "chunk_memory": {"chunk_summary": "ok"},
        }

    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        all_items = db.query(BenchmarkItem).order_by(BenchmarkItem.id).all()
        by_scene = {}
        for it in all_items:
            by_scene.setdefault(it.scene_id, []).append({
                "sequence_number": it.sequence_number,
                "speaker": it.speaker or "",
                "source_text_ja": it.source_text_ja,
                "reference_en": it.reference_en,
            })

        mock_llm.side_effect = _failing_llm

        client = TestClient(app)
        response = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "context_memory"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed_with_errors"
        assert data["completed_scenes"] >= 1

        outputs = db.query(BenchmarkOutput).filter(BenchmarkOutput.run_id == data["run_id"]).all()
        completed = [o for o in outputs if o.status == "completed"]
        failed = [o for o in outputs if o.status == "failed"]
        assert len(completed) > 0
        assert len(failed) > 0
        for f in failed:
            assert f.error_message in ("llm_request_failed", "invalid_llm_response", "missing_translation")


def test_controlled_error_categories(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json", side_effect=RuntimeError("API connection timeout")),
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        client = TestClient(app)
        response = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "plain"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"

        outputs = db.query(BenchmarkOutput).filter(BenchmarkOutput.run_id == data["run_id"]).all()
        for out in outputs:
            assert out.status == "failed"
            assert out.error_message in ("llm_request_failed", "invalid_llm_response", "missing_translation")


def test_one_output_per_item(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        items = db.query(BenchmarkItem).order_by(BenchmarkItem.sequence_number).all()
        by_scene = {}
        for it in items:
            by_scene.setdefault(it.scene_id, []).append({
                "sequence_number": it.sequence_number,
                "speaker": it.speaker or "",
                "source_text_ja": it.source_text_ja,
                "reference_en": it.reference_en,
            })

        mock_llm.side_effect = _fake_llm_with_items(by_scene)

        client = TestClient(app)
        response = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "plain"})
        assert response.status_code == 200
        run_id = response.json()["run_id"]

        outputs = db.query(BenchmarkOutput).filter(BenchmarkOutput.run_id == run_id).all()
        assert len(outputs) == 60
        output_item_ids = [o.benchmark_item_id for o in outputs]
        assert len(set(output_item_ids)) == 60

        scores = db.query(BenchmarkAutomaticScore).join(BenchmarkOutput).filter(BenchmarkOutput.run_id == run_id).all()
        assert len(scores) == 60
        score_output_ids = [s.benchmark_output_id for s in scores]
        assert len(set(score_output_ids)) == 60


def test_missing_duplicate_line_ids(shared_session):
    call_count = [0]

    def _bad_llm(messages):
        call_count[0] += 1
        return {
            "translations": [
                {"line_id": "999", "character": "", "source_text_ja": "x", "literal_meaning": "m", "localized_text_en": "t", "localization_note": ""},
            ],
            "chunk_memory": {"chunk_summary": "ok"},
        }

    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        mock_llm.side_effect = _bad_llm

        client = TestClient(app)
        response = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "plain"})
        assert response.status_code == 200
        run_id = response.json()["run_id"]

        outputs = db.query(BenchmarkOutput).filter(BenchmarkOutput.run_id == run_id).all()
        completed = [o for o in outputs if o.status == "completed"]
        failed = [o for o in outputs if o.status == "failed"]
        assert len(completed) >= 0
        assert len(failed) > 0
        for f in failed:
            if f.error_message == "missing_translation":
                break
        else:
            pytest.fail("No missing_translation errors found")


def test_chrf_computed(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        items = db.query(BenchmarkItem).order_by(BenchmarkItem.sequence_number).all()
        by_scene = {}
        for it in items:
            by_scene.setdefault(it.scene_id, []).append({
                "sequence_number": it.sequence_number,
                "speaker": it.speaker or "",
                "source_text_ja": it.source_text_ja,
                "reference_en": it.reference_en,
            })

        mock_llm.side_effect = _fake_llm_with_items(by_scene)

        client = TestClient(app)
        response = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "plain"})
        assert response.status_code == 200
        run_id = response.json()["run_id"]

        scores = db.query(BenchmarkAutomaticScore).join(BenchmarkOutput).filter(BenchmarkOutput.run_id == run_id).all()
        chrf_scores = [s.chrf_score for s in scores if s.chrf_score is not None]
        assert len(chrf_scores) > 0
        for cs in chrf_scores:
            assert 0 <= cs <= 100


def test_dataset_version_metadata_traceable(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test-provider"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model-v2"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        items = db.query(BenchmarkItem).order_by(BenchmarkItem.sequence_number).all()
        by_scene = {}
        for it in items:
            by_scene.setdefault(it.scene_id, []).append({
                "sequence_number": it.sequence_number,
                "speaker": it.speaker or "",
                "source_text_ja": it.source_text_ja,
                "reference_en": it.reference_en,
            })

        mock_llm.side_effect = _fake_llm_with_items(by_scene)

        client = TestClient(app)
        response = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "plain"})
        run_id = response.json()["run_id"]

        run_resp = client.get(f"/benchmark/runs/{run_id}")
        assert run_resp.status_code == 200
        rd = run_resp.json()
        assert rd["llm_provider"] == "test-provider"
        assert rd["llm_model"] == "test-model-v2"
        assert rd["prompt_version"] is not None

        metrics_resp = client.get(f"/benchmark/runs/{run_id}/metrics")
        assert metrics_resp.status_code == 200
        m = metrics_resp.json()
        assert m["dataset_name"] == "Echoes of the Rift Benchmark v1"
        assert m["dataset_version"] == "1.0.0"
        assert m["provider"] == "test-provider"
        assert m["model"] == "test-model-v2"


def test_production_isolation(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        items = db.query(BenchmarkItem).order_by(BenchmarkItem.sequence_number).all()
        by_scene = {}
        for it in items:
            by_scene.setdefault(it.scene_id, []).append({
                "sequence_number": it.sequence_number,
                "speaker": it.speaker or "",
                "source_text_ja": it.source_text_ja,
                "reference_en": it.reference_en,
            })

        mock_llm.side_effect = _fake_llm_with_items(by_scene)

        proj = Project(title="Sentinel", genre="Test")
        db.add(proj)
        db.commit()
        proj_id = proj.id

        client = TestClient(app)
        response = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "plain"})
        assert response.status_code == 200

        assert db.query(Project).filter(Project.id == proj_id).first() is not None
        assert db.query(Project).count() == 1
        assert db.query(Chunk).count() == 0
        assert db.query(ContextData).count() == 0
        assert db.query(SourceFile).count() == 0
        assert db.query(SourceLine).count() == 0
        assert db.query(Translation).count() == 0
        assert db.query(EvaluationRun).count() == 0
        assert db.query(EvaluationTranslation).count() == 0


def test_metrics_aggregation_includes_memory_dependent(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        db = next(iter(app.dependency_overrides[get_db]()))
        dataset_id = _seed_dataset(shared_session, db)

        items = db.query(BenchmarkItem).order_by(BenchmarkItem.sequence_number).all()
        by_scene = {}
        for it in items:
            by_scene.setdefault(it.scene_id, []).append({
                "sequence_number": it.sequence_number,
                "speaker": it.speaker or "",
                "source_text_ja": it.source_text_ja,
                "reference_en": it.reference_en,
            })

        mock_llm.side_effect = _fake_llm_with_items(by_scene)

        client = TestClient(app)
        response = client.post("/benchmark/runs", json={"dataset_id": dataset_id, "mode": "plain"})
        run_id = response.json()["run_id"]

        metrics_resp = client.get(f"/benchmark/runs/{run_id}/metrics")
        m = metrics_resp.json()
        assert m["requires_previous_memory"] is not None
        assert m["no_previous_memory"] is not None
        assert m["requires_previous_memory"]["count"] >= 10
        assert m["no_previous_memory"]["count"] >= 40
        assert "RPG" in m["per_genre"]
        assert "VN" in m["per_genre"]
        assert "Action" in m["per_genre"]
        assert "Quest" in m["per_genre"]
        assert "Item" in m["per_genre"]
