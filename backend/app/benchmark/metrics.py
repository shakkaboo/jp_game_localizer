import json
import math
import re
from typing import Any

HYPHEN = "\u30FC"
HIRAGANA_RE = re.compile(r"[\u3040-\u309F]")
KATAKANA_RE = re.compile(r"[\u30A0-\u30FF]")
CJK_RE = re.compile(r"[\u4E00-\u9FFF]")

PLACEHOLDER_RE = re.compile(r"(\{[^}]*\}|%[sdFrx]|<[^>]+>)")


def compute_chrf(hypothesis: str, reference: str) -> float | None:
    try:
        from sacrebleu import sentence_chrf
        if not hypothesis or not reference:
            return None
        result = sentence_chrf(hypothesis, [reference])
        return float(result.score)
    except Exception:
        return None


def compute_bleu(hypothesis: str, reference: str) -> float | None:
    try:
        from sacrebleu import sentence_bleu
        if not hypothesis or not reference:
            return None
        result = sentence_bleu(hypothesis, [reference])
        return float(result.score)
    except Exception:
        return None


def check_glossary_compliance(
    output: str,
    glossary_expectations_json: str | None,
) -> tuple[bool | None, list[dict]]:
    if not glossary_expectations_json:
        return None, []
    try:
        expectations = json.loads(glossary_expectations_json)
    except (json.JSONDecodeError, TypeError):
        return None, []

    if not isinstance(expectations, list):
        return None, []

    details = []
    all_pass = True
    any_checked = False

    for entry in expectations:
        if not isinstance(entry, dict):
            continue
        source_term = entry.get("source_term", "")
        expected_en = entry.get("expected_en", "")
        case_sensitive = entry.get("case_sensitive", True)
        if not source_term or not expected_en:
            continue
        any_checked = True
        if case_sensitive:
            found = expected_en in output
        else:
            found = expected_en.lower() in output.lower()
        details.append({
            "source_term": source_term,
            "expected_en": expected_en,
            "found": found,
        })
        if not found:
            all_pass = False

    if not any_checked:
        return None, details
    return all_pass, details


def check_placeholders_preserved(
    source: str,
    output: str,
    placeholder_expectations_json: str | None,
) -> tuple[bool | None, list[dict]]:
    if placeholder_expectations_json:
        try:
            expected = json.loads(placeholder_expectations_json)
        except (json.JSONDecodeError, TypeError):
            expected = []
    else:
        expected = []

    if not isinstance(expected, list):
        expected = []

    source_placeholders = PLACEHOLDER_RE.findall(source)

    all_phs = list(set(expected + source_placeholders))

    if not all_phs:
        return None, []

    details = []
    all_preserved = True
    for ph in all_phs:
        preserved = ph in output
        details.append({"placeholder": ph, "preserved": preserved})
        if not preserved:
            all_preserved = False

    return all_preserved, details


def check_untranslated_japanese(output: str) -> bool | None:
    if not output:
        return None
    has_hira = bool(HIRAGANA_RE.search(output))
    has_kata = bool(KATAKANA_RE.search(output))
    has_cjk = bool(CJK_RE.search(output))
    return bool(has_hira or has_kata or has_cjk)


def check_speaker_mismatch(
    expected_speaker: str | None,
    output_character: str | None,
) -> bool | None:
    if not expected_speaker:
        return None
    if not output_character:
        return None
    return expected_speaker.strip().lower() != output_character.strip().lower()


def compute_all_metrics(
    output_text: str | None,
    reference_text: str,
    source_text: str,
    speaker: str | None,
    output_character: str | None,
    glossary_expectations_json: str | None,
    placeholder_expectations_json: str | None,
) -> dict[str, Any]:
    missing = not output_text or not output_text.strip()

    chrf = None
    bleu = None
    if not missing:
        chrf = compute_chrf(output_text, reference_text)
        bleu = compute_bleu(output_text, reference_text)

    glossary_compliant, glossary_details = check_glossary_compliance(
        output_text or "", glossary_expectations_json,
    )
    placeholders_preserved, ph_details = check_placeholders_preserved(
        source_text, output_text or "", placeholder_expectations_json,
    )

    untranslated = check_untranslated_japanese(output_text or "") if not missing else None

    speaker_mismatch = check_speaker_mismatch(speaker, output_character) if not missing else None

    details: dict[str, Any] = {}
    if glossary_details:
        details["glossary"] = glossary_details
    if ph_details:
        details["placeholders"] = ph_details

    return {
        "chrf_score": chrf,
        "bleu_score": bleu,
        "glossary_compliant": glossary_compliant,
        "placeholders_preserved": placeholders_preserved,
        "missing_output": missing,
        "untranslated_japanese": untranslated,
        "line_id_mismatch": False,
        "speaker_mismatch": speaker_mismatch,
        "details_json": json.dumps(details, ensure_ascii=False) if details else None,
    }


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _std(values: list[float]) -> float | None:
    if not values or len(values) < 2:
        return None
    m = _mean(values)
    if m is None:
        return None
    variance = sum((v - m) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def aggregate_scores(scores: list[dict]) -> dict:
    chrf_scores = [s["chrf_score"] for s in scores if s.get("chrf_score") is not None]
    bleu_scores = [s["bleu_score"] for s in scores if s.get("bleu_score") is not None]
    total = len(scores)
    completed = sum(1 for s in scores if not s["missing_output"])
    failed = total - completed

    return {
        "total_items": total,
        "completed_items": completed,
        "failed_items": failed,
        "chrf": {
            "mean": _mean(chrf_scores),
            "std": _std(chrf_scores),
            "min": min(chrf_scores) if chrf_scores else None,
            "max": max(chrf_scores) if chrf_scores else None,
        } if chrf_scores else None,
        "bleu": {
            "mean": _mean(bleu_scores),
            "std": _std(bleu_scores),
        } if bleu_scores else None,
        "glossary_compliance_rate": (
            sum(1 for s in scores if s.get("glossary_compliant") is True) /
            max(sum(1 for s in scores if s.get("glossary_compliant") is not None), 1)
            if any(s.get("glossary_compliant") is not None for s in scores) else None
        ),
        "placeholder_preservation_rate": (
            sum(1 for s in scores if s.get("placeholders_preserved") is True) /
            max(sum(1 for s in scores if s.get("placeholders_preserved") is not None), 1)
            if any(s.get("placeholders_preserved") is not None for s in scores) else None
        ),
        "missing_output_count": sum(1 for s in scores if s["missing_output"]),
        "untranslated_japanese_count": sum(1 for s in scores if s.get("untranslated_japanese")),
        "line_id_mismatch_count": sum(1 for s in scores if s["line_id_mismatch"]),
        "speaker_mismatch_count": sum(1 for s in scores if s.get("speaker_mismatch")),
    }
