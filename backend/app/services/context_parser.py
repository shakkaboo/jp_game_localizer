import json
import os

import yaml

try:
    from docx import Document as DocxDocument

    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


class ContextParser:
    """Parse uploaded context files into a raw Python dict.

    To add a new format, create a ``_parse_<type>`` method and register it
    in ``_PARSERS``.
    """

    def parse(self, content: bytes, filename: str) -> dict | str:
        ext = os.path.splitext(filename)[1].lower()
        parser = self._PARSERS.get(ext)
        if parser is None:
            raise ValueError(f"Unsupported context format: {ext}")
        return parser(content)

    # ------------------------------------------------------------------
    # Individual format parsers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json(content: bytes) -> dict:
        return json.loads(content.decode("utf-8-sig"))

    @staticmethod
    def _parse_yaml(content: bytes) -> dict | str:
        result = yaml.safe_load(content.decode("utf-8-sig"))
        return result if result is not None else {}

    @staticmethod
    def _parse_txt(content: bytes) -> str:
        return content.decode("utf-8-sig")

    @staticmethod
    def _parse_docx(content: bytes) -> str:
        if not HAS_DOCX:
            raise RuntimeError("python-docx is not installed")
        doc = DocxDocument(stream=content)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)

    _PARSERS = {
        ".json": _parse_json,
        ".yaml": _parse_yaml,
        ".yml": _parse_yaml,
        ".txt": _parse_txt,
        ".docx": _parse_docx,
    }
