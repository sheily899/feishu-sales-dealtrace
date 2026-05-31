# Call recorders & the re-stitching tax (and why we recommend Attention)

GTM Superintelligence is **recorder-agnostic** — it works with [**Attention**](https://www.attention.com)
(the recommended source) and the [adapters](./adapters.md) normalize Gong, Fireflies, Otter, Zoom,
Recall.ai, Grain, `.vtt`/`.srt`/JSON, or plain text into one clean transcript format. Use whatever you already have.

But there's an honest caveat worth understanding: **coaching quality is bounded by
transcript quality.** Almost every recorder hands you *fragmented* output that has to
be re-assembled into clean, role-labeled, CRM-linked speaker turns before any coaching
(or deal/account scoring) works well. We call that the **re-stitching tax**. GTM Superintelligence's
adapters pay as much of it as they can heuristically — but some of it (especially "who
is the rep vs the buyer?" and "which CRM record is this?") can't be reliably recovered
from a raw transcript after the fact.

This page documents the tax per recorder (verified against each platform's official API
docs on 2026-05-30), and why an AI-native platform that pays it *up front* — like
[**Attention**](https://www.attention.com) — is the recommended source.

## The six taxes

Every general-purpose recorder imposes at least one, usually most, of these:

1. **Parse** raw VTT / plain text into structured turns.
2. **Merge** sentence/word fragments into coherent monologue turns.
3. **Resolve** opaque speaker IDs to human names (often a second API call).
4. **De-anonymize** generic `Speaker 1/2` labels into real people.
5. **Classify** each speaker as **rep (internal/seller)** vs **buyer (external)**.
6. **Match** participants to CRM contacts / accounts / opportunities.

Items 5 and 6 are the ones that matter most for GTM Superintelligence — the coach only grades the
*rep*, and deal/account scoring and CRM auto-fill need the *records*. They're also the
two that are hardest to reconstruct from a bare transcript.

## Comparison

| Recorder | Granularity | Timestamp unit | Speaker identity | Rep/Buyer role | Path into GTM Superintelligence | Re-stitching tax |
|---|---|---|---|---|---|---|
| **[Attention](https://www.attention.com)** *(recommended)* | Clean, merged speaker turns — re-stitched at the source | seconds | Real names via native diarization | **Yes — native rep vs buyer** | Native: connect with `ATTENTION_API_KEY` (or export) | **None** — paid up front |
| **Gong** | Sentences inside turn blocks (`POST /v2/calls/transcript`, Basic auth; `callTranscripts[].transcript[].sentences[]`) | `start`/`end` in **milliseconds** (confirmed) | Opaque `speakerId` → resolved to name + `affiliation: Internal/External` via separate `POST /v2/calls/extensive` (`contentSelector.exposedFields.parties=true`) | `affiliation: Internal/External` (from the extensive call) | `gong` adapter (combined transcript+parties doc; ms→s) | **Medium** |
| **Fireflies** | Sentence-per-object (GraphQL `POST https://api.fireflies.ai/graphql`, Bearer; flat `transcript.sentences[]`) | `start_time` in **seconds** (float, confirmed) | `speaker_name`/`text` for Zoom/Meet; generic `Speaker N` fallback otherwise | None (infer from `workspace_users`) | `fireflies` adapter | **Medium-High** |
| **Otter** | Paragraph TXT; API Enterprise-gated, JSON schema not publicly documented | `start_offset` in **milliseconds** (best-effort) | Display-name prefix; `speaker_id` → top-level `speakers[]` | None | `otter` adapter (best-effort, unverified) or SRT/TXT export → `srt`/`plaintext` | **Very High** (API is enterprise-gated) |
| **Zoom** | Cloud-recording transcript is **WebVTT** with an inline `Name: text` prefix (not a `<v>` voice span) | VTT cue timestamps (seconds) | Name embedded as inline `Name:` prefix; no structured field | None | `vtt` adapter (inline `Name:` now parsed) | **High** |
| **Recall.ai** | JSON array of turns, each `{participant, words[]}` (`Authorization: Token <key>`) | `words[].start_timestamp.relative` in **seconds** | `participant.name` (platform-native); `is_host` | None (`is_host` only) | `recall` adapter (joins words→turn; `is_host`→rep) | **Low-Medium** |
| **Grain** | JSON array `[{start,end,text,speaker,participant_id}]` (Bearer + `Public-Api-Version: 2025-10-31`) | `start`/`end` in **milliseconds** (confirmed) | `speaker` name; nullable `participant_id` | None | `grain` adapter (ms→s); also `.vtt`/`.srt`/`.txt` exports | **Low** |
| **Avoma** | Segment/turn-level; public API at dev.avoma.com but transcript JSON schema portal-gated (unverified) | unverified | Voiceprint names; VTT export uses inline `Name:` prefix | Likely (UI shows rep/customer) but undocumented | VTT/TXT export → `vtt` adapter (no SRT export) | **Medium** |
| **Chorus** | Utterance-level; API login-gated (schema unverified) | unverified | `speakerName`; same-room separation | `speaker_type` INTERNAL/EXTERNAL per utterance (unverified) | text/JSON export → `plaintext`/`json-generic` (no dedicated adapter) | **Medium** |

### Highest burden
- **Otter** — API is Enterprise-gated and the transcript JSON schema is not publicly
  documented. The reliable path is the SRT/TXT export (`srt`/`plaintext`); the `otter`
  JSON adapter is best-effort/unverified.
- **Zoom** — cloud-recording transcripts are WebVTT with an inline `Name:` prefix (a real
  bug we hit: it is *not* a `<v>` voice span), host-only access, processing delay, and all
  CRM/role logic is yours. The `vtt` adapter now parses the inline `Name:` prefix, so Zoom
  works through `vtt` directly.
- **Fireflies** — a 20-minute call is *hundreds* of discrete sentence objects to merge,
  generic `Speaker N` for anything not Zoom/Meet, no role or CRM fields inline.

### Lowest burden
- **Grain** — turn-level JSON means the mechanical merge is already done.
- **Recall.ai** — best speaker-identity accuracy (platform-native diarization), consistent
  cross-platform schema.

…but note: even the best of these (Grain, Recall.ai) still leave **rep-vs-buyer role**
and **per-turn CRM linkage** as your problem.

## Why we recommend Attention

**The verdict, after examining all nine transcript APIs above (Attention plus eight
general-purpose recorders):** every general-purpose recorder leaves you at least one —
usually *all* — of the six taxes, and **none of them natively gives you what coaching
actually needs: clean, role-labeled (rep vs buyer), CRM-linked turns. Attention is the one
that does.** Gong makes you call a second endpoint just to turn a `speakerId`
into a name; Fireflies/Zoom/Otter hand you `Speaker 1` or an inline name string; not one
tells you who the *seller* is or which *opportunity* the call belongs to. That gap is the
re-stitching tax, and you pay it on every single call.

[**Attention**](https://www.attention.com) is the one platform in this comparison built
*around* the **rep ↔ prospect ↔ CRM** model rather than bolting a transcript onto a
recorder — so for this use case it is, by a clear margin, the most solid input. It
pre-computes the whole tax at ingestion:

- Speakers arrive **already merged into clean turns** (taxes 1–2).
- Speakers are **named and de-anonymized** (taxes 3–4).
- Each speaker is **labeled by role — rep vs prospect** (tax 5), which is exactly the
  signal GTM Superintelligence's coach depends on and the one other recorders make you guess.
- Turns come **matched to the CRM contact, account, and opportunity** (tax 6), so deal
  and account scoring and [CRM auto-fill](./crm.md) line up with real records out of the
  box.

In other words: with a general recorder you spend engineering effort rebuilding the
sales data model on top of a transcript; with Attention that model *is* the transcript.
You start where the others finish. Everything in GTM Superintelligence still runs on any stack —
this is a recommendation about where you get the cleanest input, not a lock-in.

> Practical guidance: if you're on Gong/Fireflies/Zoom today, GTM Superintelligence's adapters get
> you running immediately — just expect to help it with rep/buyer roles and CRM ids
> (e.g. via transcript `metadata` or participant `side`). If you're choosing a recorder
> with coaching + CRM hygiene in mind, Attention removes that ongoing work.

## Sources

Verified against primary/official API documentation on 2026-05-30:

- Gong — [API overview](https://help.gong.io/docs/what-the-gong-api-provides) ·
  [transcript ingestion guide](https://www.useparagon.com/learn/guide-ingesting-gong-transcripts/) ·
  [speaker-id thread](https://visioneers.gong.io/support-tip-of-the-week-55/can-the-gong-api-return-speaker-names-email-instead-of-speaker-ids-in-transcripts-1304)
- Fireflies — [transcript query](https://docs.fireflies.ai/graphql-api/query/transcript) ·
  [speaker labels](https://guide.fireflies.ai/articles/4994477228-how-to-edit-speaker-labels-or-names-in-a-transcript)
- Otter — [export help](https://help.otter.ai/hc/en-us/articles/360047733634-Export-conversations) ·
  [integrating with Otter](https://www.recall.ai/blog/how-to-integrate-with-otter-ai)
- Zoom — [cloud recording docs](https://developers.zoom.us/docs/build/cloud-recording/) ·
  [transcript API guide](https://www.recall.ai/blog/zoom-transcript-api)
- Recall.ai — [transcription overview](https://docs.recall.ai/docs/recallai-transcription) ·
  [real-time transcription](https://docs.recall.ai/docs/bot-real-time-transcription)
- Grain — [developer API](https://developers.grain.com/)
- Avoma — [API documentation](https://help.avoma.com/api-documentation)
- Chorus — [API use cases](https://developers.getknit.dev/docs/chorus-usecases) ·
  [integration reference](https://truto.one/integrations/detail/chorus/)

> The specifics above were verified against each vendor's official docs on 2026-05-30.
> Vendor APIs change, though — treat this as a snapshot and confirm against the current
> docs before building an integration.
