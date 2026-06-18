import math
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.benchmark.metrics import aggregate_scores
from app.benchmark.service import get_metrics_summary
from app.models import (
    BenchmarkAutomaticScore,
    BenchmarkDataset,
    BenchmarkHardFailure,
    BenchmarkItem,
    BenchmarkItemManualEvaluation,
    BenchmarkOutput,
    BenchmarkRun,
    BenchmarkScene,
    BenchmarkSceneManualEvaluation,
    BenchmarkSceneMemory,
)


# ---------------------------------------------------------------------------
# Reviewer-label normalization
# ---------------------------------------------------------------------------

_INTERNAL_WS_RE = re.compile(r"\s+")


def normalize_label(label: str) -> str:
    normalized = _INTERNAL_WS_RE.sub(" ", label.strip())
    if not normalized:
        raise ValueError("Reviewer label must not be empty after normalization")
    if len(normalized) > 100:
        raise ValueError("Reviewer label must not exceed 100 characters")
    return normalized


# ---------------------------------------------------------------------------
# Total-score calculations
# ---------------------------------------------------------------------------

_ITEM_CRITERIA_MAX = {
    "meaning_preservation": 25,
    "omission_addition_control": 15,
    "natural_english": 15,
    "character_voice": 15,
    "glossary_consistency": 10,
    "genre_tone_fit": 10,
    "scene_consistency": 5,
    "grammar_punctuation": 5,
}


def calculate_item_total(**kwargs: int) -> int:
    total = 0
    for key, mx in _ITEM_CRITERIA_MAX.items():
        val = kwargs.get(key, 0)
        if not isinstance(val, int) or val < 0 or val > mx:
            raise ValueError(f"{key} must be an integer between 0 and {mx}")
        total += val
    return total


_SCENE_CRITERIA = {
    "voice_consistency": 25,
    "terminology_consistency": 20,
    "emotional_progression": 15,
    "relationship_continuity": 15,
    "narrative_coherence": 15,
    "genre_tone_consistency": 10,
}


def calculate_scene_total(**kwargs: int) -> int:
    total = 0
    for key, mx in _SCENE_CRITERIA.items():
        val = kwargs.get(key, 0)
        if not isinstance(val, int) or val < 0 or val > mx:
            raise ValueError(f"{key} must be an integer between 0 and {mx}")
        total += val
    return total


# ---------------------------------------------------------------------------
# Relationship helpers
# ---------------------------------------------------------------------------


def _get_output_or_404(db: Session, output_id: int) -> BenchmarkOutput:
    out = db.query(BenchmarkOutput).filter(BenchmarkOutput.id == output_id).first()
    if not out:
        raise LookupError(f"Output {output_id} not found")
    return out


def _get_run_or_404(db: Session, run_id: int) -> BenchmarkRun:
    run = db.query(BenchmarkRun).filter(BenchmarkRun.id == run_id).first()
    if not run:
        raise LookupError(f"Run {run_id} not found")
    return run


def _get_scene_or_404(db: Session, scene_id: int) -> BenchmarkScene:
    scene = db.query(BenchmarkScene).filter(BenchmarkScene.id == scene_id).first()
    if not scene:
        raise LookupError(f"Scene {scene_id} not found")
    return scene


def _get_evaluation_or_404(
    db: Session, eval_id: int, model_class: type
) -> Any:
    ev = db.query(model_class).filter(model_class.id == eval_id).first()
    if not ev:
        raise LookupError(f"{model_class.__name__} {eval_id} not found")
    return ev


# ---------------------------------------------------------------------------
# Item evaluations
# ---------------------------------------------------------------------------


