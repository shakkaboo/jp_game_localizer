import pytest

from app.benchmark.review_service import (
    build_human_metrics,
    create_hard_failure,
    create_item_evaluation,
    create_scene_evaluation,
)
from app.models import (
    BenchmarkDataset,
    BenchmarkItem,
    BenchmarkOutput,
    BenchmarkRun,
    BenchmarkScene,
)


def _seed_complex_run(db):
    """Seed a run with 2 scenes, 3 items each, various reviews."""
    ds = BenchmarkDataset(
        name="Report Dataset", version="1.0",
        source_or_author="tester", license_or_usage_status="test",
        reference_translation_method="manual", review_status="draft",
    )
    db.add(ds)
    db.flush()

    scenes = []
    for sn in range(1, 3):
        scene = BenchmarkScene(
            dataset_id=ds.id, scene_number=sn,
            title=f"Scene {sn}",
            genre="Action" if sn == 2 else "RPG",
            content_type="combat_dialogue" if sn == 2 else "formal_dialogue",
            context_json="{}",
        )
        db.add(scene)
        scenes.append(scene)
    db.flush()

    items = []
    for scene in scenes:
        for seq in range(1, 4):
            item = BenchmarkItem(
                scene_id=scene.id, sequence_number=seq,
                source_text_ja=f"src_{scene.scene_number}_{seq}",
                reference_en=f"ref_{scene.scene_number}_{seq}",
                speaker="Tester",
                requires_previous_memory=(seq == 1 and scene.scene_number > 1),
            )
            db.add(item)
            items.append(item)
    db.flush()

    run = BenchmarkRun(
        dataset_id=ds.id, mode="plain",
        llm_provider="test", llm_model="test-model",
        prompt_version="1.0", status="completed",
        total_scenes=2, completed_scenes=2,
    )
    db.add(run)
    db.flush()

    outputs = []
    for item in items:
        out = BenchmarkOutput(
            run_id=run.id, benchmark_item_id=item.id,
            scene_id=item.scene_id, sequence_number=item.sequence_number,
            status="completed",
            output_localized_text_en=f"t_{item.sequence_number}",
        )
        db.add(out)
        outputs.append(out)
    db.flush()

    return run, outputs, scenes, ds, items


