import os


EXTENSION_MAP = {
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".txt": "txt",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".docx": "docx",
}


def detect_file_type(filename: str, content_type: str | None = None) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return EXTENSION_MAP.get(ext, "unknown")


def is_script_file_type(file_type: str) -> bool:
    return file_type in ("csv", "xlsx", "txt", "json")


def is_context_file_type(file_type: str) -> bool:
    return file_type in ("json", "yaml", "txt", "docx")
