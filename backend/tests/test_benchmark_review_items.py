import pytest
from sqlalchemy.exc import IntegrityError

from app.benchmark.review_service import (
    calculate_item_total,
    create_item_evaluation,
    get_item_evaluation,
    list_item_evaluations,
    normalize_label,
    update_item_evaluation,
)
from app.models import BenchmarkItem, BenchmarkItemManualEvaluation, BenchmarkOutput, BenchmarkRun
from app.schemas import BenchmarkItemEvaluationUpdate


def _seed_run(db, name="Test Dataset", version="1.0"):
    from app.models import BenchmarkDataset, BenchmarkScene

    ds = BenchmarkDataset(
        name=name,
        version=version,
        source_or_author="tester",
        license_or_usage_status="test",
        reference_translation_method="manual",
        review_status="draft",
    )
    db.add(ds)
    db.flush()

    scene = BenchmarkScene(
        dataset_id=ds.id,
        scene_number=1,
        title="Test Scene",
        genre="RPG",
        content_type="dialogue",
        context_json="{}",
    )
    db.add(scene)
    db.flush()

    for i in range(1, 4):
        item = BenchmarkItem(
            scene_id=scene.id,
            sequence_number=i,
            source_text_ja=f"source_{i}",
            reference_en=f"reference_{i}",
            speaker="Tester",
        )
        db.add(item)
    db.flush()

    run = BenchmarkRun(
        dataset_id=ds.id,
        mode="plain",
        llm_provider="test",
        llm_model="test-model",
        prompt_version="1.0",
        status="completed",
        total_scenes=1,
        completed_scenes=1,
    )
    db.add(run)
    db.flush()

    items = db.query(BenchmarkItem).all()
    outputs = []
    for item in items:
        out = BenchmarkOutput(
            run_id=run.id,
            benchmark_item_id=item.id,
            scene_id=scene.id,
            sequence_number=item.sequence_number,
            status="completed",
            output_localized_text_en=f"translation_{item.sequence_number}",
        )
        db.add(out)
        outputs.append(out)
    db.flush()
    return run, outputs, scene, ds, items


class TestNormalize:
    def test_normalize_basic(self):
        assert normalize_label("  Alice  ") == "Alice"
        assert normalize_label("Alice  Smith") == "Alice Smith"

    def test_normalize_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            normalize_label("  ")

    def test_normalize_too_long_raises(self):
        with pytest.raises(ValueError, match="100"):
            normalize_label("a" * 101)


class TestCalculateItemTotal:
    def test_max(self):
        assert calculate_item_total(
            meaning_preservation=25, omission_addition_control=15,
            natural_english=15, character_voice=15,
            glossary_consistency=10, genre_tone_fit=10,
            scene_consistency=5, grammar_punctuation=5,
        ) == 100

    def test_min(self):
        assert calculate_item_total(
            meaning_preservation=0, omission_addition_control=0,
            natural_english=0, character_voice=0,
            glossary_consistency=0, genre_tone_fit=0,
            scene_consistency=0, grammar_punctuation=0,
        ) == 0

    def test_out_of_range(self):
        with pytest.raises(ValueError):
            calculate_item_total(
                meaning_preservation=26, omission_addition_control=0,
                natural_english=0, character_voice=0,
                glossary_consistency=0, genre_tone_fit=0,
                scene_consistency=0, grammar_punctuation=0,
            )


