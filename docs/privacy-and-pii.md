# Privacy and Responsible Use

Sales-call transcripts are among the most sensitive records a company produces.
They capture the words of customers and prospects who may not know they are
being transcribed, and they contain names, titles, deal sizes, business
strategies, and candid personal disclosures. Using GTM Superintelligence responsibly
requires deliberate decisions at every step: collection, storage, processing,
and access.

This page is guidance, not legal advice. Consult your legal team and data
protection officer for binding obligations in your jurisdiction.

---

## What is in a transcript

| Data type | Examples | Risk level |
|---|---|---|
| Names and titles | Buyer's full name, job title, company | Medium |
| Contact information | Email, phone mentioned in passing | High |
| Business strategy | Deal size, competitive plans, board timelines | High |
| Personal disclosures | Career pressure, stress, health, personal goals | High |
| Authentication signals | Account names, system names, process details | Medium |
| Opinions and candid views | Internal politics, competitor assessments | High |

The `rep` side of the transcript also reveals your team's sales tactics,
pricing floors, and account strategy. Transcripts are sensitive in both
directions.

---

## Consent and disclosure

### Inform participants before recording

Most jurisdictions require at least one-party consent to record a call; many
require all-party consent. Regardless of legal minimums:

- Disclose that the call is being recorded at the start of every call.
- Give participants a chance to opt out before substantive discussion begins.
- Do not retroactively process recordings taken without disclosure.

### Coaching should be disclosed to reps

Reps being coached should know that their calls are reviewed and scored. Covert
surveillance — even for coaching — erodes trust and in many jurisdictions
requires explicit employment agreement provisions.

---

## Data minimization

GTM Superintelligence can produce high-quality coaching from a transcript alone. You do not
need to send:

- Full contact records from your CRM.
- Recording audio or video.
- Email threads attached to the deal.

Before sending a transcript to any processing system, ask: what is the minimum
data needed to produce useful coaching? The `metadata` field in the normalized
transcript accepts deal context, but pass only what materially improves the
output.

---

## PII redaction

The repo includes an optional redaction step that runs before the transcript is
sent to any LLM. It is regex-based, best-effort masking (it does **not** detect
names or company names) and masks exactly these five identifiers:

- Email addresses → `[EMAIL]`
- Phone numbers → `[PHONE]`
- Social Security numbers → `[SSN]`
- Card numbers → `[CARD]`
- URLs → `[URL]`

Redaction reduces the precision of evidence quotes in the coaching report —
"reach me at [EMAIL]" instead of the actual address — but preserves all
structural information the coach needs. It is a convenience, not a compliance
guarantee.

To enable redaction:

```bash
gtmsi coach call.vtt --redact
```

Or set `redact: true` in your project configuration.

---

## Where data goes

### Claude Code (native mode)

When you use the `/coach` slash command inside Claude Code, the transcript is
processed by Anthropic's Claude API. Review [Anthropic's privacy policy and
data processing terms](https://www.anthropic.com/privacy) before processing
transcripts this way.

GTM Superintelligence does not ship any analytics, telemetry, or logging that sends data
to a third party. The only external call is to the Anthropic API.

### Python CLI with Anthropic API key

The same applies: transcripts are sent to Anthropic's API. If your organization
has data residency requirements (e.g., EU data must stay in the EU), check
whether Anthropic's API region options satisfy them.

### Choosing a model and minimizing exposure

The only relevant environment variables are `ANTHROPIC_API_KEY` (your API key),
`GTMSI_MODEL` (override the Anthropic model used — still the Anthropic API),
and `GTMSI_HOME` (point at a custom content directory). There is no
OpenAI-compatible or self-hosted endpoint.

For maximum privacy, run GTM Superintelligence entirely **inside Claude Code** with no API
key at all. In that mode the skill and subagents read the YAML rubrics and the
transcript directly and use the ambient Claude model — no transcript leaves your
machine through the Python API path.

---

## Access control

Coaching reports are more sensitive than most internal documents because they
contain verbatim customer quotes and deal intelligence alongside rep performance
data. Apply the principle of least privilege:

| Role | Recommended access |
|---|---|
| Rep | Own coaching reports only |
| Frontline manager | Reports for their direct reports |
| Enablement / RevOps | Aggregated scores and patterns; redacted individual reports |
| Senior leadership | Aggregated dashboards; no individual rep-level reports by default |

Do not store coaching reports in publicly accessible storage (e.g., a public S3
bucket or a shared drive with broad org access).

---

## Coaching as decision support, not surveillance

The coaching report is decision support for the rep and their manager — a tool
for growth, not a performance-management weapon.

Specific guidance:

- **Do not use overall scores as the primary input for termination, promotion,
  or compensation decisions.** Scores are calibrated against a rubric, not
  against business outcomes. A rep can score 85 on a discovery call and still
  lose the deal.
- **Do not build dashboards that rank reps publicly by score.** Leaderboards
  create gaming behavior and discourage honest assessment.
- **Do share strengths with the rep.** The `coaching.strengths` section is
  designed for positive reinforcement. Positive feedback from evidence is more
  effective than praise without grounding.
- **Do use patterns across calls for enablement, not individual calls for
  evaluation.** A single call is a sample. Fifty calls reveal a pattern.

---

## Third-party recorders

GTM Superintelligence is vendor-neutral and does not require any specific recorder. However,
your call recorder (Gong, Fireflies, Otter, Zoom, or any other) has its own
privacy policy, data retention rules, and subprocessor agreements. GTM Superintelligence
only receives the transcript export — it does not connect to recorder APIs or
access recorder storage.

Review your recorder's data processing agreement separately. In particular:

- Does the recorder store audio indefinitely? Can you delete recordings?
- Does the recorder use recordings to train models?
- Can you export transcripts in a format GTM Superintelligence's adapters support?

---

## Retention and deletion

Define a retention policy before deploying GTM Superintelligence in production:

- **Transcripts:** retain for the minimum period needed for coaching; delete
  when the coaching window closes (e.g., 90 days post-call).
- **Coaching reports:** retain for the period needed for performance review
  cycles; delete when no longer needed.
- **Redacted vs. unredacted:** consider retaining only redacted transcripts
  after the coaching report is generated.

Implement a deletion workflow that removes transcripts and reports when a
customer or rep requests deletion under GDPR Article 17, CCPA, or equivalent
law.

---

## Summary checklist

- [ ] Calls are disclosed to all participants before recording begins.
- [ ] Reps are informed that calls are reviewed and scored.
- [ ] PII redaction is enabled for any externally processed transcripts.
- [ ] Transcripts are not sent to third-party services beyond the LLM provider.
- [ ] LLM provider data processing terms are reviewed and accepted.
- [ ] Access to coaching reports follows least-privilege principles.
- [ ] Coaching reports are not used as the sole basis for employment decisions.
- [ ] A transcript and report retention/deletion policy is documented and enforced.

---

## Cross-references

- Adapters (including redaction options): [adapters.md](./adapters.md)
- Claude Code mode (where data goes): [claude-native.md](./claude-native.md)
- Core concepts: [concepts.md](./concepts.md)
