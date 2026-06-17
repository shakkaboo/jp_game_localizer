from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.benchmark.service import execute_benchmark_run, get_metrics_summary
from app.benchmark.validation import parse_and_validate
from app.database import get_db
from app.models import (
    BenchmarkAutomaticScore,
    BenchmarkDataset,
    BenchmarkItem,
    BenchmarkOutput,
    BenchmarkRun,
    BenchmarkScene,
    BenchmarkSceneMemory,
)
from app.schemas import (
    BenchmarkDatasetListItem,
    BenchmarkDatasetRead,
    BenchmarkItemRead,
    BenchmarkLoadResponse,
    BenchmarkMetricsSummary,
    BenchmarkOutputRead,
    BenchmarkRunDetailRead,
    BenchmarkRunRead,
    BenchmarkRunSceneOutput,
    BenchmarkRunStartResponse,
    BenchmarkSceneRead,
    BenchmarkOutputWithItemRead,
    BenchmarkAutomaticScoreRead,
)

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------


@router.post("/datasets/load", response_model=BenchmarkLoadResponse)
def load_dataset(body: dict, db: Session = Depends(get_db)):
    yaml_text = body.get("yaml", "") if isinstance(body, dict) else ""
    if not yaml_text or not yaml_text.strip():
        raise HTTPException(422, "Request body must contain a 'yaml' key with non-empty YAML text")

    try:
        parsed = parse_and_validate(yaml_text)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(422, f"Failed to parse YAML: {e}")

    ds_data = parsed["dataset"]

    existing = (
        db.query(BenchmarkDataset)
        .filter(
            BenchmarkDataset.name == ds_data["name"],
            BenchmarkDataset.version == ds_data["version"],
        )
        .first()
    )
    if existing:
        raise HTTPException(
            409,
            f"Dataset '{ds_data['name']}' version '{ds_data['version']}' already exists",
        )

    dataset = BenchmarkDataset(**ds_data)
    db.add(dataset)
    db.flush()

    total_items = 0
    for scene_data in parsed["scenes"]:
        items = scene_data.pop("items")
        scene = BenchmarkScene(dataset_id=dataset.id, **scene_data)
        db.add(scene)
        db.flush()
        for item_data in items:
            db.add(BenchmarkItem(scene_id=scene.id, **item_data))
            total_items += 1

    db.commit()
    return BenchmarkLoadResponse(
        dataset_id=dataset.id,
        name=dataset.name,
        version=dataset.version,
        scenes_loaded=len(parsed["scenes"]),
        items_loaded=total_items,
    )


@router.get("/datasets", response_model=list[BenchmarkDatasetListItem])
def list_datasets(db: Session = Depends(get_db)):
    datasets = db.query(BenchmarkDataset).order_by(BenchmarkDataset.id.desc()).all()
    result: list[BenchmarkDatasetListItem] = []
    for ds in datasets:
        scene_count = db.query(BenchmarkScene).filter(BenchmarkScene.dataset_id == ds.id).count()
        item_count = (
            db.query(BenchmarkItem)
            .join(BenchmarkScene)
            .filter(BenchmarkScene.dataset_id == ds.id)
            .count()
        )
        result.append(BenchmarkDatasetListItem(
            id=ds.id,
            name=ds.name,
            version=ds.version,
            source_or_author=ds.source_or_author,
            review_status=ds.review_status,
            created_at=ds.created_at,
            scene_count=scene_count,
            item_count=item_count,
        ))
    return result


