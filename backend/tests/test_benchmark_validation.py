import json

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app

from .conftest import db_session


def _load_yaml_str():
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


def test_valid_dataset_loads(shared_session):
    client = TestClient(app)
    yaml_text = _load_yaml_str()
    response = client.post("/benchmark/datasets/load", json={"yaml": yaml_text})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["dataset_id"] > 0
    assert data["scenes_loaded"] == 6
    assert data["items_loaded"] == 60
    assert data["name"] == "Echoes of the Rift Benchmark v1"
    assert data["version"] == "1.0.0"


def test_atomic_rollback_on_invalid(shared_session):
    client = TestClient(app)
    valid_yaml = _load_yaml_str()
    client.post("/benchmark/datasets/load", json={"yaml": valid_yaml})

    bad_yaml = valid_yaml.replace("sequence_number: 1", "sequence_number: -1")
    response = client.post("/benchmark/datasets/load", json={"yaml": bad_yaml})
    assert response.status_code == 422

    list_resp = client.get("/benchmark/datasets")
    assert len(list_resp.json()) == 1


def test_missing_provenance_rejected(shared_session):
    client = TestClient(app)
    raw = yaml.safe_load(_load_yaml_str())
    ds = raw["dataset"]
    del ds["source_or_author"]
    bad = yaml.dump({"dataset": ds}, allow_unicode=True, sort_keys=False)
    response = client.post("/benchmark/datasets/load", json={"yaml": bad})
    assert response.status_code == 422
    assert "source_or_author" in response.text


def test_duplicate_dataset_version_rejected(shared_session):
    client = TestClient(app)
    yaml_text = _load_yaml_str()
    client.post("/benchmark/datasets/load", json={"yaml": yaml_text})
    response = client.post("/benchmark/datasets/load", json={"yaml": yaml_text})
    assert response.status_code == 409


def test_duplicate_scene_number_rejected(shared_session):
    client = TestClient(app)
    raw = yaml.safe_load(_load_yaml_str())
    ds = raw["dataset"]
    ds["scenes"].append(ds["scenes"][0])
    bad = yaml.dump({"dataset": ds}, allow_unicode=True, sort_keys=False)
    response = client.post("/benchmark/datasets/load", json={"yaml": bad})
    assert response.status_code == 422


def test_duplicate_item_sequence_rejected(shared_session):
    client = TestClient(app)
    raw = yaml.safe_load(_load_yaml_str())
    ds = raw["dataset"]
    dup_item = ds["scenes"][0]["items"][0]
    ds["scenes"][0]["items"].append(dup_item)
    bad = yaml.dump({"dataset": ds}, allow_unicode=True, sort_keys=False)
    response = client.post("/benchmark/datasets/load", json={"yaml": bad})
    assert response.status_code == 422


def test_scenes_ordered(shared_session):
    from app.benchmark.validation import parse_and_validate
    result = parse_and_validate(_load_yaml_str())
    scenes = result["scenes"]
    numbers = [s["scene_number"] for s in scenes]
    assert numbers == [1, 2, 3, 4, 5, 6]


def test_items_ordered(shared_session):
    from app.benchmark.validation import parse_and_validate
    result = parse_and_validate(_load_yaml_str())
    for scene in result["scenes"]:
        seqs = [it["sequence_number"] for it in scene["items"]]
        assert seqs == list(range(1, len(seqs) + 1)), f"Scene {scene['scene_number']}: {seqs}"


def test_empty_source_rejected(shared_session):
    client = TestClient(app)
    raw = yaml.safe_load(_load_yaml_str())
    raw["dataset"]["scenes"][0]["items"][0]["source_text_ja"] = ""
    bad = yaml.dump({"dataset": raw["dataset"]}, allow_unicode=True, sort_keys=False)
    response = client.post("/benchmark/datasets/load", json={"yaml": bad})
    assert response.status_code == 422


def test_mojibake_rejected(shared_session):
    client = TestClient(app)
    raw = yaml.safe_load(_load_yaml_str())
    raw["dataset"]["scenes"][0]["items"][0]["source_text_ja"] = "��� test"
    bad = yaml.dump({"dataset": raw["dataset"]}, allow_unicode=True, sort_keys=False)
    response = client.post("/benchmark/datasets/load", json={"yaml": bad})
    assert response.status_code == 422


def test_noncontiguous_scenes_rejected(shared_session):
    client = TestClient(app)
    raw = yaml.safe_load(_load_yaml_str())
    raw["dataset"]["scenes"][0]["scene_number"] = 1
    raw["dataset"]["scenes"][1]["scene_number"] = 3
    bad = yaml.dump({"dataset": raw["dataset"]}, allow_unicode=True, sort_keys=False)
    response = client.post("/benchmark/datasets/load", json={"yaml": bad})
    assert response.status_code == 422


def test_glossary_expectation_validation(shared_session):
    client = TestClient(app)
    raw = yaml.safe_load(_load_yaml_str())
    raw["dataset"]["scenes"][0]["items"][0]["glossary_expectations"] = "not-a-list"
    bad = yaml.dump({"dataset": raw["dataset"]}, allow_unicode=True, sort_keys=False)
    response = client.post("/benchmark/datasets/load", json={"yaml": bad})
    assert response.status_code == 422


def test_placeholder_validation(shared_session):
    client = TestClient(app)
    raw = yaml.safe_load(_load_yaml_str())
    raw["dataset"]["scenes"][0]["items"][0]["placeholder_expectations"] = [""]
    bad = yaml.dump({"dataset": raw["dataset"]}, allow_unicode=True, sort_keys=False)
    response = client.post("/benchmark/datasets/load", json={"yaml": bad})
    assert response.status_code == 422


def test_malformed_context_rejected(shared_session):
    client = TestClient(app)
    raw = yaml.safe_load(_load_yaml_str())
    raw["dataset"]["scenes"][0]["context"] = "not-a-dict"
    bad = yaml.dump({"dataset": raw["dataset"]}, allow_unicode=True, sort_keys=False)
    response = client.post("/benchmark/datasets/load", json={"yaml": bad})
    assert response.status_code == 422
