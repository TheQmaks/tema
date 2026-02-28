"""SmailPro / Sonjj (smailpro.com + api.sonjj.com) — edu specialist."""

from __future__ import annotations

from typing import Any

import requests

from tema.providers.base import Provider
from tema.utils import _cf_session


class SmailProProvider(Provider):
    """
    Edu specialist — .edu.pl and custom temp domains.
    CF bypass for smailpro.com (JWT generation), plain requests for api.sonjj.com.
    """

    name = "smailpro"
    domains = ["edu"]
    requires_curl_cffi = True
    SMAILPRO = "https://smailpro.com"
    SONJJ = "https://api.sonjj.com"

    def create(self, domain: str) -> dict[str, Any]:
        s = _cf_session()
        s.get(self.SMAILPRO, timeout=20)
        r = s.get(
            f"{self.SMAILPRO}/app/payload",
            params={"url": f"{self.SONJJ}/v1/temp_email/create"},
            timeout=15,
        )
        if r.status_code != 200:
            raise RuntimeError(f"SmailPro: payload fetch failed ({r.status_code})")
        jwt = r.text.strip()
        r2 = requests.get(
            f"{self.SONJJ}/v1/temp_email/create", params={"payload": jwt}, timeout=15
        )
        if r2.status_code != 200:
            raise RuntimeError(f"SmailPro: create failed ({r2.status_code})")
        data = r2.json()
        email = data.get("email", "")
        if not email:
            raise RuntimeError(f"SmailPro: no email in response: {data}")
        return {
            "email": email,
            "provider": self.name,
            "domain": "edu",
            "cookies": {},
            "metadata": {"payload": jwt, "expired_at": data.get("expired_at", "")},
        }

    def inbox(self, state: dict[str, Any]) -> list[dict[str, str]]:
        payload = state.get("metadata", {}).get("payload", "")
        r = requests.get(
            f"{self.SONJJ}/v1/temp_email/inbox", params={"payload": payload}, timeout=15
        )
        if r.status_code != 200:
            return []
        data = r.json()
        messages = data.get("messages", data if isinstance(data, list) else [])
        return [
            {
                "id": m.get("mid", m.get("id", "")),
                "from": m.get("textFrom", m.get("from", "")),
                "subject": m.get("textSubject", m.get("subject", "")),
                "date": m.get("textDate", m.get("date", "")),
            }
            for m in messages
        ]

    def message(self, state: dict[str, Any], msg_id: str) -> str:
        payload = state.get("metadata", {}).get("payload", "")
        r = requests.get(
            f"{self.SONJJ}/v1/temp_email/message",
            params={"payload": payload, "mid": msg_id},
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            return str(data.get("body", data.get("html", r.text)))
        raise RuntimeError(f"SmailPro: message fetch failed ({r.status_code})")