@router.get("/datasets/{dataset_id}", response_model=BenchmarkDatasetRead)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    ds = db.query(BenchmarkDataset).filter(BenchmarkDataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found")
    scenes = (
        db.query(BenchmarkScene)
        .filter(BenchmarkScene.dataset_id == dataset_id)
        .order_by(BenchmarkScene.scene_number)
        .all()
    )
    scene_reads: list[BenchmarkSceneRead] = []
    for scene in scenes:
        items = (
            db.query(BenchmarkItem)
            .filter(BenchmarkItem.scene_id == scene.id)
            .order_by(BenchmarkItem.sequence_number)
            .all()
        )
        scene_reads.append(BenchmarkSceneRead(
            id=scene.id,
            dataset_id=scene.dataset_id,
            scene_number=scene.scene_number,
            title=scene.title,
            genre=scene.genre,
            content_type=scene.content_type,
            setting_or_location=scene.setting_or_location,
            tone=scene.tone,
            context_json=scene.context_json,
            notes=scene.notes,
            created_at=scene.created_at,
            items=[BenchmarkItemRead.model_validate(it) for it in items],
        ))
    return BenchmarkDatasetRead(
        id=ds.id,
        name=ds.name,
        version=ds.version,
        source_or_author=ds.source_or_author,
        license_or_usage_status=ds.license_or_usage_status,
        reference_translation_method=ds.reference_translation_method,
        review_status=ds.review_status,
        description=ds.description,
        created_at=ds.created_at,
        scenes=scene_reads,
    )


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------


@router.post("/runs", response_model=BenchmarkRunStartResponse)
def start_run(body: dict, db: Session = Depends(get_db)):
    dataset_id = body.get("dataset_id")
    mode = body.get("mode", "").strip().lower()

    if not isinstance(dataset_id, int):
        raise HTTPException(422, "dataset_id must be an integer")
    if mode not in ("plain", "context", "context_memory"):
        raise HTTPException(422, "mode must be 'plain', 'context', or 'context_memory'")

    dataset = db.query(BenchmarkDataset).filter(BenchmarkDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    run = execute_benchmark_run(db, dataset, mode)

    return BenchmarkRunStartResponse(
        run_id=run.id,
        dataset_id=run.dataset_id,
        mode=run.mode,
        status=run.status,
        total_scenes=run.total_scenes,
        completed_scenes=run.completed_scenes,
        memory_gap=run.memory_gap,
    )


@router.get("/runs", response_model=list[BenchmarkRunRead])
def list_runs(
    dataset_id: int | None = Query(None),
    mode: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(BenchmarkRun).order_by(BenchmarkRun.id.desc())
    if dataset_id is not None:
        query = query.filter(BenchmarkRun.dataset_id == dataset_id)
    if mode is not None:
        query = query.filter(BenchmarkRun.mode == mode)
    return query.all()


@router.get("/runs/{run_id}", response_model=BenchmarkRunDetailRead)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(BenchmarkRun).filter(BenchmarkRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Run not found")

    scenes = (
        db.query(BenchmarkScene)
        .filter(BenchmarkScene.dataset_id == run.dataset_id)
        .order_by(BenchmarkScene.scene_number)
        .all()
    )

    scene_outputs: list[BenchmarkRunSceneOutput] = []
    for scene in scenes:
        items = (
            db.query(BenchmarkItem)
            .filter(BenchmarkItem.scene_id == scene.id)
            .order_by(BenchmarkItem.sequence_number)
            .all()
        )
        outputs = (
            db.query(BenchmarkOutput)
            .filter(
                BenchmarkOutput.run_id == run.id,
                BenchmarkOutput.scene_id == scene.id,
            )
            .order_by(BenchmarkOutput.sequence_number)
            .all()
        )

        item_map = {it.id: it for it in items}

        output_with_items: list[BenchmarkOutputWithItemRead] = []
        for out in outputs:
            item = item_map.get(out.benchmark_item_id)
            score = None
            if out.score:
                score = BenchmarkAutomaticScoreRead.model_validate(out.score)
            output_read = BenchmarkOutputRead(
                id=out.id,
                run_id=out.run_id,
                benchmark_item_id=out.benchmark_item_id,
                scene_id=out.scene_id,
                sequence_number=out.sequence_number,
                output_localized_text_en=out.output_localized_text_en,
                output_literal_meaning=out.output_literal_meaning,
                output_localization_note=out.output_localization_note,
                status=out.status,
                error_message=out.error_message,
                score=score,
            )
            output_with_items.append(BenchmarkOutputWithItemRead(
                output=output_read,
                item=BenchmarkItemRead.model_validate(item) if item else None,
                scene=BenchmarkSceneRead.model_validate(scene),
            ))

        scene_outputs.append(BenchmarkRunSceneOutput(
            scene=BenchmarkSceneRead.model_validate(scene),
            outputs=output_with_items,
        ))

    return BenchmarkRunDetailRead(
        id=run.id,
        dataset_id=run.dataset_id,
        mode=run.mode,
        llm_provider=run.llm_provider,
        llm_model=run.llm_model,
        prompt_version=run.prompt_version,
        status=run.status,
        created_at=run.created_at,
        completed_at=run.completed_at,
        error_message=run.error_message,
        memory_gap=run.memory_gap,
        total_scenes=run.total_scenes,
        completed_scenes=run.completed_scenes,
        notes=run.notes,
        scenes=scene_outputs,
    )


@router.get("/runs/{run_id}/scenes/{scene_number}", response_model=BenchmarkRunSceneOutput)
def get_run_scene(run_id: int, scene_number: int, db: Session = Depends(get_db)):
    run = db.query(BenchmarkRun).filter(BenchmarkRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Run not found")

    scene = (
        db.query(BenchmarkScene)
        .filter(
            BenchmarkScene.dataset_id == run.dataset_id,
            BenchmarkScene.scene_number == scene_number,
        )
        .first()
    )
    if not scene:
        raise HTTPException(404, "Scene not found")

    items = (
        db.query(BenchmarkItem)
        .filter(BenchmarkItem.scene_id == scene.id)
        .order_by(BenchmarkItem.sequence_number)
        .all()
    )
    outputs = (
        db.query(BenchmarkOutput)
        .filter(
            BenchmarkOutput.run_id == run.id,
            BenchmarkOutput.scene_id == scene.id,
        )
        .order_by(BenchmarkOutput.sequence_number)
        .all()
    )

    item_map = {it.id: it for it in items}
    output_with_items: list[BenchmarkOutputWithItemRead] = []
    for out in outputs:
        item = item_map.get(out.benchmark_item_id)
        score = None
        if out.score:
            score = BenchmarkAutomaticScoreRead.model_validate(out.score)
        output_read = BenchmarkOutputRead(
            id=out.id,
            run_id=out.run_id,
            benchmark_item_id=out.benchmark_item_id,
            scene_id=out.scene_id,
            sequence_number=out.sequence_number,
            output_localized_text_en=out.output_localized_text_en,
            output_literal_meaning=out.output_literal_meaning,
            output_localization_note=out.output_localization_note,
            status=out.status,
            error_message=out.error_message,
            score=score,
        )
        output_with_items.append(BenchmarkOutputWithItemRead(
            output=output_read,
            item=BenchmarkItemRead.model_validate(item) if item else None,
            scene=BenchmarkSceneRead.model_validate(scene),
        ))

    return BenchmarkRunSceneOutput(
        scene=BenchmarkSceneRead.model_validate(scene),
        outputs=output_with_items,
    )


@router.get("/runs/{run_id}/items/{benchmark_item_id}", response_model=BenchmarkOutputWithItemRead)
def get_run_item(run_id: int, benchmark_item_id: int, db: Session = Depends(get_db)):
    run = db.query(BenchmarkRun).filter(BenchmarkRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Run not found")

    item = db.query(BenchmarkItem).filter(BenchmarkItem.id == benchmark_item_id).first()
    if not item:
        raise HTTPException(404, "Benchmark item not found")

    output = (
        db.query(BenchmarkOutput)
        .filter(
            BenchmarkOutput.run_id == run.id,
            BenchmarkOutput.benchmark_item_id == benchmark_item_id,
        )
        .first()
    )
    if not output:
        raise HTTPException(404, "Output not found for this item in this run")

    scene = db.query(BenchmarkScene).filter(BenchmarkScene.id == item.scene_id).first()
    score = None
    if output.score:
        score = BenchmarkAutomaticScoreRead.model_validate(output.score)

    return BenchmarkOutputWithItemRead(
        output=BenchmarkOutputRead(
            id=output.id,
            run_id=output.run_id,
            benchmark_item_id=output.benchmark_item_id,
            scene_id=output.scene_id,
            sequence_number=output.sequence_number,
            output_localized_text_en=output.output_localized_text_en,
            output_literal_meaning=output.output_literal_meaning,
            output_localization_note=output.output_localization_note,
            status=output.status,
            error_message=output.error_message,
            score=score,
        ),
        item=BenchmarkItemRead.model_validate(item),
        scene=BenchmarkSceneRead.model_validate(scene),
    )


@router.get("/runs/{run_id}/metrics", response_model=BenchmarkMetricsSummary)
def get_run_metrics(run_id: int, db: Session = Depends(get_db)):
    run = db.query(BenchmarkRun).filter(BenchmarkRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Run not found")
    return get_metrics_summary(db, run)
