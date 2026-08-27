"""CRM writers. A writer takes the CRMUpdate patches and applies them.

The default :class:`DryRunWriter` prints the patch and sends nothing — safe by
default. :class:`SalesforceWriter` and :class:`HubSpotWriter` show how to wire real
writeback; they need credentials and ``requests`` (kept optional). Implement the same
tiny interface (``write(updates) -> list[dict]``) for any other CRM.
"""
from __future__ import annotations

import json
from typing import Protocol

from .mapping import CRMUpdate


class CRMWriter(Protocol):
    def write(self, updates: list[CRMUpdate]) -> list[dict]: ...


class DryRunWriter:
    """Prints the CRM patch as JSON and returns it. No network calls. Default."""

    name = "dry-run"

    def write(self, updates: list[CRMUpdate]) -> list[dict]:
        payload = [u.to_dict() for u in updates]
        print(json.dumps(payload, indent=2))
        return payload


class SalesforceWriter:
    """Create or update Salesforce records via the REST API (verified against the
    Salesforce REST API guide, sObject Rows resource).

    Needs ``instance_url`` and an OAuth ``access_token``. ``instance_url`` comes from
    the OAuth token response. Update (record id present): ``PATCH
    /services/data/vXX.X/sobjects/<Object>/<Id>`` → HTTP 204. Create (no id):
    ``POST /services/data/vXX.X/sobjects/<Object>`` → HTTP 201 with the new id.
    """

    name = "salesforce"

    def __init__(self, instance_url: str, access_token: str, api_version: str = "v60.0"):
        self.base = f"{instance_url.rstrip('/')}/services/data/{api_version}/sobjects"
        self.token = access_token

    def write(self, updates: list[CRMUpdate]) -> list[dict]:
        import requests  # optional dependency

        results = []
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        for u in updates:
            if u.record_id:
                resp = requests.patch(
                    f"{self.base}/{u.object}/{u.record_id}", headers=headers, json=u.fields, timeout=30
                )
                results.append({"object": u.object, "id": u.record_id, "op": "update", "status": resp.status_code})
            else:
                resp = requests.post(f"{self.base}/{u.object}", headers=headers, json=u.fields, timeout=30)
                new_id = resp.json().get("id") if resp.ok else None
                results.append({"object": u.object, "id": new_id, "op": "create", "status": resp.status_code})
        return results


class HubSpotWriter:
    """Create or update HubSpot CRM objects via the v3 API. Needs a private-app token
    (verified against the HubSpot CRM Objects API).

    Update: ``PATCH /crm/v3/objects/<object>/<id>`` with ``{"properties": {...}}`` → 200.
    Create (no id): ``POST /crm/v3/objects/<object>`` → 201. Notes are create-only and
    require ``hs_timestamp``; we inject it (current time) if the mapping didn't supply
    one. Linking a note to a deal/company needs the Associations API — see docs/crm.md.
    """

    name = "hubspot"

    def __init__(self, access_token: str):
        self.token = access_token
        self.base = "https://api.hubapi.com/crm/v3/objects"

    def write(self, updates: list[CRMUpdate]) -> list[dict]:
        import datetime

        import requests  # optional dependency

        results = []
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        for u in updates:
            props = dict(u.fields)
            if u.object == "notes" and "hs_timestamp" not in props:
                props["hs_timestamp"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if u.record_id and u.object != "notes":
                resp = requests.patch(
                    f"{self.base}/{u.object}/{u.record_id}", headers=headers, json={"properties": props}, timeout=30
                )
                results.append({"object": u.object, "id": u.record_id, "op": "update", "status": resp.status_code})
            else:
                resp = requests.post(f"{self.base}/{u.object}", headers=headers, json={"properties": props}, timeout=30)
                new_id = resp.json().get("id") if resp.ok else None
                results.append({"object": u.object, "id": new_id, "op": "create", "status": resp.status_code})
        return results


def get_writer(name: str, **kwargs) -> CRMWriter:
    if name in ("dry-run", "dryrun", "none"):
        return DryRunWriter()
    if name == "salesforce":
        return SalesforceWriter(**kwargs)
    if name == "hubspot":
        return HubSpotWriter(**kwargs)
    raise ValueError(f"Unknown CRM writer '{name}'")
