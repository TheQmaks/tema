"""etempmail (etempmail.com) — edu specialist, .edu.pl domains."""

from __future__ import annotations

import hashlib
from typing import Any

import requests

from tema.providers.base import Provider


class EtempMailProvider(Provider):
    """
    Fallback 4 — edu specialist (.edu.pl only).
    Simplest API, no Cloudflare. Domain is random (ohm/cross/usa/beta).
    """

    name = "etempmail"
    domains = ["edu"]
    BASE = "https://etempmail.com"

    def create(self, domain: str) -> dict[str, Any]:
        s = requests.Session()
        r = s.post(f"{self.BASE}/getEmailAddress", timeout=15)
        if r.status_code != 200:
            raise RuntimeError(f"etempmail: create failed ({r.status_code})")
        data = r.json()
        email = data.get("address", "")
        if not email:
            raise RuntimeError(f"etempmail: no address in response: {data}")
        cookies = {k: v for k, v in s.cookies.items()}
        return {
            "email": email,
            "provider": self.name,
            "domain": domain,
            "cookies": cookies,
            "metadata": {
                "id": str(data.get("id", "")),
                "recover_key": data.get("recover_key", ""),
            },
        }

    def _restore(self, state: dict[str, Any]) -> requests.Session:
        s = requests.Session()
        for k, v in state.get("cookies", {}).items():
            s.cookies.set(k, v)
        return s

    def inbox(self, state: dict[str, Any]) -> list[dict[str, str]]:
        s = self._restore(state)
        r = s.post(f"{self.BASE}/getInbox", timeout=15)
        if r.status_code != 200:
            return []
        try:
            data = r.json()
        except Exception:
            return []
        messages = (
            data
            if isinstance(data, list)
            else data.get("messages", data.get("inbox", []))
        )
        if not isinstance(messages, list):
            return []
        result = []
        for m in messages:
            mid = m.get("id")
            if mid is None:
                # Stable fallback: hash from content fields
                key = f"{m.get('from', '')}{m.get('subject', '')}{m.get('date', '')}"
                mid = hashlib.md5(key.encode()).hexdigest()[:12]  # noqa: S324
            result.append(
                {
                    "id": str(mid),
                    "from": m.get("from", m.get("sender", "")),
                    "subject": m.get("subject", ""),
                    "date": m.get("date", m.get("time", "")),
                }
            )
        return result

    def message(self, state: dict[str, Any], msg_id: str) -> str:
        s = self._restore(state)
        r = s.get(f"{self.BASE}/email", params={"id": msg_id}, timeout=15)
        if r.status_code == 200:
            return str(r.text)
        raise RuntimeError(f"etempmail: message fetch failed ({r.status_code})")
