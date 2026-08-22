"""CLI wiring that runs offline (no API key)."""
from gtmsi.adapters import load_transcript
from gtmsi.cli import _apply_participants, build_parser, main


def test_apply_participants_overrides_sides(tmp_path):
    p = tmp_path / "c.txt"
    p.write_text("Riley: hello there\nPat: hi\n")
    t = load_transcript(str(p))
    _apply_participants(t, '{"Riley": "rep", "Pat": "prospect"}')
    sides = {turn.speaker: turn.side for turn in t.turns}
    assert sides["Riley"] == "rep"
    assert sides["Pat"] == "prospect"


def test_apply_participants_ignores_invalid_side(tmp_path):
    p = tmp_path / "c.txt"
    p.write_text("Riley: hello\n")
    t = load_transcript(str(p))
    _apply_participants(t, '{"Riley": "banana"}')  # invalid side -> ignored
    assert t.turns[0].side != "banana"


def test_cli_validate_and_list_offline(capsys):
    assert main(["validate"]) == 0
    assert main(["list", "rubrics"]) == 0
    out = capsys.readouterr().out
    assert "deal-health" in out and "account-health" in out


def test_cli_crm_dry_run_offline():
    # generic dry-run needs no API key and no credentials.
    assert main(["crm", "examples/reports/deal_acme.json", "--crm", "salesforce"]) == 0


def test_cli_crm_live_requires_token():
    # hubspot live writer without a token should fail cleanly (exit 1), not crash.
    assert main(["crm", "examples/reports/deal_acme.json", "--crm", "hubspot", "--writer", "hubspot"]) == 1


def test_workbench_feishu_flag_is_opt_in():
    args = build_parser().parse_args(["workbench", "--feishu", "--port", "8766"])

    assert args.feishu is True
    assert args.port == 8766
