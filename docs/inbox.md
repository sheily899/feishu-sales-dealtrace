# The coaching inbox (rep / team / company)

The coaching inbox is a prioritized "what to improve" digest built by
aggregating many call coaching reports. It exists at three scopes:

| Scope | Audience | What it contains |
|---|---|---|
| `rep` | The individual seller or CSM | Personal patterns to fix this week |
| `team` | Sales manager, enablement | Patterns across all reps on a team |
| `company` | VP of Sales, Revenue Enablement | Roll-up across all teams |

The rep inbox is the daily morning read: open it, know your top two focus
areas, go make calls. The team and company inboxes tell managers where to
direct group coaching and what to reinforce.

---

## How it works

The inbox is **fully deterministic — no LLM is involved.** It rolls up the
structured signals already present in each coaching report (criterion scores and
flagged improvements) using a straightforward algorithm:

1. **Group by criterion.** For each criterion that either appeared as a flagged
   improvement or scored below 60 in any report in the period, accumulate the
   evidence: which calls, which reps, what better-moves were suggested, and what
   scores were recorded.

2. **Rank by frequency × weakness.** Each focus area is ranked by
   `evidence_count × (100 − avg_score)`. Criteria that appear often *and*
   score poorly rise to the top; a criterion seen once at a score of 58 stays
   low.

3. **Set priority.** A focus area is `high` if it appears in 3+ calls or has an
   average score below 45; `medium` if seen in 2+ calls; `low` otherwise.

4. **Attach the drill.** Each focus area carries the best `better_move` from
   any coaching report that contributed to it — a concrete, copy-pasteable
   example the rep can rehearse or the manager can use for a role-play.

5. **Surface wins.** Strengths that appear across multiple calls are collected
   as a "keep doing" list, so positive patterns get reinforced, not just gaps
   highlighted.

6. **For team/company scope,** each focus area lists the `affected_reps` who
   show the pattern, and a per-member summary table is appended.

Because no LLM is called, an inbox run is cheap enough to schedule daily.

---

## CLI

### Rep inbox

```bash
gtmsi inbox <folder> --scope rep --for "Jordan"
```

`<folder>` can contain raw transcripts, existing coaching-report JSONs, or
both. For a rep inbox, every file in the folder is treated as belonging to that
rep. The `--for` name is stored in `generated_for` in the output.

### Team inbox

```bash
gtmsi inbox <team-folder> --scope team --for "AE Team"
```

For team and company scope, **each subfolder is treated as one rep** (the
subfolder name becomes the rep name). Put Jordan's calls in `team-folder/jordan/`
and Alex's in `team-folder/alex/`, and the team inbox will attribute patterns
correctly.

### Company inbox

```bash
gtmsi inbox <company-folder> --scope company --for "company"
```

For both `team` and `company` scope, each **immediate** subdirectory of the path
is treated as one rep (the same one-level code path as `team`). Subdirectories
are not recursed into — only the first level below the path becomes a rep.

### Accepts transcripts or existing reports

Pass a folder of raw transcripts (`.vtt`, `.srt`, plain text) and GTM Superintelligence
will run call coaching on each before building the inbox. Pass a folder of
already-computed coaching-report JSONs and it skips directly to aggregation.
Mix both freely.

---

## Example output

From `examples/reports/team_inbox.md`:

```markdown
# Team coaching inbox — AE Team

**Period:** last 3 calls  ·  **Calls:** 3  ·  **Avg score:** 59.7/100

## Work on this

### Clear Next Steps with the Right People  (seen in 1 calls · avg 38.0)
After excellent discovery, the call ended with 'send me a summary' — an open
loop with no date and no commitment. A document is not a next step; a meeting
on the calendar is.
_Reps:_ Jordan

  **Drill / better move:** "I'll have that summary to you Thursday. Rather than
  you reading it cold, can we grab 30 minutes Friday so I can walk you and your
  VP of Finance through it?"

### Booking the Meeting  (seen in 1 calls · avg 38.0)
_Reps:_ Alex

  **Drill / better move:** "How about we grab 15 minutes Wednesday at 10 so I
  can show you, rather than an email that gets buried?"

## Keep doing

- Current State & Why It Isn't Working  (in 1 calls)
- Compelling Event & Timing  (in 1 calls)

## By member

| Name   | Calls | Avg  | Top focus                        |
|--------|------:|-----:|----------------------------------|
| Riley  |     1 | 54.0 | Interactivity & Comprehension    |
| Alex   |     1 | 55.0 | Booking the Meeting              |
| Jordan |     1 | 70.0 | Decision Process & Stakeholders  |
```

---

## Running it every morning

Because the inbox is deterministic and cheap, it is practical to run it on a
schedule and deliver each rep their personal digest automatically.

A few patterns that work:

- **Cron / CI job** — schedule `gtmsi inbox rep-folder/ --scope rep --for
  "Jordan"` for each rep, then pipe the output to a DM, email, or Slack message.
- **Claude Code `/loop`** — use the `/loop` skill to re-run the inbox on an
  interval and surface the result in your current session.
- **Scheduled agent** — use the `/schedule` skill to create a daily remote
  agent that runs the inbox and posts results to a channel.

Keep delivery tool-agnostic: the inbox command outputs a JSON document
conforming to `schemas/inbox.schema.json` (or a markdown report if you pass
`--format md`). Pipe it wherever your team already reads their morning updates.

---

## Output schema

The inbox output conforms to `schemas/inbox.schema.json`. Key fields:

| Field | Type | Description |
|---|---|---|
| `scope` | `rep \| team \| company` | Who this was generated for |
| `generated_for` | string | Rep name, team name, or "company" |
| `period` | string | e.g. "last 20 calls" or "2026-05-23..2026-05-30" |
| `stats.calls_analyzed` | integer | How many calls fed this inbox |
| `stats.avg_overall_score` | number | Average overall score over the period |
| `focus_areas[]` | array | Prioritized improvement themes |
| `focus_areas[].title` | string | The criterion name |
| `focus_areas[].priority` | `high \| medium \| low` | Computed from frequency and score |
| `focus_areas[].evidence_count` | integer | How many calls showed this pattern |
| `focus_areas[].avg_score` | number | Average criterion score over the period |
| `focus_areas[].drill` | string | A concrete practice or better-move |
| `focus_areas[].example_calls` | string[] | Call ids/titles illustrating the pattern |
| `focus_areas[].affected_reps` | string[] | (team/company only) Who shows this pattern |
| `wins[]` | array | Positive patterns worth reinforcing |
| `members[]` | array | (team/company only) Per-rep summary lines |

---

## Cross-references

- Per-call coaching reports: [scorecards.md](./scorecards.md)
- Deal and account health (the other aggregations): [scoring-layers.md](./scoring-layers.md)
- CRM auto-fill: [crm.md](./crm.md)
- Schema: `schemas/inbox.schema.json`
- Source: `src/gtmsi/inbox.py`
