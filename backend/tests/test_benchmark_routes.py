from unittest.mock import patch

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import (
    BenchmarkDataset,
    BenchmarkItem,
    BenchmarkOutput,
    BenchmarkScene,
    BenchmarkSceneMemory,
)


def _load_yaml():
    with open("benchmark/dataset_v1.yaml", "r") as f:
        return f.read()


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


def _seed(shared_session, db: Session):
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
    )
    db.add(dataset)
    db.flush()

    for sd in ds_data["scenes"]:
        items_data = sd.pop("items")
        scene = BenchmarkScene(
            dataset_id=dataset.id,
            scene_number=sd["scene_number"],
            title=sd.get("title", ""),
            genre=sd["genre"],
            content_type=sd["content_type"],
            setting_or_location=sd.get("setting_or_location"),
            tone=sd.get("tone"),
        )
        db.add(scene)
        db.flush()
        for item_data in items_data:
            db.add(BenchmarkItem(
                scene_id=scene.id,
                sequence_number=item_data["sequence_number"],
                source_text_ja=item_data["source_text_ja"],
                reference_en=item_data["reference_en"],
                speaker=item_data.get("speaker"),
                requires_previous_memory=item_data.get("requires_previous_memory", False),
            ))
    db.commit()
    return dataset.id


def test_list_datasets_empty(shared_session):
    client = TestClient(app)
    response = client.get("/benchmark/datasets")
    assert response.status_code == 200
    assert response.json() == []


