"""Tests for ``redact_with_consent`` and ``summarize_redactions``."""

from __future__ import annotations

from consent_redaction_log import redact_with_consent, summarize_redactions


def test_redacts_email_by_default():
    r = redact_with_consent("ping me at alice@example.com")
    assert "alice@example.com" not in r.text
    assert "[REDACTED:email]" in r.text
    assert r.log == [{"type": "email", "length": len("alice@example.com")}]


def test_redacts_phone_by_default():
    r = redact_with_consent("call +1 555 123 4567 anytime")
    assert "555 123 4567" not in r.text
    assert "[REDACTED:phone]" in r.text
    assert r.log[0]["type"] == "phone"


def test_allowed_types_skips_listed_patterns():
    text = "alice@example.com / +1 555 123 4567"
    r = redact_with_consent(text, allowed_types=["email"])
    # Email survives, phone does not.
    assert "alice@example.com" in r.text
    assert "[REDACTED:phone]" in r.text
    types = [item["type"] for item in r.log]
    assert "email" not in types
    assert "phone" in types


def test_redacts_multiple_matches_and_logs_each():
    text = "a@x.io b@y.io"
    r = redact_with_consent(text)
    assert r.text == "[REDACTED:email] [REDACTED:email]"
    assert len(r.log) == 2
    assert all(item["type"] == "email" for item in r.log)


def test_none_input_is_treated_as_empty_string():
    r = redact_with_consent(None)
    assert r.text == ""
    assert r.log == []


def test_summarize_redactions_counts_by_type():
    log = [
        {"type": "email", "length": 10},
        {"type": "email", "length": 12},
        {"type": "phone", "length": 14},
    ]
    assert summarize_redactions(log) == {"email": 2, "phone": 1}


def test_summarize_ignores_malformed_entries():
    log = [
        {"type": "email", "length": 10},
        "not a dict",
        {"length": 12},  # missing type
        {"type": 42, "length": 12},  # type not a string
    ]
    assert summarize_redactions(log) == {"email": 1}


def test_redaction_does_not_mutate_unmatched_substrings():
    text = "Hello world, no PII here."
    r = redact_with_consent(text)
    assert r.text == text
    assert r.log == []
