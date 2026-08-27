#!/usr/bin/env python3
"""Classifier eval harness.

Runs the call-type classifier over labeled cases and reports accuracy plus a small
confusion matrix. Requires ANTHROPIC_API_KEY (it calls the real model). Extend
``cases/classification.yaml`` with your own calls to measure your fork.

Usage:
    python evals/run_evals.py
    python evals/run_evals.py --cases evals/cases/classification.yaml --model claude-sonnet-4-6
"""
from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

import yaml

# Allow running from a checkout without installing.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dealtrace.adapters import load_transcript  # noqa: E402
from dealtrace.pipeline import classify  # noqa: E402
from dealtrace.registry import load_registry  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=str(Path(__file__).parent / "cases" / "classification.yaml"))
    ap.add_argument("--model", default=None)
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    cases = yaml.safe_load(Path(args.cases).read_text())["cases"] or []
    if not cases:
        print(f"No cases found in {args.cases}.")
        return 2
    reg = load_registry()

    try:
        from dealtrace.llm import AnthropicCoach

        llm = AnthropicCoach(model=args.model) if args.model else AnthropicCoach()
    except Exception as e:  # noqa: BLE001
        print(f"Cannot run eval without an LLM: {e}")
        print("Set ANTHROPIC_API_KEY and `pip install anthropic`.")
        return 2

    correct = 0
    confusion: dict[tuple[str, str], int] = collections.Counter()
    rows = []
    for case in cases:
        path = repo_root / case["transcript"]
        t = load_transcript(str(path))
        c = classify(t, reg, llm)
        expected = case["expected_call_type"]
        ok = c.call_type == expected
        correct += ok
        confusion[(expected, c.call_type)] += 1
        rows.append((case["transcript"], expected, c.call_type, c.confidence, ok))
        mark = "✓" if ok else "✗"
        print(f"{mark} {Path(case['transcript']).name:28} expected={expected:20} got={c.call_type:20} ({c.confidence:.0%})")

    n = len(cases)
    print(f"\nAccuracy: {correct}/{n} = {correct / n:.0%}")

    misses = [(e, g, cnt) for (e, g), cnt in confusion.items() if e != g]
    if misses:
        print("\nConfusions (expected -> got):")
        for e, g, cnt in sorted(misses, key=lambda x: -x[2]):
            print(f"  {e} -> {g}  x{cnt}")

    return 0 if correct == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
