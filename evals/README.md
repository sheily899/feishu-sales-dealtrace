# Evals

A small harness to measure coaching quality as you fork and tune the rubrics. Quality
work needs a feedback loop — this is yours.

## Classifier eval

Measures how accurately the classifier picks the right call type.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python evals/run_evals.py
```

It runs every case in [`cases/classification.yaml`](./cases/classification.yaml),
compares the predicted `call_type` to the label, and prints accuracy plus a confusion
matrix (so you can see *which* types get mixed up — usually discovery↔demo or
check-in↔renewal).

### Add your own cases
Append to `cases/classification.yaml`:

```yaml
  - transcript: path/to/your_call.vtt
    expected_call_type: negotiation
    expected_phase: pre-sales
    note: optional context
```

The more varied your cases (edge cases, near-misses, every call type), the more the
number means. Aim for at least a few per call type before trusting the accuracy.

## Coaching-quality eval (suggested workflow)

Scoring quality is harder to grade automatically. Two practical approaches:

1. **Golden reports.** Hand-score a handful of calls (or have a top manager do it),
   save them as golden `*.json` reports, and diff new runs against them — focus on
   whether the *band* and the *top improvement* match, not exact wording.
2. **LLM-as-judge.** Have a second model compare a generated report to a golden one on
   rubric adherence, evidence quality (are quotes real?), and calibration. Flag
   fabricated quotes as automatic failures.

## CI

`run_evals.py` exits non-zero if any case is misclassified, so you can gate merges on
classifier accuracy once you have an API key available to CI. The default CI workflow
does **not** run live evals (no key in CI); it runs the offline unit tests +
`gtmsi validate` instead.