class TestCreateItemEvaluation:
    def test_valid(self, db_session):
        run, outputs, *_ = _seed_run(db_session)
        ev = create_item_evaluation(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "ReviewerA",
            "meaning_preservation": 20,
            "omission_addition_control": 12,
            "natural_english": 13,
            "character_voice": 10,
            "glossary_consistency": 8,
            "genre_tone_fit": 7,
            "scene_consistency": 4,
            "grammar_punctuation": 4,
            "reviewer_notes": "Good",
        })
        db_session.commit()
        assert ev.total_score == 78
        assert ev.reviewer_label == "ReviewerA"

    def test_total_server_calculated(self, db_session):
        run, outputs, *_ = _seed_run(db_session)
        ev = create_item_evaluation(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "B",
            "meaning_preservation": 20,
            "omission_addition_control": 12,
            "natural_english": 13,
            "character_voice": 10,
            "glossary_consistency": 8,
            "genre_tone_fit": 7,
            "scene_consistency": 4,
            "grammar_punctuation": 4,
        })
        assert ev.total_score == 78

    def test_duplicate_reviewer_output_raises(self, db_session):
        run, outputs, *_ = _seed_run(db_session)
        data = {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "Dup",
            "meaning_preservation": 20,
            "omission_addition_control": 12,
            "natural_english": 13,
            "character_voice": 10,
            "glossary_consistency": 8,
            "genre_tone_fit": 7,
            "scene_consistency": 4,
            "grammar_punctuation": 4,
        }
        create_item_evaluation(db_session, run.id, data)
        db_session.commit()
        with pytest.raises(IntegrityError):
            create_item_evaluation(db_session, run.id, data)
            db_session.commit()

    def test_failed_output_rejected(self, db_session):
        run, outputs, *_ = _seed_run(db_session)
        outputs[0].status = "failed"
        db_session.flush()
        with pytest.raises(ValueError, match="completed"):
            create_item_evaluation(db_session, run.id, {
                "benchmark_output_id": outputs[0].id,
                "reviewer_label": "R",
                "meaning_preservation": 20,
                "omission_addition_control": 12,
                "natural_english": 13,
                "character_voice": 10,
                "glossary_consistency": 8,
                "genre_tone_fit": 7,
                "scene_consistency": 4,
                "grammar_punctuation": 4,
            })

    def test_cross_run_output_rejected(self, db_session):
        run1, *_ = _seed_run(db_session)
        db_session.commit()
        run2, outputs2, *_ = _seed_run(db_session, name="Test Dataset 2", version="2.0")
        with pytest.raises(ValueError, match="does not belong"):
            create_item_evaluation(db_session, run1.id, {
                "benchmark_output_id": outputs2[0].id,
                "reviewer_label": "R",
                "meaning_preservation": 20,
                "omission_addition_control": 12,
                "natural_english": 13,
                "character_voice": 10,
                "glossary_consistency": 8,
                "genre_tone_fit": 7,
                "scene_consistency": 4,
                "grammar_punctuation": 4,
            })

    def test_missing_output_not_found(self, db_session):
        run, *_ = _seed_run(db_session)
        with pytest.raises(LookupError, match="not found"):
            create_item_evaluation(db_session, run.id, {
                "benchmark_output_id": 99999,
                "reviewer_label": "R",
                "meaning_preservation": 20,
                "omission_addition_control": 12,
                "natural_english": 13,
                "character_voice": 10,
                "glossary_consistency": 8,
                "genre_tone_fit": 7,
                "scene_consistency": 4,
                "grammar_punctuation": 4,
            })


class TestUpdateItemEvaluation:
    def test_update_changes_total_and_updated_at(self, db_session):
        run, outputs, *_ = _seed_run(db_session)
        ev = create_item_evaluation(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "Updater",
            "meaning_preservation": 10,
            "omission_addition_control": 5,
            "natural_english": 5,
            "character_voice": 5,
            "glossary_consistency": 3,
            "genre_tone_fit": 3,
            "scene_consistency": 1,
            "grammar_punctuation": 1,
        })
        db_session.commit()
        orig_created = ev.created_at
        orig_updated = ev.updated_at

        ev2 = update_item_evaluation(db_session, ev.id, {
            "meaning_preservation": 25,
            "omission_addition_control": 15,
            "natural_english": 15,
            "character_voice": 15,
            "glossary_consistency": 10,
            "genre_tone_fit": 10,
            "scene_consistency": 5,
            "grammar_punctuation": 5,
        })
        db_session.commit()
        assert ev2.total_score == 100
        assert ev2.created_at == orig_created
        assert ev2.updated_at > orig_updated

    def test_identity_fields_not_in_update_schema(self):
        with pytest.raises(Exception):
            BenchmarkItemEvaluationUpdate(
                meaning_preservation=20,
                omission_addition_control=12,
                natural_english=13,
                character_voice=10,
                glossary_consistency=8,
                genre_tone_fit=7,
                scene_consistency=4,
                grammar_punctuation=4,
                benchmark_output_id=999,
            )

    def test_update_not_found(self, db_session):
        with pytest.raises(LookupError):
            update_item_evaluation(db_session, 99999, {
                "meaning_preservation": 20,
                "omission_addition_control": 12,
                "natural_english": 13,
                "character_voice": 10,
                "glossary_consistency": 8,
                "genre_tone_fit": 7,
                "scene_consistency": 4,
                "grammar_punctuation": 4,
            })


