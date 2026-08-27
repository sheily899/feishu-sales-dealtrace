# Writing a Scorecard

This tutorial walks you through creating a custom scorecard from scratch, wiring
it to a call type, and testing it. It should take about 20 minutes.

---

## When to write a custom scorecard

- Your sales motion has specific behaviors the shipped scorecards don't capture
  (e.g., a required product-led growth step, a compliance disclosure, a
  security-qualification gate).
- You want to split a call type into two variants with different rubrics (e.g.,
  a lighter "champion check-in" vs. a full "executive sponsor review").
- You are running the pipeline on a post-sales motion that doesn't match any
  shipped scorecard.

---

## Step 1: Copy an existing scorecard

Start from the closest shipped scorecard rather than from a blank file.

```bash
cp scorecards/discovery.yaml scorecards/my-scorecard.yaml
```

---

## Step 2: Set the header fields

Edit the top of the file:

```yaml
id: my-scorecard          # lowercase, hyphens only — must be unique
name: My Custom Scorecard
version: "1.0"
description: >
  One or two sentences describing what this scorecard measures and for whom.
applies_to: [discovery]   # one or more call-type IDs from config/call_types.yaml
frameworks: [spiced]      # frameworks you'll reference in criteria (can be empty)
```

**Rules:**
- `id` must match `^[a-z0-9-]+$` and be unique across `scorecards/`.
- `applies_to` must reference real call-type IDs (run `dealtrace list call-types`
  to see them).
- `frameworks` is optional but enables the coach to cite framework elements in
  feedback.

---

## Step 3: Define the scoring bands

The defaults work for most use cases. Override them if you want different
thresholds or labels:

```yaml
scoring:
  scale_max: 100
  bands:
    - { label: great,      min: 80, meaning: "Textbook — share as a team example." }
    - { label: good,       min: 60, meaning: "Solid, minor gaps." }
    - { label: developing, min: 40, meaning: "Partially done, room to grow." }
    - { label: poor,       min: 0,  meaning: "Missing or counterproductive." }
```

---

## Step 4: Define your criteria

Replace the copied criteria with your own. Each criterion must have `id`,
`name`, `weight`, and `what_great_looks_like`.

**Weight guidance:**

- All weights are relative and unnormalized. Use `1` for standard criteria and
  `2` or `3` for the highest-leverage behaviors.
- A weight of `2` means this criterion counts twice as much as a weight-`1`
  criterion toward the overall score.
- Aim for 5–10 criteria. Fewer than 5 is too coarse; more than 10 creates
  fatigue and dilutes signal.

**Writing good `what_great_looks_like`:**

- Describe observable behaviors, not internal states. "Rep asked the buyer to
  put a number to the impact" is observable. "Rep understood the impact" is not.
- Use the present tense and be specific enough that a stranger reading the
  transcript could verify the behavior occurred.
- Two to four bullets is the sweet spot.

**Writing good `evidence_cues`:**

- Include verbatim phrases the rep or buyer would say when the behavior occurs.
- Include negative cues (phrases that signal the behavior was missed) if there
  are recognizable anti-patterns.

---

## Complete minimal example

Here is a self-contained example of a minimal but valid scorecard for an
executive-sponsor call:

