import csv
import io
import json

from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.models import Chunk, SourceLine, Translation


class ExportService:
    @staticmethod
    def export(project_id: int, fmt: str, db: Session) -> str | bytes:
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
        if fmt == "pdf":
            return ExportService._to_pdf(rows, project_id)
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

    @staticmethod
    def _to_pdf(rows: list, project_id: int) -> bytes:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ScriptTitle", parent=styles["Title"], spaceAfter=4 * mm,
        )
        subtitle_style = ParagraphStyle(
            "ScriptSubtitle", parent=styles["Normal"],
            textColor="#666666", fontSize=11, spaceAfter=10 * mm,
        )
        chunk_style = ParagraphStyle(
            "ChunkHeader", parent=styles["Heading2"],
            spaceBefore=8 * mm, spaceAfter=3 * mm,
            fontSize=13,
        )
        speaker_style = ParagraphStyle(
            "Speaker", parent=styles["Normal"],
            textColor="#333333", fontSize=10,
            spaceBefore=3 * mm, spaceAfter=1 * mm,
        )
        dialogue_style = ParagraphStyle(
            "Dialogue", parent=styles["Normal"],
            textColor="#111111", fontSize=10,
            leftIndent=10 * mm, spaceAfter=2 * mm,
            leading=14,
        )

        story = [Paragraph("Localized Script", title_style)]
        story.append(Paragraph(f"Project ID {project_id}", subtitle_style))

        rows_by_chunk: dict[str, list[tuple]] = {}
        for src, txn, chk in rows:
            english = ""
            if txn:
                english = txn.final_text_en or txn.localized_text_en or ""
            if not english:
                continue
            key = f"{chk.chunk_number}. {chk.chunk_title}" if chk.chunk_title else str(chk.chunk_number)
            rows_by_chunk.setdefault(key, []).append((src, english))

        for chunk_label in sorted(rows_by_chunk, key=lambda k: int(k.split(".")[0])):
            story.append(Paragraph(chunk_label, chunk_style))
            for src, english in rows_by_chunk[chunk_label]:
                speaker = (src.character or "").strip()
                if speaker:
                    story.append(Paragraph(f"{speaker}:", speaker_style))
                story.append(Paragraph(english, dialogue_style))

        doc.build(story)
        return buf.getvalue()
