# GTM Humanizer

A Claude skill that rewrites AI-generated text — especially drafted emails and messages —
so they read like a specific human wrote them, not a chatbot. Built for GTM copy: cold
emails, follow-ups, Slack messages, handoff notes, and case studies.

This skill is **original to GTM Superintelligence** (Apache-2.0, same as the rest of the
repo). The general idea — that AI prose has recognizable "tells" — is common knowledge;
for a broader public treatment see Wikipedia's
[Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).

## What it does
- Detects common AI-writing tells (em dashes, throat-clearing openers, hype adjectives,
  rule-of-three, no-specifics, etc.) — see [`patterns.md`](./patterns.md).
- Scores how AI the text sounds (0–100, lower = more human).
- Rewrites it in a chosen voice profile (professional · blunt · casual · warm ·
  technical) — see [`voice-profiles.md`](./voice-profiles.md). **Bans em dashes by default.**
- Auto-loads `humanizer-context.md` from the project root for the brand/sender voice.

## Use it
```
/gtm-humanizer "your draft email" --voice professional --purpose email
```
Modes: `--mode detect` (report tells + score only), `rewrite` (default), `edit --file <path>`.

Every message-writing agent in this repo runs it as a final pass before sending, so
drafted emails and messages don't read like a bot.