class TestListItemEvaluations:
    def test_list_for_run(self, db_session):
        run, outputs, *_ = _seed_run(db_session)
        for i, out in enumerate(outputs):
            create_item_evaluation(db_session, run.id, {
                "benchmark_output_id": out.id,
                "reviewer_label": f"R{i}",
                "meaning_preservation": 20,
                "omission_addition_control": 12,
                "natural_english": 13,
                "character_voice": 10,
                "glossary_consistency": 8,
                "genre_tone_fit": 7,
                "scene_consistency": 4,
                "grammar_punctuation": 4,
            })
        db_session.commit()
        evals = list_item_evaluations(db_session, run.id)
        assert len(evals) == 3

    def test_filter_by_output(self, db_session):
        run, outputs, *_ = _seed_run(db_session)
        for i, out in enumerate(outputs):
            create_item_evaluation(db_session, run.id, {
                "benchmark_output_id": out.id,
                "reviewer_label": f"R{i}",
                "meaning_preservation": 20,
                "omission_addition_control": 12,
                "natural_english": 13,
                "character_voice": 10,
                "glossary_consistency": 8,
                "genre_tone_fit": 7,
                "scene_consistency": 4,
                "grammar_punctuation": 4,
            })
        db_session.commit()
        evals = list_item_evaluations(db_session, run.id, benchmark_output_id=outputs[0].id)
        assert len(evals) == 1


class TestGetItemEvaluation:
    def test_get_by_id(self, db_session):
        run, outputs, *_ = _seed_run(db_session)
        ev = create_item_evaluation(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "Getter",
            "meaning_preservation": 20,
            "omission_addition_control": 12,
            "natural_english": 13,
            "character_voice": 10,
            "glossary_consistency": 8,
            "genre_tone_fit": 7,
            "scene_consistency": 4,
            "grammar_punctuation": 4,
        })
        db_session.commit()
        fetched = get_item_evaluation(db_session, ev.id)
        assert fetched.id == ev.id
        assert fetched.total_score == 78

    def test_get_not_found(self, db_session):
        with pytest.raises(LookupError):
            get_item_evaluation(db_session, 99999)


class TestBoundaries:
    def test_all_min(self, db_session):
        run, outputs, *_ = _seed_run(db_session)
        ev = create_item_evaluation(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "Min",
            "meaning_preservation": 0,
            "omission_addition_control": 0,
            "natural_english": 0,
            "character_voice": 0,
            "glossary_consistency": 0,
            "genre_tone_fit": 0,
            "scene_consistency": 0,
            "grammar_punctuation": 0,
        })
        assert ev.total_score == 0

    def test_all_max(self, db_session):
        run, outputs, *_ = _seed_run(db_session)
        ev = create_item_evaluation(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "Max",
            "meaning_preservation": 25,
            "omission_addition_control": 15,
            "natural_english": 15,
            "character_voice": 15,
            "glossary_consistency": 10,
            "genre_tone_fit": 10,
            "scene_consistency": 5,
            "grammar_punctuation": 5,
        })
        assert ev.total_score == 100
