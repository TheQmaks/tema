"""Persistent mailbox state management."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

__all__ = ["STATE_FILE", "save_state", "load_state"]


def _resolve_state_file() -> Path:
    env = os.environ.get("TEMA_STATE_FILE")
    if env:
        return Path(env)
    return Path.cwd() / ".tema_state.json"


STATE_FILE = _resolve_state_file()


def save_state(state: dict[str, Any]) -> None:
    """Persist account state to file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_state() -> dict[str, Any] | None:
    """Load persisted account state."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)  # type: ignore[no-any-return]
    return None
