# Using GTM Superintelligence inside Claude Code

GTM Superintelligence is **Claude-native**: it ships a skill, subagents, and slash commands that
run entirely inside Claude Code — no API key or server required. Claude reads the YAML
config, prompts, and transcript directly from the repo and is the engine. The same YAML
also drives the Python CLI for automation.

---

## Two modes

| Mode | What you need | When to use |
|---|---|---|
| **Claude Code (native)** | Claude Code with the repo open; no API key | Ad-hoc coaching, demos, sensitive calls, development |
| **Python CLI** | `ANTHROPIC_API_KEY`, Python 3.10+, `pip install -e ".[llm]"` | Automation, bulk, CI/CD, scheduled inboxes |

Same YAML, same prompts — only the LLM invocation differs.

---

## Zero-config quickstart

Open the repo in Claude Code and type:

```
/coach examples/transcripts/discovery_acme.txt
```

Claude reads the transcript, `config/call_types.yaml`, `config/outcomes.yaml`, the
matching scorecard, and the referenced frameworks — all from the repo — and returns a
structured coaching report. No key needed.

---

## Slash commands

| Command | What it does |
|---|---|
| `/coach <transcript>` | Full pipeline on one call → coaching report |
| `/coach-bulk <directory>` | Coach every transcript in a folder + a ranked summary |
| `/deal-score <folder> [name]` | Score an opportunity's health across its calls (sales) |
| `/account-health <folder> [name]` | Score a customer account's health across its calls (CSM) |
| `/inbox <folder> [--scope rep\|team\|company]` | Build a "what to improve" inbox |
| `/crm-fill <report.json> [--crm …]` | Map a report to CRM fields (dry-run patch) |
| `/crm-stages <folder> [--crm …]` | Resolve your org's real won/lost/open CRM stages from data |
| `/setup` | Set your stack (recorder, CRM, comms, email, agent builder) → writes `agents/config.yaml` |
| `/run-agent <agent.json>` | Run a [GTM agent](../agents): native on Attention, or as a managed Claude agent on any recorder |
| `/build-agent <agent.md> [for <builder>]` | Generate an agent's implementation for your builder (n8n / Make / Zapier / LangGraph / Claude / …) |

Each command takes a path (or pasted text) as its argument. `/coach` accepts any
supported format (`.txt`, `.md`, `.vtt`, `.srt`, `.json`) and auto-detects the adapter.
The commands live in [`.claude/commands/`](../.claude/commands).

The 30 [agent templates](../agents) ship pre-built for every builder (Attention native flow +
n8n / Make / Zapier / LangGraph / Claude Agent SDK / Claude Code subagent). Run `/setup` once,
then import on Attention or `/build-agent` for any other stack.

---

## The `sales-coach` skill

The [`sales-coach`](../.claude/skills/sales-coach) skill wraps the whole pipeline in a
conversational interface and auto-triggers when you share a transcript and ask to coach,
review, score, or analyze a call. It keeps the transcript, scorecard, and report in
context, so follow-ups stay grounded in real evidence:

```
You: /coach calls/renewal-acme.vtt
[coaching report appears]
You: What would have moved the "recap-value" outcome from partial to achieved?
Claude: The rep mentioned reporting improvements but didn't quantify them. They could
        have said: "Since January you've reclaimed ~15 hours a week — about $X a year at
        your blended rate; I want that to be the headline going into renewal." …
```

The skill also points to its `references/pipeline.md` (turn-by-turn checklist) and
`references/scoring-rubric.md` (how to calibrate scores).

## The `gtm-humanizer` skill

A second bundled skill, [`gtm-humanizer`](../.claude/skills/gtm-humanizer), rewrites any
drafted email or message so it reads like a real person wrote it, not a chatbot
(detects common AI-writing tells, bans em dashes, applies a voice profile). Every
message-writing agent runs it as a final pass, and it auto-loads `humanizer-context.md`
from the repo root for the GTM sender voice. Invoke it directly too:

```
/gtm-humanizer "your draft email" --voice professional --purpose email
```

---

## Subagents