class TestHumanMetricsBasic:
    def test_no_reviews_returns_empty(self, db_session):
        run, *_ = _seed_complex_run(db_session)
        metrics = build_human_metrics(db_session, run.id)
        assert metrics["item_review_coverage_percentage"] == 0.0
        assert metrics["item_scores"]["item_evaluation_count"] == 0
        assert metrics["item_scores"]["unique_reviewed_output_count"] == 0

    def test_unreviewed_excluded_from_averages(self, db_session):
        run, outputs, *_ = _seed_complex_run(db_session)
        # Review only output[0]
        create_item_evaluation(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "R1",
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
        metrics = build_human_metrics(db_session, run.id)
        # 6 total outputs, 1 reviewed
        assert metrics["item_review_coverage_percentage"] == pytest.approx(16.7, 0.1)
        assert metrics["item_scores"]["unique_reviewed_output_count"] == 1
        assert metrics["item_scores"]["item_evaluation_count"] == 1

    def test_multiple_reviewers_not_overweighted(self, db_session):
        run, outputs, *_ = _seed_complex_run(db_session)
        # Two reviewers on output[0], one reviewer on output[1]
        for label in ["R1", "R2"]:
            create_item_evaluation(db_session, run.id, {
                "benchmark_output_id": outputs[0].id,
                "reviewer_label": label,
                "meaning_preservation": 20,
                "omission_addition_control": 12,
                "natural_english": 13,
                "character_voice": 10,
                "glossary_consistency": 8,
                "genre_tone_fit": 7,
                "scene_consistency": 4,
                "grammar_punctuation": 4,
            })
        create_item_evaluation(db_session, run.id, {
            "benchmark_output_id": outputs[1].id,
            "reviewer_label": "R3",
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
        metrics = build_human_metrics(db_session, run.id)
        # output[0] mean total = 78, output[1] total = 33
        # average_total should be (78 + 33) / 2 = 55.5
        assert metrics["item_scores"]["average_total"] == pytest.approx(55.5, 0.1)
        assert metrics["item_scores"]["average_reviewers_per_reviewed_output"] == pytest.approx(1.5, 0.1)

    def test_criterion_averages(self, db_session):
        run, outputs, *_ = _seed_complex_run(db_session)
        create_item_evaluation(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "R1",
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
        metrics = build_human_metrics(db_session, run.id)
        assert metrics["item_scores"]["average_per_criterion"]["meaning_preservation"]["mean"] == 20.0

    def test_reviewer_breakdown(self, db_session):
        run, outputs, *_ = _seed_complex_run(db_session)
        create_item_evaluation(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "Alice",
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
        metrics = build_human_metrics(db_session, run.id)
        assert "Alice" in metrics["item_scores"]["by_reviewer"]


class TestSceneMetrics:
    def test_scene_coverage(self, db_session):
        run, outputs, scenes, *_ = _seed_complex_run(db_session)
        # Review one scene
        create_scene_evaluation(db_session, run.id, {
            "scene_id": scenes[0].id,
            "reviewer_label": "R1",
            "voice_consistency": 20,
            "terminology_consistency": 15,
            "emotional_progression": 12,
            "relationship_continuity": 10,
            "narrative_coherence": 12,
            "genre_tone_consistency": 8,
        })
        db_session.commit()
        metrics = build_human_metrics(db_session, run.id)
        assert metrics["scene_scores"]["scene_evaluation_count"] == 1
        assert metrics["scene_scores"]["unique_reviewed_scenes"] == 1
        assert metrics["scene_review_coverage_percentage"] == 50.0

    def test_scene_total_average(self, db_session):
        run, outputs, scenes, *_ = _seed_complex_run(db_session)
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
        metrics = build_human_metrics(db_session, run.id)
        assert metrics["scene_scores"]["average_total"] == pytest.approx(77.0, 0.1)


class TestHardFailureMetrics:
    def test_hard_failure_counts(self, db_session):
        run, outputs, *_ = _seed_complex_run(db_session)
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "R1",
            "invented_plot_information": True,
            "wrong_speaker": True,
        })
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": outputs[1].id,
            "reviewer_label": "R2",
            "missing_critical_meaning": True,
        })
        db_session.commit()
        metrics = build_human_metrics(db_session, run.id)
        assert metrics["hard_failures"]["hard_failure_review_count"] == 2
        assert metrics["hard_failures"]["outputs_with_any_hard_failure"] == 2
        assert metrics["hard_failures"]["count_per_flag"]["invented_plot_information"] == 1
        assert metrics["hard_failures"]["count_per_flag"]["missing_critical_meaning"] == 1
        assert metrics["hard_failures"]["count_per_flag"]["wrong_speaker"] == 1

    def test_hard_failure_coverage(self, db_session):
        run, outputs, *_ = _seed_complex_run(db_session)
        # Review only 2 out of 6 outputs
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "R1", "wrong_speaker": True,
        })
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": outputs[1].id,
            "reviewer_label": "R2", "wrong_speaker": True,
        })
        db_session.commit()
        metrics = build_human_metrics(db_session, run.id)
        assert metrics["hard_failure_review_coverage_percentage"] == pytest.approx(33.3, 0.1)

    def test_hard_failure_rate_among_reviewed(self, db_session):
        run, outputs, *_ = _seed_complex_run(db_session)
        # Create 3 hf reviews, 2 have flags, 1 has no flags
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "R1", "wrong_speaker": True,
        })
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": outputs[1].id,
            "reviewer_label": "R2", "missing_critical_meaning": True,
        })
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": outputs[2].id,
            "reviewer_label": "R3",
        })
        db_session.commit()
        metrics = build_human_metrics(db_session, run.id)
        # 2 unique flagged outputs / 3 unique reviewed outputs = 0.6667
        assert metrics["hard_failures"]["hard_failure_rate_among_reviewed_outputs"] == pytest.approx(0.6667, 0.01)

    def test_hard_failure_rate_dedup_two_reviewers_same_output(self, db_session):
        """Two reviewers flagging the same output count as one unique failed output."""
        run, outputs, *_ = _seed_complex_run(db_session)
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "R1", "wrong_speaker": True,
        })
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "R2", "missing_critical_meaning": True,
        })
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": outputs[1].id,
            "reviewer_label": "R3", "wrong_speaker": True,
        })
        db_session.commit()
        metrics = build_human_metrics(db_session, run.id)
        # 2 unique flagged / 2 unique reviewed = 1.0
        assert metrics["hard_failures"]["hard_failure_rate_among_reviewed_outputs"] == 1.0
        assert metrics["hard_failures"]["outputs_with_any_hard_failure"] == 2
        assert metrics["hard_failures"]["unique_outputs_reviewed_for_hard_failures"] == 2

    def test_hard_failure_breakdown_dedup(self, db_session):
        """Run-level breakdowns count each flagged output once, not per reviewer."""
        run, outputs, scenes, *_ = _seed_complex_run(db_session)
        # Both reviewers flag the same output[0] (scene 1, RPG, formal_dialogue)
        for lab in ("R1", "R2"):
            create_hard_failure(db_session, run.id, {
                "benchmark_output_id": outputs[0].id,
                "reviewer_label": lab,
                "wrong_speaker": True,
            })
        # R3 flags a different output[3] (scene 2, Action, combat_dialogue)
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": outputs[3].id,
            "reviewer_label": "R3",
            "invented_plot_information": True,
        })
        db_session.commit()
        metrics = build_human_metrics(db_session, run.id)
        hf = metrics["hard_failures"]
        # by_scene: 2 scenes with flagged outputs → each counted once
        assert hf["by_scene"]["Scene 1"] == 1  # output[0] once
        assert hf["by_scene"]["Scene 2"] == 1  # output[3] once
        # by_genre: each genre once
        assert hf["by_genre"]["RPG"] == 1
        assert hf["by_genre"]["Action"] == 1
        # by_content_type
        assert hf["by_content_type"]["formal_dialogue"] == 1
        assert hf["by_content_type"]["combat_dialogue"] == 1
        # requires_previous_memory: output[3] is scene 2 item 1
        assert hf["requires_previous_memory"] == 1
        assert hf["no_previous_memory"] == 1
        # by_reviewer can still count individual reviewer records
        assert hf["by_reviewer"]["R1"] == 1
        assert hf["by_reviewer"]["R2"] == 1
        assert hf["by_reviewer"]["R3"] == 1

    def test_hard_failure_rate_null_when_no_review(self, db_session):
        run, *_ = _seed_complex_run(db_session)
        db_session.commit()
        metrics = build_human_metrics(db_session, run.id)
        assert metrics["hard_failures"]["hard_failure_rate_among_reviewed_outputs"] is None

    def test_count_per_flag_dedup(self, db_session):
        """count_per_flag is unique outputs per flag, not reviewer rows."""
        run, outputs, *_ = _seed_complex_run(db_session)
        # R1 flags invented_plot on output[0]
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "R1",
            "invented_plot_information": True,
        })
        # R2 flags same flag on same output — should still count as 1
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "R2",
            "invented_plot_information": True,
        })
        # R3 flags different output
        create_hard_failure(db_session, run.id, {
            "benchmark_output_id": outputs[1].id,
            "reviewer_label": "R3",
            "wrong_speaker": True,
        })
        db_session.commit()
        metrics = build_human_metrics(db_session, run.id)
        cpf = metrics["hard_failures"]["count_per_flag"]
        assert cpf["invented_plot_information"] == 1  # unique outputs = 1
        assert cpf["wrong_speaker"] == 1


