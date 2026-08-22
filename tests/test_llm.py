"""Tests for the LLM->JSON boundary in AnthropicCoach.complete_json.

These exercise the truncation-aware retry without hitting the network or needing
the `anthropic` package: we build the coach with ``__new__`` and inject a fake
client that returns canned (text, stop_reason) responses and records the
``max_tokens`` it was called with.
"""
import json
import sys
import types

import pytest

from gtmsi.llm import AnthropicCoach, DeepSeekCoach, LLMError, _normalize_deepseek_response, build_coach


class _FakeBlock:
    type = "text"

    def __init__(self, text):
        self.text = text


class _FakeResp:
    def __init__(self, text, stop_reason):
        self.content = [_FakeBlock(text)]
        self.stop_reason = stop_reason


class _FakeMessages:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []  # max_tokens per create() call, in order

    def create(self, *, model, max_tokens, system, messages):
        self.calls.append(max_tokens)
        return self._responses.pop(0)


class _FakeClient:
    def __init__(self, responses):
        self.messages = _FakeMessages(responses)


def _coach(responses, max_tokens=4096):
    coach = AnthropicCoach.__new__(AnthropicCoach)  # bypass __init__ (no key/SDK needed)
    coach.client = _FakeClient(responses)
    coach.model = "claude-sonnet-4-6"
    coach.max_tokens = max_tokens
    return coach


def _complete(coach, max_tokens=4096):
    return coach.complete_json(system="sys", cached_blocks=[], user_text="u", max_tokens=max_tokens)


def test_truncation_retry_raises_the_budget():
    # First call truncates at the cap; the retry must go out with a larger budget.
    coach = _coach([
        _FakeResp('{"a": 1, "b": "cut off here', "max_tokens"),
        _FakeResp('{"a": 1, "b": "ok"}', "end_turn"),
    ])
    assert _complete(coach, max_tokens=4096) == {"a": 1, "b": "ok"}
    assert coach.client.messages.calls == [4096, 8192]  # doubled on truncation


def test_retry_budget_capped_at_ceiling():
    # Doubling must not exceed the 32768 ceiling (smallest model output cap headroom).
    coach = _coach([
        _FakeResp("{ truncated", "max_tokens"),
        _FakeResp('{"ok": true}', "end_turn"),
    ])
    assert _complete(coach, max_tokens=20000) == {"ok": True}
    assert coach.client.messages.calls == [20000, 32768]  # min(40000, 32768)


def test_both_truncated_raises_typed_error():
    coach = _coach([
        _FakeResp("{ truncated", "max_tokens"),
        _FakeResp("{ still truncated", "max_tokens"),
    ])
    with pytest.raises(LLMError, match="exceeded max_tokens"):
        _complete(coach)


def test_non_truncation_malformed_retries_same_budget():
    # A genuinely malformed (not truncated) first response retries with the SAME budget.
    coach = _coach([
        _FakeResp("sorry, here is prose not json", "end_turn"),
        _FakeResp('{"a": 2}', "end_turn"),
    ])
    assert _complete(coach, max_tokens=4096) == {"a": 2}
    assert coach.client.messages.calls == [4096, 4096]  # not bumped


def test_persistent_garbage_raises_typed_error_not_decode_error():
    coach = _coach([
        _FakeResp("no json", "end_turn"),
        _FakeResp("still no json", "end_turn"),
    ])
    with pytest.raises(LLMError, match="did not return valid JSON"):
        _complete(coach)


def test_valid_first_response_no_retry():
    coach = _coach([_FakeResp(json.dumps({"a": 1}), "end_turn")])
    assert _complete(coach) == {"a": 1}
    assert coach.client.messages.calls == [4096]  # single call, no retry


def test_build_coach_defaults_to_deepseek(monkeypatch):
    captured = {}

    class FakeDeepSeekCoach:
        def __init__(self, model=None):
            captured["model"] = model

    monkeypatch.setattr("gtmsi.llm.DeepSeekCoach", FakeDeepSeekCoach)
    assert isinstance(build_coach(), FakeDeepSeekCoach)
    assert captured["model"] is None


def test_build_coach_rejects_unknown_provider():
    with pytest.raises(LLMError, match="unsupported LLM provider"):
        build_coach(provider="unsupported")


def test_build_coach_loads_local_dotenv_without_overriding_environment(monkeypatch):
    calls = []
    monkeypatch.setitem(sys.modules, "dotenv", types.SimpleNamespace(load_dotenv=lambda **kwargs: calls.append(kwargs)))
    monkeypatch.setattr("gtmsi.llm.DeepSeekCoach", lambda model=None: object())
    build_coach()
    assert calls == [{"override": False}]


def test_deepseek_truncation_retry_raises_the_budget():
    class FakeCompletions:
        def __init__(self):
            self.calls = []
            self.responses = [
                type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": '{"a":'})(), "finish_reason": "length"})()]})(),
                type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": '{"a": 1}'})(), "finish_reason": "stop"})()]})(),
            ]

        def create(self, **kwargs):
            self.calls.append(kwargs)
            return self.responses.pop(0)

    coach = DeepSeekCoach.__new__(DeepSeekCoach)
    coach.client = type("Client", (), {"chat": type("Chat", (), {"completions": FakeCompletions()})()})()
    coach.model = "deepseek-v4-flash"
    coach.max_tokens = 4096
    assert _complete(coach) == {"a": 1}
    assert coach.client.chat.completions.calls[0]["response_format"] == {"type": "json_object"}
    assert [call["max_tokens"] for call in coach.client.chat.completions.calls] == [4096, 8192]


def test_normalize_deepseek_response_converts_quotes_and_score_field_names():
    raw = {
        "scores": [{
            "id": "next_steps",
            "name": "Clear next steps",
            "score": 40,
            "rationale": "No meeting booked.",
            "evidence": ["Jordan: 'Would Friday work?'"]
        }],
        "outcomes": [{
            "id": "secure-next-step",
            "statement": "Book a follow-up",
            "status": "missed",
            "evidence": ["Sam: 'Send it over.'"]
        }],
    }

    result = _normalize_deepseek_response(raw)

    assert result["scores"][0]["criterion_id"] == "next_steps"
    assert result["scores"][0]["criterion_name"] == "Clear next steps"
    assert result["scores"][0]["evidence"] == [{"speaker": "Jordan", "text": "Would Friday work?"}]
    assert result["outcomes"][0]["evidence"] == [{"speaker": "Sam", "text": "Send it over."}]


def test_normalize_deepseek_response_wraps_a_single_evidence_string():
    result = _normalize_deepseek_response({"evidence": '"Clear next steps."'})
    assert result["evidence"] == [{"speaker": "Unknown", "text": "Clear next steps."}]


def test_normalize_deepseek_response_converts_partially_outcome_status():
    result = _normalize_deepseek_response({"outcomes": [{"status": "partially"}]})

    assert result["outcomes"][0]["status"] == "partial"
