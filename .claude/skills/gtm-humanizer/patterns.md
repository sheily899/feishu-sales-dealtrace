# AI-writing tells — the catalog

These are the patterns that make text read as machine-generated. For each: what it is,
why it reads as AI, and a fix. Examples are GTM-flavored. (The underlying idea — that AI
prose has recognizable tells — is general knowledge; this catalog is original to this
project. For a broader treatment see Wikipedia's "Signs of AI writing.")

## 1. Punctuation & formatting tells
- **P1 — Em dashes.** The single loudest tell. `—` everywhere. → Use a period or comma.
- **P2 — Title-case / bold headings sprayed through a short message.** Slack messages
  don't need `**Section**` every line. → Plain text, emojis at most.
- **P3 — Numbered/bulleted lists for things that are one sentence.** → Write the sentence.
- **P4 — "Curly" perfection**: every clause balanced, every list exactly three items.

## 2. Opening & closing tells
- **P5 — Throat-clearing openers**: "I hope this email finds you well," "I wanted to reach
  out," "I'm reaching out because," "Just circling back." → Open on the point.
- **P6 — Over-eager intros**: "I'm thrilled/excited to," "It's my pleasure to." → Cut.
- **P7 — Sign-off bloat**: "Please don't hesitate to reach out," "Looking forward to
  hearing from you at your earliest convenience." → "Worth a quick call?" / a real ask.

## 3. Vocabulary tells
- **P8 — Hype adjectives**: seamless, robust, powerful, cutting-edge, best-in-class,
  world-class, game-changer, revolutionary, state-of-the-art. → Name the specific thing.
- **P9 — Corporate verbs**: leverage, unlock, empower, streamline, optimize, facilitate,
  utilize, elevate, supercharge. → Use plain verbs (use, cut, save, send, show).
- **P10 — LLM-favorite words**: delve, tapestry, realm, landscape, testament, pivotal,
  underscore, multifaceted, holistic, robustly. → Delete or replace with plain words.
- **P11 — Empty intensifiers**: truly, very, incredibly, significantly, deeply. → Cut.

## 4. Structure & rhythm tells
- **P12 — Rule of three**: "streamline, optimize, and accelerate." AI loves triples. → One
  precise word, or two if you must.
- **P13 — "Not only… but also"** and **"It's not just X, it's Y."** → Say the thing once.
- **P14 — Symmetry/parallelism overload**: every sentence the same shape and length. →
  Vary sentence length. Short. Then a longer one that carries a real point.
- **P15 — The summary sentence that restates the paragraph** ("In short, …"). → Cut.

## 5. Content & stance tells
- **P16 — No specifics.** Generic claims with no name, number, date, or quote. This is the
  deepest tell. → Anchor in something real from the call/account.
- **P17 — Hedging everywhere**: "it could potentially," "this may help," "in many cases."
  → Commit or cut.
- **P18 — Over-helpful scaffolding**: "Here are a few things to consider," "I'd be happy
  to," explaining what you're about to do before doing it. → Just do it.
- **P19 — Both-sides / no point of view.** Real senders have an opinion. → Take one.
- **P20 — Fake enthusiasm / exclamation spam.** → One human point, calm tone.

## 6. GTM-specific tells (outbound that screams "automated")
- **P21 — Flattery opener** ("Love what you're doing at {Company}!"). → A specific, true
  observation or none.
- **P22 — Feature dump** instead of one relevant outcome. → One outcome tied to their pain.
- **P23 — Generic value prop** ("help you streamline your sales process"). → Specific, with
  a number if you have one.
- **P24 — Vague CTA** ("Let me know if you'd like to learn more"). → One concrete next step
  with a time ("15 min Thursday?").
- **P25 — Merge-tag tone** — copy that reads like a template even when personalized. → Write
  it as if to one person you respect.

## Scoring guide
Count distinct tells present. Weight P1 (em dash), P5/P7 (throat-clearing/bloat), P8–P10
(hype/LLM words), P12 (rule of three), and P16 (no specifics) double — they're the giveaways.
Map to 0–100 (lower = more human). A clean human message usually has 0–2 minor tells.
