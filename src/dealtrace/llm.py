"""Thin wrapper over the Anthropic Messages API with prompt caching.

Why caching matters here: the system prompt + the frameworks + the scorecard are
identical across every call you coach. We mark them with ``cache_control`` so they
are billed/processed once and reused, which is a large cost/latency win when you
coach calls in bulk. The transcript (the part that changes) is sent uncached.

The wrapper also enforces JSON output and retries once on malformed JSON.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"


@dataclass
class CachedBlock:
    """A large, reusable chunk of context to cache (label is for readability only)."""

    label: str
    text: str


class LLMError(RuntimeError):
    pass


# Ceiling for the truncation retry. Safely under the smallest supported model
# output cap (Sonnet 4.6 tops out at 64K; Opus 4.8 at 128K), so doubling the
# coach budget here never sends an over-limit max_tokens that the API rejects.
_MAX_RETRY_TOKENS = 32768


class AnthropicCoach:
    def __init__(self, api_key: str | None = None, model: str | None = None, max_tokens: int = 4096):
        try:
            from anthropic import Anthropic
        except ImportError as e:  # pragma: no cover
            raise LLMError(
                "The 'anthropic' package is required for live coaching. "
                "Install with `pip install anthropic`, or run inside Claude Code (no API key needed)."
            ) from e
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise LLMError("ANTHROPIC_API_KEY is not set. Export it or pass api_key=...")
        self.client = Anthropic(api_key=key)
        self.model = model or os.environ.get("GTMSI_MODEL", DEFAULT_ANTHROPIC_MODEL)
        self.max_tokens = max_tokens
        self.temperature = 0
        self.top_p = 1
        self.seed = _read_seed()
        self.last_raw_response: str | None = None
        self.last_call_meta: dict[str, Any] = {}

    def complete_json(
        self,
        system: str,
        cached_blocks: list[CachedBlock],
        user_text: str,
        max_tokens: int | None = None,
    ) -> Any:
        """Run one message and parse a JSON object/array from the response.

        ``cached_blocks`` are concatenated ahead of ``user_text`` as user-content
        blocks, each marked ephemeral-cacheable. ``system`` is also cached.
        """
        content_blocks: list[dict[str, Any]] = []
        for blk in cached_blocks:
            content_blocks.append(
                {
                    "type": "text",
                    "text": f"### {blk.label}\n{blk.text}",
                    "cache_control": {"type": "ephemeral"},
                }
            )
        content_blocks.append({"type": "text", "text": user_text})

        system_blocks = [
            {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
        ]

        raw, stop_reason = self._call(system_blocks, content_blocks, max_tokens)
        try:
            return _extract_json(raw)
        except ValueError as first_err:
            # The most common cause of unparseable JSON is a response truncated at
            # the token cap. When that's what happened, retrying with the SAME budget
            # just truncates again — so bump the budget for the retry.
            truncated = stop_reason == "max_tokens"
            retry_tokens = max_tokens
            if truncated:
                base = max_tokens or self.max_tokens
                retry_tokens = min(base * 2, _MAX_RETRY_TOKENS)

            fix, fix_stop = self._call(
                system_blocks,
                content_blocks
                + [{"type": "text", "text": "Your previous output was not valid JSON. Reply with ONLY the JSON, no prose."}],
                retry_tokens,
            )
            try:
                return _extract_json(fix)
            except ValueError as retry_err:
                # Guard the final parse: surface a typed, actionable error instead of
                # letting a raw json.JSONDecodeError escape.
                if truncated or fix_stop == "max_tokens":
                    raise LLMError(
                        "model output exceeded max_tokens and was truncated; raise max_tokens "
                        "or shorten the transcript"
                    ) from retry_err
                raise LLMError(f"model did not return valid JSON: {retry_err}") from first_err

    def _call(self, system_blocks, content_blocks, max_tokens) -> tuple[str, str | None]:
        temperature = getattr(self, "temperature", 0)
        top_p = getattr(self, "top_p", 1)
        request = {
            "model": self.model,
            "max_tokens": max_tokens or self.max_tokens,
            "system": system_blocks,
            "messages": [{"role": "user", "content": content_blocks}],
        }
        if hasattr(self, "temperature"):
            request.update(temperature=temperature, top_p=top_p)
        resp = self.client.messages.create(**request)
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        self.last_raw_response = text
        stop_reason = getattr(resp, "stop_reason", None)
        self.last_call_meta = {
            "provider": "anthropic",
            "model": self.model,
            "temperature": temperature,
            "top_p": top_p,
            "seed": getattr(self, "seed", None),
            "response_format": None,
            "stop_reason": stop_reason,
        }
        return text, stop_reason


class DeepSeekCoach:
    """DeepSeek Chat Completions provider for structured sales analysis."""

    def __init__(self, api_key: str | None = None, model: str | None = None, max_tokens: int = 4096):
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover
            raise LLMError(
                "The 'openai' package is required for DeepSeek coaching. "
                "Install with `pip install -e \".[llm]\"`."
            ) from e
        key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            raise LLMError("DEEPSEEK_API_KEY is not set. Export it or pass api_key=...")
        self.client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
        self.model = model or os.environ.get("GTMSI_MODEL", DEFAULT_DEEPSEEK_MODEL)
        self.max_tokens = max_tokens
        self.temperature = 0
        self.top_p = 1
        self.seed = _read_seed()
        self.last_raw_response: str | None = None
        self.last_call_meta: dict[str, Any] = {}

    def complete_json(
        self,
        system: str,
        cached_blocks: list[CachedBlock],
        user_text: str,
        max_tokens: int | None = None,
    ) -> Any:
        context = "\n\n".join(f"### {blk.label}\n{blk.text}" for blk in cached_blocks)
        prompt = f"{context}\n\n{user_text}" if context else user_text
        raw, stop_reason = self._call(system, prompt, max_tokens)
        try:
            return _normalize_deepseek_response(_extract_json(raw))
        except ValueError as first_err:
            retry_tokens = max_tokens
            if stop_reason == "max_tokens":
                retry_tokens = min((max_tokens or self.max_tokens) * 2, _MAX_RETRY_TOKENS)
            retry, retry_stop = self._call(
                system,
                f"{prompt}\n\nYour previous output was not valid JSON. Reply with ONLY valid JSON.",
                retry_tokens,
            )
            try:
                return _normalize_deepseek_response(_extract_json(retry))
            except ValueError as retry_err:
                if stop_reason == "max_tokens" or retry_stop == "max_tokens":
                    raise LLMError("model output exceeded max_tokens and was truncated; raise max_tokens or shorten the transcript") from retry_err
                raise LLMError(f"model did not return valid JSON: {retry_err}") from first_err

    def _call(self, system: str, user_text: str, max_tokens: int | None) -> tuple[str, str | None]:
        temperature = getattr(self, "temperature", 0)
        top_p = getattr(self, "top_p", 1)
        seed = getattr(self, "seed", None)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user_text}],
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature,
            top_p=top_p,
            seed=seed,
            response_format={"type": "json_object"},
            extra_body={"thinking": {"type": "disabled"}},
        )
        choice = response.choices[0]
        stop_reason = "max_tokens" if choice.finish_reason == "length" else choice.finish_reason
        text = choice.message.content or ""
        self.last_raw_response = text
        self.last_call_meta = {
            "provider": "deepseek",
            "model": self.model,
            "temperature": temperature,
            "top_p": top_p,
            "seed": seed,
            "response_format": {"type": "json_object"},
            "stop_reason": stop_reason,
        }
        return text, stop_reason


def build_coach(provider: str | None = None, model: str | None = None):
    """Create the configured live model provider; DeepSeek is the default."""
    from dotenv import load_dotenv

    # Preserve explicitly exported environment variables over local developer settings.
    load_dotenv(override=False)
    selected = (provider or os.environ.get("GTMSI_LLM_PROVIDER", "deepseek")).lower()
    if selected == "deepseek":
        return DeepSeekCoach(model=model)
    if selected == "anthropic":
        return AnthropicCoach(model=model)
    raise LLMError(f"unsupported LLM provider: {selected}")


def _normalize_deepseek_response(value: Any) -> Any:
    """Map common DeepSeek JSON variations to the project's report contract."""
    if isinstance(value, list):
        return [_normalize_deepseek_response(item) for item in value]
    if not isinstance(value, dict):
        return value

    normalized = {key: _normalize_deepseek_response(item) for key, item in value.items()}
    # The report contract calls this state "partial"; DeepSeek may emit the
    # grammatically natural but invalid variant "partially".
    if normalized.get("status") == "partially":
        normalized["status"] = "partial"
    if "score" in normalized and "id" in normalized and "name" in normalized:
        normalized.setdefault("criterion_id", normalized["id"])
        normalized.setdefault("criterion_name", normalized["name"])
    evidence = normalized.get("evidence")
    if isinstance(evidence, str):
        normalized["evidence"] = [_normalize_deepseek_quote(evidence)]
    elif isinstance(evidence, list):
        normalized["evidence"] = [_normalize_deepseek_quote(item) for item in evidence]
    return normalized


def _normalize_deepseek_quote(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    speaker, separator, text = value.partition(":")
    if not separator:
        return {"speaker": "Unknown", "text": value.strip().strip("'\"")}
    return {"speaker": speaker.strip() or "Unknown", "text": text.strip().strip("'\"")}


def _read_seed() -> int:
    raw = os.environ.get("GTMSI_SEED")
    if raw is None or raw == "":
        return 42
    try:
        return int(raw)
    except ValueError:
        return 42


def _extract_json(text: str) -> Any:
    text = text.strip()
    # Strip ```json fences if present.
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Last resort: grab the outermost {...} or [...].
    for opener, closer in (("{", "}"), ("[", "]")):
        start, end = text.find(opener), text.rfind(closer)
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
    raise ValueError("No JSON found in model output")
