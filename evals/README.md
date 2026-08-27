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

## Customer-state lifecycle eval（正式入口）

The formal dataset lives in [`cases/`](./cases/): it contains six
multi-day cases covering discovery, product demo, technical integration, pricing,
post-signing implementation, and renewal handling. Each case declares its
`source_type`; adapted cases also name the source and the single dialogue
dynamic borrowed from it. The runner defaults to this directory, and also
uses the `cases/` directory through `--cases-dir`.

```bash
python evals/run_eval.py
```

This is the only formal daily command. It writes exactly `reports/eval_report.json`
and `reports/eval_report.md`, with identity-based state/change P/R/F1 plus evidence
grounding, hallucination interception and VSU/1K token efficiency.

State changes follow one mutually exclusive convention: `resolved` records an
explicitly resolved concern/problem or a completed todo; `status_transitions`
records only an explicit business-object transition (`opportunity`,
`customer_intent`, or `solution`). A todo completion must not be emitted in both
arrays. Golden Cases must declare `object_type` for every
`status_transitions` entry so the evaluator can reject ambiguous or duplicate
annotations before scoring.

A `todo` requires an explicit future-action commitment from a participant;
coaching recommendations and unanswered follow-up questions are not todos.
Likewise, a `resolved` item must link to an unresolved item retained from the
previous state. The current state model persists the opportunity stage, so it
can validate opportunity-stage transitions; it rejects customer-intent and
solution transitions until those business objects have persistent history.

### 统一事项生命周期口径

The canonical state now stores generic `issues`. Every issue has a stable
`issue_id`, category, business object, `open|resolved` status, evidence history,
creation/update message IDs, and source timestamps when available. The model
does not return a second full state snapshot. It proposes only
`create|update|resolve|reopen` operations; deterministic application code checks
the historical identity and new-message evidence before deriving the final
state and the legacy collection projections.

Separate business objects always receive separate IDs even when they share a
category. Ongoing correlation uses the assigned ID, so a changed title cannot
break the link. A resolve/reopen operation without a historical ID, exact new
evidence, the matching category/business object, or a compatible old status is
rejected. The compatibility adapter accepts saved v1 `{state, change}` model
responses, but deliberately ignores the duplicate `state` object and treats
`change` as its only mutation source. Exact normalized-title lookup exists only
for an unambiguous one-time legacy migration; it is not the v2 correlation rule.

The old title-similarity runner, Golden and reports are archived in `legacy/` for
historical traceability only. The formal runner scores stable identity, category,
status, operation kind, and evidence message IDs:

```bash
# One online run of all six cases, written as eval_report.{json,md}
python evals/run_eval.py

# Deterministic replay of already captured real model JSON
python evals/run_eval.py --replay-dir evals/legacy/replay_logs/run_01

# Optional: evaluate only one explicitly selected case
python evals/run_eval.py --sidecar evals/cases/case_01_discovery_lifecycle.json
```

The sidecar declares `annotation_scope: focused_tracked_issues`. Correct but
unannotated extra issues are reported under `extra_untracked` for review rather
than silently counted as false positives. A day with neither expected nor
actual lifecycle changes is reported as N/A. The frozen legacy identity,
configuration, hashes, and scores remain under `legacy/`.

## CI

`run_evals.py` exits non-zero if any case is misclassified, so you can gate merges on
classifier accuracy once you have an API key available to CI. The default CI workflow
does **not** run live evals (no key in CI); it runs the offline unit tests +
`dealtrace validate` instead.

## 最近一次六案例正式评测指标

以下为当前六案例、18 轮连续对话的一次正式评测结果；在线模型存在随机性，
这些数字不是多次运行均值，也不代表长期生产效果。

| 指标 | 结果 |
|---|---:|
| Change Precision（事项变化判断准确率） | 84.6% |
| State Precision（当前状态判断准确率） | 94.1% |
| Change F1（事项变化综合指标） | 67.8% |
| State F1（状态追踪综合指标） | 67.5% |
| Change Recall（事项变化覆盖率） | 55.6% |
| State Recall（状态追踪覆盖率） | 58.3% |
| Evidence Grounding（证据可追溯率） | 100% |

Precision 表示系统输出的事项中有多少判断正确，Recall 表示 Golden 标注事项中有多少被覆盖，F1 是二者的综合指标；Evidence Grounding 表示每条状态结论都能回溯到原始聊天消息证据。
