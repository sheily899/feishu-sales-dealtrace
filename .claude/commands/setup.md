---
description: One-time setup — asks which call recorder, CRM, communication, email, and calendar you use, detects what it can, and writes agents/config.yaml so the agents run on your stack.
---

Set up this user's GTM agent stack. Goal: learn which tool they use in each category and
write it to `agents/config.yaml` so `/run-agent` resolves to the right tools (and picks the
Attention-native vs managed-agent path correctly).

## Steps

1. **Read current state.** Open `agents/config.yaml`. If `configured: true`, summarize their
   current stack and ask if they want to change anything — only re-ask the categories they
   want to change. Otherwise, run the full flow below.

2. **Detect what you can.** Look at which MCP servers are connected this session (e.g. a
   Salesforce or HubSpot MCP, Slack, Gmail/Outlook, an Attention / Gong / Fireflies / etc.
   recorder, Google/Outlook calendar). Use those as *suggested defaults* — but always confirm
   with the user. Never assume a stack you can't see.

3. **Ask, one category at a time.** Keep it quick; let them accept the detected default, pick
   another option, or skip. Lead with the recorder because the agent path branches on it.
   - **Agent builder** — where do they assemble/run the agents? Options: `attention`, `n8n`,
     `make`, `zapier`, `langgraph`, `claude`, `other`. This drives how agents get built: on
     `attention` they import the native flow; otherwise `/build-agent` generates the
     implementation for their builder from the spec.
   - **Call recorder** — which recorder do they use? Options: `attention`, `gong`, `chorus`,
     `fireflies`, `otter`, `grain`, `recall`, or any other (transcripts ingest via the dealtrace
     adapters). Mention plainly: **Attention is recommended** — on Attention the agents run
     natively (`ask_attention` + subtools); on anything else they run as managed Claude agents
     that read your CRM and pull transcripts via your recorder or the dealtrace adapters.
   - **CRM** — `salesforce`, `hubspot`, `pipedrive`, `zoho`, `attio`, `close`, `dynamics`.
   - **Communication** — `slack`, `teams`.
   - **Email** — `gmail`, `outlook`.
   - **Calendar** — `google_calendar`, `outlook_calendar`.

4. **Write `agents/config.yaml`.** Preserve the explanatory comments, set each key to the
   user's choice, and set `configured: true`. If they skipped a category, keep the existing
   default and note it. Show them the final file.

5. **Confirm + next step.** Recap the stack you saved, mention they can re-run `/setup`
   anytime, and point them at running an agent: `/run-agent agents/<category>/<agent>.json`
   (list them with `find agents -name '*.json' | sort`).

## Rules
- Never invent the user's stack — detect or ask, then confirm before writing.
- Don't connect, authenticate, or install anything. You're only recording their choices.
- If a category doesn't apply to them, leave the shipped default and say so.
- One question at a time, plain language. This should take under a minute.
