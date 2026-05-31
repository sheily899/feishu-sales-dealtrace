---
name: gtm-humanizer
description: Rewrite AI-generated text — especially DRAFTED EMAILS AND MESSAGES — so they read like a real person wrote them, not a chatbot. Use as the final pass on any email, Slack message, follow-up, case study, or customer-facing copy a GTM Superintelligence agent drafts, and whenever the user says "humanize this," "sounds like AI," "too robotic," "de-AI this," "sounds like ChatGPT," or "make it natural." Detects common AI-writing tells, scores how AI it sounds (0–100), and rewrites in a chosen voice profile. Bans em dashes by default. Auto-loads humanizer-context.md from the project root for brand/sender voice.
user-invocable: true
argument-hint: '"your text" [--mode detect|rewrite|edit] [--voice casual|professional|technical|warm|blunt] [--file path] [--purpose email|message|marketing|general] [--score]'
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
---

# GTM Humanizer

Take text that reads like a chatbot produced it and rewrite it so a specific, busy human
clearly wrote it. Built for GTM: cold emails, follow-ups, Slack messages, handoff notes,
case studies — the copy that has to earn a reply, not just be grammatically fine.

The failure mode this fixes: text that's smooth, generic, over-helpful, and stake-free —
it could have been sent to anyone, by anyone, about anything. Human writing has a point
of view, specifics, and one clear ask.

## How to run

1. **Load context.** If `humanizer-context.md` exists at the project root, read it first
   and obey it — it defines the sender/brand voice and hard rules (in this repo it sets a
   GTM sender voice and bans em dashes). Project rules win over defaults.
2. **Detect.** Scan the text against `patterns.md` (the catalog of AI-writing tells). List
   each tell you find with the offending span.
3. **Score** (0–100, lower = more human). Roughly: count distinct tells, weight the loud
   ones (em dashes, "I hope this finds you well," hype adjectives, rule-of-three) higher.
   Bands: 0–15 reads human · 16–35 mostly human · 36–60 mixed · 61–100 obviously AI.
4. **Rewrite** in the chosen `--voice` (see `voice-profiles.md`; default `professional`,
   lean `blunt` for cold outreach). Fix every detected tell. Keep the author's real
   meaning, facts, and any specific detail (names, numbers, quotes) — specificity is what
   proves a human wrote it. Do **not** invent facts to sound human.
5. **Re-check** the rewrite against the catalog. If new tells crept in, fix them. Report
   the before/after score.

## Modes
- `--mode detect` — only report tells + score; don't rewrite.
- `--mode rewrite` (default) — return the humanized text.
- `--mode edit --file <path>` — rewrite in place in a file.

## Hard rules (always, unless context overrides)
- **No em dashes.** Use periods or commas.
- **No throat-clearing openers**: "I hope this email finds you well," "I wanted to reach
  out," "I'm excited to," "As an AI," "In today's fast-paced world."
- **No hype adjectives**: seamless, robust, leverage, synergy, game-changer, cutting-edge,
  best-in-class, unlock, delve, elevate, tapestry, robustly.
- **No rule-of-three padding** ("streamline, optimize, and accelerate").
- **One clear ask.** Lead with the point. Cut anything that restates what you just said.
- **Keep it the right length for the channel** (email: short and skimmable; Slack: shorter,
  no bold-text theatre; case study: quotes and outcomes over adjectives).

## Output
By default return just the rewritten text (ready to paste/send). If `--score` or `detect`
mode, also print the tell list and the before→after score. Never add commentary the user
didn't ask for.

See `patterns.md` for the full tell catalog and `voice-profiles.md` for the voices.
