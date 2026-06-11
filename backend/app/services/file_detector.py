import mimetypes
import os


class FileDetector:
    SUPPORTED_SCRIPT_EXTENSIONS = {
        ".csv": "csv",
        ".xlsx": "xlsx",
        ".txt": "txt",
        ".json": "json",
    }

    SUPPORTED_CONTEXT_EXTENSIONS = {
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".txt": "txt",
        ".docx": "docx",
    }

    @staticmethod
    def detect(filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        if ext in FileDetector.SUPPORTED_SCRIPT_EXTENSIONS:
            return FileDetector.SUPPORTED_SCRIPT_EXTENSIONS[ext]
        if ext in FileDetector.SUPPORTED_CONTEXT_EXTENSIONS:
            return FileDetector.SUPPORTED_CONTEXT_EXTENSIONS[ext]
        raise ValueError(f"Unsupported file extension: {ext}")

    @staticmethod
    def is_script(filename: str) -> bool:
        ext = os.path.splitext(filename)[1].lower()
        return ext in FileDetector.SUPPORTED_SCRIPT_EXTENSIONS

    @staticmethod
    def is_context(filename: str) -> bool:
        ext = os.path.splitext(filename)[1].lower()
        return ext in FileDetector.SUPPORTED_CONTEXT_EXTENSIONS
