# Team Collab Agent — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../team-collab-agent.md`](../team-collab-agent.md)). A verified, importable Make **blueprint JSON**
will be added here once we validate it against a blueprint exported from a real Make account. Until
then, assemble the scenario from these modules.

## Modules (in order)

1. **Webhooks → Custom webhook** — point your call recorder's "conversation analyzed" webhook here.
   The payload should carry the call id.
2. **HTTP → Make a request** to your call recorder's API — fetch the transcript + metadata for that
   call. (Recorder that only exports transcripts? Pull from where you store them, or pre-ingest via
   the gtmsi adapters.)
3. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 2000`, a single user message = the **Team Collab operating prompt**
     (see [`../team-collab-agent.md`](../team-collab-agent.md)) with the call mapped in. Tell it to
     output `NO_SIGNALS` when no team is needed, otherwise one block per team.
4. **Router / Filter** — only continue if `{{3.content[0].text}}` does not contain `NO_SIGNALS`.
5. **Slack → Create a Message** — post the model output. To route each team's block to its own
   channel, add a Router with one route per team and map the matching block + channel id; otherwise
   post the combined output to a general collaboration channel.

## Notes
- One call can route to several teams; the per-team routing happens at step 5.
- Guardrails from the spec hold: alerts-only to internal channels, evidence-bound, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