The [`.claude/agents/`](../.claude/agents) directory holds focused, single-responsibility
subagents. The **`coaching-orchestrator`** runs the per-call pipeline and delegates to the
others as useful.

```
coaching-orchestrator         full per-call pipeline
├── call-classifier           classify the call type (prompts/classifier.md)
├── outcome-mapper            infer deal-specific outcomes (prompts/outcome_inference.md)
└── per-call-type coaches     specialized scorers:
    ├── discovery-coach
    ├── demo-coach
    ├── negotiation-coach
    └── renewal-coach          (others follow the same pattern; the orchestrator can
                                coach any call type directly from its scorecard)

deal-scorer                   deal/opportunity health across calls (rubrics/deal-health.yaml)
account-health-scorer         account health across calls (rubrics/account-health.yaml)
inbox-builder                 rep/team/company "what to improve" roll-up
crm-sync                      map a report to any CRM's fields (dry-run by default)
```

A subagent per call type lets each system prompt be tuned per motion (discovery is
question-focused; negotiation is commercial) and keeps the scorecard/frameworks loaded
once per call for effective caching. Not every call type has a dedicated coach file — the
orchestrator coaches the rest directly from the call type's scorecard, so coverage is
complete either way.

---

## Running without any API key

Inside Claude Code with no `ANTHROPIC_API_KEY`, the commands and skill still work — Claude
reads the repo files and reasons over them. Good for evaluating GTM Superintelligence, coaching
sensitive calls you'd rather not send over an API, and developing new scorecards. The
trade-off: bulk work is slower than the Python CLI because Claude handles one call per
turn.

---

## Python CLI reference

```bash
pip install -e ".[llm]"          # from a checkout; or pip install gtm-superintelligence
export ANTHROPIC_API_KEY=sk-ant-…
```

| Command | Description |
|---|---|
| `dealtrace coach <transcript>` | Full pipeline on one transcript (`--format md\|json\|text`, `--out`, `--redact`, `--adapter`, `--model`) |
| `dealtrace classify <transcript>` | Classify only (`--json`) |
| `dealtrace bulk <directory>` | Coach a folder → md + json per call + `index.md` (`--out`, `--glob`) |
| `dealtrace deal <folder>` | Deal-health across a folder of one deal's calls (`--name`, `--owner`, `--stage`, `--amount`, `--date`) |
| `dealtrace account <folder>` | Account-health across a folder of one account's calls |
| `dealtrace inbox <path>` | Rep/team/company inbox (`--scope`, `--for`; subfolders = reps) |
| `dealtrace crm <report.json>` | Map a report to CRM fields (`--crm`, `--writer`) |
| `dealtrace crm-stages` | Resolve the org's real CRM stages + where pipeline sits (`--crm`) |
| `dealtrace share <report.json>` | Render a paste-ready "post your score" card for LinkedIn/X |
| `dealtrace demo` | Print the tracked Attention demo booking link (no data collected) |
| `dealtrace inspect <transcript>` | Show the normalized transcript (debug adapters) |
| `dealtrace list frameworks\|scorecards\|call-types\|rubrics` | List the knowledge base |
| `dealtrace validate` | Check knowledge-base integrity (no argument — validates everything) |
| `dealtrace telemetry status\|enable\|disable` | Opt-in anonymous usage stats (off by default) |

```bash
dealtrace coach call.vtt --adapter gong --format json --out report.json
dealtrace bulk calls/ --out reports/ --glob "*.vtt"
dealtrace deal ./acme_deal --name "Acme — Platform" --owner Jordan
dealtrace inbox ./team --scope team --for "AE Team"
dealtrace crm reports/deal_acme.json --crm salesforce        # dry-run patch
```

---

## Cross-references

- Core concepts: [concepts.md](./concepts.md)
- Pipeline architecture: [architecture.md](./architecture.md)
- Three scoring layers: [scoring-layers.md](./scoring-layers.md)
- The coaching inbox: [inbox.md](./inbox.md)
- CRM auto-fill: [crm.md](./crm.md)
- Scorecard anatomy: [scorecards.md](./scorecards.md)
- Adapters: [adapters.md](./adapters.md)
- Privacy and responsible use: [privacy-and-pii.md](./privacy-and-pii.md)
