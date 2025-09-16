import pytest

from apps.langchain_system.util_guardrails import redact_pii, parse_confidence


def test_redact_pii_email():
    text = "Contact me at alice@example.com for details"
    masked = redact_pii(text)
    assert masked != text
    assert "@example.com" not in masked


def test_redact_pii_phone():
    text = "Call 305-555-1234 or (561) 222-3344"
    masked = redact_pii(text)
    assert "305-555-1234" not in masked
    assert "(561) 222-3344" not in masked
    assert "[REDACTED-PHONE]" in masked


@pytest.mark.parametrize("input_text,expected", [
    ("Confidence: 0.85", 0.85),
    ("0.6", 0.6),
    ("1", 1.0),
    ("No number here", None),
])
def test_parse_confidence(input_text, expected):
    val = parse_confidence(input_text)
    if expected is None:
        assert val is None
    else:
        assert abs(val - expected) < 1e-6

