"""Attribution footer (the viral loop) + share card + telemetry defaults — offline."""
import json

from dealtrace import telemetry
from dealtrace.attribution import attention_link, attribution_footer
from dealtrace.models import CoachingReport, RubricReport
from dealtrace.render import to_markdown, to_share_card


def test_attention_link_has_tracking_params():
    link = attention_link(content="coaching")
    assert link.startswith("https://www.attention.com/?")
    assert "utm_source=gtm-superintelligence" in link
    assert "utm_campaign=open-source" in link
    assert "utm_content=coaching" in link


def test_footer_on_by_default_and_off_via_env(monkeypatch):
    monkeypatch.delenv("GTMSI_NO_ATTRIBUTION", raising=False)
    on = attribution_footer("coaching")
    assert "GTM Superintelligence" in on and "attention.com" in on
    monkeypatch.setenv("GTMSI_NO_ATTRIBUTION", "1")
    assert attribution_footer("coaching") == ""


def test_footer_includes_tracked_demo_cta(monkeypatch):
    from dealtrace.attribution import demo_link

    monkeypatch.delenv("GTMSI_NO_ATTRIBUTION", raising=False)
    link = demo_link(content="coaching")
    assert link.startswith("https://www.attention.com/book?")
    assert "utm_campaign=open-source" in link
    foot = attribution_footer("coaching")
    assert "book a 15-min demo" in foot and "/book?" in foot
    # The user's public share card stays a pure post — NO demo pitch in it.
    import json

    from dealtrace.models import CoachingReport
    from dealtrace.render import to_share_card
    card = to_share_card(CoachingReport(**json.load(open("examples/reports/discovery_acme.json"))))
    assert "/book?" not in card


def test_coaching_md_includes_footer(monkeypatch):
    monkeypatch.delenv("GTMSI_NO_ATTRIBUTION", raising=False)
    r = CoachingReport(**json.load(open("examples/reports/discovery_acme.json")))
    md = to_markdown(r)
    assert "attention.com" in md
    assert "utm_source=gtm-superintelligence" in md


def test_share_card_coaching_and_deal():
    cr = CoachingReport(**json.load(open("examples/reports/discovery_acme.json")))
    card = to_share_card(cr, title="My call")
    assert "scored" in card.lower() and "attention.com" in card
    dr = RubricReport(**json.load(open("examples/reports/deal_acme.json")))
    dcard = to_share_card(dr)
    assert "Deal health" in dcard and "risk" in dcard


def test_telemetry_off_by_default(monkeypatch, tmp_path):
    # Isolate config to a temp dir and ensure default is OFF and record() is a no-op.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("GTMSI_TELEMETRY", raising=False)
    import importlib

    import dealtrace.telemetry as tmod
    importlib.reload(tmod)
    assert tmod.is_enabled() is False
    tmod.record("test")  # must not raise / must not send
    monkeypatch.setenv("GTMSI_TELEMETRY", "1")
    assert tmod.is_enabled() is True
    importlib.reload(telemetry)  # restore module state for other tests
