import csv
import io
import json

from sqlalchemy.orm import Session

from app.models import SourceLine, Translation


class ExportService:
    """Export localized script as CSV or JSON."""

    @staticmethod
    def export(project_id: int, fmt: str, db: Session) -> str:
        lines = (
            db.query(SourceLine, Translation)
            .outerjoin(Translation, Translation.source_line_id == SourceLine.id)
            .filter(SourceLine.project_id == project_id)
            .order_by(SourceLine.id)
            .all()
        )

        if fmt == "json":
            return ExportService._to_json(lines)
        return ExportService._to_csv(lines)

    @staticmethod
    def _to_csv(lines: list) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "line_id",
                "character",
                "source_text_ja",
                "scene_hint",
                "literal_meaning",
                "localized_text_en",
                "final_text_en",
                "status",
            ]
        )
        for src, txn in lines:
            writer.writerow(
                [
                    src.line_id or "",
                    src.character or "",
                    src.source_text_ja,
                    src.scene_hint or "",
                    txn.literal_meaning if txn else "",
                    txn.localized_text_en if txn else "",
                    txn.final_text_en if txn else "",
                    txn.status if txn else "pending",
                ]
            )
        return output.getvalue()

    @staticmethod
    def _to_json(lines: list) -> str:
        data = []
        for src, txn in lines:
            data.append(
                {
                    "line_id": src.line_id or "",
                    "character": src.character or "",
                    "source_text_ja": src.source_text_ja,
                    "scene_hint": src.scene_hint or "",
                    "literal_meaning": txn.literal_meaning if txn else "",
                    "localized_text_en": txn.localized_text_en if txn else "",
                    "final_text_en": txn.final_text_en if txn else "",
                    "status": txn.status if txn else "pending",
                }
            )
        return json.dumps(data, ensure_ascii=False, indent=2)
