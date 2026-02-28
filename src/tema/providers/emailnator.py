"""Emailnator (emailnator.com) — gmail, googlemail (dot/plus trick)."""

from __future__ import annotations

import urllib.parse
from typing import Any

from tema.providers.base import Provider
from tema.utils import _cf_session


class EmailnatorProvider(Provider):
    """
    Fallback 2 — gmail only (dot trick, plus trick, googlemail).
    Cloudflare + XSRF token.
    """

    name = "emailnator"
    domains = ["gmail", "googlemail"]
    requires_curl_cffi = True
    BASE = "https://www.emailnator.com"

    def _init_session(self) -> Any:
        s = _cf_session()
        r = s.get(self.BASE, timeout=20)
        if r.status_code != 200:
            raise RuntimeError(f"Emailnator: page load failed ({r.status_code})")
        return s

    def _xsrf(self, s: Any) -> str:
        token = s.cookies.get("XSRF-TOKEN", "")
        return urllib.parse.unquote(token)

    def create(self, domain: str) -> dict[str, Any]:
        s = self._init_session()
        token = self._xsrf(s)
        # Email type: dotGmail, plusGmail, googleMail, domain
        email_types = (
            ["googleMail"] if domain == "googlemail" else ["dotGmail", "plusGmail"]
        )
        r = s.post(
            f"{self.BASE}/generate-email",
            json={"email": email_types},
            headers={"X-XSRF-TOKEN": token},
            timeout=15,
        )
        if r.status_code != 200:
            raise RuntimeError(f"Emailnator: generate failed ({r.status_code})")
        data = r.json()
        email_list = data.get("email", [])
        email = (
            email_list[0]
            if isinstance(email_list, list) and email_list
            else data.get("email", "")
        )
        if not isinstance(email, str) or not email:
            raise RuntimeError(f"Emailnator: no email in response: {data}")
        cookies = {k: v for k, v in s.cookies.items()}
        return {
            "email": email,
            "provider": self.name,
            "domain": domain,
            "cookies": cookies,
            "metadata": {"xsrf": token},
        }

    def _restore(self, state: dict[str, Any]) -> Any:
        s = _cf_session()
        for k, v in state.get("cookies", {}).items():
            s.cookies.set(k, v)
        return s

    def inbox(self, state: dict[str, Any]) -> list[dict[str, str]]:
        s = self._restore(state)
        token = state.get("metadata", {}).get("xsrf", self._xsrf(s))
        r = s.post(
            f"{self.BASE}/message-list",
            json={"email": state["email"]},
            headers={"X-XSRF-TOKEN": token},
            timeout=15,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        messages = data.get("messageData", data if isinstance(data, list) else [])
        return [
            {
                "id": m.get("messageID", m.get("id", "")),
                "from": m.get("from", ""),
                "subject": m.get("subject", ""),
                "date": m.get("time", m.get("date", "")),
            }
            for m in messages
            if m.get("messageID", "") != "ADSVPN"
        ]

    def message(self, state: dict[str, Any], msg_id: str) -> str:
        s = self._restore(state)
        token = state.get("metadata", {}).get("xsrf", self._xsrf(s))
        r = s.post(
            f"{self.BASE}/message-list",
            json={"email": state["email"], "messageID": msg_id},
            headers={"X-XSRF-TOKEN": token},
            timeout=15,
        )
        if r.status_code == 200:
            return str(r.text)
        raise RuntimeError(f"Emailnator: message fetch failed ({r.status_code})")
