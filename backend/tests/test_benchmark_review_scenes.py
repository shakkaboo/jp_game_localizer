import pytest
from sqlalchemy.exc import IntegrityError

from app.benchmark.review_service import (
    calculate_scene_total,
    create_scene_evaluation,
    get_scene_evaluation,
    list_scene_evaluations,
    update_scene_evaluation,
)
from app.models import BenchmarkDataset, BenchmarkOutput, BenchmarkRun, BenchmarkScene
from app.schemas import BenchmarkSceneEvaluationUpdate


def _seed_run(db):
    ds = BenchmarkDataset(
        name="Test Dataset",
        version="1.0",
        source_or_author="tester",
        license_or_usage_status="test",
        reference_translation_method="manual",
        review_status="draft",
    )
    db.add(ds)
    db.flush()

    scenes = []
    for sn in range(1, 4):
        scene = BenchmarkScene(
            dataset_id=ds.id,
            scene_number=sn,
            title=f"Scene {sn}",
            genre="RPG",
            content_type="dialogue",
            context_json="{}",
        )
        db.add(scene)
        scenes.append(scene)
    db.flush()

    run = BenchmarkRun(
        dataset_id=ds.id,
        mode="plain",
        llm_provider="test",
        llm_model="test-model",
        prompt_version="1.0",
        status="completed",
        total_scenes=3,
        completed_scenes=3,
    )
    db.add(run)
    db.flush()
    return run, scenes, ds


class TestCalculateSceneTotal:
    def test_max(self):
        assert calculate_scene_total(
            voice_consistency=25, terminology_consistency=20,
            emotional_progression=15, relationship_continuity=15,
            narrative_coherence=15, genre_tone_consistency=10,
        ) == 100

    def test_min(self):
        assert calculate_scene_total(
            voice_consistency=0, terminology_consistency=0,
            emotional_progression=0, relationship_continuity=0,
            narrative_coherence=0, genre_tone_consistency=0,
        ) == 0

    def test_out_of_range(self):
        with pytest.raises(ValueError):
            calculate_scene_total(
                voice_consistency=26, terminology_consistency=0,
                emotional_progression=0, relationship_continuity=0,
                narrative_coherence=0, genre_tone_consistency=0,
            )


class TestCreateSceneEvaluation:
    def test_valid(self, db_session):
        run, scenes, *_ = _seed_run(db_session)
        ev = create_scene_evaluation(db_session, run.id, {
            "scene_id": scenes[0].id,
            "reviewer_label": "ReviewerA",
            "voice_consistency": 20,
            "terminology_consistency": 15,
            "emotional_progression": 12,
            "relationship_continuity": 10,
            "narrative_coherence": 12,
            "genre_tone_consistency": 8,
            "reviewer_notes": "Nice scene",
        })
        db_session.commit()
        assert ev.total_score == 77
        assert ev.reviewer_label == "ReviewerA"
        assert ev.run_id == run.id

    def test_total_server_calculated(self, db_session):
        run, scenes, *_ = _seed_run(db_session)
        ev = create_scene_evaluation(db_session, run.id, {
            "scene_id": scenes[0].id,
            "reviewer_label": "B",
            "voice_consistency": 20,
            "terminology_consistency": 15,
            "emotional_progression": 12,
            "relationship_continuity": 10,
            "narrative_coherence": 12,
            "genre_tone_consistency": 8,
        })
        assert ev.total_score == 77

    def test_duplicate_reviewer_raises(self, db_session):
        run, scenes, *_ = _seed_run(db_session)
        data = {
            "scene_id": scenes[0].id,
            "reviewer_label": "Dup",
            "voice_consistency": 20,
            "terminology_consistency": 15,
            "emotional_progression": 12,
            "relationship_continuity": 10,
            "narrative_coherence": 12,
            "genre_tone_consistency": 8,
        }
        create_scene_evaluation(db_session, run.id, data)
        db_session.commit()
        with pytest.raises(IntegrityError):
            create_scene_evaluation(db_session, run.id, data)
            db_session.commit()

    def test_wrong_dataset_scene_rejected(self, db_session):
        run, scenes, ds = _seed_run(db_session)
        ds2 = BenchmarkDataset(
            name="Other Dataset", version="1.0",
            source_or_author="tester", license_or_usage_status="test",
            reference_translation_method="manual", review_status="draft",
        )
        db_session.add(ds2)
        db_session.flush()
        other_scene = BenchmarkScene(
            dataset_id=ds2.id, scene_number=1, title="Other",
            genre="RPG", content_type="dialogue", context_json="{}",
        )
        db_session.add(other_scene)
        db_session.flush()

        with pytest.raises(ValueError, match="does not belong"):
            create_scene_evaluation(db_session, run.id, {
                "scene_id": other_scene.id,
                "reviewer_label": "R",
                "voice_consistency": 20,
                "terminology_consistency": 15,
                "emotional_progression": 12,
                "relationship_continuity": 10,
                "narrative_coherence": 12,
                "genre_tone_consistency": 8,
            })


