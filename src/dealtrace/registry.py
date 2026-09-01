"""Loads and validates the YAML knowledge base: call types, outcomes, frameworks,
and scorecards. Everything the coach reasons over lives in editable YAML so any
business can fork and tune it without touching code.
"""
from __future__ import annotations

import functools

# Repo root resolves to the package's grandparent (src/dealtrace -> src -> repo).
# When installed, GTMSI_HOME can point at a custom content directory.
import os
from pathlib import Path

import yaml

from .models import CallType, Framework, Outcome, Scorecard

_PKG_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PKG_DIR.parent.parent


def _looks_like_content(p: Path) -> bool:
    return (p / "frameworks").is_dir() and (p / "config" / "call_types.yaml").is_file()


def content_root() -> Path:
    """Locate the editable YAML knowledge base.

    Resolution order:
      1. ``GTMSI_HOME`` environment variable.
      2. The repo root inferred from this file's location (the common case when
         running from a clone or editable install).
      3. Walk up from the current working directory looking for the content dirs.
    """
    env = os.environ.get("GTMSI_HOME")
    if env:
        return Path(env).expanduser().resolve()
    if _looks_like_content(_REPO_ROOT):
        return _REPO_ROOT
    for parent in [Path.cwd(), *Path.cwd().parents]:
        if _looks_like_content(parent):
            return parent
    return _REPO_ROOT


class Registry:
    """In-memory index of all coaching content, loaded from a content root."""

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else content_root()
        self.frameworks: dict[str, Framework] = {}
        self.scorecards: dict[str, Scorecard] = {}
        self.call_types: dict[str, CallType] = {}
        self.outcomes: dict[str, Outcome] = {}
        self._load()

    # ------------------------------------------------------------------ loading
    def _load(self) -> None:
        self._load_frameworks()
        self._load_scorecards()
        self._load_call_types()
        self._load_outcomes()

    def _load_frameworks(self) -> None:
        for f in sorted((self.root / "frameworks").glob("*.yaml")):
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            fw = Framework(**data)
            self.frameworks[fw.id] = fw

    def _load_scorecards(self) -> None:
        for f in sorted((self.root / "scorecards").glob("*.yaml")):
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            sc = Scorecard(**data)
            self.scorecards[sc.id] = sc

    def _load_call_types(self) -> None:
        data = yaml.safe_load((self.root / "config" / "call_types.yaml").read_text(encoding="utf-8"))
        for ct in data["call_types"]:
            obj = CallType(**ct)
            self.call_types[obj.id] = obj

    def _load_outcomes(self) -> None:
        data = yaml.safe_load((self.root / "config" / "outcomes.yaml").read_text(encoding="utf-8"))
        for o in data["outcomes"]:
            obj = Outcome(**o)
            self.outcomes[obj.id] = obj

    # ------------------------------------------------------------------ lookups
    def scorecard_for(self, call_type_id: str) -> Scorecard | None:
        ct = self.call_types.get(call_type_id)
        if not ct or not ct.scorecards:
            return None
        return self.scorecards.get(ct.scorecards[0])

    def frameworks_for_scorecard(self, sc: Scorecard) -> list[Framework]:
        return [self.frameworks[fid] for fid in sc.frameworks if fid in self.frameworks]

    def default_outcomes_for(self, call_type_id: str) -> list[Outcome]:
        ct = self.call_types.get(call_type_id)
        if not ct:
            return []
        return [self.outcomes[o] for o in ct.default_outcomes if o in self.outcomes]

    # --------------------------------------------------------------- validation
    def validate(self) -> list[str]:
        """Cross-reference integrity check. Returns a list of human-readable problems
        (empty list == healthy)."""
        problems: list[str] = []

        # Every call type points at scorecards that exist.
        for ct in self.call_types.values():
            for sid in ct.scorecards:
                if sid not in self.scorecards:
                    problems.append(f"call_type '{ct.id}' references missing scorecard '{sid}'")
            for oid in ct.default_outcomes:
                if oid not in self.outcomes:
                    problems.append(f"call_type '{ct.id}' references missing outcome '{oid}'")

        # Every scorecard applies_to real call types and cites real frameworks.
        for sc in self.scorecards.values():
            for cid in sc.applies_to:
                if cid not in self.call_types:
                    problems.append(f"scorecard '{sc.id}' applies_to unknown call_type '{cid}'")
            for fid in sc.frameworks:
                if fid not in self.frameworks:
                    problems.append(f"scorecard '{sc.id}' references missing framework '{fid}'")
            # framework_refs resolve to framework.element
            for crit in sc.criteria:
                for ref in crit.framework_refs:
                    if "." not in ref:
                        problems.append(
                            f"scorecard '{sc.id}'.{crit.id}: framework_ref '{ref}' is not 'framework.element'"
                        )
                        continue
                    fwid, elid = ref.split(".", 1)
                    fw = self.frameworks.get(fwid)
                    if not fw:
                        problems.append(
                            f"scorecard '{sc.id}'.{crit.id}: framework_ref '{ref}' -> unknown framework '{fwid}'"
                        )
                    elif elid not in {e.id for e in fw.elements}:
                        problems.append(
                            f"scorecard '{sc.id}'.{crit.id}: framework_ref '{ref}' -> '{fwid}' has no element '{elid}'"
                        )

        # Every call type has at least one scorecard available.
        for ct in self.call_types.values():
            if not self.scorecard_for(ct.id):
                problems.append(f"call_type '{ct.id}' has no resolvable scorecard")

        return problems


@functools.lru_cache(maxsize=4)
def load_registry(root: str | None = None) -> Registry:
    return Registry(Path(root) if root else None)
