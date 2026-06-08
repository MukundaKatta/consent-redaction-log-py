# consent-redaction-log-py

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Record consent-aware redactions for privacy review trails.** Zero runtime dependencies.

Python port of [@mukundakatta/consent-redaction-log](https://github.com/MukundaKatta/consent-redaction-log). The JS sibling has the broader rationale; this README sticks to the Python API.

## Why

Compliance, evals, and incident review all want the same thing: an auditable trail of *what was redacted, why, and under whose consent*. Most apps redact in flight and throw the trail away. This library keeps the trail without keeping the secret.

## Install

```bash
pip install consent-redaction-log-py
```

## Usage

```python
from consent_redaction_log import RedactionLog, redact_with_consent, summarize_redactions

# 1) Inline redaction with a one-shot helper.
text = "Contact me at alice@example.com or +1 555 123 4567"
result = redact_with_consent(text, allowed_types=["email"])
result.text   # "Contact me at alice@example.com or [REDACTED:phone]"
result.log    # [{"type": "phone", "length": 15}]
summarize_redactions(result.log)
# {"phone": 1}

# 2) Long-running log of structured field-level redactions.
log = RedactionLog()
log.record(
    field="user.message",
    original="alice@example.com",
    redacted="[REDACTED:email]",
    consent_basis="legitimate-interest:safety-review",
)
log.record(
    field="user.message",
    original="+1 555 123 4567",
    redacted="[REDACTED:phone]",
    consent_basis="explicit:opt-in-debug",
)
log.dump()
# [
#   {"field": "user.message", "redacted": "[REDACTED:email]",
#    "consent_basis": "legitimate-interest:safety-review",
#    "original_length": 17, "ts": "2026-04-26T12:00:00Z"},
#   ...
# ]
```

`RedactionLog` does **not** persist the raw original; it stores the original's
length so you can spot anomalies (e.g. truncated values) without keeping the
PII. Reach for `original=` only at record time so you can compute the length
in one place; the value never leaves the function.

## API

| Symbol | What it does |
|---|---|
| `RedactionLog()` | Container for structured redaction events. |
| `RedactionLog.record(field, original, redacted, consent_basis)` | Append one event. Returns the appended record dict. |
| `RedactionLog.dump()` | Return a list copy of all records. Safe to mutate. |
| `RedactionLog.clear()` | Reset the log. |
| `redact_with_consent(text, allowed_types=...)` | Inline one-shot redaction + per-call log. Returns a `RedactionResult` dataclass. |
| `summarize_redactions(log)` | Count events by type. Returns a `dict[str, int]`. |

## Pattern coverage

`redact_with_consent` ships with the same two patterns as the JS sibling:

* `email` -- RFC 5322-ish address regex.
* `phone` -- international-friendly number regex (8+ digits with optional `+`, spaces, dots, parens).

Pass `allowed_types=["email"]` to keep emails verbatim.

## API differences from the JS sibling

* Python keyword args (`allowed_types=`, `consent_basis=`) instead of the JS options object.
* `redact_with_consent` returns a `RedactionResult` dataclass instead of a plain object.
* `RedactionLog` adds a structured `record/dump` surface that the JS module didn't ship; matches the spec for "consent-aware redactions for privacy review trails".

See the JS sibling's [README](https://github.com/MukundaKatta/consent-redaction-log) for the broader design context.
