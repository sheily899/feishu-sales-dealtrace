# CRM auto-fill (any CRM)

GTM Superintelligence can write coaching results — call scores, deal health, account health
— back to your CRM automatically. The design is deliberately vendor-neutral:

- **The mapping is data.** A YAML file (`config/crm/<crm>.yaml`) declares which
  report fields map to which CRM field API names. No code changes are needed to
  support a new CRM.
- **The writer is pluggable.** A writer takes the resolved field patches and
  decides what to do with them. The default writer is a dry-run that prints the
  patch and sends nothing. Salesforce and HubSpot writers are included; any CRM
  with a REST endpoint can be supported with a few lines of Python.
- **Create or update.** Each writer inspects the resolved record id: if an id is
  present it **updates** (PATCH); if the id is absent it **creates** (POST) and
  returns the new id. The `id_field` path on the mapping object decides which
  branch runs.
- **Dry-run is the default.** Nothing is sent to your CRM unless you explicitly
  pass a credentialed `--writer`.

---

## The mapping file

Mapping files live in `config/crm/` and conform to `schemas/crm_mapping.schema.json`.
Each file targets one CRM and lists one or more **objects** (CRM record types)
to write to.

### Structure

```yaml
crm: salesforce          # identifier used by --crm flag
description: "..."

objects:
  - source: coaching_report    # which GTM Superintelligence report to read from
    object: Task               # CRM object / API name
    id_field: metadata.salesforce_task_id   # dotted path to the record id
    fields:
      - crm_field: GTMSI_Score__c
        from: overall_score
        transform: round
      - crm_field: Subject
        from: "GTM Superintelligence: {{classification.call_type}} ({{overall_score}})"
```

### `source` values

| Source | Report it reads |
|---|---|
| `coaching_report` | A single per-call coaching report |
| `deal_report` | A deal health report (from `gtmsi deal`) |
| `account_report` | An account health report (from `gtmsi account`) |

### `from` path syntax

`from` is either a **dotted path** into the report JSON or a **`{{template}}`**
string that interpolates multiple paths.

**Dotted paths** navigate nested dicts and lists:

| Example path | Resolves to |
|---|---|
| `overall_score` | The numeric overall score |
| `classification.call_type` | e.g. `"discovery"` |
| `band` | e.g. `"at-risk"` |
| `risk` | e.g. `"medium"` |
| `summary` | The 2–4 sentence manager summary |
| `dimensions.pain_and_impact.rationale` | Rationale for a named dimension |
| `dimensions.economic_buyer.rationale` | Rationale for another dimension |
| `coaching.next_call_focus` | Next-call focus list from a coaching report |
| `risks` | The full risks array |
| `recommended_actions` | The full recommended actions array |
| `subject.id` | The deal/account CRM record id |

For list segments, a non-numeric key selects the element whose `id`,
`dimension_id`, or `criterion_id` matches (so
`dimensions.pain_and_impact.rationale` works even though `dimensions` is an
array).

**Templates** interpolate any number of paths:

```yaml
from: "GTM Superintelligence: {{classification.call_type}} ({{overall_score}}): {{summary}}"
```

### `transform` options

| Transform | Effect |
|---|---|
| `none` (default) | Pass through as-is |
| `round` | Round a float to the nearest integer |
| `title_case` | Convert `"at-risk"` → `"At Risk"` |
| `join_lines` | Convert a list to bullet lines (`- item\n- item`) |
| `first` | Take only the first element of a list |
| `percent` | Multiply by 100 and append `%` |

### `when_empty` options

| Value | Effect when source path is missing or null |
|---|---|
| `skip` (default) | Omit the field from the patch entirely |
| `blank` | Write an empty string |
| `null` | Write null |

### `id_field`

`id_field` is a dotted path into the report that holds the CRM record id to
update (e.g. `subject.id` for deal/account reports, or
`metadata.salesforce_task_id` for per-call tasks). If the path resolves to
null, that object's update is skipped with a `"skipped": "no record_id"` entry
in the result.

---

## CLI

### Dry run (default — nothing is sent)

```bash
gtmsi crm report.json --crm salesforce
```

Prints the JSON patch that *would* be sent. Safe to run at any time.

Example dry-run output for a deal report with the Salesforce mapping:

```json
[
  {
    "crm": "salesforce",
    "object": "Opportunity",
    "record_id": "006Hu00000AbCdEFGH",
    "fields": {
      "GTMSI_Deal_Health__c": 49,
      "GTMSI_Deal_Band__c": "At Risk",
      "GTMSI_Deal_Risk__c": "Medium",
      "GTMSI_Deal_Summary__c": "Early but real: strong, quantified pain ...",
      "GTMSI_Top_Risks__c": "- Single-threaded on one contact\n- No next step on the calendar",
      "MEDDPICC_Economic_Buyer__c": "Finance must sign off but the economic buyer has not been identified.",
      "MEDDPICC_Champion__c": "Sam is engaged but unproven as a champion."
    }
  }
]
```

### Live write — Salesforce

```bash
gtmsi crm report.json --crm salesforce \
  --writer salesforce \
  --instance-url https://yourorg.my.salesforce.com \
  --access-token $SF_TOKEN
```

