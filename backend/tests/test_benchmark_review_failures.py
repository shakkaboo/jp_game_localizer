import pytest
from sqlalchemy.exc import IntegrityError

from app.benchmark.review_service import (
    create_hard_failure,
    create_item_evaluation,
    get_hard_failure,
    list_hard_failures,
    update_hard_failure,
)
from app.models import BenchmarkDataset, BenchmarkItem, BenchmarkOutput, BenchmarkRun, BenchmarkScene


def _seed_run(db):
    ds = BenchmarkDataset(
        name="Test Dataset", version="1.0",
        source_or_author="tester", license_or_usage_status="test",
        reference_translation_method="manual", review_status="draft",
    )
    db.add(ds)
    db.flush()

    scene = BenchmarkScene(
        dataset_id=ds.id, scene_number=1, title="Test", genre="RPG",
        content_type="dialogue", context_json="{}",
    )
    db.add(scene)
    db.flush()

    item = BenchmarkItem(
        scene_id=scene.id, sequence_number=1,
        source_text_ja="source", reference_en="reference",
        speaker="Tester",
    )
    db.add(item)
    db.flush()

    run = BenchmarkRun(
        dataset_id=ds.id, mode="plain",
        llm_provider="test", llm_model="test-model",
        prompt_version="1.0", status="completed",
        total_scenes=1, completed_scenes=1,
    )
    db.add(run)
    db.flush()

    out = BenchmarkOutput(
        run_id=run.id, benchmark_item_id=item.id,
        scene_id=scene.id, sequence_number=1,
        status="completed", output_localized_text_en="translation",
    )
    db.add(out)
    db.flush()
    return run, out


class TestCreateHardFailure:
    def test_one_flag(self, db_session):
        run, out = _seed_run(db_session)
        rec = create_hard_failure(db_session, run.id, {
            "benchmark_output_id": out.id,
            "reviewer_label": "R1",
            "invented_plot_information": True,
        })
        db_session.commit()
        assert rec.id is not None
        assert rec.invented_plot_information is True
        assert rec.missing_critical_meaning is False

    def test_multiple_flags(self, db_session):
        run, out = _seed_run(db_session)
        rec = create_hard_failure(db_session, run.id, {
            "benchmark_output_id": out.id,
            "reviewer_label": "R2",
            "invented_plot_information": True,
            "missing_critical_meaning": True,
            "wrong_speaker": True,
            "broken_placeholder": False,
            "major_glossary_violation": True,
            "contradiction_with_previous_scene": False,
            "unjustified_untranslated_japanese": True,
        })
        db_session.commit()
        assert rec.invented_plot_information is True
        assert rec.missing_critical_meaning is True
        assert rec.wrong_speaker is True
        assert rec.broken_placeholder is False
        assert rec.major_glossary_violation is True
        assert rec.contradiction_with_previous_scene is False
        assert rec.unjustified_untranslated_japanese is True

    def test_all_flags_false(self, db_session):
        run, out = _seed_run(db_session)
        rec = create_hard_failure(db_session, run.id, {
            "benchmark_output_id": out.id,
            "reviewer_label": "R3",
        })
        db_session.commit()
        assert all(
            not getattr(rec, flag) for flag in [
                "invented_plot_information", "missing_critical_meaning",
                "wrong_speaker", "broken_placeholder",
                "major_glossary_violation", "contradiction_with_previous_scene",
                "unjustified_untranslated_japanese",
            ]
        )

    def test_completed_output_allowed(self, db_session):
        run, out = _seed_run(db_session)
        rec = create_hard_failure(db_session, run.id, {
            "benchmark_output_id": out.id,
            "reviewer_label": "R4",
            "wrong_speaker": True,
        })
        db_session.commit()
        assert rec.id is not None

    def test_failed_output_allowed(self, db_session):
        run, out = _seed_run(db_session)
        out.status = "failed"
        db_session.flush()
        rec = create_hard_failure(db_session, run.id, {
            "benchmark_output_id": out.id,
            "reviewer_label": "R5",
            "missing_critical_meaning": True,
        })
        db_session.commit()
        assert rec.id is not None

    def test_independent_from_numeric_score(self, db_session):
        """Hard failure and numeric score can coexist from same reviewer on same output."""
        run, out = _seed_run(db_session)
        create_item_evaluation(db_session, run.id, {
            "benchmark_output_id": out.id,
            "reviewer_label": "R6",
            "meaning_preservation": 20,
            "omission_addition_control": 12,
            "natural_english": 13,
            "character_voice": 10,
            "glossary_consistency": 8,
            "genre_tone_fit": 7,
            "scene_consistency": 4,
            "grammar_punctuation": 4,
        })
        rec = create_hard_failure(db_session, run.id, {
            "benchmark_output_id": out.id,
            "reviewer_label": "R6",
            "major_glossary_violation": True,
        })
        db_session.commit()
        assert rec.id is not None
        assert rec.major_glossary_violation is True

    def test_duplicate_reviewer_output_raises(self, db_session):
        run, out = _seed_run(db_session)
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": out.id,
            "reviewer_label": "Dup",
            "wrong_speaker": True,
        })
        db_session.commit()
        with pytest.raises(IntegrityError):
            create_hard_failure(db_session, run.id, {
                "benchmark_output_id": out.id,
                "reviewer_label": "Dup",
                "wrong_speaker": True,
            })
            db_session.commit()

    def test_explanation_stored(self, db_session):
        run, out = _seed_run(db_session)
        rec = create_hard_failure(db_session, run.id, {
            "benchmark_output_id": out.id,
            "reviewer_label": "R7",
            "invented_plot_information": True,
            "explanation": "The translation added details not in the source.",
        })
        db_session.commit()
        assert rec.explanation == "The translation added details not in the source."


