# Voice profiles

Pick the voice with `--voice` (or infer it from the audience). Default `professional`;
lean `blunt` for cold outreach. All voices obey the hard rules in SKILL.md (no em dashes,
no throat-clearing, no hype words) and any `humanizer-context.md` at the project root.

## professional (default)
A competent peer who respects the reader's time. Plain, direct, warm enough. Short
sentences, one ask, specific nouns. Not stiff, not chummy.
- *"Quick recap from today plus the two things you wanted before looping in Finance."*

## blunt
For cold outreach and busy execs. Maximum signal, minimum words. Lead with the point or
the number. No hedging, no setup. One sharp ask.
- *"You said reporting eats ~15 hrs/week. We cut that to near-zero. 15 min Thursday?"*

## casual
Peer-to-peer, conversational, contractions, a little personality. For warm relationships
and internal messages. Still tight, still one point.
- *"Hey, that pricing question from the call kept nagging me. Here's the real answer."*

## warm
Relationship-first: for renewals, check-ins, and customers you have history with.
Acknowledges the person, stays specific, never gushes.
- *"Great catching up. You'd flagged onboarding for the new team — here's the plan we
  talked through, plus who owns what."*

## technical
For technical buyers/evaluators. Precise, concrete, no marketing. Names the mechanism,
the constraint, the trade-off. Respects that the reader can smell fluff instantly.
- *"It writes back to the Opportunity on stage change via the REST API. Field-level
  security applies, so the integration user needs edit on those fields."*

---

**Choosing:** match the voice to the *audience*, not the topic. A technical topic to a CFO
is still `professional`/`blunt`, not `technical`. When unsure, default to `professional`,
and keep the sender's real voice if one is evident in the source.
