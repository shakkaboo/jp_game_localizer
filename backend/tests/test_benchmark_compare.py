import pytest
from unittest.mock import patch

from app.benchmark.review_service import (
    build_comparison,
    create_item_evaluation,
)
from app.benchmark.service import execute_benchmark_run
from app.models import (
    BenchmarkAutomaticScore,
    BenchmarkDataset,
    BenchmarkItem,
    BenchmarkOutput,
    BenchmarkRun,
    BenchmarkScene,
)


def _seed_dataset_with_three_runs(db, name="Compare Dataset", version="1.0"):
    """Seed one dataset and three completed runs (plain, context, context_memory)."""
    ds = BenchmarkDataset(
        name=name, version=version,
        source_or_author="tester", license_or_usage_status="test",
        reference_translation_method="manual", review_status="draft",
    )
    db.add(ds)
    db.flush()

    scene = BenchmarkScene(
        dataset_id=ds.id, scene_number=1, title="Test",
        genre="RPG", content_type="dialogue", context_json="{}",
    )
    db.add(scene)
    db.flush()

    for seq in range(1, 4):
        item = BenchmarkItem(
            scene_id=scene.id, sequence_number=seq,
            source_text_ja=f"source_{seq}", reference_en=f"reference_{seq}",
            speaker="Tester",
        )
        db.add(item)
    db.flush()

    items = db.query(BenchmarkItem).all()
    runs = []
    for mode in ("plain", "context", "context_memory"):
        run = BenchmarkRun(
            dataset_id=ds.id, mode=mode,
            llm_provider="test", llm_model="test-model",
            prompt_version="1.0", status="completed",
            total_scenes=1, completed_scenes=1,
        )
        db.add(run)
        db.flush()

        outputs = []
        for item in items:
            out = BenchmarkOutput(
                run_id=run.id, benchmark_item_id=item.id,
                scene_id=scene.id, sequence_number=item.sequence_number,
                status="completed",
                output_localized_text_en=f"t_{mode}_{item.sequence_number}",
            )
            db.add(out)
            outputs.append(out)
        db.flush()
        for out in outputs:
            db.add(BenchmarkAutomaticScore(
                benchmark_output_id=out.id,
                run_id=run.id,
                chrf_score=50.0,
                bleu_score=25.0,
                glossary_compliant=True,
                placeholders_preserved=True,
                missing_output=False,
                untranslated_japanese=False,
                line_id_mismatch=False,
                speaker_mismatch=False,
            ))
        db.flush()
        runs.append(run)

    return ds, runs


class TestExplicitComparison:
    def test_explicit_three_runs(self, db_session):
        ds, runs = _seed_dataset_with_three_runs(db_session)
        result = build_comparison(
            db_session,
            plain_run_id=runs[0].id,
            context_run_id=runs[1].id,
            context_memory_run_id=runs[2].id,
        )
        assert result["dataset_id"] == ds.id
        assert len(result["runs"]) == 3
        modes = {r["mode"] for r in result["runs"]}
        assert modes == {"plain", "context", "context_memory"}

    def test_wrong_mode_rejected(self, db_session):
        ds, runs = _seed_dataset_with_three_runs(db_session)
        with pytest.raises(ValueError, match="mode"):
            build_comparison(
                db_session,
                plain_run_id=runs[1].id,  # runs[1] is context, not plain
                context_run_id=runs[2].id,
                context_memory_run_id=runs[0].id,
            )

    def test_mixed_datasets_rejected(self, db_session):
        ds1, runs1 = _seed_dataset_with_three_runs(db_session)
        db_session.commit()
        ds2, runs2 = _seed_dataset_with_three_runs(db_session, name="Compare Dataset 2", version="2.0")
        with pytest.raises(ValueError, match="same dataset"):
            build_comparison(
                db_session,
                plain_run_id=runs1[0].id,
                context_run_id=runs1[1].id,
                context_memory_run_id=runs2[2].id,
            )

    def test_duplicate_run_ids_rejected(self, db_session):
        ds, runs = _seed_dataset_with_three_runs(db_session)
        with pytest.raises(ValueError, match="Duplicate"):
            build_comparison(
                db_session,
                plain_run_id=runs[0].id,
                context_run_id=runs[0].id,
                context_memory_run_id=runs[2].id,
            )

    def test_automatic_and_human_separate(self, db_session):
        ds, runs = _seed_dataset_with_three_runs(db_session)
        # Add a review to the plain run
        outputs = db_session.query(BenchmarkOutput).filter(
            BenchmarkOutput.run_id == runs[0].id
        ).all()
        create_item_evaluation(db_session, runs[0].id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "R1",
            "meaning_preservation": 20, "omission_addition_control": 12,
            "natural_english": 13, "character_voice": 10,
            "glossary_consistency": 8, "genre_tone_fit": 7,
            "scene_consistency": 4, "grammar_punctuation": 4,
        })
        db_session.commit()

        result = build_comparison(
            db_session,
            plain_run_id=runs[0].id,
            context_run_id=runs[1].id,
            context_memory_run_id=runs[2].id,
        )
        for r in result["runs"]:
            assert "automatic_metrics" in r
            if r["mode"] == "plain":
                assert r["human_metrics"] is not None
            else:
                assert r["human_metrics"] is None

    def test_model_provider_warnings(self, db_session):
        ds, runs = _seed_dataset_with_three_runs(db_session)
        runs[1].llm_provider = "different-provider"
        runs[1].llm_model = "different-model"
        db_session.flush()

        result = build_comparison(
            db_session,
            plain_run_id=runs[0].id,
            context_run_id=runs[1].id,
            context_memory_run_id=runs[2].id,
        )
        warnings = " ".join(result["warnings"]).lower()
        assert "provider" in warnings
        assert "model" in warnings


