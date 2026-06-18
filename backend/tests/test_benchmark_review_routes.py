"""Route-level integration tests for Phase 2B benchmark review endpoints."""

from unittest.mock import patch

import pytest
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
)


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


@pytest.fixture
def client(shared_session):
    return TestClient(app)


def _seed_run_data(session, name="Route Dataset", version="1.0", mode="plain", status="completed"):
    ds = BenchmarkDataset(
        name=name, version=version,
        source_or_author="tester", license_or_usage_status="test",
        reference_translation_method="manual", review_status="draft",
    )
    session.add(ds)
    session.flush()

    scene = BenchmarkScene(
        dataset_id=ds.id, scene_number=1, title="Route Test",
        genre="RPG", content_type="dialogue", context_json="{}",
    )
    session.add(scene)
    session.flush()

    items = []
    for seq in range(1, 4):
        item = BenchmarkItem(
            scene_id=scene.id, sequence_number=seq,
            source_text_ja=f"src_{seq}", reference_en=f"ref_{seq}",
            speaker="Tester",
        )
        session.add(item)
        items.append(item)
    session.flush()

    run = BenchmarkRun(
        dataset_id=ds.id, mode=mode,
        llm_provider="test", llm_model="test-model",
        prompt_version="1.0", status=status,
        total_scenes=1, completed_scenes=1 if status in ("completed", "completed_with_errors") else 0,
    )
    session.add(run)
    session.flush()

    outputs = []
    for item in items:
        out = BenchmarkOutput(
            run_id=run.id, benchmark_item_id=item.id,
            scene_id=scene.id, sequence_number=item.sequence_number,
            status="completed",
            output_localized_text_en=f"t_{item.sequence_number}",
        )
        session.add(out)
        outputs.append(out)
    session.flush()

    for out in outputs:
        session.add(BenchmarkAutomaticScore(
            benchmark_output_id=out.id, run_id=run.id,
            chrf_score=50.0, bleu_score=25.0,
            glossary_compliant=True, placeholders_preserved=True,
            missing_output=False, untranslated_japanese=False,
            line_id_mismatch=False, speaker_mismatch=False,
        ))
    session.flush()

    return ds, scene, run, outputs, items


# ---------------------------------------------------------------------------
# Item review routes
# ---------------------------------------------------------------------------

