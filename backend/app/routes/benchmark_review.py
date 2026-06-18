from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.benchmark.review_service import (
    build_comparison,
    build_human_metrics,
    create_hard_failure,
    create_item_evaluation,
    create_scene_evaluation,
    get_hard_failure,
    get_item_evaluation,
    get_scene_evaluation,
    list_hard_failures,
    list_item_evaluations,
    list_scene_evaluations,
    update_hard_failure,
    update_item_evaluation,
    update_scene_evaluation,
)
from app.database import get_db

router = APIRouter(prefix="/benchmark", tags=["review"])


def _handle_service_error(e: Exception) -> HTTPException:
    if isinstance(e, LookupError):
        return HTTPException(404, str(e))
    if isinstance(e, IntegrityError):
        return HTTPException(409, "Duplicate review — this reviewer has already submitted for this target")
    if isinstance(e, ValueError):
        return HTTPException(422, str(e))
    return HTTPException(500, "internal_review_error")


# ---------------------------------------------------------------------------
# Item evaluations
# ---------------------------------------------------------------------------


@router.post("/runs/{run_id}/evaluations/items", status_code=201)
def post_item_evaluation(run_id: int, body: dict, db: Session = Depends(get_db)):
    from app.schemas import BenchmarkItemEvaluationCreate
    from app.schemas import BenchmarkItemEvaluationRead as Res

    try:
        parsed = BenchmarkItemEvaluationCreate(**body)
    except Exception as e:
        raise HTTPException(422, str(e))

    try:
        ev = create_item_evaluation(db, run_id, parsed.model_dump())
        db.commit()
        return Res.model_validate(ev)
    except Exception as e:
        raise _handle_service_error(e)


@router.put("/evaluations/items/{evaluation_id}")
def put_item_evaluation(evaluation_id: int, body: dict, db: Session = Depends(get_db)):
    from app.schemas import BenchmarkItemEvaluationUpdate
    from app.schemas import BenchmarkItemEvaluationRead as Res

    try:
        parsed = BenchmarkItemEvaluationUpdate(**body)
    except Exception as e:
        raise HTTPException(422, str(e))

    try:
        ev = update_item_evaluation(db, evaluation_id, parsed.model_dump())
        db.commit()
        return Res.model_validate(ev)
    except Exception as e:
        raise _handle_service_error(e)


@router.get("/evaluations/items/{evaluation_id}")
def get_item_evaluation_route(evaluation_id: int, db: Session = Depends(get_db)):
    from app.schemas import BenchmarkItemEvaluationRead as Res

    try:
        ev = get_item_evaluation(db, evaluation_id)
        return Res.model_validate(ev)
    except Exception as e:
        raise _handle_service_error(e)