```yaml
id: exec-sponsor
name: Executive Sponsor / C-Suite Call
version: "1.0"
description: >
  Evaluates how well the rep led a senior executive conversation: leading with
  business outcomes, quantifying ROI, and securing strategic alignment and a
  next commitment.
applies_to: [discovery, demo]
frameworks: [command-of-the-message, meddpicc]

scoring:
  scale_max: 100
  bands:
    - { label: great,      min: 80, meaning: "Textbook executive conversation." }
    - { label: good,       min: 60, meaning: "Solid; minor gaps." }
    - { label: developing, min: 40, meaning: "Partially done." }
    - { label: poor,       min: 0,  meaning: "Missing or counterproductive." }

criteria:
  - id: opens_with_outcome
    name: Opens with Business Outcome, Not Product
    weight: 2
    intent: >
      Executives allocate time based on relevance to their priorities.
      Leading with a product pitch wastes that window.
    framework_refs: [command-of-the-message.positive_business_outcomes]
    what_great_looks_like:
      - "Rep's opening references a business metric or outcome the exec owns."
      - "Rep validates the exec's priorities before introducing any product angle."
    what_poor_looks_like:
      - "Rep leads with a product overview or company history."
      - "Rep asks the exec to re-explain context that was shared in an earlier call."
    evidence_cues:
      - "\"You mentioned revenue growth is the priority — I want to make sure we focus on that.\""
      - "Rep references a metric the exec tracks (revenue, retention, cost)."
    coaching_prompts:
      - "How did you confirm the exec's top priority before the call? Did it match what you led with?"

  - id: quantifies_roi
    name: Quantifies ROI in the Exec's Language
    weight: 3
    intent: >
      Executives approve spend based on numbers, not features. ROI must be
      stated in terms they own and report on.
    framework_refs: [command-of-the-message.metrics, meddpicc.metrics]
    what_great_looks_like:
      - "Rep states a specific, exec-level business outcome (dollars, %, headcount)."
      - "ROI is tied to something the exec is measured on."
      - "Rep helps the exec calculate or confirm the number rather than asserting it."
    what_poor_looks_like:
      - "Value is described as 'efficiency' or 'better' with no number."
      - "Rep presents a generic ROI slide disconnected from the exec's stated priorities."
    evidence_cues:
      - "\"Based on what you shared, this should be worth roughly X per quarter.\""
      - "\"What does a 10% improvement here mean in actual dollars for your team?\""
    coaching_prompts:
      - "Could the exec repeat your ROI claim to their CFO using the language you gave them?"

  - id: identifies_economic_buyer
    name: Confirms Exec Is (or Is Not) the Economic Buyer
    weight: 2
    intent: >
      Not every C-suite contact has signing authority. Knowing the economic buyer
      prevents last-minute escalations that collapse deals.
    framework_refs: [meddpicc.economic_buyer]
    what_great_looks_like:
      - "Rep explicitly confirms whether this exec can approve the spend unilaterally."
      - "If not, rep asks who does and secures a path to that person."
    what_poor_looks_like:
      - "Rep assumes the exec can sign because of their title."
      - "Economic buyer topic never comes up."
    evidence_cues:
      - "\"Is this an investment you can approve on your own, or does it need sign-off from someone else?\""
    coaching_prompts:
      - "Do you know the exact approval path from this call to a signed contract?"

  - id: secures_next_commitment
    name: Secures a Specific, Calendared Next Commitment
    weight: 2
    intent: >
      An exec meeting without a committed next step resets the deal clock.
    framework_refs: [command-of-the-message.positive_business_outcomes]
    what_great_looks_like:
      - "A specific next action with date and owner is agreed before the call ends."
      - "Next step advances the deal (not just 'I'll send a summary')."
    what_poor_looks_like:
      - "Call ends with 'I'll follow up' and no concrete commitment."
    evidence_cues:
      - "\"Can we get 30 minutes with your CFO on the 15th?\""
    coaching_prompts:
      - "What specific action did the exec commit to, and by when?"
```

---

## Step 5: Wire it to a call type

Open `config/call_types.yaml` and add your scorecard's `id` to the relevant
call type's `scorecards` list:

```yaml
  - id: discovery
    name: Discovery
    # … other fields …
    scorecards: [discovery, exec-sponsor]   # add your scorecard here
```

Today the pipeline uses only the **first** scorecard in the list
(`registry.scorecard_for()` resolves `scorecards[0]`). Additional entries act as
documented alternates and are reserved for future multi-scorecard support — they
are not scored or merged yet.

So if you want your new scorecard to be the one that runs, list it **first**
(e.g. `scorecards: [exec-sponsor, discovery]`), or replace the list entirely.

---

## Step 6: Validate

Run the validator to catch problems before your scorecard is used in production. It
checks the whole knowledge base (so it picks up your new file automatically):

```bash
dealtrace validate
# also run the JSON-Schema check used in CI:
python .github/scripts/validate_schemas.py
```

Together they check:
- YAML parses and conforms to `schemas/scorecard.schema.json`.
- All required fields are present and `id` matches the allowed pattern.
- `applies_to` references real call-type IDs.
- `frameworks` references real framework IDs.
- `framework_refs` in criteria match `<framework_id>.<element_id>` pairs that
  exist in the framework files.
- Weights are positive numbers.

---

## Step 7: Test it

Run the pipeline on a real or synthetic transcript to see the scorecard in action:

```bash
dealtrace coach samples/discovery-example.txt
```

Review the output JSON:
- Do the criterion scores look calibrated? (An average call should land 50–65.)
- Are the `evidence` quotes actually from the transcript?
- Do the `better_move` suggestions feel actionable?
- Are the `next_call_focus` items the right 1–3 things?

If a criterion consistently scores 0 or 100 for most calls, it may be too coarse
or too specific. Adjust `what_great_looks_like` and `what_poor_looks_like` to
give the model more calibration signal.

---

## Tuning tips

| Problem | Fix |
|---|---|
| Scores are consistently too high | Add more `what_poor_looks_like` examples; raise the `great` band threshold. |
| Scores are consistently too low | Add more `what_great_looks_like` examples; check that `evidence_cues` are realistic. |
| Criterion is nearly always "developing" | The criterion may be too ambitious for the call type; consider splitting it into two. |
| `better_move` suggestions feel generic | Make `evidence_cues` more specific; add `coaching_prompts` to guide the model. |
| Framework references aren't cited in output | Verify `framework_refs` use the exact `<id>.<element_id>` format and that the framework file exists. |

---

## Cross-references

- Scorecard anatomy: [scorecards.md](./scorecards.md)
- Framework reference: [frameworks.md](./frameworks.md)
- Call type taxonomy: [call-types.md](./call-types.md)
- CLI reference: [architecture.md](./architecture.md)
