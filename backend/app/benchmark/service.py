import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.ai.llm_client import call_llm_json, get_llm_settings, get_normalized_provider
from app.ai.prompts import PROMPT_VERSION, build_chunk_localization_prompt
from app.benchmark.metrics import compute_all_metrics
from app.models import (
    BenchmarkAutomaticScore,
    BenchmarkDataset,
    BenchmarkItem,
    BenchmarkOutput,
    BenchmarkRun,
    BenchmarkScene,
    BenchmarkSceneMemory,
)

_CAT_LLM_FAILED = "llm_request_failed"
_CAT_INVALID_RESPONSE = "invalid_llm_response"
_CAT_MISSING_TRANSLATION = "missing_translation"


def _build_scene_context(scene: BenchmarkScene) -> dict:
    if scene.context_json:
        try:
            return json.loads(scene.context_json)
        except json.JSONDecodeError:
            return {}
    return {}


def _build_chunk_lines(items: list[BenchmarkItem]) -> list[dict[str, str]]:
    return [
        {
            "line_id": str(item.sequence_number),
            "character": item.speaker or "",
            "source_text_ja": item.source_text_ja,
        }
        for item in items
    ]


def _match_translations(
    items: list[BenchmarkItem],
    translations: list[dict],
) -> tuple[dict[int, dict], list[int], bool, int]:
    item_by_seq: dict[str, BenchmarkItem] = {
        str(it.sequence_number): it for it in items
    }
    matched: dict[int, dict] = {}
    used: set[str] = set()
    has_duplicate = False

    for t in translations:
        lid = str(t.get("line_id", ""))
        if lid in item_by_seq:
            if lid in used:
                has_duplicate = True
            used.add(lid)
            matched[item_by_seq[lid].id] = t

    unmatched_item_ids = [
        it.id for it in items if str(it.sequence_number) not in used
    ]
    extra_count = len(translations) - len(used)
    return matched, unmatched_item_ids, has_duplicate, extra_count


def _categorize_error(exc: Exception) -> str:
    msg = str(exc).lower()
    if "json" in msg or "empty" in msg or "retry also failed" in msg:
        return _CAT_INVALID_RESPONSE
    if "translation" in msg or "no translation" in msg:
        return _CAT_MISSING_TRANSLATION
    return _CAT_LLM_FAILED


def _create_output(
    db: Session,
    run_id: int,
    item: BenchmarkItem,
    translation: dict | None,
    has_line_id_mismatch: bool,
) -> BenchmarkOutput:
    output = BenchmarkOutput(
        run_id=run_id,
        benchmark_item_id=item.id,
        scene_id=item.scene_id,
        sequence_number=item.sequence_number,
        status="completed" if translation else "failed",
        error_message=None if translation else _CAT_MISSING_TRANSLATION,
    )
    if translation:
        output.output_localized_text_en = (translation.get("localized_text_en") or "").strip() or None
        output.output_literal_meaning = (translation.get("literal_meaning") or "").strip() or None
        output.output_localization_note = (translation.get("localization_note") or "").strip() or None
    db.add(output)
    db.flush()
    return output


def _create_automatic_score(
    db: Session,
    output: BenchmarkOutput,
    item: BenchmarkItem,
    has_line_id_mismatch: bool,
) -> BenchmarkAutomaticScore:
    metrics = compute_all_metrics(
        output_text=output.output_localized_text_en,
        reference_text=item.reference_en,
        source_text=item.source_text_ja,
        speaker=item.speaker,
        output_character=None,
        glossary_expectations_json=item.glossary_expectations,
        placeholder_expectations_json=item.placeholder_expectations,
    )

    metrics["line_id_mismatch"] = has_line_id_mismatch

    score = BenchmarkAutomaticScore(
        benchmark_output_id=output.id,
        run_id=output.run_id,
        chrf_score=metrics["chrf_score"],
        bleu_score=metrics["bleu_score"],
        glossary_compliant=metrics["glossary_compliant"],
        placeholders_preserved=metrics["placeholders_preserved"],
        missing_output=metrics["missing_output"],
        untranslated_japanese=metrics["untranslated_japanese"],
        line_id_mismatch=metrics["line_id_mismatch"],
        speaker_mismatch=metrics["speaker_mismatch"],
        details_json=metrics["details_json"],
    )
    db.add(score)
    db.flush()
    return score


