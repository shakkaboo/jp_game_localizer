import csv
import io
import json

from sqlalchemy.orm import Session

from app.models import Chunk, SourceLine, Translation


class ExportService:
    @staticmethod
    def export(project_id: int, fmt: str, db: Session) -> str:
        rows = (
            db.query(SourceLine, Translation, Chunk)
            .outerjoin(Translation, Translation.source_line_id == SourceLine.id)
            .join(Chunk, Chunk.id == SourceLine.chunk_id)
            .filter(SourceLine.project_id == project_id)
            .order_by(SourceLine.id)
            .all()
        )

        if fmt == "json":
            return ExportService._to_json(rows)
        return ExportService._to_csv(rows)

    @staticmethod
    def _extract(src: SourceLine, txn: Translation | None, chk: Chunk) -> dict:
        final = ""
        if txn:
            final = txn.final_text_en or txn.localized_text_en or ""
        return {
            "line_id": src.line_id or "",
            "character": src.character or "",
            "source_text_ja": src.source_text_ja,
            "localized_text_en": txn.localized_text_en if txn else "",
            "final_text_en": final,
            "chunk_number": chk.chunk_number if chk else "",
            "chunk_title": chk.chunk_title if chk else "",
            "status": txn.status if txn else "pending",
        }

    @staticmethod
    def _to_csv(rows: list) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "line_id",
                "character",
                "source_text_ja",
                "localized_text_en",
                "final_text_en",
                "chunk_number",
                "chunk_title",
                "status",
            ]
        )
        for src, txn, chk in rows:
            d = ExportService._extract(src, txn, chk)
            writer.writerow(
                [
                    d["line_id"],
                    d["character"],
                    d["source_text_ja"],
                    d["localized_text_en"],
                    d["final_text_en"],
                    d["chunk_number"],
                    d["chunk_title"],
                    d["status"],
                ]
            )
        return output.getvalue()

    @staticmethod
    def _to_json(rows: list) -> str:
        data = [ExportService._extract(src, txn, chk) for src, txn, chk in rows]
        return json.dumps(data, ensure_ascii=False, indent=2)
