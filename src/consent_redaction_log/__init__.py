"""consent-redaction-log -- record consent-aware redactions for privacy review trails.

Python port of @mukundakatta/consent-redaction-log.

Public surface:

    from consent_redaction_log import (
        RedactionLog,
        RedactionResult,
        redact_with_consent,
        summarize_redactions,
    )

* ``RedactionLog`` -- append-only container of structured redaction events.
* ``redact_with_consent(text, allowed_types=...)`` -- inline redactor mirroring the JS sibling.
* ``summarize_redactions(log)`` -- count events by type.
"""

from .log import RedactionLog
from .redact import RedactionResult, redact_with_consent, summarize_redactions

__version__ = "0.1.0"
VERSION = __version__

__all__ = [
    "VERSION",
    "RedactionLog",
    "RedactionResult",
    "redact_with_consent",
    "summarize_redactions",
]
