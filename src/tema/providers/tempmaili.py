"""TempMaili (tempmaili.com) — edu specialist, munik.edu.pl domain."""

from __future__ import annotations

import urllib.parse
from typing import Any

import requests

from tema.providers.base import Provider


class TempMailiProvider(Provider):
    """
    Edu specialist — munik.edu.pl domain.
    Laravel backend with CSRF session auth. No Cloudflare needed.
    """

    name = "tempmaili"
    domains = ["edu"]
    BASE = "https://tempmaili.com"

    def _init_session(self) -> tuple[requests.Session, str]:
        s = requests.Session()
        s.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        s.get(self.BASE, timeout=15)
        xsrf = s.cookies.get("XSRF-TOKEN", "")
        token = urllib.parse.unquote(xsrf)
        return s, token

    def create(self, domain: str) -> dict[str, Any]:
        s, token = self._init_session()
        r = s.post(
            f"{self.BASE}/get_messages",
            data={"_token": token},
            headers={"X-CSRF-TOKEN": token, "X-Requested-With": "XMLHttpRequest"},
            timeout=15,
        )
        if r.status_code != 200:
            raise RuntimeError(f"TempMaili: create failed ({r.status_code})")
        data = r.json()
        email = data.get("mailbox", "")
        if not email:
            raise RuntimeError(f"TempMaili: no mailbox in response: {data}")
        cookies = {k: v for k, v in s.cookies.items()}
        return {
            "email": email,
            "provider": self.name,
            "domain": domain,
            "cookies": cookies,
            "metadata": {"email_token": data.get("email_token", "")},
        }

    def _restore(self, state: dict[str, Any]) -> tuple[requests.Session, str]:
        s = requests.Session()
        s.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        for k, v in state.get("cookies", {}).items():
            s.cookies.set(k, v)
        xsrf = s.cookies.get("XSRF-TOKEN", "")
        token = urllib.parse.unquote(xsrf)
        return s, token

    def inbox(self, state: dict[str, Any]) -> list[dict[str, str]]:
        s, token = self._restore(state)
        r = s.post(
            f"{self.BASE}/get_messages",
            data={"_token": token},
            headers={"X-CSRF-TOKEN": token, "X-Requested-With": "XMLHttpRequest"},
            timeout=15,
        )
        if r.status_code != 200:
            return []
        try:
            data = r.json()
        except Exception:
            return []
        messages = data.get("messages", [])
        if not isinstance(messages, list):
            return []
        return [
            {
                "id": str(m.get("id", "")),
                "from": m.get("from_email", m.get("from", "")),
                "subject": m.get("subject", ""),
                "date": m.get("receivedAt", ""),
            }
            for m in messages
        ]

    def message(self, state: dict[str, Any], msg_id: str) -> str:
        s, _ = self._restore(state)
        r = s.get(f"{self.BASE}/view/{msg_id}", timeout=15)
        if r.status_code == 200:
            return str(r.text)
        raise RuntimeError(f"TempMaili: message fetch failed ({r.status_code})")
