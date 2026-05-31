"""Turn a GTM Superintelligence report into CRM field updates using a declarative mapping
(config/crm/<crm>.yaml, schema: crm_mapping). Vendor-neutral: the mapping is data,
the writer is pluggable.

The output is a list of :class:`CRMUpdate` "patches" — by default nothing is sent
anywhere; a writer (generic/salesforce/hubspot) decides what to do with them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_TEMPLATE = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")

# Keys used to label a list element when a path selects it by name, and to stringify
# list items for join_lines.
_NAME_KEYS = ("id", "dimension_id", "criterion_id")
_STR_KEYS = ("title", "action", "statement", "text", "name")


@dataclass
class CRMUpdate:
    crm: str
    object: str
    record_id: str | None
    fields: dict[str, Any] = field(default_factory=dict)
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"crm": self.crm, "object": self.object, "record_id": self.record_id, "fields": self.fields}


def resolve_path(obj: Any, path: str) -> Any:
    """Navigate a dotted path into nested dicts/lists. For a list, a numeric segment
    indexes it; a non-numeric segment selects the element whose id/dimension_id/
    criterion_id matches (so 'dimensions.pain_and_impact.rationale' works)."""
    cur = obj
    for seg in path.split("."):
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(seg)
        elif isinstance(cur, list):
            if seg.isdigit():
                idx = int(seg)
                cur = cur[idx] if 0 <= idx < len(cur) else None
            else:
                match = None
                for el in cur:
                    if isinstance(el, dict) and any(el.get(k) == seg for k in _NAME_KEYS):
                        match = el
                        break
                cur = match
        else:
            return None
    return cur


def _stringify_item(item: Any) -> str:
    if isinstance(item, dict):
        for k in _STR_KEYS:
            if item.get(k):
                return str(item[k])
        return str(item)
    return str(item)


def _apply_transform(value: Any, transform: str) -> Any:
    if value is None:
        return None
    if transform == "round":
        try:
            return round(float(value))
        except (TypeError, ValueError):
            return value
    if transform == "percent":
        try:
            return f"{round(float(value) * 100)}%"
        except (TypeError, ValueError):
            return value
    if transform == "title_case":
        return str(value).replace("-", " ").replace("_", " ").title()
    if transform == "first":
        if isinstance(value, list) and value:
            return _stringify_item(value[0])
        return value
    if transform == "join_lines":
        if isinstance(value, list):
            return "\n".join(f"- {_stringify_item(v)}" for v in value)
        return str(value)
    return value


def _render(spec: str, report: dict[str, Any]) -> Any:
    """If spec is a {{template}}, interpolate paths; else treat spec as a single path."""
    if "{{" in spec:
        def sub(m):
            v = resolve_path(report, m.group(1))
            return "" if v is None else (_stringify_item(v) if isinstance(v, (dict, list)) else str(v))
        return _TEMPLATE.sub(sub, spec)
    return resolve_path(report, spec)


def build_crm_patch(mapping: dict, reports: dict[str, dict]) -> list[CRMUpdate]:
    """Build CRM updates.

    Args:
        mapping: a loaded crm mapping dict (config/crm/<crm>.yaml).
        reports: available reports keyed by source name, e.g.
            ``{"coaching_report": {...}, "deal_report": {...}, "account_report": {...}}``.
    """
    crm = mapping.get("crm", "generic")
    updates: list[CRMUpdate] = []
    for obj in mapping.get("objects", []):
        source = obj["source"]
        report = reports.get(source)
        if report is None:
            continue  # that report wasn't supplied this run
        record_id = resolve_path(report, obj["id_field"]) if obj.get("id_field") else None
        out_fields: dict[str, Any] = {}
        for f in obj.get("fields", []):
            value = _render(f["from"], report)
            value = _apply_transform(value, f.get("transform", "none"))
            when_empty = f.get("when_empty", "skip")
            if value in (None, ""):
                if when_empty == "skip":
                    continue
                value = None if when_empty == "null" else ""
            out_fields[f["crm_field"]] = value
        if out_fields:
            updates.append(CRMUpdate(crm=crm, object=obj["object"], record_id=record_id, fields=out_fields, source=source))
    return updates
