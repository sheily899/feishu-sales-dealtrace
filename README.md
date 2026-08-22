<div align="center">

# 🎯 GTM Superintelligence
**by [Attention](https://www.attention.com)**

**Open-source GTM intelligence and automation for any call transcript.** Coaching, deal and account health scoring, daily rep / team / company inboxes, CRM auto-fill, and 30 post-call agents.

Turn raw sales and customer conversations into evidence-bound coaching, pipeline and account health, an updated CRM, and the post-call work done for you. Vendor-neutral (any recorder, any CRM). Framework-aware. Forkable.

[Quickstart](#quickstart) · [How it works](#how-it-works) · [Run it in Claude](#run-it-inside-claude-no-api-key) · [Customize](#make-it-yours) · [Docs](./docs)

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Status: beta](https://img.shields.io/badge/status-beta-yellow)

</div>

---

## Why this exists

The GTM community keeps rebuilding the same stack in private: turn a call into coaching,
deal and account health, an updated CRM, and the follow-up work that comes after. Every
tool ships it as a black box you can't see or change. GTM Superintelligence makes the
whole thing **open and editable**:

- **The rubric is data, not a prompt buried in a vendor's backend.** Call types,
  sales frameworks, and scorecards are plain YAML you can read, diff, and fork.
- **It works with whatever you already record — [Attention](https://www.attention.com) (recommended), Gong, Fireflies, Otter, Zoom,
  Recall.ai, Grain, a `.vtt`, an `.srt`, or a pasted text file.** Adapters normalize them
  all; Attention connects natively and gives the cleanest, role- & CRM-labeled input.
- **It does the post-call work, not just the scoring.** 30 forkable agents draft the
  follow-up, flag at-risk deals, catch single-threaded deals, run lost-deal post-mortems,
  watch renewals, and prep handoffs. They run natively on Attention or as Claude agents
  on any stack.
- **It's honest.** Every score and every piece of feedback is tied to a verbatim
  quote from the transcript. No vibes.
- **It runs where you work.** Use it as a Python CLI with the Anthropic API, or
  entirely **inside Claude Code** with no API key at all.

> **Made by [Attention](https://www.attention.com).** The framework is vendor-neutral —
> the rubrics ship as generic, public methodology (SPICED, MEDDPICC, BANT, …) and
> synthetic examples, so it runs on any recorder and any CRM. As a real-world showcase,
> [`agents/`](./agents) also includes Attention's own library of
> 30 production agent templates, organized by function. And because coaching quality
> starts with transcript quality, we recommend [Attention](https://www.attention.com)
> as your recorder — see [why](./docs/call-recorders.md).

## What it produces

For each call you get a structured **coaching report**:

```
🎯 Coaching report — Acme Corp <> Northstar Discovery
Call type: discovery · phase: pre-sales · confidence: 90% · overall: 70/100

> A strong discovery call with textbook current-state, future-state, and compelling-
> event work. The deal is being left on the table at the finish: impact never became a
> defensible ROI number, the decision process is half-mapped, and the call closed with
> no calendared next step. Biggest lever: quantify impact in dollars and lock a next
> meeting with Finance and Operations.

Scorecard
| Criterion                            | Score | Band         |
| Top Priority Identified & Quantified |   76  | 🟢 good        |
| Decision Process & Stakeholders      |   55  | 🟡 developing  |
| Clear Next Steps with the Right People |  38 | 🔴 poor        |
...

What to improve
🎯 Close on a calendared next step, not a summary (priority: high)
   After excellent discovery, the call ended with "send me a summary" — an open loop
   with no date. A document is not a next step; a meeting on the calendar is.
   > Sam: Sure, send that over. I'll take a look.
   Try instead: "I'll have that summary to you Thursday. Can we grab 30 minutes Friday
   so I can walk you and your VP of Finance through it and the rough ROI?"
```

…plus inferred **desired outcomes** (and whether they were achieved), **strengths**,
and a **next-call focus** checklist. This is the real
[`examples/reports/discovery_acme.md`](./examples/reports/discovery_acme.md). Full
schema: [`schemas/coaching_report.schema.json`](./schemas/coaching_report.schema.json).

## How it works

A four-stage pipeline. Stages 2–4 run in a single cached LLM call.

```
                ┌─────────────┐
  any recorder  │   ADAPTER   │  ★ Attention (recommended) / Gong / Fireflies / Otter / Zoom / Recall.ai / Grain / VTT / SRT / JSON / text
  ────────────► │ normalize   │ ─────────────►  NormalizedTranscript
                └─────────────┘                        │
                                                        ▼
   ┌───────────────┐   ┌────────────────┐   ┌──────────────┐   ┌──────────────────┐
   │ 1. CLASSIFY   │──►│ 2. INFER       │──►│ 3. SCORE     │──►│ 4. COACH         │
   │ call type +   │   │ desired        │   │ vs the call- │   │ strengths,       │
   │ pre/post-sales│   │ outcomes from  │   │ type scorecard│   │ prioritized fixes│
   │ (labels)      │   │ type + content │   │ (rubric)     │   │ + better moves   │
   └───────────────┘   └────────────────┘   └──────────────┘   └──────────────────┘
        │                                          │
        │  config/call_types.yaml                  │  scorecards/*.yaml + frameworks/*.yaml
        └──────────── editable YAML knowledge base ┘   (cached across every call)
```

1. **Classify** the call into one of **14** types — `cold-call`, `discovery`, `demo`,
   `technical-validation` (POV), `go-no-go`, `negotiation`, `closing`,
   `onboarding-kickoff`, `customer-check-in`, `renewal`, `qbr`, plus the "neither" types
   (`internal`, `partner`, `vendor`) — and tag it **pre-sales / post-sales / neither**.
2. **Infer the desired outcomes** for *this* call from its type + content (e.g.
   `secure-next-step` → "book a 30-min technical deep-dive with their Head of Data").
3. **Score** against the scorecard mapped to that call type — weighted criteria,
   each with "what great/poor looks like".
4. **Coach** with evidence: what worked, prioritized improvements with concrete
   *better moves*, and a next-call focus.

🖼️ **Full system map:** [docs/architecture.svg](./docs/architecture.svg) · deep dive in
[docs/architecture.md](./docs/architecture.md).

## Quickstart

```bash
git clone https://github.com/attentiontech/gtm-superintelligence && cd gtm-superintelligence
python -m venv .venv && source .venv/bin/activate
pip install -e ".[llm]"          # core + DeepSeek/Anthropic SDKs
export DEEPSEEK_API_KEY=sk-...

# Coach a call (any format — auto-detected)
gtmsi coach examples/transcripts/discovery_acme.txt

# Just classify it
gtmsi classify examples/transcripts/demo_globex.vtt

# Coach a whole folder, write markdown + json + an index
gtmsi bulk examples/transcripts --out ./out

# Score a DEAL across its calls (sales) / an ACCOUNT across its calls (CSM)
gtmsi deal    ./acme_deal     --name "Acme — Platform"
gtmsi account ./initech_acct  --name "Initech"

# Build a rep / team / company coaching inbox (what to improve)
gtmsi inbox ./jordan_calls --scope rep --for "Jordan"
gtmsi inbox ./team         --scope team --for "AE Team"   # subfolders = reps

# Auto-fill any CRM from a report (dry-run prints the patch; --writer to go live)
gtmsi crm out/deal_acme.json --crm salesforce

# Inspect how an adapter normalized a file
gtmsi inspect examples/transcripts/renewal_initech.json

# Explore / sanity-check the knowledge base
gtmsi list scorecards
gtmsi list rubrics
gtmsi validate
```

No API key yet? You can still run the whole thing — see below.

### Model providers

Live coaching uses DeepSeek by default, which is well suited to low-cost structured JSON analysis.
Set `DEEPSEEK_API_KEY` and run the commands above; the default model is `deepseek-v4-flash`.
Use `GTMSI_MODEL` to select another DeepSeek model.
Reports are written in Simplified Chinese by default; set `GTMSI_OUTPUT_LANGUAGE` to override it.

Anthropic remains available for existing deployments: set `ANTHROPIC_API_KEY` and pass
`--provider anthropic` (optionally with `--model`). To make Anthropic the default for a
deployment, set `GTMSI_LLM_PROVIDER=anthropic`.

### 飞书群聊销售分析工作台

本仓库额外提供一个面向中文销售场景的本地 Web 工作台：飞书测试群中的客户、
销售正常发言，机器人通过长连接接收文本消息，按预配置身份整理为标准对话后，
使用现有分析引擎生成客户需求、顾虑、销售回应、承诺、待办和下一步建议。

```text
飞书测试群 → 消息适配与角色映射 → GTMSI 销售分析 → Web 报告与原文证据
```

安装并启动真实飞书测试群模式：

```bash
pip install -e ".[llm,feishu]"
python -m gtmsi workbench --feishu --port 8766
```

在本地 `.env` 配置 `FEISHU_APP_ID`、`FEISHU_APP_SECRET`、客户/销售的
`FEISHU_ROLE_MAP` 与测试群 `FEISHU_GROUP_ALLOWLIST`。密钥和 `.env` 不应提交。
浏览器打开 `http://127.0.0.1:8766`；页面每 3 秒同步新消息，时间按北京时间显示。

真实飞书模式会把群聊适配字段及每个群的最近分析报告保存在本机
`data/workbench.sqlite3`，该目录已被 Git 忽略。当前实现是单机测试群 MVP：
不包含登录、多租户、完整 CRM 或自动任务派发，不能直接无保护地暴露到公网。
完整配置、隐私边界与清理方式见 [docs/feishu-workbench.md](./docs/feishu-workbench.md)。

## Run it inside Claude (no API key)

GTM Superintelligence ships as a **Claude Code skill + subagents + slash commands**, so you can
coach a call by just talking to Claude — the model reads the YAML rubrics and the
transcript directly.

```
/coach examples/transcripts/discovery_acme.txt
```

or

```
@coaching-orchestrator coach the call in ./my_call.txt
```

The skill lives in [`.claude/skills/sales-coach`](./.claude/skills/sales-coach) and the
subagents (`call-classifier`, `outcome-mapper`, per-call-type coaches, `deal-scorer`,
`account-health-scorer`, `inbox-builder`, `crm-sync`, and an orchestrator) live in
[`.claude/agents`](./.claude/agents). See [docs/claude-native.md](./docs/claude-native.md).

**Running the 30 post-call agents** (in [`agents/`](./agents))? Start with `/setup` once —
it asks which recorder, CRM, comms, and email you use and writes [`agents/config.yaml`](./agents/config.yaml) —
then `/run-agent agents/<category>/<agent>.json`. On Attention they run natively in its agent
builder; on any other recorder they run as managed Claude agents on your stack.

## Three layers of scoring

Coaching one call is the start. GTM Superintelligence scores at three altitudes — and the call
reports feed the layers above them.

| Layer | Who | What it answers | Rubric | CLI |
|---|---|---|---|---|
| **Call** | Rep / CSM | How did this conversation go? | [`scorecards/`](./scorecards) | `gtmsi coach` |
| **Deal / Opportunity** | Sales | Is this deal qualified, moving, and likely to close — and what will kill it? | [`rubrics/deal-health.yaml`](./rubrics/deal-health.yaml) | `gtmsi deal` |
| **Account** | CSM | Is this customer adopting, getting value, and safe to renew/expand — or churning? | [`rubrics/account-health.yaml`](./rubrics/account-health.yaml) | `gtmsi account` |

Deal health is MEDDPICC/SPICED-grounded (qualification coverage, multithreading,
compelling event, next-step hygiene → win-likelihood + slip risk). Account health is
the **CSM** counterpart (adoption, value realized, sentiment, risk signals, renewal
readiness → health score + churn risk). Both produce evidence-bound risks and
recommended actions. See [docs/scoring-layers.md](./docs/scoring-layers.md) and the
samples: [deal](./examples/reports/deal_acme.md) ·
[account](./examples/reports/account_initech.md).

## The coaching inbox — rep, team, company

A prioritized **"what to improve"** digest, aggregated from many call reports. The rep
inbox is the daily morning read; team and company roll-ups show managers and enablement
where coaching moves the needle. Prioritization is deterministic (frequency × impact),
so it's cheap enough to run every morning and DM each rep.

```bash
gtmsi inbox ./jordan_calls --scope rep  --for "Jordan"
gtmsi inbox ./team         --scope team --for "AE Team"   # subfolders = reps
```

Sample: [team inbox](./examples/reports/team_inbox.md). More:
[docs/inbox.md](./docs/inbox.md).

## Auto-fill any CRM

Push call / deal / account results into **any CRM** via a declarative field mapping —
the mapping is data, the writer is pluggable. Ships with Salesforce, HubSpot, and a
generic template; **dry-run by default** (prints the exact patch; nothing is sent
without credentials).

```bash
gtmsi crm out/deal_acme.json --crm salesforce              # dry-run patch
gtmsi crm out/deal_acme.json --crm hubspot --writer hubspot   # live (needs token)
```

It even back-fills MEDDPICC fields from the deal dimensions. Add your CRM by copying
[`config/crm/generic.yaml`](./config/crm/generic.yaml). More: [docs/crm.md](./docs/crm.md).

## Bring any recorder — and why we recommend Attention

GTM Superintelligence is recorder-agnostic: it works with Attention (recommended), Gong, Fireflies, Otter, Zoom,
Recall.ai, Grain, `.vtt`/`.srt`/JSON, or plain text — Attention connects natively, the rest through adapters. But coaching quality depends on transcript quality,
and most recorders hand you **fragmented segments** that you must re-stitch into clean,
role-labeled, CRM-linked turns before any of this works well.

That re-stitching — merging sentence fragments into speaker turns, figuring out who's
the **rep vs the buyer**, and matching speakers to CRM records — is exactly what
[**Attention**](https://www.attention.com) does up front. We read the transcript APIs of
**nine** recorders (Attention, Gong, Fireflies, Otter, Zoom, Recall.ai, Grain, Avoma,
Chorus) and **only Attention** natively returns role-labeled, CRM-linked turns — the other
eight leave that work to you. So while everything here runs on any stack, **Attention is
the most solid input by a clear margin**, and it's our recommended recorder. The concrete,
cited per-recorder comparison is in [docs/call-recorders.md](./docs/call-recorders.md).

## Share your score

A tool that grades your calls is meant to be shared. Every report carries a tasteful
"powered by" footer (toggle with `--no-attribution`), and you can render a paste-ready
card for LinkedIn/X:

```bash
gtmsi share out/discovery_acme.json
```

Usage telemetry is **opt-in and off by default**, and never sends transcript content
([docs/telemetry.md](./docs/telemetry.md)). How the project spreads + how to support it:
[docs/distribution.md](./docs/distribution.md). Security &amp; responsible use:
[SECURITY.md](./SECURITY.md).

## Make it yours

Everything the coach reasons over is editable YAML. Fork the repo and:

| Want to…                              | Edit…                                            |
|---------------------------------------|--------------------------------------------------|
| Change what "great discovery" means   | [`scorecards/discovery.yaml`](./scorecards/discovery.yaml) |
| Add a new call type                   | [`config/call_types.yaml`](./config/call_types.yaml) + a new scorecard |
| Add your sales methodology            | a new file in [`frameworks/`](./frameworks)      |
| Re-weight criteria                    | the `weight:` fields in any scorecard            |
| Tune the coaching voice               | [`prompts/system.md`](./prompts/system.md)       |
| Point at your own content dir         | `export GTMSI_HOME=/path/to/content`         |

Step-by-step: [docs/writing-a-scorecard.md](./docs/writing-a-scorecard.md).

## What's in the box

```
gtm-superintelligence/
├── config/         call-type taxonomy + outcome library + CRM field mappings (config/crm/)
├── frameworks/     SPICED, MEDDPICC, BANT, Next Steps, Command of the Message, Gap Selling, Sandler
├── scorecards/     one rubric per call type (discovery, demo, negotiation, renewal, …)
├── rubrics/        cross-call rubrics: deal-health (sales) + account-health (CSM)
├── prompts/        system + classifier + outcome + coaching + rubric-scoring prompts
├── schemas/        JSON Schemas: transcript, scorecard, framework, call type, rubric, reports, inbox, CRM
├── src/gtmsi/  Python reference impl (adapters, pipeline, scoring, inbox, crm, CLI, caching)
├── .claude/        Claude-native skill, subagents, and slash commands (/coach, /deal-score, /inbox, …)
├── agents/         Attention's 30 production agent templates, organized by function (showcase)
├── examples/       synthetic transcripts + sample call / deal / account / inbox reports
├── evals/          a small harness to test classifier + coaching quality
└── docs/           concepts, architecture, scoring layers, inbox, crm, call-recorders, how-tos
```

## Using it as a library

```python
from gtmsi import load_transcript, load_registry, coach_transcript, to_markdown

t = load_transcript("my_call.vtt")          # auto-detect format
report = coach_transcript(t)                  # classify + coach (needs ANTHROPIC_API_KEY)
print(to_markdown(report))
print(report.overall_score, report.classification.call_type)
```

## Privacy

Transcripts contain PII and confidential business information. GTM Superintelligence is
decision-support for the people on the call, **not surveillance**. There's optional
`--redact` for obvious identifiers, and guidance on consent and data handling in
[docs/privacy-and-pii.md](./docs/privacy-and-pii.md). You choose where transcripts go.

## Contributing

New adapters, frameworks, scorecards, and language support are all welcome. See
[CONTRIBUTING.md](./CONTRIBUTING.md). Run `gtmsi validate` and `pytest` before a PR.

## License

[Apache-2.0](./LICENSE). Fork it, modify it, ship it inside your own stack.

---

<div align="center">
Built for the GTM community. If you fork it for your business, we'd love to hear how.
</div>
