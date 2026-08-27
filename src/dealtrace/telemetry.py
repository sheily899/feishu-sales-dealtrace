"""Optional, **opt-in**, anonymous usage telemetry.

Why opt-in: dev tools live or die on trust, and silent/opt-out telemetry reliably
backfires (Go's toolchain proposed opt-out and reversed after backlash). So this is
**off by default**, prints a one-time transparent notice, has a documented kill-switch,
and never sends transcript content or PII. See ``docs/telemetry.md``.

Most attribution actually comes from the tracked "powered by" links (see
``attribution.py``) and from connecting Attention — telemetry is just a bonus signal
for the people who choose to share it.

What it sends when enabled: an event name, the package version, a coarse command name,
a salted one-way machine hash (not reversible to a user), and — only if you've
connected Attention — a hashed account reference. Nothing else.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import urllib.request
from pathlib import Path

from . import __version__

# No default endpoint is published. Telemetry only sends if you both opt in AND set a
# collector via GTMSI_TELEMETRY_ENDPOINT — so the public repo ships no live ingest host.
_ENDPOINT = os.environ.get("GTMSI_TELEMETRY_ENDPOINT")
_CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "gtm-superintelligence"
_CONFIG = _CONFIG_DIR / "config.json"
_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}


def _read_config() -> dict:
    try:
        return json.loads(_CONFIG.read_text())
    except Exception:  # noqa: BLE001
        return {}


def _write_config(cfg: dict) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG.write_text(json.dumps(cfg, indent=2))


def is_enabled() -> bool:
    """Env wins over config. Default: OFF."""
    env = os.environ.get("GTMSI_TELEMETRY", "").lower()
    if env in _TRUTHY:
        return True
    if env in _FALSY:
        return False
    return bool(_read_config().get("telemetry", False))


def enable() -> None:
    cfg = _read_config()
    cfg["telemetry"] = True
    _write_config(cfg)


def disable() -> None:
    cfg = _read_config()
    cfg["telemetry"] = False
    _write_config(cfg)


def status() -> str:
    return "enabled" if is_enabled() else "disabled"


def maybe_first_run_notice(emit) -> None:
    """Show a one-time, honest notice (only when telemetry is OFF and unseen). ``emit``
    is a function that prints to stderr."""
    cfg = _read_config()
    if cfg.get("notice_shown") or is_enabled():
        return
    emit(
        "▸ Anonymous usage stats are OFF. If you'd like to help improve this project, "
        "enable them with `dealtrace telemetry enable` (no transcript content is ever sent). "
        "See docs/telemetry.md."
    )
    cfg["notice_shown"] = True
    try:
        _write_config(cfg)
    except Exception:  # noqa: BLE001
        pass


def _machine_id() -> str:
    seed = f"{os.environ.get('USER','')}@{os.uname().nodename if hasattr(os,'uname') else ''}"
    return hashlib.sha256(("dealtrace-salt:" + seed).encode()).hexdigest()[:16]


def account_ref() -> str | None:
    """Hashed reference to the connected Attention account, if any (never the raw key)."""
    key = os.environ.get("ATTENTION_API_KEY")
    return hashlib.sha256(key.encode()).hexdigest()[:12] if key else None


def record(event: str, **props) -> None:
    """Best-effort, non-blocking, swallow-all. No-op unless explicitly enabled AND a
    collector endpoint is configured (GTMSI_TELEMETRY_ENDPOINT)."""
    if not is_enabled() or not _ENDPOINT:
        return
    payload = {
        "event": event,
        "version": __version__,
        "machine": _machine_id(),
        "account": account_ref(),
        **props,
    }

    def _send():
        try:
            req = urllib.request.Request(
                _ENDPOINT,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json", "User-Agent": f"dealtrace/{__version__}"},
            )
            urllib.request.urlopen(req, timeout=2)  # noqa: S310
        except Exception:  # noqa: BLE001 - telemetry must never affect the user
            pass

    threading.Thread(target=_send, daemon=True).start()