def execute_benchmark_run(
    db: Session,
    dataset: BenchmarkDataset,
    mode: str,
) -> BenchmarkRun:
    settings = get_llm_settings()

    run = BenchmarkRun(
        dataset_id=dataset.id,
        mode=mode,
        llm_provider=get_normalized_provider(),
        llm_model=settings["model"],
        prompt_version=PROMPT_VERSION,
        status="running",
        created_at=datetime.now(timezone.utc),
        total_scenes=0,
        completed_scenes=0,
    )
    db.add(run)
    db.flush()

    scenes: list[BenchmarkScene] = (
        db.query(BenchmarkScene)
        .filter(BenchmarkScene.dataset_id == dataset.id)
        .order_by(BenchmarkScene.scene_number)
        .all()
    )
    run.total_scenes = len(scenes)
    db.flush()

    previous_memory: dict | None = None
    memory_gap = False

    for scene in scenes:
        items: list[BenchmarkItem] = (
            db.query(BenchmarkItem)
            .filter(BenchmarkItem.scene_id == scene.id)
            .order_by(BenchmarkItem.sequence_number)
            .all()
        )

        chunk_lines = _build_chunk_lines(items)
        context_data = _build_scene_context(scene)

        project_context = {
            "title": dataset.name,
            "genre": scene.genre,
            "target_tone": scene.tone or "",
        } if mode in ("context", "context_memory") else None

        characters = context_data.get("characters", None) if mode in ("context", "context_memory") else None
        relationships = context_data.get("relationships", None) if mode in ("context", "context_memory") else None
        glossary = context_data.get("glossary", None) if mode in ("context", "context_memory") else None
        style_rules = context_data.get("style_rules", None) if mode in ("context", "context_memory") else None
        raw_context = context_data.get("raw_context", "") if mode in ("context", "context_memory") else ""

        show_memory = (mode == "context_memory")

        try:
            messages = build_chunk_localization_prompt(
                chunk_lines=chunk_lines,
                project_context=project_context,
                characters=characters,
                relationships=relationships,
                glossary=glossary,
                style_rules=style_rules,
                raw_context=raw_context,
                previous_memory=previous_memory if show_memory else None,
                mode=mode,
            )
        except Exception as e:
            _mark_scene_failed(db, run, scene, items, _categorize_error(e))
            if show_memory:
                memory_gap = True
            continue

        try:
            result = call_llm_json(messages)
        except Exception as e:
            _mark_scene_failed(db, run, scene, items, _categorize_error(e))
            if show_memory:
                memory_gap = True
            continue

        translations_raw = result.get("translations", [])
        if not translations_raw:
            _mark_scene_failed(db, run, scene, items, _CAT_MISSING_TRANSLATION)
            if show_memory:
                memory_gap = True
            continue

        matched, unmatched_ids, has_duplicate, extra_count = _match_translations(
            items, translations_raw,
        )

        has_mismatch = bool(unmatched_ids) or has_duplicate or extra_count > 0

        for item in items:
            translation = matched.get(item.id)
            output = _create_output(db, run.id, item, translation, has_mismatch)
            _create_automatic_score(db, output, item, has_mismatch)

        if show_memory:
            chunk_memory = result.get("chunk_memory")
            if chunk_memory and isinstance(chunk_memory, dict):
                memory_record = BenchmarkSceneMemory(
                    run_id=run.id,
                    scene_id=scene.id,
                    memory_json=json.dumps(chunk_memory, ensure_ascii=False),
                )
                db.add(memory_record)
                db.flush()
                previous_memory = chunk_memory
            else:
                memory_gap = True

        run.completed_scenes += 1
        db.flush()

    run.memory_gap = memory_gap
    run.status = _determine_status(run)
    run.completed_at = datetime.now(timezone.utc)
    db.commit()
    return run


def _mark_scene_failed(
    db: Session,
    run: BenchmarkRun,
    scene: BenchmarkScene,
    items: list[BenchmarkItem],
    error_category: str,
) -> None:
    for item in items:
        output = BenchmarkOutput(
            run_id=run.id,
            benchmark_item_id=item.id,
            scene_id=scene.id,
            sequence_number=item.sequence_number,
            status="failed",
            error_message=error_category,
        )
        db.add(output)
        db.flush()

        score = BenchmarkAutomaticScore(
            benchmark_output_id=output.id,
            run_id=run.id,
            missing_output=True,
        )
        db.add(score)
        db.flush()


