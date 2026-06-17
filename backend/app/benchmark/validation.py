import json
import re
import unicodedata
from typing import Any

import yaml


REQUIRED_PROVENANCE = [
    "name",
    "version",
    "source_or_author",
    "license_or_usage_status",
    "reference_translation_method",
    "review_status",
]

MOJIBAKE_REPLACEMENT = "\ufffd"

LATIN1_SUSPECT_RANGES = [
    (0x80, 0xBF),
]


def _has_japanese(text: str) -> bool:
    for ch in text:
        cp = ord(ch)
        if 0x3040 <= cp <= 0x30FF:
            return True
        if 0x4E00 <= cp <= 0x9FFF:
            return True
        if 0x3000 <= cp <= 0x303F:
            return True
    return False


def _has_mojibake(text: str) -> bool:
    if MOJIBAKE_REPLACEMENT in text:
        return True
    if not _has_japanese(text):
        return False
    latin1_count = sum(
        1 for ch in text
        if any(lo <= ord(ch) <= hi for lo, hi in LATIN1_SUSPECT_RANGES)
    )
    return latin1_count > 3


_VALID_PLACEHOLDER_RE = re.compile(r"\{[^}]*\}")


def _validate_placeholder(ph: Any) -> None:
    if not isinstance(ph, str):
        raise ValueError(f"Placeholder must be a string, got {type(ph).__name__}")
    if not ph.strip():
        raise ValueError("Placeholder must not be empty")
    if ph.startswith("{") and ph.endswith("}"):
        inner = ph[1:-1].strip()
        if not inner:
            raise ValueError(f"Empty placeholder braces: {ph}")
    elif ph.startswith("%"):
        if len(ph) < 2 or ph[1] not in ("s", "d", "f", "r", "x"):
            raise ValueError(f"Invalid format placeholder: {ph}")
    else:
        if not re.match(r"^<[^>]+>$", ph):
            raise ValueError(f"Unrecognized placeholder syntax: {ph}")


def _validate_glossary_expectation(entry: Any) -> None:
    if not isinstance(entry, dict):
        raise ValueError(f"Glossary expectation must be a dict, got {type(entry).__name__}")
    if "source_term" not in entry:
        raise ValueError("Glossary expectation missing 'source_term'")
    if "expected_en" not in entry:
        raise ValueError("Glossary expectation missing 'expected_en'")
    if not isinstance(entry["source_term"], str) or not entry["source_term"].strip():
        raise ValueError("Glossary expectation 'source_term' must be a non-empty string")
    if not isinstance(entry["expected_en"], str) or not entry["expected_en"].strip():
        raise ValueError("Glossary expectation 'expected_en' must be a non-empty string")
    if "case_sensitive" in entry and not isinstance(entry["case_sensitive"], bool):
        raise ValueError("Glossary expectation 'case_sensitive' must be a boolean")


def _validate_item(item: dict, scene_number: int, seq: int) -> None:
    src = item.get("source_text_ja")
    ref = item.get("reference_en")
    if not src or not isinstance(src, str) or not src.strip():
        raise ValueError(f"Scene {scene_number}, item {seq}: source_text_ja must be a non-empty string")
    if not ref or not isinstance(ref, str) or not ref.strip():
        raise ValueError(f"Scene {scene_number}, item {seq}: reference_en must be a non-empty string")
    if _has_mojibake(src):
        raise ValueError(f"Scene {scene_number}, item {seq}: source_text_ja contains mojibake")
    if _has_mojibake(ref):
        raise ValueError(f"Scene {scene_number}, item {seq}: reference_en contains mojibake")

    if "glossary_expectations" in item:
        ge = item["glossary_expectations"]
        if not isinstance(ge, list):
            raise ValueError(f"Scene {scene_number}, item {seq}: glossary_expectations must be a list")
        for entry in ge:
            try:
                _validate_glossary_expectation(entry)
            except ValueError as e:
                raise ValueError(f"Scene {scene_number}, item {seq}: {e}")

    if "placeholder_expectations" in item:
        pe = item["placeholder_expectations"]
        if not isinstance(pe, list):
            raise ValueError(f"Scene {scene_number}, item {seq}: placeholder_expectations must be a list")
        for ph in pe:
            try:
                _validate_placeholder(ph)
            except ValueError as e:
                raise ValueError(f"Scene {scene_number}, item {seq}: {e}")


def _validate_context(context: Any, scene_number: int) -> None:
    if not isinstance(context, dict):
        raise ValueError(f"Scene {scene_number}: context must be a dict")
    for key in ("characters", "relationships", "glossary", "placeholders"):
        val = context.get(key)
        if val is not None and not isinstance(val, list):
            raise ValueError(f"Scene {scene_number}: context.{key} must be a list")
    if "glossary" in context:
        for entry in context["glossary"]:
            if not isinstance(entry, dict):
                raise ValueError(f"Scene {scene_number}: context.glossary entries must be dicts")
            if "term" not in entry or "translation" not in entry:
                raise ValueError(f"Scene {scene_number}: context.glossary entry missing 'term' or 'translation'")
    if "placeholders" in context:
        for ph in context["placeholders"]:
            try:
                _validate_placeholder(ph)
            except ValueError as e:
                raise ValueError(f"Scene {scene_number}: {e}")