For each object in the patch the Salesforce writer either updates or creates,
depending on whether the resolved record id is present:

- **Update** (id present): `PATCH {instance_url}/services/data/v60.0/sobjects/<Object>/<Id>`
  with `Authorization: Bearer <token>` and `Content-Type: application/json`. A
  success returns **HTTP 204** with no body.
- **Create** (no id): `POST {instance_url}/services/data/v60.0/sobjects/<Object>`
  → **HTTP 201** with `{"id": "..."}`.

`instance_url` comes from the OAuth token response. `requests` must be installed
(`pip install requests`).

Field notes:

- Custom fields use the `__c` suffix; `Task` uses the standard `Subject` /
  `Description` fields.
- Dates are `YYYY-MM-DD`; datetimes are ISO-8601.
- Read-only / system fields are rejected with **HTTP 400**.
- The writer defaults to API version `v60.0` (valid). The latest is `v66.0` —
  you can pass a newer version when constructing the writer.

### Live write — HubSpot

```bash
gtmsi crm report.json --crm hubspot \
  --writer hubspot \
  --access-token $HS_TOKEN
```

The HubSpot writer uses a private-app token (`Authorization: Bearer <token>`)
and, per object, either updates or creates:

- **Update** (id present): `PATCH https://api.hubapi.com/crm/v3/objects/<type>/<id>`
  with body `{"properties": {...}}` → **HTTP 200** with the object.
- **Create** (no id): `POST https://api.hubapi.com/crm/v3/objects/<type>`
  → **HTTP 201** with the object. `requests` must be installed.

Field notes:

- Property internal names are `lowercase_underscored`.
- **Dates must be Unix epoch milliseconds, as strings** (not `YYYY-MM-DD`).
- **Notes are create-only**: they are created via `POST /crm/v3/objects/notes`
  and require `hs_timestamp` — the writer injects the current time if the mapping
  didn't supply it. **Linking** a note to a deal or company is *not* done in the
  note body; it requires the Associations API
  (`/crm/v4/objects/notes/<id>/associations/...`). The shipped mapping creates the
  note; the association is an extension you add.
- Required write scopes: `crm.objects.deals.write`, `crm.objects.companies.write`,
  `crm.objects.notes.write`.

---

## Supported CRM configs

| File | CRM | Notes |
|---|---|---|
| `config/crm/generic.yaml` | Any | Vendor-neutral template; field names to rename |
| `config/crm/salesforce.yaml` | Salesforce | Custom fields use `__c` suffix convention |
| `config/crm/hubspot.yaml` | HubSpot | Properties use `lowercase_underscore` convention |

---

## Adding a new CRM

### Step 1 — Copy the generic config

```bash
cp config/crm/generic.yaml config/crm/mycrm.yaml
```

Edit `crm: generic` to `crm: mycrm` and rename every `crm_field` value to
your CRM's actual field API names. The `from` paths, `transform`, and
`when_empty` values stay the same — they reference GTM Superintelligence report structure,
not CRM structure.

### Step 2 — Run a dry-run to verify the patch

```bash
gtmsi crm report.json --crm mycrm
```

Inspect the JSON output. Every field should resolve to the value you expect.

### Step 3 — Implement a writer (optional)

If your CRM exposes a REST endpoint, implement a writer in
`src/gtmsi/crm/writers.py`. The interface is a single method; mirror the shipped
writers' create-or-update behavior — PATCH when a record id is present, POST to
create when it is absent:

```python
class MyCRMWriter:
    name = "mycrm"

    def write(self, updates: list[CRMUpdate]) -> list[dict]:
        results = []
        for u in updates:
            if u.record_id:
                # issue your PATCH here; u.fields is the dict of field -> value
                results.append({"object": u.object, "id": u.record_id, "op": "update", "status": 200})
            else:
                # issue your POST here to create the record, capture the new id
                new_id = "..."
                results.append({"object": u.object, "id": new_id, "op": "create", "status": 201})
        return results
```

Register it in `get_writer()` and pass `--writer mycrm` on the CLI. See
`src/gtmsi/crm/writers.py` for the full `DryRunWriter`, `SalesforceWriter`,
and `HubSpotWriter` implementations.

---

## Safety note

**Dry-run is always the default.** The `DryRunWriter` is used unless you
explicitly pass `--writer salesforce` or `--writer hubspot` along with valid
credentials. Live writes are an explicit, credentialed action — you will never
accidentally modify CRM records by running `gtmsi crm` without the writer
flag.

The recommended workflow is:

1. Run without `--writer` to inspect the patch.
2. Verify field names and values against your CRM's schema.
3. Run with `--writer` and credentials to apply.

---

## Cross-references

- Deal and account reports (the inputs to CRM writeback): [scoring-layers.md](./scoring-layers.md)
- Per-call coaching reports: [scorecards.md](./scorecards.md)
- Schema reference: `schemas/crm_mapping.schema.json`
- Mapping source: `config/crm/`
- Writer source: `src/gtmsi/crm/writers.py`
- Mapping engine: `src/gtmsi/crm/mapping.py`