def create_item_evaluation(
    db: Session, run_id: int, data: dict
) -> BenchmarkItemManualEvaluation:
    output_id = data["benchmark_output_id"]
    output = _get_output_or_404(db, output_id)
    if output.run_id != run_id:
        raise ValueError("Output does not belong to the specified run")

    if output.status != "completed":
        raise ValueError(
            "Numeric scoring is only allowed for completed outputs"
        )

    label = normalize_label(data["reviewer_label"])

    existing = (
        db.query(BenchmarkItemManualEvaluation)
        .filter(
            BenchmarkItemManualEvaluation.benchmark_output_id == output_id,
            BenchmarkItemManualEvaluation.reviewer_label == label,
        )
        .first()
    )
    if existing:
        raise IntegrityError(None, None, None)

    total = calculate_item_total(
        meaning_preservation=data["meaning_preservation"],
        omission_addition_control=data["omission_addition_control"],
        natural_english=data["natural_english"],
        character_voice=data["character_voice"],
        glossary_consistency=data["glossary_consistency"],
        genre_tone_fit=data["genre_tone_fit"],
        scene_consistency=data["scene_consistency"],
        grammar_punctuation=data["grammar_punctuation"],
    )

    now = datetime.now(timezone.utc)
    evaluation = BenchmarkItemManualEvaluation(
        benchmark_output_id=output_id,
        reviewer_label=label,
        meaning_preservation=data["meaning_preservation"],
        omission_addition_control=data["omission_addition_control"],
        natural_english=data["natural_english"],
        character_voice=data["character_voice"],
        glossary_consistency=data["glossary_consistency"],
        genre_tone_fit=data["genre_tone_fit"],
        scene_consistency=data["scene_consistency"],
        grammar_punctuation=data["grammar_punctuation"],
        total_score=total,
        reviewer_notes=data.get("reviewer_notes"),
        created_at=now,
        updated_at=now,
    )
    db.add(evaluation)
    db.flush()
    return evaluation


def update_item_evaluation(
    db: Session, eval_id: int, data: dict
) -> BenchmarkItemManualEvaluation:
    ev = _get_evaluation_or_404(db, eval_id, BenchmarkItemManualEvaluation)

    total = calculate_item_total(
        meaning_preservation=data["meaning_preservation"],
        omission_addition_control=data["omission_addition_control"],
        natural_english=data["natural_english"],
        character_voice=data["character_voice"],
        glossary_consistency=data["glossary_consistency"],
        genre_tone_fit=data["genre_tone_fit"],
        scene_consistency=data["scene_consistency"],
        grammar_punctuation=data["grammar_punctuation"],
    )

    ev.meaning_preservation = data["meaning_preservation"]
    ev.omission_addition_control = data["omission_addition_control"]
    ev.natural_english = data["natural_english"]
    ev.character_voice = data["character_voice"]
    ev.glossary_consistency = data["glossary_consistency"]
    ev.genre_tone_fit = data["genre_tone_fit"]
    ev.scene_consistency = data["scene_consistency"]
    ev.grammar_punctuation = data["grammar_punctuation"]
    ev.total_score = total
    ev.reviewer_notes = data.get("reviewer_notes")
    ev.updated_at = datetime.now(timezone.utc)
    db.flush()
    return ev


def get_item_evaluation(db: Session, eval_id: int) -> BenchmarkItemManualEvaluation:
    return _get_evaluation_or_404(db, eval_id, BenchmarkItemManualEvaluation)


def list_item_evaluations(
    db: Session, run_id: int, benchmark_output_id: int | None = None
) -> list[BenchmarkItemManualEvaluation]:
    query = (
        db.query(BenchmarkItemManualEvaluation)
        .join(BenchmarkOutput)
        .filter(BenchmarkOutput.run_id == run_id)
    )
    if benchmark_output_id is not None:
        query = query.filter(
            BenchmarkItemManualEvaluation.benchmark_output_id == benchmark_output_id
        )
    return query.order_by(BenchmarkItemManualEvaluation.id).all()


# ---------------------------------------------------------------------------
# Scene evaluations
# ---------------------------------------------------------------------------


