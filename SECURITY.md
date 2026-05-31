# Security Policy

GTM Superintelligence processes sales/customer call transcripts and can connect to
CRMs — so we take security and privacy seriously, and we hardened the project *before*
asking anyone to put it in front of real data.

## Reporting a vulnerability

Please report security issues privately to **security@attention.com** (or open a GitHub
security advisory). Do not file public issues for vulnerabilities. We aim to acknowledge
within 2 business days.

## What the tool does and doesn't do with your data

- **Transcripts stay local** unless *you* send them somewhere: the Anthropic API (only
  when you run live coaching with your `ANTHROPIC_API_KEY`), or a CRM you explicitly
  connect. Running inside Claude Code needs no API key and sends nothing externally.
- **Telemetry is opt-in and off by default**, and never includes transcript content or
  PII — see [docs/telemetry.md](./docs/telemetry.md).
- **CRM writes are dry-run by default.** Live writes require credentials you provide and
  are clearly flagged.
- **`--redact`** masks obvious PII (emails, phones, SSNs, cards, URLs) before any model
  call. It's best-effort, not a compliance guarantee — see
  [docs/privacy-and-pii.md](./docs/privacy-and-pii.md).

## Using community-contributed templates safely

The [agent templates](./agents) and YAML rubrics are configuration/prompts, not executable
code — but they *do* instruct an LLM and can reference CRM/Slack actions. Treat any
**externally contributed** template like untrusted input:

- Review a template's instructions and tool/trigger config before enabling it against
  real systems.
- Grant the **least privilege** needed (read-only CRM scopes where possible; scoped
  Slack channels).
- Be wary of prompt-injection in transcripts themselves: an agent that reads call text
  should not be given destructive, unconfirmed write permissions.

## Secrets

Never commit API keys. Use environment variables / `.env` (gitignored). `ATTENTION_API_KEY`,
`SF_ACCESS_TOKEN`, `HUBSPOT_ACCESS_TOKEN`, and `ANTHROPIC_API_KEY` should come from your
secret manager in production.