def _check_unique_ordered(values: list[int], label: str, context: str) -> None:
    if not values:
        return
    expected = list(range(1, len(values) + 1))
    if values != expected:
        raise ValueError(f"{context}: {label} must be contiguous 1..{len(values)}, got {values}")


def parse_and_validate(yaml_text: str) -> dict:
    raw = yaml.safe_load(yaml_text)

    if not isinstance(raw, dict) or "dataset" not in raw:
        raise ValueError("YAML must contain a top-level 'dataset' key")

    dataset = raw["dataset"]

    for field in REQUIRED_PROVENANCE:
        val = dataset.get(field)
        if not val or not isinstance(val, str) or not val.strip():
            raise ValueError(f"Missing or empty required provenance field: '{field}'")

    if "scenes" not in dataset or not isinstance(dataset["scenes"], list):
        raise ValueError("dataset must contain a 'scenes' list")

    scene_numbers = []
    seen_scene_numbers = set()
    all_items_total = 0

    for si, scene in enumerate(dataset["scenes"]):
        if not isinstance(scene, dict):
            raise ValueError(f"Scene index {si}: must be a dict")

        sn = scene.get("scene_number")
        if not isinstance(sn, int):
            raise ValueError(f"Scene index {si}: 'scene_number' must be an integer")
        if sn < 1:
            raise ValueError(f"Scene index {si}: 'scene_number' must be >= 1")
        if sn in seen_scene_numbers:
            raise ValueError(f"Duplicate scene_number: {sn}")
        seen_scene_numbers.add(sn)
        scene_numbers.append(sn)

        if "context" in scene:
            try:
                _validate_context(scene["context"], sn)
            except ValueError as e:
                raise ValueError(f"Scene {sn}: {e}")
        else:
            raise ValueError(f"Scene {sn}: missing 'context'")

        items = scene.get("items", [])
        if not isinstance(items, list):
            raise ValueError(f"Scene {sn}: 'items' must be a list")
        if not items:
            raise ValueError(f"Scene {sn}: must have at least one item")

        seq_numbers = []
        seen_seq = set()
        for item in items:
            seq = item.get("sequence_number")
            if not isinstance(seq, int):
                raise ValueError(f"Scene {sn}: 'sequence_number' must be an integer")
            if seq < 1:
                raise ValueError(f"Scene {sn}: 'sequence_number' must be >= 1")
            if seq in seen_seq:
                raise ValueError(f"Scene {sn}: duplicate sequence_number: {seq}")
            seen_seq.add(seq)
            seq_numbers.append(seq)
            _validate_item(item, sn, seq)
            all_items_total += 1

        _check_unique_ordered(seq_numbers, "item sequence numbers", f"Scene {sn}")

    _check_unique_ordered(scene_numbers, "scene numbers", "Dataset")

    if all_items_total < 1:
        raise ValueError("Dataset must contain at least one item")

    dataset_data = {
        "name": dataset["name"].strip(),
        "version": dataset["version"].strip(),
        "source_or_author": dataset["source_or_author"].strip(),
        "license_or_usage_status": dataset["license_or_usage_status"].strip(),
        "reference_translation_method": dataset["reference_translation_method"].strip(),
        "review_status": dataset["review_status"].strip(),
        "description": dataset.get("description", "").strip() or None,
    }

    scenes_data = []
    for scene in dataset["scenes"]:
        context = scene.get("context", {})
        scenes_data.append({
            "scene_number": scene["scene_number"],
            "title": scene.get("title", "").strip() or None,
            "genre": scene["genre"].strip() if "genre" in scene else "",
            "content_type": scene["content_type"].strip() if "content_type" in scene else "",
            "setting_or_location": scene.get("setting_or_location", "").strip() or None,
            "tone": scene.get("tone", "").strip() or None,
            "context_json": json.dumps(context, ensure_ascii=False) if context else None,
            "notes": scene.get("notes", "").strip() or None,
            "items": [
                {
                    "sequence_number": it["sequence_number"],
                    "source_text_ja": it["source_text_ja"],
                    "reference_en": it["reference_en"],
                    "speaker": it.get("speaker", "").strip() or None,
                    "character_voice_context": it.get("character_voice_context", "").strip() or None,
                    "relationship_context": it.get("relationship_context", "").strip() or None,
                    "glossary_expectations": json.dumps(it["glossary_expectations"], ensure_ascii=False)
                    if it.get("glossary_expectations") else None,
                    "placeholder_expectations": json.dumps(it["placeholder_expectations"], ensure_ascii=False)
                    if it.get("placeholder_expectations") else None,
                    "requires_previous_memory": it.get("requires_previous_memory", False),
                }
                for it in scene["items"]
            ],
        })

    return {
        "dataset": dataset_data,
        "scenes": scenes_data,
    }
