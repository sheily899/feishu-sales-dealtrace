"""Redaction must mask PII without eating quantified values (dates, prices, hours)."""
from dealtrace.redaction import redact_text


def test_redacts_real_pii():
    assert "[EMAIL]" in redact_text("reach me at sam@acme.com")
    assert "[PHONE]" in redact_text("call +1 (415) 555-0198")
    assert "[SSN]" in redact_text("ssn 123-45-6789")
    assert "[URL]" in redact_text("see https://acme.com/x")


def test_does_not_eat_quantified_values():
    # Regression: the PHONE regex used to swallow these.
    for s in ["it's about 10 hours a week", "costs 1 200 000 dollars",
              "we met 2024 01 02 at 10 30", "saved 15 hours and $300k"]:
        out = redact_text(s)
        assert "[PHONE]" not in out, f"over-redacted: {s!r} -> {out!r}"