class TestUpdateHardFailure:
    def test_update_flags(self, db_session):
        run, out = _seed_run(db_session)
        rec = create_hard_failure(db_session, run.id, {
            "benchmark_output_id": out.id,
            "reviewer_label": "U1",
            "invented_plot_information": True,
            "explanation": "Original",
        })
        db_session.commit()
        orig_updated = rec.updated_at

        rec2 = update_hard_failure(db_session, rec.id, {
            "invented_plot_information": False,
            "missing_critical_meaning": True,
            "explanation": "Updated",
        })
        db_session.commit()
        assert rec2.invented_plot_information is False
        assert rec2.missing_critical_meaning is True
        assert rec2.explanation == "Updated"
        assert rec2.updated_at > orig_updated

    def test_update_not_found(self, db_session):
        with pytest.raises(LookupError):
            update_hard_failure(db_session, 99999, {"wrong_speaker": True})


class TestGetHardFailure:
    def test_get_by_id(self, db_session):
        run, out = _seed_run(db_session)
        rec = create_hard_failure(db_session, run.id, {
            "benchmark_output_id": out.id,
            "reviewer_label": "Get",
            "broken_placeholder": True,
        })
        db_session.commit()
        fetched = get_hard_failure(db_session, rec.id)
        assert fetched.id == rec.id
        assert fetched.broken_placeholder is True

    def test_get_not_found(self, db_session):
        with pytest.raises(LookupError):
            get_hard_failure(db_session, 99999)


class TestListHardFailures:
    def test_list_for_run(self, db_session):
        run, out = _seed_run(db_session)
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": out.id, "reviewer_label": "R1",
            "wrong_speaker": True,
        })
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": out.id, "reviewer_label": "R2",
            "wrong_speaker": True,
        })
        db_session.commit()
        recs = list_hard_failures(db_session, run.id)
        assert len(recs) == 2

    def test_filter_by_output(self, db_session):
        run, out = _seed_run(db_session)

        # Create a second output
        from app.models import BenchmarkItem
        item2 = BenchmarkItem(
            scene_id=out.benchmark_item.scene_id,
            sequence_number=2,
            source_text_ja="src2", reference_en="ref2",
        )
        db_session.add(item2)
        db_session.flush()
        out2 = BenchmarkOutput(
            run_id=run.id, benchmark_item_id=item2.id,
            scene_id=out.scene_id, sequence_number=2,
            status="completed", output_localized_text_en="t2",
        )
        db_session.add(out2)
        db_session.flush()

        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": out.id, "reviewer_label": "R1",
            "wrong_speaker": True,
        })
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": out2.id, "reviewer_label": "R2",
            "wrong_speaker": True,
        })
        db_session.commit()

        recs = list_hard_failures(db_session, run.id, benchmark_output_id=out.id)
        assert len(recs) == 1