class TestItemReviewRoutes:
    def test_post_get_put_list(self, client, shared_session):
        _, _, run, outputs, _ = _seed_run_data(shared_session)
        shared_session.commit()

        # POST create
        resp = client.post(
            f"/benchmark/runs/{run.id}/evaluations/items",
            json={
                "benchmark_output_id": outputs[0].id,
                "reviewer_label": "Alice",
                "meaning_preservation": 20, "omission_addition_control": 12,
                "natural_english": 13, "character_voice": 10,
                "glossary_consistency": 8, "genre_tone_fit": 7,
                "scene_consistency": 4, "grammar_punctuation": 4,
            },
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["total_score"] == 78
        eval_id = data["id"]

        # GET single
        resp = client.get(f"/benchmark/evaluations/items/{eval_id}")
        assert resp.status_code == 200, resp.text
        assert resp.json()["id"] == eval_id

        # PUT update
        resp = client.put(
            f"/benchmark/evaluations/items/{eval_id}",
            json={
                "meaning_preservation": 25, "omission_addition_control": 15,
                "natural_english": 15, "character_voice": 15,
                "glossary_consistency": 10, "genre_tone_fit": 10,
                "scene_consistency": 5, "grammar_punctuation": 5,
            },
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["total_score"] == 100

        # GET list
        resp = client.get(f"/benchmark/runs/{run.id}/evaluations/items")
        assert resp.status_code == 200, resp.text
        assert len(resp.json()) == 1

    def test_old_duplicated_url_returns_404(self, client, shared_session):
        _, _, run, outputs, _ = _seed_run_data(shared_session)
        shared_session.commit()

        resp = client.put(
            "/benchmark/benchmark/evaluations/items/999",
            json={
                "meaning_preservation": 20, "omission_addition_control": 12,
                "natural_english": 13, "character_voice": 10,
                "glossary_consistency": 8, "genre_tone_fit": 7,
                "scene_consistency": 4, "grammar_punctuation": 4,
            },
        )
        assert resp.status_code == 404, resp.text

        resp = client.get("/benchmark/benchmark/evaluations/items/999")
        assert resp.status_code == 404, resp.text


# ---------------------------------------------------------------------------
# Scene review routes
# ---------------------------------------------------------------------------

class TestSceneReviewRoutes:
    def test_post_get_put_list(self, client, shared_session):
        _, scene, run, _, _ = _seed_run_data(shared_session)
        shared_session.commit()

        # POST create
        resp = client.post(
            f"/benchmark/runs/{run.id}/evaluations/scenes",
            json={
                "scene_id": scene.id,
                "reviewer_label": "ReviewerX",
                "voice_consistency": 20, "terminology_consistency": 15,
                "emotional_progression": 12, "relationship_continuity": 10,
                "narrative_coherence": 12, "genre_tone_consistency": 8,
            },
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["total_score"] == 77
        eval_id = data["id"]

        # GET single
        resp = client.get(f"/benchmark/evaluations/scenes/{eval_id}")
        assert resp.status_code == 200, resp.text
        assert resp.json()["id"] == eval_id

        # PUT update
        resp = client.put(
            f"/benchmark/evaluations/scenes/{eval_id}",
            json={
                "voice_consistency": 25, "terminology_consistency": 20,
                "emotional_progression": 15, "relationship_continuity": 15,
                "narrative_coherence": 15, "genre_tone_consistency": 10,
            },
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["total_score"] == 100

        # GET list
        resp = client.get(f"/benchmark/runs/{run.id}/evaluations/scenes")
        assert resp.status_code == 200, resp.text
        assert len(resp.json()) == 1


# ---------------------------------------------------------------------------
# Hard-failure routes
# ---------------------------------------------------------------------------

class TestHardFailureRoutes:
    def test_post_get_put_list(self, client, shared_session):
        _, _, run, outputs, _ = _seed_run_data(shared_session)
        shared_session.commit()

        # POST create
        resp = client.post(
            f"/benchmark/runs/{run.id}/hard-failures",
            json={
                "benchmark_output_id": outputs[0].id,
                "reviewer_label": "Bob",
                "invented_plot_information": True,
            },
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        failure_id = data["id"]
        assert data["invented_plot_information"] is True

        # GET single
        resp = client.get(f"/benchmark/hard-failures/{failure_id}")
        assert resp.status_code == 200, resp.text
        assert resp.json()["id"] == failure_id

        # PUT update
        resp = client.put(
            f"/benchmark/hard-failures/{failure_id}",
            json={"invented_plot_information": False, "missing_critical_meaning": True},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["invented_plot_information"] is False
        assert resp.json()["missing_critical_meaning"] is True

        # GET list
        resp = client.get(f"/benchmark/runs/{run.id}/hard-failures")
        assert resp.status_code == 200, resp.text
        assert len(resp.json()) == 1


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class TestHumanMetricsRoute:
    def test_get_human_metrics(self, client, shared_session):
        _, _, run, outputs, _ = _seed_run_data(shared_session)
        shared_session.commit()

        resp = client.get(f"/benchmark/runs/{run.id}/human-metrics")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["run_id"] == run.id
        assert data["item_review_coverage_percentage"] == 0.0


# ---------------------------------------------------------------------------
# Comparison routes
# ---------------------------------------------------------------------------

class TestComparisonRoutes:
    def test_explicit_three_mode(self, client, shared_session):
        ds = BenchmarkDataset(
            name="Cmp", version="1.0",
            source_or_author="tester", license_or_usage_status="test",
            reference_translation_method="manual", review_status="draft",
        )
        shared_session.add(ds)
        shared_session.flush()

        scene = BenchmarkScene(
            dataset_id=ds.id, scene_number=1, title="Cmp",
            genre="RPG", content_type="dialogue", context_json="{}",
        )
        shared_session.add(scene)
        shared_session.flush()

        item = BenchmarkItem(
            scene_id=scene.id, sequence_number=1,
            source_text_ja="src", reference_en="ref", speaker="T",
        )
        shared_session.add(item)
        shared_session.flush()

        runs = []
        for mode in ("plain", "context", "context_memory"):
            run = BenchmarkRun(
                dataset_id=ds.id, mode=mode,
                llm_provider="test", llm_model="test-model",
                prompt_version="1.0", status="completed",
                total_scenes=1, completed_scenes=1,
            )
            shared_session.add(run)
            shared_session.flush()
            out = BenchmarkOutput(
                run_id=run.id, benchmark_item_id=item.id,
                scene_id=scene.id, sequence_number=1,
                status="completed", output_localized_text_en=f"t_{mode}",
            )
            shared_session.add(out)
            shared_session.flush()
            shared_session.add(BenchmarkAutomaticScore(
                benchmark_output_id=out.id, run_id=run.id,
                chrf_score=50.0, bleu_score=25.0,
                glossary_compliant=True, placeholders_preserved=True,
                missing_output=False, untranslated_japanese=False,
                line_id_mismatch=False, speaker_mismatch=False,
            ))
            shared_session.flush()
            runs.append(run)

        shared_session.commit()

        resp = client.get(
            "/benchmark/compare",
            params={
                "plain_run_id": runs[0].id,
                "context_run_id": runs[1].id,
                "context_memory_run_id": runs[2].id,
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data["runs"]) == 3

    def test_latest_completed(self, client, shared_session):
        _seed_run_data(shared_session)
        shared_session.commit()

        # Get the dataset id
        ds = shared_session.query(BenchmarkDataset).first()
        resp = client.get(
            "/benchmark/compare",
            params={"dataset_id": ds.id, "selection": "latest_completed"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data["runs"]) == 1  # only 1 mode seeded

    def test_partial_explicit_rejected(self, client, shared_session):
        _, _, run, _, _ = _seed_run_data(shared_session)
        shared_session.commit()

        resp = client.get(
            "/benchmark/compare",
            params={"plain_run_id": run.id, "context_run_id": run.id},
        )
        assert resp.status_code == 422, resp.text

    def test_pending_run_rejected(self, client, shared_session):
        ds = BenchmarkDataset(
            name="PendingDs", version="1.0",
            source_or_author="tester", license_or_usage_status="test",
            reference_translation_method="manual", review_status="draft",
        )
        shared_session.add(ds)
        shared_session.flush()

        scene = BenchmarkScene(
            dataset_id=ds.id, scene_number=1, title="P",
            genre="RPG", content_type="dialogue", context_json="{}",
        )
        shared_session.add(scene)
        shared_session.flush()

        item = BenchmarkItem(
            scene_id=scene.id, sequence_number=1,
            source_text_ja="src", reference_en="ref", speaker="T",
        )
        shared_session.add(item)
        shared_session.flush()

        modes = ("plain", "context", "context_memory")
        runs = []
        for mode in modes:
            run = BenchmarkRun(
                dataset_id=ds.id, mode=mode,
                llm_provider="test", llm_model="test-model",
                prompt_version="1.0", status="pending",
                total_scenes=1, completed_scenes=0,
            )
            shared_session.add(run)
            shared_session.flush()

            out = BenchmarkOutput(
                run_id=run.id, benchmark_item_id=item.id,
                scene_id=scene.id, sequence_number=1,
                status="pending",
            )
            shared_session.add(out)
            shared_session.flush()
            shared_session.add(BenchmarkAutomaticScore(
                benchmark_output_id=out.id, run_id=run.id,
                chrf_score=None, bleu_score=None,
                glossary_compliant=None, placeholders_preserved=None,
                missing_output=True, untranslated_japanese=None,
                line_id_mismatch=False, speaker_mismatch=None,
            ))
            shared_session.flush()
            runs.append(run)

        shared_session.commit()

        resp = client.get(
            "/benchmark/compare",
            params={
                "plain_run_id": runs[0].id,
                "context_run_id": runs[1].id,
                "context_memory_run_id": runs[2].id,
            },
        )
        assert resp.status_code == 422, resp.text
        assert "pending" in resp.text


# ---------------------------------------------------------------------------
# Error safety
# ---------------------------------------------------------------------------

class TestErrorSafety:
    def test_unexpected_error_returns_internal_review_error(self, client, shared_session):
        with patch(
            "app.routes.benchmark_review.create_item_evaluation",
            side_effect=RuntimeError("something sensitive"),
        ):
            resp = client.post(
                "/benchmark/runs/999/evaluations/items",
                json={
                    "benchmark_output_id": 1,
                    "reviewer_label": "X",
                    "meaning_preservation": 20, "omission_addition_control": 12,
                    "natural_english": 13, "character_voice": 10,
                    "glossary_consistency": 8, "genre_tone_fit": 7,
                    "scene_consistency": 4, "grammar_punctuation": 4,
                },
            )
            assert resp.status_code == 500, resp.text
            assert resp.json()["detail"] == "internal_review_error"
            assert "sensitive" not in resp.text
