"""Privatix (temp-mail.org) — disposable temp domains."""

from __future__ import annotations

from typing import Any

from tema.providers.base import Provider
from tema.utils import _cf_session


class PrivatixProvider(Provider):
    """
    Disposable temp domains (server-assigned, rotating).
    Direct backend — no RapidAPI, no API key. Self-service JWT from POST /mailbox.
    Behind Cloudflare — requires curl_cffi.
    """

    name = "privatix"
    domains = ["temp"]
    requires_curl_cffi = True
    BASE = "https://mob2.temp-mail.org"

    def _session(self) -> Any:
        s = _cf_session()
        s.headers.update({"User-Agent": "3.49", "Accept": "application/json"})
        return s

    def create(self, domain: str) -> dict[str, Any]:
        s = self._session()
        r = s.post(f"{self.BASE}/mailbox", timeout=20)
        if r.status_code != 200:
            raise RuntimeError(f"Privatix: create failed ({r.status_code})")
        data = r.json()
        token = data.get("token", "")
        email = data.get("mailbox", "")
        if not email or not token:
            raise RuntimeError(f"Privatix: invalid response: {data}")
        return {
            "email": email,
            "provider": self.name,
            "domain": domain,
            "cookies": {},
            "metadata": {"token": token},
        }

    def _headers(self, state: dict[str, Any]) -> dict[str, str]:
        token = state.get("metadata", {}).get("token", "")
        return {
            "Authorization": f"Bearer {token}",
            "User-Agent": "3.49",
            "Accept": "application/json",
        }

    def inbox(self, state: dict[str, Any]) -> list[dict[str, str]]:
        s = self._session()
        r = s.get(f"{self.BASE}/messages", headers=self._headers(state), timeout=15)
        if r.status_code != 200:
            return []
        data = r.json()
        messages = data.get("messages", data if isinstance(data, list) else [])
        if not isinstance(messages, list):
            return []
        result = []
        for m in messages:
            from_val = m.get("from", "")
            if isinstance(from_val, dict):
                from_val = from_val.get("address", from_val.get("name", ""))
            result.append(
                {
                    "id": m.get("_id", m.get("id", "")),
                    "from": from_val,
                    "subject": m.get("subject", ""),
                    "date": str(m.get("receivedAt", m.get("date", ""))),
                }
            )
        return result

    def message(self, state: dict[str, Any], msg_id: str) -> str:
        s = self._session()
        r = s.get(
            f"{self.BASE}/messages/{msg_id}/", headers=self._headers(state), timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            return str(data.get("bodyHtml", data.get("body", r.text)))
        raise RuntimeError(f"Privatix: message fetch failed ({r.status_code})")
