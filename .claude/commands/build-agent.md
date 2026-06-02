---
description: Build a GTM agent on the user's stack. On Attention, hand them the native agent-builder flow to import. On any other builder (n8n, Make, Zapier, LangGraph, a Claude agent, ...), read the agent spec and generate the implementation for THAT builder.
argument-hint: <agent-name-or-json-path> [for <builder>]
---

Build the GTM agent referenced in: $ARGUMENTS

The repo ships every agent in three forms — use them as the source of truth:
- `agents/<fn>/<agent>.md` — the canonical, builder-agnostic spec (goal, trigger, inputs, the generic-action → connector map, full step logic, output, edge cases, guardrails). **This is your primary input.**
- `agents/<fn>/<agent>.json` — the Attention agent-builder template (the verbatim operating prompt lives in `template.agent.instructions`).
- `agents/<fn>/<agent>.activepieces.json` — the native Attention agent-builder (Activepieces) flow.

## Step 1 — Resolve the target builder

Read `agent_builder` from `agents/config.yaml`. If `$ARGUMENTS` says "for <builder>", that wins. If neither is set, ask the user which agent builder they use (Attention, n8n, Make, Zapier, LangGraph / code, a Claude agent, or something else) and offer to save it via `/setup`.

## Step 2 — Branch

### Path A — `attention` → native, no translation
These specs are Attention agent-builder flows already. Tell the user to **import `agents/<fn>/<agent>.activepieces.json`** into their Attention agent builder (or the template `.json`), then:
- connect their Attention + chat/email accounts,
- fill the placeholders (`<YOUR_ATTENTION_USER_ID>`, `<…_SLACK_…>`, channel ids),
- confirm the trigger (per-call `webhookTrigger` vs schedule).
Do not re-generate anything; the native flow is the strongest path. Summarize what it will do and what to set.

### Path B — any other builder → figure out what to build
Read the agent's `.md` spec and `.json` instructions, then produce a working implementation for the user's builder. Be smart about the target:

1. **Map the generic actions** the agent uses to that builder's connectors/nodes:
   - `query_records` → the builder's CRM node (Salesforce/HubSpot/…),
   - `search_calls` / `get_call_details` → the recorder's node/API, or ingest exports via the **gtmsi adapters** (`gtmsi inspect` / `load_transcript`) when the recorder only exports transcripts,
   - `analyze_calls` → an LLM node (Anthropic/OpenAI) running the agent's operating prompt over the transcript,
   - `send_message` / `send_direct_message` / `send_email` → the chat/email node.
2. **Emit native config when you know the builder's format**, ready to import:
   - **n8n** → a workflow JSON (`nodes` + `connections`, trigger node + steps),
   - **Make** → a scenario blueprint JSON,
   - **Zapier** → the trigger + action steps with field mappings (Zapier has no import JSON, so give exact per-step setup),
   - **LangGraph / code** → a runnable Python script (nodes = functions, the LLM step carries the prompt),
   - **a Claude agent / subagent** → a `.claude/agents/<agent>.md` with the operating prompt + the tools it needs.
   If you are not fully sure of the builder's import schema, say so and produce precise step-by-step build instructions instead of a malformed file.
3. **Preserve, on every path:** the trigger semantics (per-call vs schedule + cron), the full operating prompt, the output format, the edge cases, and the guardrails — especially **draft-only / never auto-send to a customer** where the spec says so, and the final **gtm-humanizer** pass on any drafted message.
4. **Fidelity check:** before finishing, confirm your build covers each numbered step and each edge case in the `.md`. List anything the target builder cannot do natively (e.g., no LLM node connected) and tell the user what to add.

## Step 3 — Report
Summarize: the trigger, the steps you built (or the file you produced and where), which connectors the user must connect, and any gaps. Offer to do the next agent.

## Rules
- The `.md` spec is the contract. Never drop a step, an edge case, or a guardrail in translation.
- Never invent a builder's import schema. Native file when you know it; clear instructions when you don't.
- Don't connect or authenticate anything. You produce the build; the user wires credentials.
