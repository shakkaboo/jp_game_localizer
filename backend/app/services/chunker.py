from collections import defaultdict
from typing import Any


class Chunker:
    @staticmethod
    def chunk(
        lines: list[dict[str, str]], project_id: int, source_file_id: int
    ) -> list[dict[str, Any]]:
        grouped = defaultdict(list)
        for line in lines:
            hint = line.get("scene_hint") or "未分類"
            grouped[hint].append(line)

        chunks = []
        for idx, (hint, scene_lines) in enumerate(grouped.items(), start=1):
            chunks.append(
                {
                    "project_id": project_id,
                    "source_file_id": source_file_id,
                    "chunk_number": idx,
                    "chunk_title": hint,
                    "scene_hint": hint,
                    "status": "pending",
                    "lines": scene_lines,
                }
            )
        return chunks