@router.get("/runs/{run_id}/evaluations/items")
def list_item_evaluations_route(
    run_id: int,
    benchmark_output_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    from app.schemas import BenchmarkItemEvaluationRead as Res

    evals = list_item_evaluations(db, run_id, benchmark_output_id)
    return [Res.model_validate(e) for e in evals]


# ---------------------------------------------------------------------------
# Scene evaluations
# ---------------------------------------------------------------------------


@router.post("/runs/{run_id}/evaluations/scenes", status_code=201)
def post_scene_evaluation(run_id: int, body: dict, db: Session = Depends(get_db)):
    from app.schemas import BenchmarkSceneEvaluationCreate
    from app.schemas import BenchmarkSceneEvaluationRead as Res

    try:
        parsed = BenchmarkSceneEvaluationCreate(**body)
    except Exception as e:
        raise HTTPException(422, str(e))

    try:
        ev = create_scene_evaluation(db, run_id, parsed.model_dump())
        db.commit()
        return Res.model_validate(ev)
    except Exception as e:
        raise _handle_service_error(e)


@router.put("/evaluations/scenes/{evaluation_id}")
def put_scene_evaluation(evaluation_id: int, body: dict, db: Session = Depends(get_db)):
    from app.schemas import BenchmarkSceneEvaluationUpdate
    from app.schemas import BenchmarkSceneEvaluationRead as Res

    try:
        parsed = BenchmarkSceneEvaluationUpdate(**body)
    except Exception as e:
        raise HTTPException(422, str(e))

    try:
        ev = update_scene_evaluation(db, evaluation_id, parsed.model_dump())
        db.commit()
        return Res.model_validate(ev)
    except Exception as e:
        raise _handle_service_error(e)


@router.get("/evaluations/scenes/{evaluation_id}")
def get_scene_evaluation_route(evaluation_id: int, db: Session = Depends(get_db)):
    from app.schemas import BenchmarkSceneEvaluationRead as Res

    try:
        ev = get_scene_evaluation(db, evaluation_id)
        return Res.model_validate(ev)
    except Exception as e:
        raise _handle_service_error(e)


@router.get("/runs/{run_id}/evaluations/scenes")
def list_scene_evaluations_route(run_id: int, db: Session = Depends(get_db)):
    from app.schemas import BenchmarkSceneEvaluationRead as Res

    evals = list_scene_evaluations(db, run_id)
    return [Res.model_validate(e) for e in evals]


# ---------------------------------------------------------------------------
# Hard-failure reviews
# ---------------------------------------------------------------------------


@router.post("/runs/{run_id}/hard-failures", status_code=201)
def post_hard_failure(run_id: int, body: dict, db: Session = Depends(get_db)):
    from app.schemas import BenchmarkHardFailureCreate
    from app.schemas import BenchmarkHardFailureRead as Res

    try:
        parsed = BenchmarkHardFailureCreate(**body)
    except Exception as e:
        raise HTTPException(422, str(e))

    try:
        rec = create_hard_failure(db, run_id, parsed.model_dump())
        db.commit()
        return Res.model_validate(rec)
    except Exception as e:
        raise _handle_service_error(e)


@router.put("/hard-failures/{failure_id}")
def put_hard_failure(failure_id: int, body: dict, db: Session = Depends(get_db)):
    from app.schemas import BenchmarkHardFailureUpdate
    from app.schemas import BenchmarkHardFailureRead as Res

    try:
        parsed = BenchmarkHardFailureUpdate(**body)
    except Exception as e:
        raise HTTPException(422, str(e))

    try:
        rec = update_hard_failure(db, failure_id, parsed.model_dump())
        db.commit()
        return Res.model_validate(rec)
    except Exception as e:
        raise _handle_service_error(e)


@router.get("/hard-failures/{failure_id}")
def get_hard_failure_route(failure_id: int, db: Session = Depends(get_db)):
    from app.schemas import BenchmarkHardFailureRead as Res

    try:
        rec = get_hard_failure(db, failure_id)
        return Res.model_validate(rec)
    except Exception as e:
        raise _handle_service_error(e)


@router.get("/runs/{run_id}/hard-failures")
def list_hard_failures_route(
    run_id: int,
    benchmark_output_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    from app.schemas import BenchmarkHardFailureRead as Res

    recs = list_hard_failures(db, run_id, benchmark_output_id)
    return [Res.model_validate(r) for r in recs]


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


@router.get("/runs/{run_id}/human-metrics")
def get_human_metrics(run_id: int, db: Session = Depends(get_db)):
    try:
        return build_human_metrics(db, run_id)
    except Exception as e:
        raise _handle_service_error(e)


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


@router.get("/compare")
def get_comparison(
    plain_run_id: int | None = Query(None),
    context_run_id: int | None = Query(None),
    context_memory_run_id: int | None = Query(None),
    dataset_id: int | None = Query(None),
    selection: str | None = Query(None),
    db: Session = Depends(get_db),
):
    try:
        return build_comparison(
            db,
            plain_run_id=plain_run_id,
            context_run_id=context_run_id,
            context_memory_run_id=context_memory_run_id,
            dataset_id=dataset_id,
            selection=selection,
        )
    except Exception as e:
        raise _handle_service_error(e)
