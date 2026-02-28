"""Burner Mailbox (burnermailbox.com) — simple anonymous temp email."""

from __future__ import annotations

from typing import Any

import requests

from tema.providers.base import Provider


class BurnerMailboxProvider(Provider):
    """
    Simple REST API with key in URL. 90-day email retention.
    Single domain (kihasl.com), fully anonymous.
    """

    name = "burner"
    domains = ["temp"]
    BASE = "https://burnermailbox.com/api"
    _KEY = "he4PQF6bnGHvYu7Jx3cU"

    def create(self, domain: str) -> dict[str, Any]:
        r = requests.get(f"{self.BASE}/email/kihasl.com/{self._KEY}", timeout=15)
        if r.status_code != 200:
            raise RuntimeError(f"Burner: create failed ({r.status_code})")
        email = r.text.strip()
        if not email or "@" not in email:
            raise RuntimeError(f"Burner: invalid email: {email!r}")
        return {
            "email": email,
            "provider": self.name,
            "domain": domain,
            "cookies": {},
            "metadata": {},
        }

    def inbox(self, state: dict[str, Any]) -> list[dict[str, str]]:
        email = state["email"]
        r = requests.get(f"{self.BASE}/messages/{email}/{self._KEY}", timeout=15)
        if r.status_code != 200:
            return []
        try:
            data = r.json()
        except Exception:
            return []
        if not isinstance(data, list):
            return []
        return [
            {
                "id": str(m.get("id", "")),
                "from": m.get("sender_email", m.get("sender_name", "")),
                "subject": m.get("subject", ""),
                "date": m.get("datediff", m.get("date", "")),
            }
            for m in data
        ]

    def message(self, state: dict[str, Any], msg_id: str) -> str:
        email = state["email"]
        r = requests.get(f"{self.BASE}/messages/{email}/{self._KEY}", timeout=15)
        if r.status_code != 200:
            raise RuntimeError(f"Burner: message fetch failed ({r.status_code})")
        data = r.json()
        for m in data:
            if str(m.get("id", "")) == msg_id:
                return str(m.get("content", ""))
        raise RuntimeError(f"Burner: message {msg_id!r} not found")
