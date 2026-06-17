import json

import pytest

from app.benchmark.metrics import (
    check_glossary_compliance,
    check_placeholders_preserved,
    check_speaker_mismatch,
    check_untranslated_japanese,
    compute_all_metrics,
    compute_bleu,
    compute_chrf,
)


def test_chrf_identical():
    score = compute_chrf("Hello world", "Hello world")
    assert score is not None
    assert score == pytest.approx(100.0, abs=1.0)


def test_chrf_different():
    score = compute_chrf("Goodbye moon", "Hello world")
    assert score is not None
    assert score < 50


def test_chrf_empty():
    assert compute_chrf("", "Hello") is None
    assert compute_chrf("Hello", "") is None


def test_bleu_identical():
    score = compute_bleu("Hello world", "Hello world")
    if score is not None:
        assert score == pytest.approx(100.0, abs=1.0)


def test_glossary_compliance_all_pass():
    ge_json = json.dumps([
        {"source_term": "聖剣", "expected_en": "Sacred Sword", "case_sensitive": True},
    ])
    ok, details = check_glossary_compliance("The Sacred Sword is here", ge_json)
    assert ok is True
    assert len(details) == 1
    assert details[0]["found"] is True


def test_glossary_compliance_fail():
    ge_json = json.dumps([
        {"source_term": "聖剣", "expected_en": "Sacred Sword", "case_sensitive": True},
    ])
    ok, details = check_glossary_compliance("The sword is here", ge_json)
    assert ok is False
    assert details[0]["found"] is False


def test_glossary_compliance_none():
    ok, details = check_glossary_compliance("Hello", None)
    assert ok is None
    assert details == []


def test_placeholder_preserved():
    ok, details = check_placeholders_preserved(
        "Hello {player}", "Hello {player}",
        json.dumps(["{player}"]),
    )
    assert ok is True
    assert details[0]["preserved"] is True


def test_placeholder_broken():
    ok, details = check_placeholders_preserved(
        "Hello {player}", "Hello John",
        json.dumps(["{player}"]),
    )
    assert ok is False
    assert details[0]["preserved"] is False


def test_missing_output_flag():
    metrics = compute_all_metrics(
        output_text=None,
        reference_text="Hello",
        source_text="こんにちは",
        speaker="Hero",
        output_character="Hero",
        glossary_expectations_json=None,
        placeholder_expectations_json=None,
    )
    assert metrics["missing_output"] is True


def test_untranslated_japanese_detected():
    metrics = compute_all_metrics(
        output_text="Hello 世界",
        reference_text="Hello world",
        source_text="こんにちは世界",
        speaker="Hero",
        output_character="Hero",
        glossary_expectations_json=None,
        placeholder_expectations_json=None,
    )
    assert metrics["untranslated_japanese"] is True


def test_untranslated_japanese_not_detected():
    metrics = compute_all_metrics(
        output_text="Hello world",
        reference_text="Hello world",
        source_text="こんにちは",
        speaker="Hero",
        output_character="Hero",
        glossary_expectations_json=None,
        placeholder_expectations_json=None,
    )
    assert metrics["untranslated_japanese"] is False


def test_speaker_mismatch():
    mismatch = check_speaker_mismatch("Aldric", "Kaelen")
    assert mismatch is True


def test_speaker_match():
    mismatch = check_speaker_mismatch("Aldric", "Aldric")
    assert mismatch is False


def test_speaker_mismatch_none():
    assert check_speaker_mismatch(None, "Kaelen") is None
    assert check_speaker_mismatch("Aldric", None) is None


def test_compute_all_metrics_happy():
    metrics = compute_all_metrics(
        output_text="The Sacred Sword",
        reference_text="The Sacred Sword",
        source_text="聖剣",
        speaker="Hero",
        output_character="Hero",
        glossary_expectations_json=json.dumps([
            {"source_term": "聖剣", "expected_en": "Sacred Sword", "case_sensitive": True},
        ]),
        placeholder_expectations_json=None,
    )
    assert metrics["chrf_score"] is not None
    assert metrics["glossary_compliant"] is True
    assert metrics["missing_output"] is False
    assert metrics["untranslated_japanese"] is False
    assert metrics["speaker_mismatch"] is False
    assert metrics["line_id_mismatch"] is False