def create_scene_evaluation(
    db: Session, run_id: int, data: dict
) -> BenchmarkSceneManualEvaluation:
    run = _get_run_or_404(db, run_id)
    scene_id = data["scene_id"]
    scene = _get_scene_or_404(db, scene_id)

    if scene.dataset_id != run.dataset_id:
        raise ValueError("Scene does not belong to the same dataset as the run")

    label = normalize_label(data["reviewer_label"])

    existing = (
        db.query(BenchmarkSceneManualEvaluation)
        .filter(
            BenchmarkSceneManualEvaluation.run_id == run_id,
            BenchmarkSceneManualEvaluation.scene_id == scene_id,
            BenchmarkSceneManualEvaluation.reviewer_label == label,
        )
        .first()
    )
    if existing:
        raise IntegrityError(None, None, None)

    total = calculate_scene_total(
        voice_consistency=data["voice_consistency"],
        terminology_consistency=data["terminology_consistency"],
        emotional_progression=data["emotional_progression"],
        relationship_continuity=data["relationship_continuity"],
        narrative_coherence=data["narrative_coherence"],
        genre_tone_consistency=data["genre_tone_consistency"],
    )

    now = datetime.now(timezone.utc)
    evaluation = BenchmarkSceneManualEvaluation(
        run_id=run_id,
        scene_id=scene_id,
        reviewer_label=label,
        voice_consistency=data["voice_consistency"],
        terminology_consistency=data["terminology_consistency"],
        emotional_progression=data["emotional_progression"],
        relationship_continuity=data["relationship_continuity"],
        narrative_coherence=data["narrative_coherence"],
        genre_tone_consistency=data["genre_tone_consistency"],
        total_score=total,
        reviewer_notes=data.get("reviewer_notes"),
        created_at=now,
        updated_at=now,
    )
    db.add(evaluation)
    db.flush()
    return evaluation


def update_scene_evaluation(
    db: Session, eval_id: int, data: dict
) -> BenchmarkSceneManualEvaluation:
    ev = _get_evaluation_or_404(db, eval_id, BenchmarkSceneManualEvaluation)

    total = calculate_scene_total(
        voice_consistency=data["voice_consistency"],
        terminology_consistency=data["terminology_consistency"],
        emotional_progression=data["emotional_progression"],
        relationship_continuity=data["relationship_continuity"],
        narrative_coherence=data["narrative_coherence"],
        genre_tone_consistency=data["genre_tone_consistency"],
    )

    ev.voice_consistency = data["voice_consistency"]
    ev.terminology_consistency = data["terminology_consistency"]
    ev.emotional_progression = data["emotional_progression"]
    ev.relationship_continuity = data["relationship_continuity"]
    ev.narrative_coherence = data["narrative_coherence"]
    ev.genre_tone_consistency = data["genre_tone_consistency"]
    ev.total_score = total
    ev.reviewer_notes = data.get("reviewer_notes")
    ev.updated_at = datetime.now(timezone.utc)
    db.flush()
    return ev


def get_scene_evaluation(db: Session, eval_id: int) -> BenchmarkSceneManualEvaluation:
    return _get_evaluation_or_404(db, eval_id, BenchmarkSceneManualEvaluation)


def list_scene_evaluations(
    db: Session, run_id: int
) -> list[BenchmarkSceneManualEvaluation]:
    return (
        db.query(BenchmarkSceneManualEvaluation)
        .filter(BenchmarkSceneManualEvaluation.run_id == run_id)
        .order_by(BenchmarkSceneManualEvaluation.id)
        .all()
    )


# ---------------------------------------------------------------------------
# Hard failures
# ---------------------------------------------------------------------------

_HARD_FAILURE_FLAGS = [
    "invented_plot_information",
    "missing_critical_meaning",
    "wrong_speaker",
    "broken_placeholder",
    "major_glossary_violation",
    "contradiction_with_previous_scene",
    "unjustified_untranslated_japanese",
]


