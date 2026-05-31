# Coaching pipeline — turn-by-turn checklist

A condensed version of the four stages. Follow top to bottom for one transcript.

## 0. Normalize
- [ ] Read the transcript. If it's a recorder export or subtitle file, convert to
      `Speaker (side): text` turns. Identify which speaker is the **rep** (seller/CSM)
      vs the **buyer** (prospect/customer). Coach the rep.

## 1. Classify  → `config/call_types.yaml`
- [ ] Pick ONE `call_type` from the dominant *purpose* of the call.
- [ ] Set `phase` (pre-sales / post-sales / neither).
- [ ] Confidence (0–1) + one-line rationale citing evidence.
- [ ] Tie-breakers: cold-call vs discovery (ask = meeting vs info); discovery vs demo
      (questioning vs showing); demo vs technical-validation (seller shows vs buyer
      tests); negotiation vs closing vs go-no-go (terms vs signature vs whether-to);
      check-in vs renewal (no contract event vs contract event).

## 2. Outcomes  → `config/outcomes.yaml`
- [ ] Pull the call type's `default_outcomes`.
- [ ] Refine each into a concrete, deal-specific statement.
- [ ] Add any obvious missing outcome; drop ones that didn't apply.
- [ ] Status each: achieved / partial / missed / unknown + evidence.

## 3. Score  → `scorecards/<call_type>.yaml` (+ cited `frameworks/*.yaml`)
- [ ] For each criterion: score 0–100, band via `scoring.bands`, rationale, 1–3 quotes.
- [ ] Use framework vocabulary where it sharpens the point.
- [ ] Overall = weighted average (normalize the `weight` fields).

## 4. Coach
- [ ] Strengths (2–4) with evidence.
- [ ] Improvements (2–5, high→low): what happened + why + criterion + evidence +
      a concrete **better move** in quotes.
- [ ] Next-call focus (1–3).
- [ ] Optional manager notes (deal risk / patterns).

## 5. Render
- [ ] Markdown report by default; JSON (per `schemas/coaching_report.schema.json`) on
      request.
