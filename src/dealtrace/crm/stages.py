"""Resolve a CRM's REAL opportunity/deal stages from the org's own data.

Stage names are org-specific ("Closed Won" vs "Closed - Won" vs "7. Won"), so agents
must never hardcode a label. This module:

  1. Lists the org's actual stages with their semantics (won / lost / open).
  2. Finds *where the opportunities actually sit* (count + amount per open stage), so an
     agent understands the org's real pipeline shape, not an assumed one.

The classification (`classify_*`) is pure and unit-tested; the `fetch_*` helpers add
the HTTP calls (need credentials + ``requests``). Verified against the Salesforce REST
API (OpportunityStage object) and the HubSpot CRM Pipelines API.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StageInfo:
    label: str          # the human label, e.g. "Closed Won"
    value: str | None = None   # API value / id (HubSpot stage id; SF label == value)
    is_closed: bool = False
    is_won: bool = False
    order: float | None = None
    open_count: int | None = None      # how many open opps sit here (where they lie)
    open_amount: float | None = None
    pipeline: str | None = None        # HubSpot: which pipeline this stage belongs to


@dataclass
class ResolvedStages:
    crm: str
    stages: list[StageInfo] = field(default_factory=list)

    @property
    def won(self) -> list[str]:
        return [s.label for s in self.stages if s.is_won]

    @property
    def lost(self) -> list[str]:
        return [s.label for s in self.stages if s.is_closed and not s.is_won]

    @property
    def open(self) -> list[str]:
        return [s.label for s in self.stages if not s.is_closed]

    def busiest_open_stages(self, n: int = 3) -> list[StageInfo]:
        ranked = [s for s in self.stages if not s.is_closed and (s.open_count or 0) > 0]
        # Rank by open count, then by open amount (the more meaningful tiebreaker).
        return sorted(ranked, key=lambda s: (s.open_count or 0, s.open_amount or 0), reverse=True)[:n]

    def to_dict(self) -> dict[str, Any]:
        return {
            "crm": self.crm,
            "won": self.won,
            "lost": self.lost,
            "open": self.open,
            "stages": [s.__dict__ for s in self.stages],
        }


# --------------------------------------------------------------------------- Salesforce
def classify_salesforce_stages(
    stage_rows: list[dict], open_distribution: list[dict] | None = None
) -> ResolvedStages:
    """Classify rows from ``SELECT MasterLabel, IsClosed, IsWon, IsActive, SortOrder
    FROM OpportunityStage WHERE IsActive = true ORDER BY SortOrder``.

    ``open_distribution`` (optional) is rows from a GROUP BY aggregate like
    ``SELECT StageName, COUNT(Id) cnt, SUM(Amount) amt FROM Opportunity
    WHERE IsClosed = false GROUP BY StageName`` to record where open opps sit.
    """
    dist = {}
    for r in open_distribution or []:
        label = r.get("StageName") or r.get("label")
        dist[label] = (r.get("cnt", r.get("expr0")), r.get("amt", r.get("expr1")))
    out = ResolvedStages(crm="salesforce")
    for r in stage_rows:
        label = r.get("MasterLabel") or r.get("label") or r.get("ApiName")
        cnt, amt = dist.get(label, (None, None))
        out.stages.append(
            StageInfo(
                label=label,
                value=label,
                is_closed=bool(r.get("IsClosed")),
                is_won=bool(r.get("IsWon")),
                order=r.get("SortOrder"),
                open_count=cnt,
                open_amount=amt,
            )
        )
    return out


def fetch_salesforce_stages(instance_url: str, access_token: str, api_version: str = "v60.0") -> ResolvedStages:
    import requests

    base = f"{instance_url.rstrip('/')}/services/data/{api_version}"
    headers = {"Authorization": f"Bearer {access_token}"}
    stages_q = "SELECT MasterLabel, IsClosed, IsWon, IsActive, SortOrder FROM OpportunityStage WHERE IsActive = true ORDER BY SortOrder"
    rows = requests.get(f"{base}/query", headers=headers, params={"q": stages_q}, timeout=30).json().get("records", [])
    dist_q = "SELECT StageName, COUNT(Id) cnt, SUM(Amount) amt FROM Opportunity WHERE IsClosed = false GROUP BY StageName"
    dist = requests.get(f"{base}/query", headers=headers, params={"q": dist_q}, timeout=30).json().get("records", [])
    return classify_salesforce_stages(rows, dist)


# --------------------------------------------------------------------------- HubSpot
def classify_hubspot_pipelines(
    pipelines: list[dict], stage_counts: dict[str, int] | None = None
) -> ResolvedStages:
    """Classify HubSpot ``GET /crm/v3/pipelines/deals`` → ``results[].stages[]``.
    A stage is won if ``metadata.probability == 1.0``, lost if closed with probability
    0.0. ``stage_counts`` maps stage id -> open deal count (where deals lie)."""
    counts = stage_counts or {}
    out = ResolvedStages(crm="hubspot")
    for p in pipelines:
        pname = p.get("label")
        for s in p.get("stages", []):
            meta = s.get("metadata") or {}
            prob = meta.get("probability")
            try:
                prob = float(prob) if prob is not None else None
            except (TypeError, ValueError):
                prob = None
            # Trust the authoritative `isClosed` flag when present (an open early-funnel
            # stage commonly has probability 0.0 — that must NOT be read as Closed-Lost).
            closed_flag = meta.get("isClosed")
            if closed_flag is not None:
                is_closed = str(closed_flag).lower() == "true"
            else:
                is_closed = prob in (0.0, 1.0)
            is_won = is_closed and prob == 1.0
            out.stages.append(
                StageInfo(
                    label=s.get("label"),
                    value=s.get("id"),
                    is_closed=is_closed,
                    is_won=is_won,
                    order=s.get("displayOrder"),
                    open_count=counts.get(s.get("id")),
                    pipeline=pname,
                )
            )
    return out


def fetch_hubspot_stages(access_token: str) -> ResolvedStages:
    import requests

    headers = {"Authorization": f"Bearer {access_token}"}
    pipes = requests.get("https://api.hubapi.com/crm/v3/pipelines/deals", headers=headers, timeout=30).json().get("results", [])
    resolved = classify_hubspot_pipelines(pipes)
    # Where deals lie: one search per open stage (HubSpot search returns `total`).
    counts: dict[str, int] = {}
    for s in resolved.stages:
        if s.is_closed:
            continue
        body = {"filterGroups": [{"filters": [{"propertyName": "dealstage", "operator": "EQ", "value": s.value}]}], "limit": 1}
        resp = requests.post("https://api.hubapi.com/crm/v3/objects/deals/search", headers=headers, json=body, timeout=30)
        counts[s.value] = resp.json().get("total", 0) if resp.ok else None
    for s in resolved.stages:
        s.open_count = counts.get(s.value, s.open_count)
    return resolved