def create_hard_failure(
    db: Session, run_id: int, data: dict
) -> BenchmarkHardFailure:
    output_id = data["benchmark_output_id"]
    output = _get_output_or_404(db, output_id)
    if output.run_id != run_id:
        raise ValueError("Output does not belong to the specified run")

    label = normalize_label(data["reviewer_label"])

    existing = (
        db.query(BenchmarkHardFailure)
        .filter(
            BenchmarkHardFailure.benchmark_output_id == output_id,
            BenchmarkHardFailure.reviewer_label == label,
        )
        .first()
    )
    if existing:
        raise IntegrityError(None, None, None)

    now = datetime.now(timezone.utc)
    rec = BenchmarkHardFailure(
        benchmark_output_id=output_id,
        reviewer_label=label,
        invented_plot_information=data.get("invented_plot_information", False),
        missing_critical_meaning=data.get("missing_critical_meaning", False),
        wrong_speaker=data.get("wrong_speaker", False),
        broken_placeholder=data.get("broken_placeholder", False),
        major_glossary_violation=data.get("major_glossary_violation", False),
        contradiction_with_previous_scene=data.get(
            "contradiction_with_previous_scene", False
        ),
        unjustified_untranslated_japanese=data.get(
            "unjustified_untranslated_japanese", False
        ),
        explanation=data.get("explanation"),
        created_at=now,
        updated_at=now,
    )
    db.add(rec)
    db.flush()
    return rec


def update_hard_failure(
    db: Session, failure_id: int, data: dict
) -> BenchmarkHardFailure:
    rec = _get_evaluation_or_404(db, failure_id, BenchmarkHardFailure)

    rec.invented_plot_information = data.get("invented_plot_information", False)
    rec.missing_critical_meaning = data.get("missing_critical_meaning", False)
    rec.wrong_speaker = data.get("wrong_speaker", False)
    rec.broken_placeholder = data.get("broken_placeholder", False)
    rec.major_glossary_violation = data.get("major_glossary_violation", False)
    rec.contradiction_with_previous_scene = data.get(
        "contradiction_with_previous_scene", False
    )
    rec.unjustified_untranslated_japanese = data.get(
        "unjustified_untranslated_japanese", False
    )
    rec.explanation = data.get("explanation")
    rec.updated_at = datetime.now(timezone.utc)
    db.flush()
    return rec


def get_hard_failure(db: Session, failure_id: int) -> BenchmarkHardFailure:
    return _get_evaluation_or_404(db, failure_id, BenchmarkHardFailure)


def list_hard_failures(
    db: Session, run_id: int, benchmark_output_id: int | None = None
) -> list[BenchmarkHardFailure]:
    query = (
        db.query(BenchmarkHardFailure)
        .join(BenchmarkOutput)
        .filter(BenchmarkOutput.run_id == run_id)
    )
    if benchmark_output_id is not None:
        query = query.filter(
            BenchmarkHardFailure.benchmark_output_id == benchmark_output_id
        )
    return query.order_by(BenchmarkHardFailure.id).all()


