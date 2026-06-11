from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project
from app.services.export_service import ExportService

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/{project_id}")
async def export_localized_script(
    project_id: int,
    format: str = Query("csv", pattern="^(csv|json)$"),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    content = ExportService.export(project_id, format, db)

    media_type = "application/json" if format == "json" else "text/csv"
    filename = f"localized_script_{project_id}.{format}"

    return PlainTextResponse(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
