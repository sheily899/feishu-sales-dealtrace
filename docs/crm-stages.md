# CRM stage discovery — use the org's *real* stages

Stage names are different in every org: one company's "Closed Won" is another's
"Closed - Won", "7. Won", or "Signed". An agent that hardcodes `"Closed Won"` silently
breaks in most orgs. So any agent whose trigger or logic keys off a pipeline stage must
**resolve the org's actual stages from its own CRM data first** — and understand *where
the opportunities actually sit* — rather than assuming labels.

GTM Superintelligence ships this as `gtmsi crm-stages` and `src/gtmsi/crm/stages.py`.

```bash
gtmsi crm-stages --crm salesforce      # dry-run prints the queries; add creds to run live
gtmsi crm-stages --crm hubspot --access-token $HUBSPOT_ACCESS_TOKEN
```

Output (live):
```
# salesforce stages
Won:  Closed Won
Lost: Closed Lost
Open: Prospecting, Qualification, Proposal, Negotiation
Where open opportunities sit:
  Qualification: 38 open ($1,240,000)
  Proposal: 21 open ($2,100,000)
  Negotiation: 9 open ($1,650,000)
```

## How it resolves stages

### Salesforce
The semantics live on the **`OpportunityStage`** object — not the `StageName` picklist
(which lacks won/closed flags). Resolve from data:

```sql
-- the org's real stages, with semantics
SELECT MasterLabel, IsClosed, IsWon, IsActive, SortOrder
FROM OpportunityStage WHERE IsActive = true ORDER BY SortOrder

-- where the open pipeline actually sits
SELECT StageName, COUNT(Id) cnt, SUM(Amount) amt
FROM Opportunity WHERE IsClosed = false GROUP BY StageName
```

Then:
- **Won** = stages with `IsWon = true`
- **Lost** = `IsClosed = true AND IsWon = false`
- **Open** = `IsClosed = false`

> Gotcha: stages can vary by **record type / sales process**. `OpportunityStage` is the
> global set; if the org uses multiple sales processes, confirm which stages are
> available for the relevant record type.

### HubSpot
Stages live on **deal pipelines**:

```
GET https://api.hubapi.com/crm/v3/pipelines/deals     → results[].stages[]
```

Each stage has `label`, `id`, `displayOrder`, and `metadata` with `isClosed` and
`probability`:
- **Won** = `metadata.probability == 1.0`
- **Lost** = closed with `metadata.probability == 0.0`
- **Open** = `metadata.isClosed != true`

Note there can be **multiple pipelines**; a deal's stored `dealstage` is a stage **id**
that maps to a label via this endpoint. To see where deals sit, query
`POST /crm/v3/objects/deals/search` per stage and read `total`.

## How agents use this

Every stage- or date-aware agent (e.g. **AE Handoff**, **Lost-Deal Intel**, **Cross
Team Handoff**, **Deal Stage Clarity**, **Revenue Sentry**, **Win Loss Insights**,
**Renewal Countdown**) is configured to resolve stages first:

- **AE Handoff** fires when an Opportunity enters one of the org's *resolved* **won**
  stages — not a literal `"Closed Won"`.
- **Lost-Deal Intel** fires on the org's *resolved* **lost** stages.
- Pipeline-health agents rank risk against the org's *real* open stages and where its
  pipeline concentrates.

In code: call `gtmsi.crm.fetch_salesforce_stages(...)` / `fetch_hubspot_stages(...)`
(or the pure `classify_*` functions on data you already have) and use `.won`, `.lost`,
`.open`, and `.busiest_open_stages()`.

## Sources
- Salesforce — [OpportunityStage object](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_opportunitystage.htm) · [SOQL aggregate functions](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_agg_functions.htm)
- HubSpot — [CRM Pipelines API](https://developers.hubspot.com/docs/api-reference/crm-pipelines-v3/guide) · [Deal pipelines & stages](https://knowledge.hubspot.com/deals/set-up-and-customize-your-deal-pipelines-and-deal-stages)
