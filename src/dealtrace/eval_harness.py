"""Small, evidence-oriented metrics for customer-state Golden Cases."""
from __future__ import annotations

from typing import Any

from .models import AppliedIssueOperation, CustomerIssue

# 相似度阈值：中文短句在改写后，关键实词的 bigram 重合度通常能到 0.35+；
# 完全不相关的句子通常低于 0.2。这个值需要你拿实际报告里的几组配对结果
# 手动核对几次后微调——先偏保守（宁可漏判为不匹配，也不要把两件不相关
# 的事误判为同一件事）。
DEFAULT_SIMILARITY_THRESHOLD = 0.35


def _char_bigrams(text: str) -> set[str]:
    """Character bigrams; works reasonably for Chinese without a segmenter."""
    text = text.strip()
    if len(text) < 2:
        return {text} if text else set()
    return {text[i : i + 2] for i in range(len(text) - 1)}


def _similarity(a: str, b: str) -> float:
    """Dice coefficient over character bigrams. 1.0 = identical, 0.0 = no overlap."""
    if a == b:
        return 1.0
    set_a, set_b = _char_bigrams(a), _char_bigrams(b)
    if not set_a or not set_b:
        return 0.0
    return 2 * len(set_a & set_b) / (len(set_a) + len(set_b))


def _match_group(
    expected: set[str], actual: set[str], threshold: float
) -> tuple[int, int, int, list[tuple[str, str, float]]]:
    """Greedy best-match bipartite matching within one change group (added/resolved/transitions).

    Returns (tp, fp, fn, matched_pairs) where matched_pairs is for debugging/inspection —
    print it when a report looks wrong, to see exactly which gold/actual strings were paired
    and at what similarity score.
    """
    expected_list, actual_list = list(expected), list(actual)
    used_actual: set[int] = set()
    matched_pairs: list[tuple[str, str, float]] = []
    tp = 0
    for exp_item in expected_list:
        best_index, best_score = None, 0.0
        for index, act_item in enumerate(actual_list):
            if index in used_actual:
                continue
            score = _similarity(exp_item, act_item)
            if score > best_score:
                best_score, best_index = score, index
        if best_index is not None and best_score >= threshold:
            used_actual.add(best_index)
            tp += 1
            matched_pairs.append((exp_item, actual_list[best_index], best_score))
    fn = len(expected_list) - tp
    fp = len(actual_list) - len(used_actual)
    return tp, fp, fn, matched_pairs


def score_changes(
    expected: dict[str, set[str]],
    actual: dict[str, set[str]],
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> dict[str, float | int]:
    """Score state-change keys across all change kinds using fuzzy (bigram) matching
    instead of exact string equality, because gold labels and model output are written
    in different wording even when they describe the same fact.

    Matching is done independently within each group (added / resolved / transitions) —
    an "added" item can never match a "resolved" item, even if the text is similar,
    since being newly identified and being marked resolved are different claims.
    """
    tp = fp = fn = 0
    debug_pairs: list[tuple[str, str, str, float]] = []
    for key in set(expected) | set(actual):
        group_tp, group_fp, group_fn, pairs = _match_group(
            expected.get(key, set()), actual.get(key, set()), threshold
        )
        tp += group_tp
        fp += group_fp
        fn += group_fn
        debug_pairs.extend((key, e, a, s) for e, a, s in pairs)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "_matched_pairs": debug_pairs,  # 调试用，run_eval.py 若不需要可以忽略这个 key
    }


