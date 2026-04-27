"""RedactionLog -- append-only structured trail of consent-aware redactions.

Designed for privacy-review and audit workflows: store *what* was redacted,
*from where*, and under *which consent basis*, without storing the raw value.
The original value is kept only long enough to compute its length, then
discarded.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, List, Optional


def _utcnow_iso() -> str:
    # ISO 8601 in UTC, e.g. "2026-04-26T12:34:56.789012Z".
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class RedactionLog:
    """Container for redaction events. Append-only; no PII is retained.

    Each ``record(...)`` call produces a dict with:
      - ``field``: caller-supplied field path or label.
      - ``redacted``: the post-redaction value (typically ``[REDACTED:type]``).
      - ``consent_basis``: legal/operational basis under which the redaction
        was performed (e.g. ``"explicit:opt-in"`` or ``"legitimate-interest"``).
      - ``original_length``: length of the original value (the value itself
        is **not** stored).
      - ``ts``: ISO-8601 UTC timestamp of when the event was recorded.

    The optional ``clock`` parameter lets tests inject a deterministic
    timestamp source.
    """

    def __init__(self, *, clock: Optional[Callable[[], str]] = None) -> None:
        self._records: List[dict] = []
        self._clock = clock or _utcnow_iso

    def record(
        self,
        field: str,
        original: object,
        redacted: object,
        consent_basis: str,
    ) -> dict:
        """Append a redaction event. Returns the appended dict.

        ``original`` is consumed only to compute its length; it is **never**
        stored on the log. Pass it as a keyword for clarity at call sites.
        """
        if not isinstance(field, str) or not field:
            raise ValueError("RedactionLog.record: field must be a non-empty string")
        if not isinstance(consent_basis, str) or not consent_basis:
            raise ValueError(
                "RedactionLog.record: consent_basis must be a non-empty string"
            )

        original_str = "" if original is None else str(original)
        redacted_str = "" if redacted is None else str(redacted)

        record = {
            "field": field,
            "redacted": redacted_str,
            "consent_basis": consent_basis,
            "original_length": len(original_str),
            "ts": self._clock(),
        }
        self._records.append(record)
        return record

    def dump(self) -> List[dict]:
        """Return a shallow copy of all records. Safe to mutate."""
        return [dict(r) for r in self._records]

    def clear(self) -> None:
        """Reset the log."""
        self._records.clear()

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self):
        return iter(self.dump())
