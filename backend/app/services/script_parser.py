import csv
import io
import json
import os
import re
from typing import Any

import pandas as pd


COLON_RE = re.compile(r"^(.+?)[\uFF1A:]\s*(.+)$")


class ScriptParser:
    def parse(self, content: bytes, filename: str) -> list[dict[str, Any]]:
        ext = os.path.splitext(filename)[1].lower()
        parser = self._PARSERS.get(ext)
        if parser is None:
            raise ValueError(f"Unsupported script format: {ext}")
        return parser(content)

    # ------------------------------------------------------------------

    @staticmethod
    def _parse_csv(content: bytes) -> list[dict[str, Any]]:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        return [row for row in reader]

    @staticmethod
    def _parse_xlsx(content: bytes) -> list[dict[str, Any]]:
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
        df = df.fillna("")
        return df.to_dict(orient="records")

    @staticmethod
    def _parse_txt(content: bytes) -> list[dict[str, Any]]:
        text = content.decode("utf-8-sig")
        lines = []
        for i, line in enumerate(text.splitlines()):
            stripped = line.strip()
            if not stripped:
                continue

            entry: dict[str, str] = {
                "line_id": str(i + 1),
                "character": "",
                "source_text_ja": stripped,
                "scene_hint": "",
            }

            m = COLON_RE.match(stripped)
            if m:
                candidate = m.group(1).strip()
                dialogue = m.group(2).strip()
                if dialogue:
                    entry["character"] = candidate
                    entry["source_text_ja"] = dialogue

            lines.append(entry)
        return lines

    @staticmethod
    def _parse_json(content: bytes) -> list[dict[str, Any]]:
        data = json.loads(content.decode("utf-8-sig"))

        # Array of objects
        if isinstance(data, list):
            return data

        # Dict with a "lines" key
        if isinstance(data, dict):
            lines = data.get("lines")
            if isinstance(lines, list):
                return lines

            # Key-value format: {"KEY": "value"}
            result = []
            for key, value in data.items():
                if isinstance(value, str):
                    result.append(
                        {
                            "line_id": key,
                            "character": "",
                            "source_text_ja": value,
                            "scene_hint": "",
                        }
                    )
                else:
                    result.append(
                        {
                            "line_id": key,
                            "character": "",
                            "source_text_ja": str(value),
                            "scene_hint": "",
                        }
                    )
            return result

        raise ValueError("JSON script must be an array, a key-value object, or {lines: [...]}")

    _PARSERS = {
        ".csv": _parse_csv,
        ".xlsx": _parse_xlsx,
        ".txt": _parse_txt,
        ".json": _parse_json,
    }
