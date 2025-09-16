"""
Guardrail utilities for ConcordBroker agents.
Currently provides lightweight PII redaction to reduce accidental exposure.
"""

import re
from typing import Optional


EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+)\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?)?\d{3}[-.\s]?\d{4}")


def redact_pii(text: Optional[str]) -> Optional[str]:
    """Mask common PII patterns (emails, US-style phone numbers) in text.

    This is a best-effort safeguard and should be combined with upstream
    policy controls. If input is None or not a string, returns as-is.
    """
    if not isinstance(text, str):
        return text

    masked = EMAIL_RE.sub(lambda m: f"{m.group(1)[:2]}***@***.{m.group(2)[-2:]}", text)
    masked = PHONE_RE.sub("[REDACTED-PHONE]", masked)
    return masked


def parse_confidence(text: Optional[str]) -> Optional[float]:
    """Extract the first float in [0,1] from text.

    Returns None if not found.
    """
    if not isinstance(text, str):
        return None
    m = re.search(r"0?\.\d+|1(?:\.0+)?", text)
    if not m:
        return None
    try:
        val = float(m.group(0))
        return max(0.0, min(1.0, val))
    except Exception:
        return None
