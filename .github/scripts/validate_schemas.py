#!/usr/bin/env python3
"""Validate every YAML content file against its JSON Schema.

Independent of the pydantic models — this checks the language-agnostic contract in
``schemas/`` directly, so a broken schema or a malformed YAML fails CI loudly.
Run from the repo root: ``python .github/scripts/validate_schemas.py``
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent.parent


def load_schema(name: str) -> dict:
    return json.loads((ROOT / "schemas" / name).read_text())


def validate_glob(pattern: str, schema_name: str, errors: list[str]) -> int:
    schema = load_schema(schema_name)
    validator = Draft202012Validator(schema)
    count = 0
    for f in sorted(ROOT.glob(pattern)):
        data = yaml.safe_load(f.read_text())
        for err in validator.iter_errors(data):
            loc = "/".join(str(p) for p in err.path)
            errors.append(f"{f.relative_to(ROOT)} :: {loc}: {err.message}")
        count += 1
    return count


def _check(data, schema_name: str, label: str, errors: list[str]) -> None:
    for err in Draft202012Validator(load_schema(schema_name)).iter_errors(data):
        loc = "/".join(str(p) for p in err.path)
        errors.append(f"{label} :: {loc}: {err.message}")


def main() -> int:
    errors: list[str] = []
    n = 0
    n += validate_glob("frameworks/*.yaml", "framework.schema.json", errors)
    n += validate_glob("scorecards/*.yaml", "scorecard.schema.json", errors)
    n += validate_glob("rubrics/*.yaml", "rubric.schema.json", errors)
    n += validate_glob("config/crm/*.yaml", "crm_mapping.schema.json", errors)

    # Single-document configs.
    _check(yaml.safe_load((ROOT / "config/call_types.yaml").read_text()), "call_type.schema.json", "config/call_types.yaml", errors)
    n += 1

    # Example transcripts must conform to the transcript schema (JSON ones).
    for f in sorted(ROOT.glob("examples/transcripts/*.json")):
        _check(json.loads(f.read_text()), "transcript.schema.json", str(f.relative_to(ROOT)), errors)
        n += 1

    # Example reports: route to the right schema by content.
    for f in sorted(ROOT.glob("examples/reports/**/*.json")):
        data = json.loads(f.read_text())
        if "classification" in data:
            schema = "coaching_report.schema.json"
        elif data.get("kind") in ("deal-health", "account-health"):
            schema = "rubric_report.schema.json"
        elif "focus_areas" in data or data.get("scope") in ("rep", "team", "company"):
            schema = "inbox.schema.json"
        else:
            errors.append(f"{f.relative_to(ROOT)} :: could not determine report type")
            n += 1
            continue
        _check(data, schema, str(f.relative_to(ROOT)), errors)
        n += 1

    if errors:
        print(f"✗ {len(errors)} schema violation(s) across {n} file(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"✓ all {n} content files conform to their JSON Schemas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