def test_list_datasets_after_load(shared_session):
    client = TestClient(app)
    client.post("/benchmark/datasets/load", json={"yaml": _load_yaml()})
    response = client.get("/benchmark/datasets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Echoes of the Rift Benchmark v1"
    assert data[0]["scene_count"] == 6
    assert data[0]["item_count"] == 60


def test_get_dataset_detail(shared_session):
    client = TestClient(app)
    load_resp = client.post("/benchmark/datasets/load", json={"yaml": _load_yaml()})
    ds_id = load_resp.json()["dataset_id"]

    response = client.get(f"/benchmark/datasets/{ds_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Echoes of the Rift Benchmark v1"
    assert len(data["scenes"]) == 6
    for scene in data["scenes"]:
        assert len(scene["items"]) == 10


def test_get_dataset_not_found(shared_session):
    client = TestClient(app)
    response = client.get("/benchmark/datasets/999")
    assert response.status_code == 404


def test_start_run_invalid_dataset(shared_session):
    client = TestClient(app)
    response = client.post("/benchmark/runs", json={"dataset_id": 999, "mode": "plain"})
    assert response.status_code == 404


def test_start_run_invalid_mode(shared_session):
    client = TestClient(app)
    response = client.post("/benchmark/runs", json={"dataset_id": 1, "mode": "invalid"})
    assert response.status_code == 422


def test_list_runs_filtered(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        mock_llm.return_value = {
            "translations": [{"line_id": "1", "character": "", "source_text_ja": "x", "literal_meaning": "m", "localized_text_en": "t", "localization_note": ""}],
            "chunk_memory": {"chunk_summary": "ok"},
        }

        db = next(iter(app.dependency_overrides[get_db]()))
        ds_id = _seed(shared_session, db)

        client = TestClient(app)
        client.post("/benchmark/runs", json={"dataset_id": ds_id, "mode": "plain"})
        client.post("/benchmark/runs", json={"dataset_id": ds_id, "mode": "context"})
        client.post("/benchmark/runs", json={"dataset_id": ds_id, "mode": "context_memory"})

        all_runs = client.get("/benchmark/runs")
        assert len(all_runs.json()) == 3

        filtered = client.get(f"/benchmark/runs?dataset_id={ds_id}")
        assert len(filtered.json()) == 3

        mode_filtered = client.get(f"/benchmark/runs?mode=plain")
        assert len(mode_filtered.json()) == 1


def test_get_run_detail(shared_session):
    def _smart_llm(messages):
        import re
        user_content = messages[1]["content"]
        line_ids = re.findall(r'\[(\d+)\]', user_content)
        translations = [
            {"line_id": lid, "character": "", "source_text_ja": f"src_{lid}", "literal_meaning": "m", "localized_text_en": f"t_{lid}", "localization_note": ""}
            for lid in line_ids
        ]
        return {"translations": translations, "chunk_memory": {"chunk_summary": "ok"}}

    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        mock_llm.side_effect = _smart_llm

        db = next(iter(app.dependency_overrides[get_db]()))
        ds_id = _seed(shared_session, db)

        client = TestClient(app)
        run_resp = client.post("/benchmark/runs", json={"dataset_id": ds_id, "mode": "plain"})
        run_id = run_resp.json()["run_id"]

        detail = client.get(f"/benchmark/runs/{run_id}")
        assert detail.status_code == 200
        data = detail.json()
        assert data["mode"] == "plain"
        assert len(data["scenes"]) == 6
        for scene_output in data["scenes"]:
            assert len(scene_output["outputs"]) == 10
            for out_with_item in scene_output["outputs"]:
                assert out_with_item["output"]["status"] == "completed"


def test_get_run_scene(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        mock_llm.return_value = {
            "translations": [{"line_id": "1", "character": "", "source_text_ja": "x", "literal_meaning": "m", "localized_text_en": "t", "localization_note": ""}],
            "chunk_memory": {"chunk_summary": "ok"},
        }

        db = next(iter(app.dependency_overrides[get_db]()))
        ds_id = _seed(shared_session, db)

        client = TestClient(app)
        run_resp = client.post("/benchmark/runs", json={"dataset_id": ds_id, "mode": "plain"})
        run_id = run_resp.json()["run_id"]

        scene_resp = client.get(f"/benchmark/runs/{run_id}/scenes/1")
        assert scene_resp.status_code == 200
        data = scene_resp.json()
        assert data["scene"]["scene_number"] == 1
        assert len(data["outputs"]) >= 1


def test_get_run_item(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        mock_llm.return_value = {
            "translations": [{"line_id": "1", "character": "", "source_text_ja": "x", "literal_meaning": "m", "localized_text_en": "t", "localization_note": ""}],
            "chunk_memory": {"chunk_summary": "ok"},
        }

        db = next(iter(app.dependency_overrides[get_db]()))
        ds_id = _seed(shared_session, db)

        client = TestClient(app)
        run_resp = client.post("/benchmark/runs", json={"dataset_id": ds_id, "mode": "plain"})
        run_id = run_resp.json()["run_id"]

        items = db.query(BenchmarkItem).order_by(BenchmarkItem.id).limit(1).all()
        assert len(items) > 0
        item_id = items[0].id

        item_resp = client.get(f"/benchmark/runs/{run_id}/items/{item_id}")
        assert item_resp.status_code == 200
        data = item_resp.json()
        assert data["item"]["id"] == item_id
        assert data["output"]["status"] == "completed"


def test_get_run_item_not_found(shared_session):
    client = TestClient(app)
    response = client.get("/benchmark/runs/999/items/1")
    assert response.status_code == 404


def test_get_run_metrics(shared_session):
    with (
        patch("app.benchmark.service.call_llm_json") as mock_llm,
        patch("app.benchmark.service.get_normalized_provider", return_value="test"),
        patch("app.benchmark.service.get_llm_settings", return_value={"model": "test-model"}),
    ):
        mock_llm.return_value = {
            "translations": [{"line_id": "1", "character": "", "source_text_ja": "x", "literal_meaning": "m", "localized_text_en": "t", "localization_note": ""}],
            "chunk_memory": {"chunk_summary": "ok"},
        }

        db = next(iter(app.dependency_overrides[get_db]()))
        ds_id = _seed(shared_session, db)

        client = TestClient(app)
        run_resp = client.post("/benchmark/runs", json={"dataset_id": ds_id, "mode": "plain"})
        run_id = run_resp.json()["run_id"]

        metrics_resp = client.get(f"/benchmark/runs/{run_id}/metrics")
        assert metrics_resp.status_code == 200
        m = metrics_resp.json()
        assert m["total_items"] >= 10
        assert m["mode"] == "plain"