def score_traps(
    traps: list[dict[str, Any]],
    expected: dict[str, Any],
    actual: dict[str, Any],
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> dict[str, int]:
    """Judge only explicit retention/no-jump traps; skip business rules marked optional."""
    checked = intercepted = violations = 0
    expected_concerns = set(expected.get("unresolved_concerns", []))
    actual_concerns = set(actual.get("unresolved_concerns", []))
    for trap in traps:
        rule = str(trap.get("expected_behavior", ""))
        if "暂不强制" in rule or "开放判断点" in rule:
            continue
        if "阶段" in rule and ("跳" in rule or "迁移" in rule):
            checked += 1
            ok = actual.get("stage") == expected.get("stage")
        elif "未解决" in rule or "未确认" in rule or "保持" in rule:
            checked += 1
            # 模糊匹配替代 issubset 的精确集合包含判断：每条期望保留的顾虑，
            # 只要能在 actual 里找到相似度达标的对应项就算保留成功；
            # 不要求文字完全一致。
            ok = all(
                any(_similarity(exp, act) >= threshold for act in actual_concerns)
                for exp in expected_concerns
            )
        else:
            continue
        intercepted += int(ok)
        violations += int(not ok)
    return {"checked": checked, "intercepted": intercepted, "violations": violations}


def grounding_rate(change: Any, message_texts: list[str]) -> tuple[int, int]:
    """Return grounded change evidence count and total evidence count.

    Kept as exact substring containment on purpose — evidence should literally
    quote the source message, so this is the one place exact matching is correct,
    not a bug to fix.
    """
    evidence = list(change.evidence)
    for group in (change.added, change.resolved, change.status_transitions):
        for item in group:
            evidence.extend(item.evidence)
    total = len(evidence)
    grounded = sum(bool(q.text) and any(q.text in text for text in message_texts) for q in evidence)
    return grounded, total


def estimate_tokens(*parts: str) -> int:
    """Conservative character estimate; providers currently do not expose usage here."""
    return sum((len(part) + 3) // 4 for part in parts)


def _exact_metrics(tp: int, fp: int, fn: int, applicable: bool) -> dict[str, Any]:
    if not applicable:
        return {
            "tp": 0,
            "fp": 0,
            "fn": 0,
            "precision": None,
            "recall": None,
            "f1": None,
            "applicable": False,
        }
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "applicable": True,
    }


def _evidence_ids(operation: AppliedIssueOperation) -> set[str]:
    return {quote.message_id for quote in operation.evidence if quote.message_id}


def score_issue_operations(
    expected: list[dict[str, Any]],
    actual: list[AppliedIssueOperation],
    issue_bindings: dict[str, str],
) -> dict[str, Any]:
    """Score lifecycle changes without title similarity.

    A gold ``issue_key`` is bound to the program-assigned ``issue_id`` when its
    create operation first matches. Later operations must use that exact identity.
    Category, operation kind, and evidence message IDs must also agree.
    """
    if not expected and not actual:
        return _exact_metrics(0, 0, 0, False) | {
            "matched": [], "unmatched_gold": [], "unmatched_actual": [], "extra_untracked": []
        }
    if not expected:
        return _exact_metrics(0, 0, 0, False) | {
            "matched": [],
            "unmatched_gold": [],
            "unmatched_actual": [],
            "extra_untracked": [operation.model_dump() for operation in actual],
        }

    used_actual: set[int] = set()
    matched: list[dict[str, Any]] = []
    unmatched_gold: list[dict[str, Any]] = []
    for gold in expected:
        issue_key = str(gold["issue_key"])
        required_evidence = set(gold.get("evidence_message_ids", []))
        expected_id = issue_bindings.get(issue_key)
        found: int | None = None
        for index, operation in enumerate(actual):
            if index in used_actual:
                continue
            if operation.operation != gold["operation"] or operation.category != gold["category"]:
                continue
            if required_evidence and not required_evidence.issubset(_evidence_ids(operation)):
                continue
            if gold["operation"] == "create":
                if expected_id and operation.issue_id != expected_id:
                    continue
            elif not expected_id or operation.issue_id != expected_id:
                continue
            found = index
            break
        if found is None:
            unmatched_gold.append(gold)
            continue
        used_actual.add(found)
        operation = actual[found]
        if gold["operation"] == "create":
            issue_bindings[issue_key] = operation.issue_id
        matched.append({"gold": gold, "actual": operation.model_dump()})

    tracked_ids = set(issue_bindings.values())
    unmatched_operations = [
        operation for index, operation in enumerate(actual) if index not in used_actual
    ]
    unmatched_actual = [
        operation.model_dump() for operation in unmatched_operations
        if operation.issue_id in tracked_ids
    ]
    extra_untracked = [
        operation.model_dump() for operation in unmatched_operations
        if operation.issue_id not in tracked_ids
    ]
    metrics = _exact_metrics(
        len(matched), len(unmatched_actual), len(unmatched_gold), True
    )
    return metrics | {
        "matched": matched,
        "unmatched_gold": unmatched_gold,
        "unmatched_actual": unmatched_actual,
        "extra_untracked": extra_untracked,
    }


def apply_strict_audit(
    score: dict[str, Any],
    reviewed_false_matches: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Apply human-confirmed match corrections without changing official scoring.

    A reviewed false match is represented by its ``matched`` index (or a gold
    ``issue_key``).  It is removed from TP and counted as both FP and FN: the
    predicted operation is wrong, and the expected business event remains
    missed.  This deliberately lives beside, rather than inside, the frozen
    scorer so historical reports remain comparable.
    """
    reviews = reviewed_false_matches or []
    if not reviews:
        return dict(score) | {"audit_reviews": [], "audit_metrics": {
            key: score[key] for key in ("tp", "fp", "fn", "precision", "recall", "f1")
        }}
    matched = list(score.get("matched", []))
    selected: list[dict[str, Any]] = []
    for review in reviews:
        idx = review.get("matched_index")
        if idx is None and review.get("issue_key") is not None:
            idx = next((i for i, item in enumerate(matched)
                        if item.get("gold", {}).get("issue_key") == review["issue_key"]), None)
        if isinstance(idx, int) and 0 <= idx < len(matched) and idx not in {x.get("matched_index") for x in selected}:
            selected.append({**review, "matched_index": idx})
    n = len(selected)
    tp = max(0, int(score.get("tp", 0)) - n)
    fp = int(score.get("fp", 0)) + n
    fn = int(score.get("fn", 0)) + n
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return dict(score) | {"audit_reviews": selected, "audit_metrics": {
        "tp": tp, "fp": fp, "fn": fn, "precision": precision,
        "recall": recall, "f1": f1,
    }}


def score_issue_state(
    expected: list[dict[str, Any]],
    actual: list[CustomerIssue],
    issue_bindings: dict[str, str],
) -> dict[str, Any]:
    """Score tracked state by stable identity, category, status, and evidence.

    Lifecycle v2 sidecars are explicitly focused annotations. Untracked extra
    issues are reported separately and are not silently counted as false positives.
    """
    if not expected:
        return _exact_metrics(0, 0, 0, False) | {
            "matched": [], "unmatched_gold": [], "mismatched_actual": [],
            "extra_untracked": [issue.model_dump() for issue in actual],
        }
    actual_by_id = {issue.issue_id: issue for issue in actual}
    tracked_ids = {issue_id for issue_id in issue_bindings.values()}
    matched: list[dict[str, Any]] = []
    unmatched_gold: list[dict[str, Any]] = []
    mismatched_actual: list[dict[str, Any]] = []
    for gold in expected:
        issue_id = issue_bindings.get(str(gold["issue_key"]))
        issue = actual_by_id.get(issue_id or "")
        required_evidence = set(gold.get("evidence_message_ids", []))
        actual_evidence = {
            quote.message_id for quote in issue.evidence_history if quote.message_id
        } if issue else set()
        ok = bool(
            issue
            and issue.category == gold["category"]
            and issue.status == gold["status"]
            and required_evidence.issubset(actual_evidence)
        )
        if ok:
            matched.append({"gold": gold, "actual": issue.model_dump()})
        else:
            unmatched_gold.append(gold)
            if issue:
                mismatched_actual.append(issue.model_dump())
    extra_untracked = [
        issue.model_dump() for issue in actual if issue.issue_id not in tracked_ids
    ]
    metrics = _exact_metrics(
        len(matched), len(mismatched_actual), len(unmatched_gold), True
    )
    return metrics | {
        "matched": matched,
        "unmatched_gold": unmatched_gold,
        "mismatched_actual": mismatched_actual,
        "extra_untracked": extra_untracked,
    }
