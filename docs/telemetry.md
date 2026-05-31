# Telemetry & privacy

GTM Superintelligence has **opt-in, anonymous** usage telemetry. It is **OFF by
default**. We chose opt-in deliberately: dev tools run on trust, and silent or
opt-out telemetry reliably backfires.

## What it does (only when you enable it)

When enabled, the tool sends a tiny event on each command:

| Field | Example | Notes |
|---|---|---|
| `event` | `command` | the kind of event |
| `name` | `coach` | which subcommand ran |
| `version` | `0.1.0` | the package version |
| `machine` | `a1b2c3…` (16 hex) | a salted one-way hash of user@host — **not reversible** to a person |
| `account` | `9f8e…` (12 hex) | present **only if** you've connected Attention (`ATTENTION_API_KEY`); a hash, never the key |

**It never sends:** transcript content, call text, customer names, scores, report
contents, file paths, CRM data, or any PII.

## Turning it on / off

```bash
gtmsi telemetry status     # show current state (default: disabled)
gtmsi telemetry enable     # opt in
gtmsi telemetry disable    # opt out
```

Or via environment (env wins over the saved setting):

```bash
export GTMSI_TELEMETRY=1   # on
export GTMSI_TELEMETRY=0   # off
```

State is stored in `~/.config/gtm-superintelligence/config.json`. **No collector
endpoint ships with the project** — events are only sent if you *both* opt in **and**
set your own collector via `GTMSI_TELEMETRY_ENDPOINT`. So out of the box, even "enabled"
sends nowhere until you point it at an endpoint you control.

## How adoption is understood without telemetry

Most signal comes from things that need **no** tracking code:
- The tracked **"powered by" links** on rendered output (UTM params → Attention's web
  analytics). Turn the footer off with `GTMSI_NO_ATTRIBUTION=1`.
- **Connecting Attention** (`ATTENTION_API_KEY`) — that's an explicit, identified action.
- Public GitHub stars/forks and package download counts.

See [distribution.md](./distribution.md).