def _determine_status(run: BenchmarkRun) -> str:
    if run.completed_scenes == 0:
        return "failed"
    if run.completed_scenes >= run.total_scenes:
        return "completed"
    return "completed_with_errors"


def get_metrics_summary(db: Session, run: BenchmarkRun) -> dict[str, Any]:
    dataset = db.query(BenchmarkDataset).filter(BenchmarkDataset.id == run.dataset_id).first()

    outputs = (
        db.query(BenchmarkOutput)
        .filter(BenchmarkOutput.run_id == run.id)
        .order_by(BenchmarkOutput.sequence_number)
        .all()
    )

    scores_rows = (
        db.query(BenchmarkAutomaticScore)
        .join(BenchmarkOutput)
        .filter(BenchmarkOutput.run_id == run.id)
        .all()
    )

    score_map: dict[int, dict] = {}
    for s in scores_rows:
        score_map[s.benchmark_output_id] = {
            "chrf_score": s.chrf_score,
            "bleu_score": s.bleu_score,
            "glossary_compliant": s.glossary_compliant,
            "placeholders_preserved": s.placeholders_preserved,
            "missing_output": s.missing_output,
            "untranslated_japanese": s.untranslated_japanese,
            "line_id_mismatch": s.line_id_mismatch,
            "speaker_mismatch": s.speaker_mismatch,
        }

    all_scores: list[dict] = []
    for out in outputs:
        sc = score_map.get(out.id, {"missing_output": True})
        all_scores.append(sc)

    from app.benchmark.metrics import aggregate_scores

    base = aggregate_scores(all_scores)

    items_with_items = (
        db.query(BenchmarkOutput, BenchmarkItem)
        .join(BenchmarkItem, BenchmarkOutput.benchmark_item_id == BenchmarkItem.id)
        .filter(BenchmarkOutput.run_id == run.id)
        .all()
    )

    per_genre: dict[str, list[dict]] = {}
    per_content: dict[str, list[dict]] = {}
    per_scene: dict[str, list[dict]] = {}
    mem_dep_scores: list[dict] = []
    no_mem_scores: list[dict] = []

    for out, item in items_with_items:
        sc = score_map.get(out.id, {"missing_output": True})
        scene = (
            db.query(BenchmarkScene)
            .filter(BenchmarkScene.id == out.scene_id)
            .first()
        )
        if scene:
            per_genre.setdefault(scene.genre, []).append(sc)
            per_content.setdefault(scene.content_type, []).append(sc)
            key = f"Scene {scene.scene_number}"
            per_scene.setdefault(key, []).append(sc)

        if item.requires_previous_memory:
            mem_dep_scores.append(sc)
        else:
            no_mem_scores.append(sc)

    def _summarize(scores_list: list[dict]) -> dict:
        chrf = [s["chrf_score"] for s in scores_list if s.get("chrf_score") is not None]
        return {
            "count": len(scores_list),
            "mean_chrf": (sum(chrf) / len(chrf)) if chrf else None,
            "std_chrf": (
                (sum((v - sum(chrf) / len(chrf)) ** 2 for v in chrf) / len(chrf)) ** 0.5
                if len(chrf) > 1 else None
            ),
        }

    return {
        "dataset_name": dataset.name if dataset else "unknown",
        "dataset_version": dataset.version if dataset else "unknown",
        "mode": run.mode,
        "model": run.llm_model,
        "provider": run.llm_provider,
        "prompt_version": run.prompt_version,
        "status": run.status,
        "memory_gap": run.memory_gap,
        **base,
        "per_genre": {k: _summarize(v) for k, v in per_genre.items()},
        "per_content_type": {k: _summarize(v) for k, v in per_content.items()},
        "per_scene": {k: _summarize(v) for k, v in per_scene.items()},
        "requires_previous_memory": _summarize(mem_dep_scores) if mem_dep_scores else None,
        "no_previous_memory": _summarize(no_mem_scores) if no_mem_scores else None,
    }
