"""``gtmsi`` command-line interface.

Commands
  coach <transcript>     classify + coach one call -> markdown/json/text
  classify <transcript>  just the call-type classification
  bulk <dir>             coach every transcript in a directory
  inspect <transcript>   show the normalized transcript (debug adapters)
  list <kind>            list frameworks | scorecards | call-types
  validate               check the YAML knowledge base for integrity problems
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from .adapters import ADAPTERS_BY_NAME, load_transcript
from .registry import load_registry
from .render import to_markdown, to_terminal


def _eprint(*a):
    print(*a, file=sys.stderr)


def _build_llm(args):
    from .llm import build_coach

    return build_coach(provider=getattr(args, "provider", None), model=getattr(args, "model", None))


def cmd_workbench(args):
    from .workbench import run_workbench
    run_workbench(host=args.host, port=args.port)
    return 0


def _infer_two_party_sides(t):
    """In a clean 2-speaker call, if exactly one speaker's side is known (rep or
    prospect) and the other is unknown, label the other as the counterpart.

    Lets the user name just one side — e.g. ``--participants '{"Dana": "rep"}'`` on a
    Fireflies/Zoom/Grain call (which carry no role field) — and have the whole call
    resolve, instead of forcing them to enumerate both speakers.
    """
    opp = {"rep": "prospect", "prospect": "rep"}
    # Best-known side per speaker (a known side on any turn wins over unknown).
    sides: dict[str, str] = {}
    for turn in t.turns:
        if turn.speaker not in sides or turn.side != "unknown":
            sides[turn.speaker] = turn.side
    if len(sides) != 2:
        return t
    known = [(name, s) for name, s in sides.items() if s in opp]
    unknown = [name for name, s in sides.items() if s == "unknown"]
    if len(known) != 1 or len(unknown) != 1:
        return t
    target, other_side = unknown[0], opp[known[0][1]]
    for turn in t.turns:
        if turn.speaker == target:
            turn.side = other_side
    for p in t.participants:
        if target in (p.name, p.id):
            p.side = other_side
    return t


def _apply_participants(t, spec: str | None):
    """Override speaker→side mapping from a JSON string or a path to a JSON file.

    Example: --participants '{"Alex": "rep", "Sam": "prospect"}'. This fixes the
    common case where side detection from names alone is ambiguous. In a 2-speaker
    call you can name just one side (e.g. only the rep) and the other is inferred.
    """
    if not spec:
        return t
    text = Path(spec).read_text() if Path(spec).exists() else spec
    mapping = json.loads(text)
    valid = {"rep", "prospect", "customer", "partner", "internal", "unknown"}
    for turn in t.turns:
        side = mapping.get(turn.speaker)
        if side in valid:
            turn.side = side
    for p in t.participants:
        side = mapping.get(p.name) or mapping.get(p.id)
        if side in valid:
            p.side = side
    _infer_two_party_sides(t)
    return t


def cmd_coach(args) -> int:
    from .pipeline import classify as run_classify
    from .pipeline import coach as run_coach

    reg = load_registry()
    t = load_transcript(args.transcript, adapter=args.adapter)
    t = _apply_participants(t, getattr(args, "participants", None))
    if args.redact:
        from .redaction import redact_transcript

        t = redact_transcript(t)
    llm = _build_llm(args)
    classification = run_classify(t, reg, llm)
    report = run_coach(t, classification, reg, llm)

    if args.format == "json":
        out = report.model_dump_json(indent=2)
    elif args.format == "text":
        out = to_terminal(report)
    else:
        out = to_markdown(report, title=t.title)

    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        _eprint(f"wrote {args.out}")
    else:
        print(out)
    return 0


def cmd_classify(args) -> int:
    from .pipeline import classify as run_classify

    reg = load_registry()
    t = load_transcript(args.transcript, adapter=args.adapter)
    t = _apply_participants(t, getattr(args, "participants", None))
    llm = _build_llm(args)
    c = run_classify(t, reg, llm)
    if args.json:
        print(c.model_dump_json(indent=2))
    else:
        print(f"{c.call_type} ({c.phase}) — confidence {c.confidence:.0%}")
        print(f"  {c.rationale}")
        for alt in c.alternatives:
            print(f"  alt: {alt.get('call_type')} {alt.get('confidence')}")
    return 0


def cmd_bulk(args) -> int:
    from .pipeline import classify as run_classify
    from .pipeline import coach as run_coach

    reg = load_registry()
    llm = _build_llm(args)
    src = Path(args.directory)
    files = sorted(p for p in src.glob(args.glob) if p.is_file())
    if not files:
        _eprint(f"no files matching {args.glob} in {src}")
        return 1
    out_dir = Path(args.out) if args.out else src / "coaching"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for p in files:
        try:
            t = load_transcript(str(p), adapter=args.adapter)
            c = run_classify(t, reg, llm)
            r = run_coach(t, c, reg, llm)
            (out_dir / f"{p.stem}.md").write_text(to_markdown(r, title=t.title), encoding="utf-8")
            (out_dir / f"{p.stem}.json").write_text(r.model_dump_json(indent=2), encoding="utf-8")
            rows.append((p.name, c.call_type, r.overall_score))
            _eprint(f"✓ {p.name}: {c.call_type} ({round(r.overall_score or 0)})")
        except Exception as e:  # noqa: BLE001
            rows.append((p.name, "ERROR", None))
            _eprint(f"✗ {p.name}: {e}")
    # index
    index = ["# Coaching index\n", "| File | Call type | Overall |", "|---|---|---:|"]
    for name, ct, sc in rows:
        index.append(f"| {name} | {ct} | {round(sc) if sc is not None else '-'} |")
    (out_dir / "index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    _eprint(f"wrote reports to {out_dir}")
    return 0


def cmd_inspect(args) -> int:
    t = load_transcript(args.transcript, adapter=args.adapter)
    t = _apply_participants(t, getattr(args, "participants", None))
    if args.json:
        print(t.model_dump_json(indent=2))
        return 0
    print(f"# {t.title}  (recorder={t.source.get('recorder')}, turns={len(t.turns)})")
    print(f"talk ratio: {t.talk_ratio()}")
    print()
    print(t.as_text())
    return 0


def cmd_list(args) -> int:
    reg = load_registry()
    if args.kind == "frameworks":
        for fw in reg.frameworks.values():
            print(f"{fw.id:28} {fw.name}  ({len(fw.elements)} elements)")
    elif args.kind == "scorecards":
        for sc in reg.scorecards.values():
            print(f"{sc.id:28} {sc.name} v{sc.version}  ({len(sc.criteria)} criteria) -> {', '.join(sc.applies_to)}")
    elif args.kind == "call-types":
        for ct in reg.call_types.values():
            print(f"{ct.id:22} [{ct.phase:10}] {ct.name}  -> {', '.join(ct.scorecards)}")
    elif args.kind == "rubrics":
        for rb in reg.rubrics.values():
            print(f"{rb.id:22} [{rb.kind:14}] {rb.name} v{rb.version}  ({len(rb.dimensions)} dimensions)")
    return 0


def cmd_validate(args) -> int:
    reg = load_registry()
    problems = reg.validate()
    if not problems:
        print(
            f"✓ knowledge base healthy: {len(reg.call_types)} call types, "
            f"{len(reg.scorecards)} scorecards, {len(reg.frameworks)} frameworks, "
            f"{len(reg.outcomes)} outcomes, {len(reg.rubrics)} rubrics"
        )
        return 0
    _eprint(f"✗ {len(problems)} problem(s):")
    for p in problems:
        _eprint(f"  - {p}")
    return 1


def _coach_dir(directory: Path, glob: str, reg, llm, adapter) -> list[tuple[str, object]]:
    """Coach every transcript in a directory; return [(call_id, CoachingReport)]."""
    from .pipeline import classify as run_classify
    from .pipeline import coach as run_coach

    out = []
    for p in sorted(x for x in directory.glob(glob) if x.is_file()):
        try:
            t = load_transcript(str(p), adapter=adapter)
            c = run_classify(t, reg, llm)
            r = run_coach(t, c, reg, llm)
            out.append((p.stem, r))
            _eprint(f"  ✓ {p.name}: {c.call_type} ({round(r.overall_score or 0)})")
        except Exception as e:  # noqa: BLE001
            _eprint(f"  ✗ {p.name}: {e}")
    return out


def _load_reports_dir(directory: Path):
    """Load existing coaching report JSONs from a directory -> [(call_id, report)]."""
    from .models import CoachingReport

    out = []
    for p in sorted(directory.glob("*.json")):
        try:
            data = json.loads(p.read_text())
            if "classification" in data:  # it's a coaching report
                out.append((data.get("call_id") or p.stem, CoachingReport(**data)))
        except Exception:  # noqa: BLE001
            continue
    return out


def cmd_deal(args) -> int:
    from .render import rubric_report_to_markdown
    from .scoring import score_account, score_deal

    reg = load_registry()
    llm = _build_llm(args)
    directory = Path(args.directory)
    _eprint(f"coaching calls in {directory} ...")
    reports = _coach_dir(directory, args.glob, reg, llm, args.adapter)
    if not reports:
        _eprint("no transcripts coached")
        return 1
    subject = {"name": args.name or directory.name, "owner": args.owner, "stage": args.stage,
               "amount": args.amount, "close_or_renewal_date": args.date}
    subject = {k: v for k, v in subject.items() if v is not None}
    scorer = score_account if args.kind == "account" else score_deal
    rep = scorer(reports, reg, llm, subject)
    out = rep.model_dump_json(indent=2) if args.format == "json" else rubric_report_to_markdown(rep)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        _eprint(f"wrote {args.out}")
    else:
        print(out)
    return 0


def cmd_inbox(args) -> int:
    from .inbox import build_inbox
    from .render import inbox_to_markdown

    reg = load_registry()
    base = Path(args.path)
    collected: list[tuple[dict, object]] = []

    def add(reports, rep):
        for cid, r in reports:
            collected.append(({"rep": rep, "call_id": cid}, r))

    subdirs = [d for d in sorted(base.iterdir()) if d.is_dir()] if base.is_dir() else []
    if args.scope in ("team", "company") and subdirs:
        # Each subdirectory is treated as a rep.
        for d in subdirs:
            existing = _load_reports_dir(d)
            if existing:
                add(existing, d.name)
            else:
                llm = _build_llm(args)
                add(_coach_dir(d, args.glob, reg, llm, args.adapter), d.name)
    else:
        existing = _load_reports_dir(base)
        if existing:
            add(existing, args.for_ or base.name)
        else:
            llm = _build_llm(args)
            add(_coach_dir(base, args.glob, reg, llm, args.adapter), args.for_ or base.name)

    if not collected:
        _eprint("no reports/transcripts found")
        return 1
    inbox = build_inbox(collected, scope=args.scope, generated_for=args.for_ or base.name,
                        period=args.period or f"{len(collected)} calls", reg=reg)
    out = inbox.model_dump_json(indent=2) if args.format == "json" else inbox_to_markdown(inbox)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        _eprint(f"wrote {args.out}")
    else:
        print(out)
    return 0


def cmd_crm(args) -> int:
    from .crm import build_crm_patch, get_writer

    reg = load_registry()
    mapping = reg.crm_mapping(args.crm)
    data = json.loads(Path(args.report).read_text())
    # Detect report type.
    if "classification" in data:
        source = "coaching_report"
    elif data.get("kind") == "deal-health":
        source = "deal_report"
    elif data.get("kind") == "account-health":
        source = "account_report"
    else:
        source = args.source or "coaching_report"
    updates = build_crm_patch(mapping, {source: data})
    if not updates:
        _eprint("no CRM fields produced (check the mapping's source/fields)")
        return 1

    import os

    writer_kwargs: dict = {}
    if args.writer == "salesforce":
        writer_kwargs = {
            "instance_url": args.instance_url or os.environ.get("SF_INSTANCE_URL"),
            "access_token": args.access_token or os.environ.get("SF_ACCESS_TOKEN"),
        }
        if not writer_kwargs["instance_url"] or not writer_kwargs["access_token"]:
            _eprint("salesforce writer needs --instance-url and --access-token (or SF_INSTANCE_URL / SF_ACCESS_TOKEN)")
            return 1
    elif args.writer == "hubspot":
        writer_kwargs = {"access_token": args.access_token or os.environ.get("HUBSPOT_ACCESS_TOKEN")}
        if not writer_kwargs["access_token"]:
            _eprint("hubspot writer needs --access-token (or HUBSPOT_ACCESS_TOKEN)")
            return 1
    if args.writer != "dry-run":
        _eprint(f"⚠ writing {len(updates)} record(s) to {args.writer} (live)")
    writer = get_writer(args.writer, **writer_kwargs)
    writer.write(updates)
    return 0


def cmd_crm_stages(args) -> int:
    """Resolve the org's real opportunity stages (and where open pipeline sits)."""
    import os

    if args.crm == "salesforce":
        instance = args.instance_url or os.environ.get("SF_INSTANCE_URL")
        token = args.access_token or os.environ.get("SF_ACCESS_TOKEN")
        if not instance or not token:
            print("Dry run (no Salesforce credentials). Stage discovery WOULD run:\n"
                  "  GET {instance}/services/data/v60.0/query?q=\n"
                  "    SELECT MasterLabel, IsClosed, IsWon, IsActive, SortOrder\n"
                  "    FROM OpportunityStage WHERE IsActive = true ORDER BY SortOrder\n"
                  "  GET .../query?q=\n"
                  "    SELECT StageName, COUNT(Id) cnt, SUM(Amount) amt\n"
                  "    FROM Opportunity WHERE IsClosed = false GROUP BY StageName\n"
                  "Won = IsWon; Lost = IsClosed AND NOT IsWon; Open = NOT IsClosed.\n"
                  "Provide --instance-url/--access-token (or SF_INSTANCE_URL/SF_ACCESS_TOKEN) to run live.")
            return 0
        from .crm import fetch_salesforce_stages

        resolved = fetch_salesforce_stages(instance, token)
    elif args.crm == "hubspot":
        token = args.access_token or os.environ.get("HUBSPOT_ACCESS_TOKEN")
        if not token:
            print("Dry run (no HubSpot token). Stage discovery WOULD run:\n"
                  "  GET https://api.hubapi.com/crm/v3/pipelines/deals  (pipelines[].stages[])\n"
                  "  POST /crm/v3/objects/deals/search per stage  (where deals sit)\n"
                  "Won = metadata.probability == 1.0; Lost = closed & 0.0; Open = not isClosed.\n"
                  "Provide --access-token (or HUBSPOT_ACCESS_TOKEN) to run live.")
            return 0
        from .crm import fetch_hubspot_stages

        resolved = fetch_hubspot_stages(token)
    else:
        _eprint(f"unknown crm '{args.crm}'")
        return 1

    if args.format == "json":
        print(json.dumps(resolved.to_dict(), indent=2))
        return 0
    print(f"# {args.crm} stages")
    print(f"Won:  {', '.join(resolved.won) or '(none found)'}")
    print(f"Lost: {', '.join(resolved.lost) or '(none found)'}")
    print(f"Open: {', '.join(resolved.open) or '(none found)'}")
    busy = resolved.busiest_open_stages()
    if busy:
        print("Where open opportunities sit:")
        for s in busy:
            amt = f" (${s.open_amount:,.0f})" if s.open_amount else ""
            print(f"  {s.label}: {s.open_count} open{amt}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gtmsi", description="Open-source, Claude-native sales coaching for any call transcript.")
    p.add_argument("--version", action="version", version=f"gtmsi {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    wb = sub.add_parser("workbench", help="run the local sales analysis workbench")
    wb.add_argument("--host", default="127.0.0.1")
    wb.add_argument("--port", type=int, default=8765)
    wb.set_defaults(func=cmd_workbench)

    def add_common(sp):
        sp.add_argument("--adapter", choices=sorted(ADAPTERS_BY_NAME), help="force a transcript adapter")
        sp.add_argument("--provider", choices=["deepseek", "anthropic"], help="LLM provider (default: GTMSI_LLM_PROVIDER or deepseek)")
        sp.add_argument("--model", help="model id (default: GTMSI_MODEL, or provider default)")
        sp.add_argument("--no-attribution", action="store_true",
                        help="omit the 'powered by' footer from rendered output (or set GTMSI_NO_ATTRIBUTION=1)")

    def add_participants(sp):
        sp.add_argument(
            "--participants",
            help='JSON (or path) mapping speaker -> side, e.g. \'{"Alex":"rep","Sam":"prospect"}\'',
        )

    c = sub.add_parser("coach", help="classify + coach one call")
    c.add_argument("transcript")
    add_common(c)
    add_participants(c)
    c.add_argument("--redact", action="store_true", help="mask obvious PII before sending to the model")
    c.add_argument("--format", choices=["md", "json", "text"], default="md")
    c.add_argument("--out", help="write to a file instead of stdout")
    c.set_defaults(func=cmd_coach)

    cl = sub.add_parser("classify", help="classify the call type only")
    cl.add_argument("transcript")
    add_common(cl)
    add_participants(cl)
    cl.add_argument("--json", action="store_true")
    cl.set_defaults(func=cmd_classify)

    b = sub.add_parser("bulk", help="coach every transcript in a directory")
    b.add_argument("directory")
    add_common(b)
    b.add_argument("--glob", default="*", help="filename glob (default: *)")
    b.add_argument("--out", help="output directory (default: <dir>/coaching)")
    b.set_defaults(func=cmd_bulk)

    ins = sub.add_parser("inspect", help="show the normalized transcript (debug adapters)")
    ins.add_argument("transcript")
    ins.add_argument("--adapter", choices=sorted(ADAPTERS_BY_NAME))
    add_participants(ins)
    ins.add_argument("--json", action="store_true")
    ins.set_defaults(func=cmd_inspect)

    ls = sub.add_parser("list", help="list frameworks | scorecards | call-types | rubrics")
    ls.add_argument("kind", choices=["frameworks", "scorecards", "call-types", "rubrics"])
    ls.set_defaults(func=cmd_list)

    v = sub.add_parser("validate", help="check the YAML knowledge base for problems")
    v.set_defaults(func=cmd_validate)

    # Deal / opportunity health (sales): coach a folder of one deal's calls, then score.
    d = sub.add_parser("deal", help="score an opportunity's health across its calls")
    d.add_argument("directory", help="folder of transcripts for ONE opportunity")
    add_common(d)
    d.add_argument("--name", help="deal/opportunity name")
    d.add_argument("--owner", help="rep who owns it")
    d.add_argument("--stage", help="CRM stage")
    d.add_argument("--amount", type=float, help="deal amount")
    d.add_argument("--date", help="close date")
    d.add_argument("--glob", default="*", help="filename glob (default: *)")
    d.add_argument("--format", choices=["md", "json"], default="md")
    d.add_argument("--out", help="write to a file instead of stdout")
    d.set_defaults(func=cmd_deal, kind="deal")

    # Account health (CSM): same shape, account rubric.
    ac = sub.add_parser("account", help="score a customer account's health across its calls")
    ac.add_argument("directory", help="folder of post-sales transcripts for ONE account")
    add_common(ac)
    ac.add_argument("--name", help="account name")
    ac.add_argument("--owner", help="CSM who owns it")
    ac.add_argument("--stage", help="lifecycle stage")
    ac.add_argument("--amount", type=float, help="ARR / contract value")
    ac.add_argument("--date", help="renewal date")
    ac.add_argument("--glob", default="*", help="filename glob (default: *)")
    ac.add_argument("--format", choices=["md", "json"], default="md")
    ac.add_argument("--out", help="write to a file instead of stdout")
    ac.set_defaults(func=cmd_deal, kind="account")

    # Inbox: rep / team / company "what to improve" roll-up.
    ib = sub.add_parser("inbox", help="build a rep/team/company coaching inbox")
    ib.add_argument("path", help="a folder of transcripts or coaching-report JSONs (subfolders = reps for team/company)")
    add_common(ib)
    ib.add_argument("--scope", choices=["rep", "team", "company"], default="rep")
    ib.add_argument("--for", dest="for_", help="rep/team/company name")
    ib.add_argument("--period", help="label for the period (e.g. 'last 7 days')")
    ib.add_argument("--glob", default="*", help="filename glob (default: *)")
    ib.add_argument("--format", choices=["md", "json"], default="md")
    ib.add_argument("--out", help="write to a file instead of stdout")
    ib.set_defaults(func=cmd_inbox)

    # CRM auto-fill: map a report to CRM fields (dry-run by default).
    cr = sub.add_parser("crm", help="map a report to CRM fields and (optionally) write them")
    cr.add_argument("report", help="a coaching/deal/account report JSON")
    cr.add_argument("--crm", default="generic", help="CRM mapping name (config/crm/<crm>.yaml)")
    cr.add_argument("--writer", default="dry-run", help="dry-run (default) | salesforce | hubspot")
    cr.add_argument("--source", choices=["coaching_report", "deal_report", "account_report"], help="override source detection")
    cr.add_argument("--instance-url", help="Salesforce instance URL (or env SF_INSTANCE_URL)")
    cr.add_argument("--access-token", help="CRM API token for live writes (or env SF_ACCESS_TOKEN / HUBSPOT_ACCESS_TOKEN)")
    cr.set_defaults(func=cmd_crm)

    # CRM stage discovery: resolve the org's real won/lost/open stages + where opps sit.
    cs = sub.add_parser("crm-stages", help="resolve the org's real CRM opportunity stages (and where pipeline sits)")
    cs.add_argument("--crm", default="salesforce", choices=["salesforce", "hubspot"])
    cs.add_argument("--instance-url", help="Salesforce instance URL (or env SF_INSTANCE_URL)")
    cs.add_argument("--access-token", help="API token (or env SF_ACCESS_TOKEN / HUBSPOT_ACCESS_TOKEN)")
    cs.add_argument("--format", choices=["text", "json"], default="text")
    cs.set_defaults(func=cmd_crm_stages)

    # Share card: a paste-ready "post your score" snippet for LinkedIn/X.
    sh = sub.add_parser("share", help="render a paste-ready share card from a report JSON")
    sh.add_argument("report", help="a coaching/deal/account report JSON")
    sh.add_argument("--title", help="title for the card")
    sh.set_defaults(func=cmd_share)

    # Demo: print the tracked Attention demo link (no data collected).
    dm = sub.add_parser("demo", help="print the Attention demo booking link (tracked)")
    dm.set_defaults(func=cmd_demo)

    # Telemetry: opt-in, off by default.
    tel = sub.add_parser("telemetry", help="anonymous usage stats (opt-in, off by default)")
    tel.add_argument("action", choices=["status", "enable", "disable"], nargs="?", default="status")
    tel.set_defaults(func=cmd_telemetry)

    return p


def cmd_share(args) -> int:
    from .models import CoachingReport, RubricReport
    from .render import to_share_card

    data = json.loads(Path(args.report).read_text())
    report = CoachingReport(**data) if "classification" in data else RubricReport(**data)
    print(to_share_card(report, title=args.title))
    return 0


def cmd_demo(args) -> int:
    """Print the tracked Attention demo link. (No data is collected here — for a guided,
    consent-based booking flow, use the `book-attention-demo` skill inside Claude.)"""
    from .attribution import demo_link

    print("See GTM Superintelligence on your own calls with clean, role- & CRM-labeled")
    print("transcripts. Book a 15-min Attention demo:")
    print(f"  {demo_link(content='cli')}")
    print("\nInside Claude Code, `/book-attention-demo` will walk you through it.")
    return 0


def cmd_telemetry(args) -> int:
    from . import telemetry

    if args.action == "enable":
        telemetry.enable()
        print("✓ anonymous usage stats enabled. Disable any time: `gtmsi telemetry disable`.")
    elif args.action == "disable":
        telemetry.disable()
        print("✓ anonymous usage stats disabled.")
    else:
        print(f"telemetry: {telemetry.status()} (opt-in; never sends transcript content — see docs/telemetry.md)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # Opt-out of the output footer for this run if requested.
    if getattr(args, "no_attribution", False):
        os.environ["GTMSI_NO_ATTRIBUTION"] = "1"
    from . import telemetry

    telemetry.maybe_first_run_notice(_eprint)
    telemetry.record("command", name=getattr(args, "cmd", None))
    try:
        return args.func(args)
    except KeyboardInterrupt:  # pragma: no cover
        return 130
    except Exception as e:  # noqa: BLE001
        _eprint(f"error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
