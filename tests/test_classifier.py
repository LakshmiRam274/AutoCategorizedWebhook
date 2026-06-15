"""
Unit tests for the pure, dependency-free helper functions in app.classifier.

These tests do NOT make any network calls and do NOT require an API key,
so they can run in any environment (including CI).
"""

import json

import pytest

from app import classifier
from app.models import TicketIn


SAMPLE_TICKET = TicketIn(
    ticket_id="TCK-9001",
    subject="Cannot login to VPN",
    description="Getting an authentication error since this morning when connecting to the VPN.",
)


def test_load_samples_reads_default_file():
    samples = classifier.load_samples()
    assert isinstance(samples, list)
    assert len(samples) > 0
    # Every sample must have the fields used to build few-shot prompts.
    for ex in samples:
        assert "subject" in ex
        assert "description" in ex
        assert "category" in ex
        assert "subcategory" in ex
        assert "priority" in ex


def test_load_samples_missing_file_returns_empty_list(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    assert classifier.load_samples(str(missing)) == []


def test_load_samples_invalid_json_returns_empty_list(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json", encoding="utf-8")
    assert classifier.load_samples(str(bad_file)) == []


def test_build_messages_includes_examples_and_ticket():
    samples = classifier.load_samples()
    messages = classifier.build_messages(SAMPLE_TICKET, samples)

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"

    user_content = messages[1]["content"]
    # The new ticket's content must be present.
    assert "Cannot login to VPN" in user_content
    # At least one few-shot example should be embedded.
    assert "Classification" in user_content


def test_build_messages_with_no_samples():
    messages = classifier.build_messages(SAMPLE_TICKET, [])
    user_content = messages[1]["content"]
    assert "Cannot login to VPN" in user_content


@pytest.mark.parametrize(
    "raw_text",
    [
        '{"category": "Network", "subcategory": "VPN Access", "priority": "High", "confidence": 0.9, "reasoning": "VPN auth failure"}',
        '```json\n{"category": "Network", "subcategory": "VPN Access", "priority": "High", "confidence": 0.9, "reasoning": "VPN auth failure"}\n```',
        'Sure! Here is the classification:\n{"category": "Network", "subcategory": "VPN Access", "priority": "High", "confidence": 0.9, "reasoning": "VPN auth failure"}\nLet me know if you need anything else.',
    ],
)
def test_extract_json_handles_various_formats(raw_text):
    parsed = classifier.extract_json(raw_text)
    assert parsed["category"] == "Network"
    assert parsed["subcategory"] == "VPN Access"
    assert parsed["priority"] == "High"
    assert parsed["confidence"] == 0.9


def test_extract_json_raises_on_unparseable_text():
    with pytest.raises(ValueError):
        classifier.extract_json("This response has no JSON at all.")


def test_normalize_result_fills_defaults_for_missing_fields():
    normalized = classifier.normalize_result({})
    assert normalized["category"] == classifier.config.DEFAULT_CATEGORY
    assert normalized["subcategory"] == classifier.config.DEFAULT_SUBCATEGORY
    assert normalized["priority"] == classifier.config.DEFAULT_PRIORITY
    assert 0.0 <= normalized["confidence"] <= 1.0
    assert normalized["reasoning"] == ""


def test_normalize_result_rejects_invalid_priority():
    normalized = classifier.normalize_result({"priority": "Super Urgent!!"})
    assert normalized["priority"] == classifier.config.DEFAULT_PRIORITY


def test_normalize_result_clamps_confidence():
    too_high = classifier.normalize_result({"confidence": 5})
    too_low = classifier.normalize_result({"confidence": -3})
    assert too_high["confidence"] == 1.0
    assert too_low["confidence"] == 0.0


def test_normalize_result_title_cases_priority():
    normalized = classifier.normalize_result({"priority": "high"})
    assert normalized["priority"] == "High"
