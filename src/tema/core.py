"""Core logic: create, inbox, message, wait."""

from __future__ import annotations

import time
from typing import Any

from tema.providers import DOMAIN_PROVIDERS, get_provider
from tema.state import load_state, save_state
from tema.utils import _log

__all__ = ["create_email", "get_inbox", "get_message_body", "wait_for_message"]


def create_email(
    domain: str = "gmail", provider_name: str | None = None
) -> dict[str, Any]:
    """Create temp email with auto-fallback across providers."""
    if provider_name:
        p = get_provider(provider_name)
        if domain not in p.domains:
            supported = ", ".join(p.domains)
            raise ValueError(
                f"{provider_name} doesn't support '{domain}'. Supported: {supported}"
            )
        state = p.create(domain)
        state["created_at"] = int(time.time())
        save_state(state)
        return state

    provider_order = DOMAIN_PROVIDERS.get(domain)
    if not provider_order:
        raise ValueError(
            f"Unknown domain: {domain}. Available: {', '.join(DOMAIN_PROVIDERS)}"
        )

    errors = []
    for pname in provider_order:
        p = get_provider(pname)
        try:
            _log(f"Trying {pname}...")
            state = p.create(domain)
            state["created_at"] = int(time.time())
            save_state(state)
            _log(f"OK: {pname} -> {state['email']}")
            return state
        except Exception as e:
            errors.append(f"{pname}: {e}")
            _log(f"FAIL: {pname}: {e}")

    raise RuntimeError(f"All providers failed for '{domain}':\n" + "\n".join(errors))


def get_inbox() -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Get inbox messages for active mailbox."""
    state = load_state()
    if not state or "provider" not in state:
        raise RuntimeError("No active mailbox. Run 'create' first.")
    p = get_provider(state["provider"])
    return p.inbox(state), state


def get_message_body(msg_id: str, state: dict[str, Any] | None = None) -> str:
    """Get full message HTML body."""
    if state is None:
        state = load_state()
    if not state or "provider" not in state:
        raise RuntimeError("No active mailbox. Run 'create' first.")
    p = get_provider(state["provider"])
    return p.message(state, msg_id)


def wait_for_message(
    timeout: int = 120, poll_interval: float = 5
) -> dict[str, str] | None:
    """Poll for new messages with exponential backoff."""
    state = load_state()
    if not state or "provider" not in state:
        raise RuntimeError("No active mailbox. Run 'create' first.")

    p = get_provider(state["provider"])
    start = time.time()
    initial_msgs = p.inbox(state)
    initial_ids = {m["id"] for m in initial_msgs}
    interval = poll_interval

    _log(f"Waiting for new message at {state['email']} (timeout={timeout}s)...")

    while time.time() - start < timeout:
        time.sleep(interval)
        messages = p.inbox(state)
        new_msgs = [m for m in messages if m["id"] not in initial_ids]
        if new_msgs:
            msg = new_msgs[0]
            try:
                msg["html"] = p.message(state, msg["id"])
            except Exception:
                msg["html"] = ""
            return msg
        interval = min(interval * 1.3, 15)
        elapsed = int(time.time() - start)
        _log(f"  ... {elapsed}s elapsed, {len(messages)} messages")

    _log("ERROR: Timeout waiting for message")
    return None
