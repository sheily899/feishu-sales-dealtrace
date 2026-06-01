---
description: Run a GTM agent from its spec file — reads the agent JSON and runs it natively on Attention, or as a managed Claude agent on any other recorder.
argument-hint: <agent-json-path>
---

Run the GTM agent defined in the spec file.

Target: $ARGUMENTS

## Steps

1. **Load the agent spec.** Read the JSON file at the path above. Extract:
   - `name` — agent display name
   - `template.agent.instructions` — the core prompt (what to do)
   - `integrations` — which service categories this agent needs (crm, communication, call_recorder, email, calendar)
   - `template.agent.tools` — which actions it needs per integration
   - `template.agent.triggers` — what event fires this agent
   - `recommended_trigger` — trigger metadata (type, cron, crm_event)

2. **Confirm the stack, then resolve integrations.** Read `agents/config.yaml`.
   - **If `configured` is not `true`**, the user hasn't set up their stack yet. Pause and run
     `/setup` — or ask inline which call recorder, CRM, communication tool, and email they use —
     confirm, and write the answers back to `agents/config.yaml`. **Do not run on the shipped
     defaults silently**; the `call_recorder` value decides which path below you take.
   - **If `configured: true`**, briefly echo the stack you're about to use (recorder, CRM,
     comms) so the user can catch a wrong setting before anything runs.

   Once the stack is confirmed, the agent's instructions are written Attention-native
   (`ask_attention`, `search_calls`, `get_call_details`); how you run them depends on `call_recorder`:

   **A) `call_recorder: attention` → native path.** The instructions already speak Attention's language. Two ways to run:
   - **Attention's agent builder (best):** these JSON specs are Attention agent-builder templates — import the spec into Attention and it runs natively with `ask_attention` + subtools, no translation. Tell the user this is the recommended way.
   - **Here, via Claude:** if Attention's MCP is connected, call `ask_attention` (NL query/analysis over calls + CRM), `search_calls`, and `get_call_details` directly as the instructions say.

   **B) any other `call_recorder` (gong / chorus / fireflies / otter / grain / recall / …) → managed-agent path.** `ask_attention` doesn't exist off-Attention, so translate it using each tool's `generic_action` (in `template.agent.tools`):
   - `ask_attention` (`generic_action: analyze_calls` / `query_records`) → do the equivalent yourself: read pipeline/deal data from the configured **CRM** (Salesforce/HubSpot/… MCP or API), and retrieve transcripts from the configured recorder — or, if it only exports transcripts, ingest the export with the **gtmsi adapters** (`gtmsi inspect <file>` / `load_transcript`) — then **Claude analyzes the normalized turns** to produce the same result.
   - `search_calls` / `get_call_details` → the recorder's own search/fetch tools, or the gtmsi adapters. Any recorder works this way.

   For both paths, communication/email/calendar resolve the same: `communication: slack` → `mcp__claude_ai_Slack__` (`slack_send_message`); `teams` → Teams MCP; `email: gmail` → `mcp__claude_ai_Gmail__` (`create_draft`); `outlook` → Outlook MCP; `calendar` → that calendar's MCP (`list_events`, `get_event`). If a needed integration isn't connected, tell the user what to connect and continue with what's available.

3. **Handle the trigger.**
   - **`conversation_analyzed`**: Ask the user which call to analyze. Use the call recorder MCP to search for and fetch call data. Then run the agent instructions against that call.
   - **`schedule`**: Tell the user: "This agent is designed to run on a schedule (`{cron}`). Running it once now. To schedule it, use `/schedule`." Then run the agent instructions immediately.
   - **`crm_stage_change`**: Ask the user for the specific opportunity/deal that triggered the change. Use the CRM to fetch the record. Then run the agent instructions.
   - **On-demand** (user just wants to run it): Run the instructions with whatever context is available.

4. **Execute the agent.**
   - Use the agent's `instructions` as your primary guide for what to do
   - Fetch data from the resolved MCP tools as the instructions require
   - For call_recorder data: on Attention, use `ask_attention` / `search_calls` / `get_call_details` directly; on any other recorder, translate per step 2B — read CRM data from the configured CRM and retrieve transcripts via the recorder's tools or the gtmsi adapters, then analyze with Claude
   - For CRM data: query the CRM for accounts, opportunities, contacts as needed
   - For communication output: send messages via the resolved communication MCP
   - For email output: draft/send via the resolved email MCP
   - Format output exactly as the instructions specify

5. **Report results.** After executing, summarize what was done:
   - What data was fetched
   - What messages were sent or drafted
   - Any integrations that weren't available
   - Suggested next steps

## Rules
- Never fabricate data — only use what MCPs return
- If an MCP tool isn't connected, tell the user and skip that part gracefully
- For scheduled agents run on-demand, fetch the data range the agent expects (e.g., "last 7 days" for weekly agents)
- Respect the agent's output format precisely
- If $ARGUMENTS is empty, list available agents from the `agents/` directory and ask the user to pick one

## Available agents
To see all agents: `find agents/ -name "*.json" -not -path "*/_raw/*" | sort`
