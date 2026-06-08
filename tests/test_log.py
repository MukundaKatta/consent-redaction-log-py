"""Tests for ``RedactionLog``."""

from __future__ import annotations

import itertools

import pytest

from consent_redaction_log import RedactionLog


def _fixed_clock():
    """Deterministic clock that returns ts-1, ts-2, ts-3, ..."""
    counter = itertools.count(1)
    return lambda: f"ts-{next(counter)}"


def test_record_appends_structured_event_without_original_value():
    log = RedactionLog(clock=_fixed_clock())
    rec = log.record(
        field="user.email",
        original="alice@example.com",
        redacted="[REDACTED:email]",
        consent_basis="explicit:opt-in",
    )
    assert rec["field"] == "user.email"
    assert rec["redacted"] == "[REDACTED:email]"
    assert rec["consent_basis"] == "explicit:opt-in"
    assert rec["original_length"] == len("alice@example.com")
    assert rec["ts"] == "ts-1"
    # The raw value must NOT be persisted.
    assert "original" not in rec


def test_dump_returns_copy_not_internal_list():
    log = RedactionLog(clock=_fixed_clock())
    log.record("f", "o", "r", "consent")
    snapshot = log.dump()
    snapshot.append({"injected": True})
    # Internal log unaffected.
    assert len(log.dump()) == 1
    assert all("injected" not in r for r in log.dump())


def test_records_are_appended_in_order():
    log = RedactionLog(clock=_fixed_clock())
    log.record("a", "x", "[X]", "c1")
    log.record("b", "y", "[Y]", "c2")
    log.record("c", "z", "[Z]", "c3")
    fields = [r["field"] for r in log.dump()]
    assert fields == ["a", "b", "c"]
    assert [r["ts"] for r in log.dump()] == ["ts-1", "ts-2", "ts-3"]


def test_clear_resets_log():
    log = RedactionLog(clock=_fixed_clock())
    log.record("a", "x", "[X]", "c")
    assert len(log) == 1
    log.clear()
    assert len(log) == 0
    assert log.dump() == []


def test_record_rejects_empty_field():
    log = RedactionLog()
    with pytest.raises(ValueError):
        log.record("", "x", "[X]", "consent")


def test_record_rejects_empty_consent_basis():
    log = RedactionLog()
    with pytest.raises(ValueError):
        log.record("f", "x", "[X]", "")


def test_iter_yields_records():
    log = RedactionLog(clock=_fixed_clock())
    log.record("a", "x", "[X]", "c1")
    log.record("b", "y", "[Y]", "c2")
    fields = [r["field"] for r in log]
    assert fields == ["a", "b"]


def test_none_original_is_treated_as_empty_string():
    log = RedactionLog(clock=_fixed_clock())
    rec = log.record("f", None, "[REDACTED]", "consent")
    assert rec["original_length"] == 0


def test_dump_records_are_independent_copies():
    # Mutating a dict returned by dump() must not corrupt the internal trail.
    log = RedactionLog(clock=_fixed_clock())
    log.record("f", "original", "[R]", "c")
    snapshot = log.dump()
    snapshot[0]["field"] = "MUTATED"
    assert log.dump()[0]["field"] == "f"


def test_record_stores_length_not_raw_value():
    # The audit trail keeps the original's length but never the value itself.
    log = RedactionLog(clock=_fixed_clock())
    rec = log.record("user.message", "alice@example.com", "[REDACTED:email]", "c")
    assert rec["original_length"] == len("alice@example.com")
    assert "alice@example.com" not in rec.values()


def test_default_clock_returns_iso_utc_string():
    log = RedactionLog()
    rec = log.record("f", "x", "[X]", "c")
    ts = rec["ts"]
    # YYYY-MM-DDTHH:MM:SS.<frac>Z
    assert ts.endswith("Z")
    assert "T" in ts
    assert ts.count("-") >= 2