class TestMemoryDependencyBreakdown:
    def test_memory_dependent_separated(self, db_session):
        run, outputs, scenes, *_ = _seed_complex_run(db_session)
        # outputs[3] (scene 2, item 1) has requires_previous_memory=True
        create_item_evaluation(db_session, run.id, {
            "benchmark_output_id": outputs[3].id,
            "reviewer_label": "R1",
            "meaning_preservation": 20, "omission_addition_control": 12,
            "natural_english": 13, "character_voice": 10,
            "glossary_consistency": 8, "genre_tone_fit": 7,
            "scene_consistency": 4, "grammar_punctuation": 4,
        })
        # Non-memory-dependent output
        create_item_evaluation(db_session, run.id, {
            "benchmark_output_id": outputs[0].id,
            "reviewer_label": "R2",
            "meaning_preservation": 10, "omission_addition_control": 5,
            "natural_english": 5, "character_voice": 5,
            "glossary_consistency": 3, "genre_tone_fit": 3,
            "scene_consistency": 1, "grammar_punctuation": 1,
        })
        db_session.commit()
        metrics = build_human_metrics(db_session, run.id)
        mem = metrics["item_scores"]["requires_previous_memory"]
        no_mem = metrics["item_scores"]["no_previous_memory"]
        assert mem["count"] == 1
        assert no_mem["count"] == 1


class TestGenreContentBreakdown:
    def test_genre_breakdown(self, db_session):
        run, outputs, scenes, *_ = _seed_complex_run(db_session)
        for i, out in enumerate(outputs):
            create_item_evaluation(db_session, run.id, {
                "benchmark_output_id": out.id,
                "reviewer_label": f"R{i}",
                "meaning_preservation": 20, "omission_addition_control": 12,
                "natural_english": 13, "character_voice": 10,
                "glossary_consistency": 8, "genre_tone_fit": 7,
                "scene_consistency": 4, "grammar_punctuation": 4,
            })
        db_session.commit()
        metrics = build_human_metrics(db_session, run.id)
        # 3 outputs in RPG (scene 1), 3 in Action (scene 2)
        rpg = metrics["item_scores"]["by_genre"].get("RPG", {})
        action = metrics["item_scores"]["by_genre"].get("Action", {})
        assert rpg["count"] == 3
        assert action["count"] == 3


class TestNoRun:
    def test_nonexistent_run(self, db_session):
        with pytest.raises(LookupError):
            build_human_metrics(db_session, 99999)
