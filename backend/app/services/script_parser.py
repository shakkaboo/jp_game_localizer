import csv
import io
import json
import os
from typing import Any

import pandas as pd


class ScriptParser:
    """Parse uploaded script files into a list of raw dicts.

    To add a new format, create a ``_parse_<type>`` method and add it to
    ``_PARSERS``.
    """

    def parse(self, content: bytes, filename: str) -> list[dict[str, Any]]:
        ext = os.path.splitext(filename)[1].lower()
        parser = self._PARSERS.get(ext)
        if parser is None:
            raise ValueError(f"Unsupported script format: {ext}")
        return parser(content)

    # ------------------------------------------------------------------
    # Individual format parsers
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
            lines.append({"line_id": str(i + 1), "source_text_ja": stripped})
        return lines

    @staticmethod
    def _parse_json(content: bytes) -> list[dict[str, Any]]:
        data = json.loads(content.decode("utf-8-sig"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            lines = data.get("lines") or data.get("lines", [])
            if isinstance(lines, list):
                return lines
        raise ValueError('JSON script must be an array of line objects or {"lines": [...]}')

    _PARSERS = {
        ".csv": _parse_csv,
        ".xlsx": _parse_xlsx,
        ".txt": _parse_txt,
        ".json": _parse_json,
    }
