from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project
from app.schemas import ExportRequest
from app.services.export_service import ExportService

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/")
async def export_localized_script(
    body: ExportRequest,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == body.project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    content = ExportService.export(body.project_id, body.format, db)

    media_type = "application/json" if body.format == "json" else "text/csv"
    filename = f"localized_script_{body.project_id}.{body.format}"

    return PlainTextResponse(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