class TestLatestCompletedSelection:
    def test_latest_completed(self, db_session):
        ds, _ = _seed_dataset_with_three_runs(db_session)
        # Create a second batch of runs with a newer id
        scene = db_session.query(BenchmarkScene).first()
        items = db_session.query(BenchmarkItem).all()

        for mode in ("plain", "context", "context_memory"):
            run = BenchmarkRun(
                dataset_id=ds.id, mode=mode,
                llm_provider="test", llm_model="test-model",
                prompt_version="1.0", status="completed",
                total_scenes=1, completed_scenes=1,
            )
            db_session.add(run)
            db_session.flush()
            new_outputs = []
            for item in items:
                out = BenchmarkOutput(
                    run_id=run.id, benchmark_item_id=item.id,
                    scene_id=scene.id, sequence_number=item.sequence_number,
                    status="completed",
                    output_localized_text_en=f"t_{item.sequence_number}",
                )
                db_session.add(out)
                new_outputs.append(out)
            db_session.flush()
            for out in new_outputs:
                db_session.add(BenchmarkAutomaticScore(
                    benchmark_output_id=out.id,
                    run_id=run.id,
                    chrf_score=50.0,
                    bleu_score=25.0,
                    glossary_compliant=True,
                    placeholders_preserved=True,
                    missing_output=False,
                    untranslated_japanese=False,
                    line_id_mismatch=False,
                    speaker_mismatch=False,
                ))
            db_session.flush()

        result = build_comparison(
            db_session,
            dataset_id=ds.id,
            selection="latest_completed",
        )
        assert len(result["runs"]) == 3

    def test_no_completed_run_for_mode(self, db_session):
        ds, runs = _seed_dataset_with_three_runs(db_session)
        # Delete one run
        db_session.query(BenchmarkOutput).filter(
            BenchmarkOutput.run_id == runs[1].id
        ).delete()
        db_session.delete(runs[1])
        db_session.flush()

        result = build_comparison(
            db_session,
            dataset_id=ds.id,
            selection="latest_completed",
        )
        assert len(result["runs"]) == 2

    def test_invalid_selection_params(self, db_session):
        with pytest.raises(ValueError, match="Provide"):
            build_comparison(db_session)

    def test_invalid_selection_method(self, db_session):
        with pytest.raises(ValueError, match="Provide"):
            build_comparison(db_session, dataset_id=1, selection="oldest")

    def test_pending_run_rejected(self, db_session):
        ds, _ = _seed_dataset_with_three_runs(db_session)
        # Set all runs to pending
        for run in db_session.query(BenchmarkRun).all():
            run.status = "pending"
        db_session.flush()
        with pytest.raises(ValueError, match="pending"):
            build_comparison(
                db_session,
                plain_run_id=1, context_run_id=2, context_memory_run_id=3,
            )

    def test_partial_explicit_rejected(self, db_session):
        ds, runs = _seed_dataset_with_three_runs(db_session)
        with pytest.raises(ValueError, match="All three run IDs"):
            build_comparison(
                db_session,
                plain_run_id=runs[0].id,
                context_run_id=runs[1].id,
                # context_memory_run_id omitted
            )


class TestCoverageNotes:
    def test_incomplete_coverage_note(self, db_session):
        ds, runs = _seed_dataset_with_three_runs(db_session)
        outputs = db_session.query(BenchmarkOutput).filter(
            BenchmarkOutput.run_id == runs[0].id
        ).all()
        create_item_evaluation(db_session, runs[0].id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "R1",
            "meaning_preservation": 20, "omission_addition_control": 12,
            "natural_english": 13, "character_voice": 10,
            "glossary_consistency": 8, "genre_tone_fit": 7,
            "scene_consistency": 4, "grammar_punctuation": 4,
        })
        db_session.commit()

        result = build_comparison(
            db_session,
            plain_run_id=runs[0].id,
            context_run_id=runs[1].id,
            context_memory_run_id=runs[2].id,
        )
        plain_entry = [r for r in result["runs"] if r["mode"] == "plain"][0]
        context_entry = [r for r in result["runs"] if r["mode"] == "context"][0]
        assert "coverage is" in plain_entry["coverage_note"]
        assert "No reviewer data" in context_entry["coverage_note"]

    def test_zero_coverage_note(self, db_session):
        """When item review coverage is 0, coverage_note must indicate no data."""
        ds, runs = _seed_dataset_with_three_runs(db_session)
        result = build_comparison(
            db_session,
            plain_run_id=runs[0].id,
            context_run_id=runs[1].id,
            context_memory_run_id=runs[2].id,
        )
        for entry in result["runs"]:
            assert entry["coverage_note"] == "No reviewer data for this mode."
