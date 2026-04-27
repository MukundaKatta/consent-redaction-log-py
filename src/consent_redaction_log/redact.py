"""Inline redactor and summary helper.

Ports the JS surface 1:1 -- same regexes, same default behavior.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

# Mirror the JS regexes from @mukundakatta/consent-redaction-log/src/index.js.
# JS used /i flag on email -- so use re.IGNORECASE here too.
_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
# Phone: optional `+`, then a digit, then 8+ chars of digits/spaces/dots/parens/dashes,
# then a digit. Matches the JS: /\+?\d[\d\s().-]{7,}\d/g.
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")

_RULES: dict[str, re.Pattern[str]] = {
    "email": _EMAIL_RE,
    "phone": _PHONE_RE,
}


@dataclass
class RedactionResult:
    """Result of a one-shot ``redact_with_consent`` call.

    Attributes:
        text: Redacted text. Unmatched substrings are preserved verbatim.
        log: List of ``{"type": str, "length": int}`` entries, one per redacted span.
    """

    text: str
    log: List[dict] = field(default_factory=list)


def redact_with_consent(
    text: object,
    *,
    allowed_types: Optional[Iterable[str]] = None,
) -> RedactionResult:
    """Replace PII patterns in ``text`` with ``[REDACTED:<type>]`` markers.

    Mirrors the JS ``redactWithConsent(text, { allowedTypes }) -> { text, log }``.

    Args:
        text: Anything stringifiable. ``None`` is coerced to ``""`` to match
            the JS ``String(text ?? "")`` behavior.
        allowed_types: Iterable of pattern names to *skip* (i.e. honor
            consent for). Currently supported: ``"email"``, ``"phone"``.
    """
    allowed = set(allowed_types or ())
    value = "" if text is None else str(text)
    log: List[dict] = []

    for pattern_name, pattern in _RULES.items():
        if pattern_name in allowed:
            continue

        def _on_match(m: re.Match[str], _name: str = pattern_name) -> str:
            log.append({"type": _name, "length": len(m.group(0))})
            return f"[REDACTED:{_name}]"

        value = pattern.sub(_on_match, value)

    return RedactionResult(text=value, log=log)


def summarize_redactions(log: Iterable[dict]) -> dict:
    """Count entries in a redaction log by ``type``.

    Mirrors the JS ``summarizeRedactions(log) -> { type: count }``.
    """
    out: dict = {}
    for item in log:
        if not isinstance(item, dict):
            continue
        t = item.get("type")
        if not isinstance(t, str):
            continue
        out[t] = out.get(t, 0) + 1
    return out