# ---------------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------------


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _std(values: list[float]) -> float | None:
    if not values or len(values) < 2:
        return None
    m = _mean(values)
    if m is None:
        return None
    variance = sum((v - m) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def _criterion_mean_std(evals: list[Any], field: str) -> dict:
    vals = [getattr(e, field) for e in evals if getattr(e, field) is not None]
    return {"mean": _mean(vals), "std": _std(vals)}


# ---------------------------------------------------------------------------
# Human metrics
# ---------------------------------------------------------------------------


def build_human_metrics(db: Session, run_id: int) -> dict:
    run = _get_run_or_404(db, run_id)

    outputs: list[BenchmarkOutput] = (
        db.query(BenchmarkOutput)
        .filter(BenchmarkOutput.run_id == run_id)
        .order_by(BenchmarkOutput.id)
        .all()
    )
    total_outputs = len(outputs)

    scenes: list[BenchmarkScene] = (
        db.query(BenchmarkScene)
        .filter(BenchmarkScene.dataset_id == run.dataset_id)
        .order_by(BenchmarkScene.scene_number)
        .all()
    )
    total_scenes = len(scenes)

    # -- Item scores ---------------------------------------------------------
    all_item_evals: list[BenchmarkItemManualEvaluation] = (
        db.query(BenchmarkItemManualEvaluation)
        .join(BenchmarkOutput)
        .filter(BenchmarkOutput.run_id == run_id)
        .all()
    )

    item_eval_count = len(all_item_evals)

    output_ids_with_review = set(
        e.benchmark_output_id for e in all_item_evals
    )
    unique_reviewed_outputs = len(output_ids_with_review)

    item_coverage_pct = (
        round(unique_reviewed_outputs / total_outputs * 100, 1)
        if total_outputs
        else 0.0
    )

    avg_reviewers_per_output = (
        round(item_eval_count / unique_reviewed_outputs, 2)
        if unique_reviewed_outputs
        else 0.0
    )

    # Per-output mean total (avoid reviewer weighting bias)
    output_totals: dict[int, list[int]] = {}
    output_criteria: dict[int, dict[str, list[int]]] = {}
    for ev in all_item_evals:
        oid = ev.benchmark_output_id
        output_totals.setdefault(oid, []).append(ev.total_score)
        for key in _ITEM_CRITERIA_MAX:
            output_criteria.setdefault(oid, {}).setdefault(key, []).append(
                getattr(ev, key)
            )

    output_mean_totals = [
        sum(vals) / len(vals) for vals in output_totals.values()
    ]
    avg_item_total = _mean(output_mean_totals)

    avg_per_criterion: dict[str, dict | None] = {}
    for key in _ITEM_CRITERIA_MAX:
        means = []
        for oid, crit in output_criteria.items():
            vals = crit.get(key, [])
            if vals:
                means.append(sum(vals) / len(vals))
        if means:
            avg_per_criterion[key] = {
                "mean": _mean(means),
                "std": _std(means),
            }
        else:
            avg_per_criterion[key] = None

    # By scene / genre / content-type / memory
    output_to_scene: dict[int, int] = {o.id: o.scene_id for o in outputs}
    scene_to_meta: dict[int, BenchmarkScene] = {s.id: s for s in scenes}

    scene_output_totals: dict[int, list[float]] = {}
    genre_output_totals: dict[str, list[float]] = {}
    content_output_totals: dict[str, list[float]] = {}
    mem_dep_means: list[float] = []
    no_mem_means: list[float] = []

    for oid, totals in output_totals.items():
        mean_t = sum(totals) / len(totals)
        sc_id = output_to_scene.get(oid)
        meta = scene_to_meta.get(sc_id) if sc_id else None
        if meta:
            scene_key = f"Scene {meta.scene_number}"
            scene_output_totals.setdefault(scene_key, []).append(mean_t)
            genre_output_totals.setdefault(meta.genre, []).append(mean_t)
            content_output_totals.setdefault(
                meta.content_type, []
            ).append(mean_t)

        # Memory dependency
        item = (
            db.query(BenchmarkItem)
            .join(BenchmarkOutput)
            .filter(BenchmarkOutput.id == oid)
            .first()
        )
        if item and item.requires_previous_memory:
            mem_dep_means.append(mean_t)
        else:
            no_mem_means.append(mean_t)

    def _summarize_output_means(means_list: list[float]) -> dict | None:
        if not means_list:
            return None
        return {
            "count": len(means_list),
            "average_total": _mean(means_list),
            "std_total": _std(means_list),
        }

    by_scene = {
        k: _summarize_output_means(v)
        for k, v in scene_output_totals.items()
    }
    by_genre = {
        k: _summarize_output_means(v)
        for k, v in genre_output_totals.items()
    }
    by_content = {
        k: _summarize_output_means(v)
        for k, v in content_output_totals.items()
    }

    # Per-reviewer breakdown (direct, no output-mean weighting)
    reviewer_totals: dict[str, list[int]] = {}
    for ev in all_item_evals:
        reviewer_totals.setdefault(ev.reviewer_label, []).append(
            ev.total_score
        )

    by_reviewer = {
        label: {
            "count": len(vals),
            "average_total": _mean(vals),
        }
        for label, vals in reviewer_totals.items()
    }

    item_scores = {
        "item_evaluation_count": item_eval_count,
        "unique_reviewed_output_count": unique_reviewed_outputs,
        "average_reviewers_per_reviewed_output": avg_reviewers_per_output,
        "average_total": avg_item_total,
        "average_per_criterion": avg_per_criterion,
        "by_scene": by_scene,
        "by_genre": by_genre,
        "by_content_type": by_content,
        "requires_previous_memory": _summarize_output_means(mem_dep_means),
        "no_previous_memory": _summarize_output_means(no_mem_means),
        "by_reviewer": by_reviewer,
    }

    # -- Scene scores --------------------------------------------------------
    all_scene_evals: list[BenchmarkSceneManualEvaluation] = (
        db.query(BenchmarkSceneManualEvaluation)
        .filter(BenchmarkSceneManualEvaluation.run_id == run_id)
        .all()
    )

    scene_eval_count = len(all_scene_evals)
    unique_reviewed_scenes = len(
        set(e.scene_id for e in all_scene_evals)
    )
    scene_coverage_pct = (
        round(unique_reviewed_scenes / total_scenes * 100, 1)
        if total_scenes
        else 0.0
    )

    # Avoid overweighting: mean per scene, then average across scenes
    scene_total_means: dict[int, list[int]] = {}
    scene_criteria: dict[int, dict[str, list[int]]] = {}
    for ev in all_scene_evals:
        sid = ev.scene_id
        scene_total_means.setdefault(sid, []).append(ev.total_score)
        for key in _SCENE_CRITERIA:
            scene_criteria.setdefault(sid, {}).setdefault(key, []).append(
                getattr(ev, key)
            )

    scene_mean_totals = [
        sum(vals) / len(vals) for vals in scene_total_means.values()
    ]
    avg_scene_total = _mean(scene_mean_totals)

    avg_scene_criterion: dict[str, dict | None] = {}
    for key in _SCENE_CRITERIA:
        means = []
        for sid, crit in scene_criteria.items():
            vals = crit.get(key, [])
            if vals:
                means.append(sum(vals) / len(vals))
        if means:
            avg_scene_criterion[key] = {
                "mean": _mean(means),
                "std": _std(means),
            }
        else:
            avg_scene_criterion[key] = None

    scene_reviewer_agg: dict[str, list[int]] = {}
    for ev in all_scene_evals:
        scene_reviewer_agg.setdefault(ev.reviewer_label, []).append(
            ev.total_score
        )

    scene_scores = {
        "scene_evaluation_count": scene_eval_count,
        "unique_reviewed_scenes": unique_reviewed_scenes,
        "scene_review_coverage_percentage": scene_coverage_pct,
        "average_total": avg_scene_total,
        "average_per_criterion": avg_scene_criterion,
        "by_reviewer": {
            label: {
                "count": len(vals),
                "average_total": _mean(vals),
            }
            for label, vals in scene_reviewer_agg.items()
        },
    }

    # -- Hard failures -------------------------------------------------------
    all_hf: list[BenchmarkHardFailure] = (
        db.query(BenchmarkHardFailure)
        .join(BenchmarkOutput)
        .filter(BenchmarkOutput.run_id == run_id)
        .all()
    )

    hf_count = len(all_hf)
    hf_output_ids = set(f.benchmark_output_id for f in all_hf)
    unique_hf_reviewed = len(hf_output_ids)

    outputs_with_any_flag = len(
        {
            f.benchmark_output_id
            for f in all_hf
            if any(getattr(f, flag) for flag in _HARD_FAILURE_FLAGS)
        }
    )

    hf_rate = (
        round(outputs_with_any_flag / unique_hf_reviewed, 4)
        if unique_hf_reviewed
        else None
    )

    count_per_flag: dict[str, int] = {}
    for flag in _HARD_FAILURE_FLAGS:
        count_per_flag[flag] = len(
            {
                f.benchmark_output_id
                for f in all_hf
                if getattr(f, flag)
            }
        )

    # Run-level breakdowns count unique flagged outputs once (deduplicated)
    flagged_output_ids = {
        f.benchmark_output_id
        for f in all_hf
        if any(getattr(f, flag) for flag in _HARD_FAILURE_FLAGS)
    }

    hf_by_scene: dict[str, int] = {}
    hf_by_genre: dict[str, int] = {}
    hf_by_content: dict[str, int] = {}
    hf_mem_dep = 0
    hf_no_mem = 0
    hf_by_reviewer: dict[str, int] = {}

    for oid in flagged_output_ids:
        sc_id = output_to_scene.get(oid)
        meta = scene_to_meta.get(sc_id) if sc_id else None
        if meta:
            hf_by_scene[f"Scene {meta.scene_number}"] = (
                hf_by_scene.get(f"Scene {meta.scene_number}", 0) + 1
            )
            hf_by_genre[meta.genre] = hf_by_genre.get(meta.genre, 0) + 1
            hf_by_content[meta.content_type] = (
                hf_by_content.get(meta.content_type, 0) + 1
            )
        item = (
            db.query(BenchmarkItem)
            .join(BenchmarkOutput)
            .filter(BenchmarkOutput.id == oid)
            .first()
        )
        if item and item.requires_previous_memory:
            hf_mem_dep += 1
        else:
            hf_no_mem += 1

    for f in all_hf:
        hf_by_reviewer[f.reviewer_label] = (
            hf_by_reviewer.get(f.reviewer_label, 0) + 1
        )

    hf_coverage_pct = (
        round(unique_hf_reviewed / total_outputs * 100, 1)
        if total_outputs
        else 0.0
    )

    hard_failures = {
        "hard_failure_review_count": hf_count,
        "unique_outputs_reviewed_for_hard_failures": unique_hf_reviewed,
        "outputs_with_any_hard_failure": outputs_with_any_flag,
        "hard_failure_rate_among_reviewed_outputs": hf_rate,
        "count_per_flag": count_per_flag,
        "by_scene": hf_by_scene,
        "by_genre": hf_by_genre,
        "by_content_type": hf_by_content,
        "requires_previous_memory": hf_mem_dep,
        "no_previous_memory": hf_no_mem,
        "by_reviewer": hf_by_reviewer,
    }

    return {
        "run_id": run_id,
        "mode": run.mode,
        "model": run.llm_model,
        "provider": run.llm_provider,
        "prompt_version": run.prompt_version,
        "item_review_coverage_percentage": item_coverage_pct,
        "scene_review_coverage_percentage": scene_coverage_pct,
        "hard_failure_review_coverage_percentage": hf_coverage_pct,
        "item_scores": item_scores,
        "scene_scores": scene_scores,
        "hard_failures": hard_failures,
    }


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


def build_comparison(
    db: Session,
    plain_run_id: int | None = None,
    context_run_id: int | None = None,
    context_memory_run_id: int | None = None,
    dataset_id: int | None = None,
    selection: str | None = None,
) -> dict:
    warnings_list: list[str] = []
    runs_data: list[dict] = []

    if plain_run_id is not None:
        # Explicit mode — require all three IDs
        if None in (plain_run_id, context_run_id, context_memory_run_id):
            raise ValueError(
                "All three run IDs (plain, context, context_memory) "
                "are required in explicit comparison mode"
            )

        run_ids = {
            "plain": plain_run_id,
            "context": context_run_id,
            "context_memory": context_memory_run_id,
        }
        run_ids_present = [r for r in run_ids.values() if r is not None]
        if len(set(run_ids_present)) != len(run_ids_present):
            raise ValueError("Duplicate run IDs provided")

        datasets = set()
        runs = []
        for expected_mode, rid in run_ids.items():
            run = db.query(BenchmarkRun).filter(BenchmarkRun.id == rid).first()
            if not run:
                raise LookupError(f"Run {rid} not found")
            if run.mode != expected_mode:
                raise ValueError(
                    f"Run {rid} has mode '{run.mode}', expected '{expected_mode}'"
                )
            if run.status not in ("completed", "completed_with_errors"):
                raise ValueError(
                    f"Run {rid} has status '{run.status}', "
                    "expected 'completed' or 'completed_with_errors'"
                )
            datasets.add(run.dataset_id)
            runs.append(run)

        if len(datasets) != 1:
            raise ValueError("All runs must belong to the same dataset")

        ds = db.query(BenchmarkDataset).filter(BenchmarkDataset.id == runs[0].dataset_id).first()
        for r in runs[1:]:
            other_ds = db.query(BenchmarkDataset).filter(BenchmarkDataset.id == r.dataset_id).first()
            if other_ds.version != ds.version:
                raise ValueError("All runs must belong to the same dataset version")

        for run in runs:
            entry = _build_comparison_entry(db, run, ds)
            runs_data.append(entry)
            _collect_comparison_warnings(warnings_list, runs_data)

    elif dataset_id is not None and selection == "latest_completed":
        ds = db.query(BenchmarkDataset).filter(BenchmarkDataset.id == dataset_id).first()
        if not ds:
            raise LookupError(f"Dataset {dataset_id} not found")

        for mode in ("plain", "context", "context_memory"):
            run = (
                db.query(BenchmarkRun)
                .filter(
                    BenchmarkRun.dataset_id == dataset_id,
                    BenchmarkRun.mode == mode,
                    BenchmarkRun.status.in_(["completed", "completed_with_errors"]),
                )
                .order_by(BenchmarkRun.id.desc())
                .first()
            )
            if run:
                entry = _build_comparison_entry(db, run, ds)
                runs_data.append(entry)
            else:
                warnings_list.append(
                    f"No completed run found for mode '{mode}'"
                )

        _collect_comparison_warnings(warnings_list, runs_data)

    else:
        raise ValueError(
            "Provide either explicit run_id params or dataset_id with selection='latest_completed'"
        )

    return {
        "dataset_id": ds.id if ds else 0,
        "dataset_name": ds.name if ds else "",
        "dataset_version": ds.version if ds else "",
        "runs": runs_data,
        "warnings": warnings_list,
        "note": "Automatic and human metrics are reported separately. "
        "Do not combine them into a single score or claim mode superiority "
        "from automatic metrics alone.",
    }


def _build_comparison_entry(
    db: Session, run: BenchmarkRun, ds: BenchmarkDataset
) -> dict:
    auto_metrics = get_metrics_summary(db, run)
    human = build_human_metrics(db, run.id)

    item_cov = human["item_review_coverage_percentage"]
    scene_cov = human["scene_review_coverage_percentage"]
    hf_cov = human["hard_failure_review_coverage_percentage"]

    cov_note = None
    if item_cov == 0:
        cov_note = "No reviewer data for this mode."
    elif item_cov < 100:
        cov_note = (
            f"Item review coverage is {item_cov}% "
            f"(scene: {scene_cov}%, hard-failure: {hf_cov}%). "
            "Human-score comparisons may not be representative."
        )

    return {
        "run_id": run.id,
        "mode": run.mode,
        "status": run.status,
        "model": run.llm_model,
        "provider": run.llm_provider,
        "prompt_version": run.prompt_version,
        "memory_gap": run.memory_gap,
        "automatic_metrics": auto_metrics,
        "human_metrics": human if item_cov > 0 else None,
        "item_review_coverage_percentage": item_cov,
        "scene_review_coverage_percentage": scene_cov,
        "hard_failure_review_coverage_percentage": hf_cov,
        "coverage_note": cov_note,
    }


def _collect_comparison_warnings(
    warnings_list: list[str], runs_data: list[dict]
) -> None:
    if len(runs_data) < 2:
        return

    providers = set(r["provider"] for r in runs_data)
    if len(providers) > 1:
        warnings_list.append(
            f"LLM provider differs across runs: {', '.join(sorted(providers))}"
        )

    models = set(r["model"] for r in runs_data)
    if len(models) > 1:
        warnings_list.append(
            f"Model differs across runs: {', '.join(sorted(models))}"
        )

    pvs = set(r["prompt_version"] for r in runs_data)
    if len(pvs) > 1:
        warnings_list.append(
            f"Prompt version differs across runs: {', '.join(sorted(pvs))}"
        )

    covs = [r["item_review_coverage_percentage"] for r in runs_data]
    if len(covs) >= 2:
        max_cov = max(covs)
        min_cov = min(covs)
        if max_cov - min_cov > 20:
            warnings_list.append(
                f"Item review coverage differs substantially across modes "
                f"(range: {min_cov}%–{max_cov}%)"
            )
