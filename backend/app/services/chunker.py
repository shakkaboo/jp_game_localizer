import re
from collections import defaultdict

from app.schemas import ScriptLineNormalized


class Chunker:
    """Group normalized script lines into scene-based chunks."""

    @staticmethod
    def chunk(
        lines: list[ScriptLineNormalized], project_id: int, source_file_id: int
    ) -> list[dict]:
        grouped = defaultdict(list)
        for line in lines:
            hint = line.scene_hint if line.scene_hint else "__no_scene__"
            grouped[hint].append(line)

        chunks = []
        for idx, (hint, scene_lines) in enumerate(grouped.items(), start=1):
            title = Chunker._make_title(hint, scene_lines)
            chunks.append(
                {
                    "project_id": project_id,
                    "source_file_id": source_file_id,
                    "chunk_number": idx,
                    "chunk_title": title,
                    "scene_hint": hint if hint != "__no_scene__" else None,
                    "status": "pending",
                    "lines": scene_lines,
                }
            )
        return chunks

    @staticmethod
    def _make_title(hint: str, lines: list[ScriptLineNormalized]) -> str:
        if hint and hint != "__no_scene__":
            words = re.sub(r"[_-]", " ", hint).title()
            return words[:100]
        first = next(
            (l.source_text_ja[:40] for l in lines if l.source_text_ja.strip()), ""
        )
        return f"Scene {first}" if first else "Untitled Scene"