class TestUpdateSceneEvaluation:
    def test_update_preserves_created_at(self, db_session):
        run, scenes, *_ = _seed_run(db_session)
        ev = create_scene_evaluation(db_session, run.id, {
            "scene_id": scenes[0].id,
            "reviewer_label": "Updater",
            "voice_consistency": 10,
            "terminology_consistency": 10,
            "emotional_progression": 5,
            "relationship_continuity": 5,
            "narrative_coherence": 5,
            "genre_tone_consistency": 3,
        })
        db_session.commit()
        orig_created = ev.created_at
        orig_updated = ev.updated_at

        ev2 = update_scene_evaluation(db_session, ev.id, {
            "voice_consistency": 25,
            "terminology_consistency": 20,
            "emotional_progression": 15,
            "relationship_continuity": 15,
            "narrative_coherence": 15,
            "genre_tone_consistency": 10,
        })
        db_session.commit()
        assert ev2.total_score == 100
        assert ev2.created_at == orig_created
        assert ev2.updated_at > orig_updated

    def test_identity_fields_not_in_update_schema(self):
        with pytest.raises(Exception):
            BenchmarkSceneEvaluationUpdate(
                voice_consistency=20, terminology_consistency=15,
                emotional_progression=12, relationship_continuity=10,
                narrative_coherence=12, genre_tone_consistency=8,
                run_id=999,
            )

    def test_update_not_found(self, db_session):
        with pytest.raises(LookupError):
            update_scene_evaluation(db_session, 99999, {
                "voice_consistency": 20,
                "terminology_consistency": 15,
                "emotional_progression": 12,
                "relationship_continuity": 10,
                "narrative_coherence": 12,
                "genre_tone_consistency": 8,
            })


class TestGetSceneEvaluation:
    def test_get_by_id(self, db_session):
        run, scenes, *_ = _seed_run(db_session)
        ev = create_scene_evaluation(db_session, run.id, {
            "scene_id": scenes[0].id,
            "reviewer_label": "Getter",
            "voice_consistency": 20,
            "terminology_consistency": 15,
            "emotional_progression": 12,
            "relationship_continuity": 10,
            "narrative_coherence": 12,
            "genre_tone_consistency": 8,
        })
        db_session.commit()
        fetched = get_scene_evaluation(db_session, ev.id)
        assert fetched.id == ev.id

    def test_get_not_found(self, db_session):
        with pytest.raises(LookupError):
            get_scene_evaluation(db_session, 99999)


class TestListSceneEvaluations:
    def test_list_for_run(self, db_session):
        run, scenes, *_ = _seed_run(db_session)
        for i, scene in enumerate(scenes):
            create_scene_evaluation(db_session, run.id, {
                "scene_id": scene.id,
                "reviewer_label": f"R{i}",
                "voice_consistency": 20,
                "terminology_consistency": 15,
                "emotional_progression": 12,
                "relationship_continuity": 10,
                "narrative_coherence": 12,
                "genre_tone_consistency": 8,
            })
        db_session.commit()
        evals = list_scene_evaluations(db_session, run.id)
        assert len(evals) == 3


class TestBoundaries:
    def test_all_min(self, db_session):
        run, scenes, *_ = _seed_run(db_session)
        ev = create_scene_evaluation(db_session, run.id, {
            "scene_id": scenes[0].id,
            "reviewer_label": "Min",
            "voice_consistency": 0,
            "terminology_consistency": 0,
            "emotional_progression": 0,
            "relationship_continuity": 0,
            "narrative_coherence": 0,
            "genre_tone_consistency": 0,
        })
        assert ev.total_score == 0

    def test_all_max(self, db_session):
        run, scenes, *_ = _seed_run(db_session)
        ev = create_scene_evaluation(db_session, run.id, {
            "scene_id": scenes[0].id,
            "reviewer_label": "Max",
            "voice_consistency": 25,
            "terminology_consistency": 20,
            "emotional_progression": 15,
            "relationship_continuity": 15,
            "narrative_coherence": 15,
            "genre_tone_consistency": 10,
        })
        assert ev.total_score == 100
