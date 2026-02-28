"""EmailMux (emailmux.com) — gmail, googlemail, outlook, hotmail, icloud."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from tema.providers.base import Provider
from tema.utils import _cf_session


class EmailMuxProvider(Provider):
    """
    Primary provider — supports gmail, googlemail, outlook, hotmail, icloud.
    Uses Cloudflare (curl_cffi) + MD5 API signing.
    Auth: X-API-Signature = MD5(secret + email + timestamp),
    X-API-Timestamp = Date.now()
    """

    name = "emailmux"
    domains = ["gmail", "googlemail", "outlook", "hotmail", "icloud"]
    requires_curl_cffi = True
    BASE = "https://emailmux.com"
    _SECRET = "yjd683c@47"

    @staticmethod
    def _sign(email: str) -> tuple[str, str]:
        ts = str(int(time.time() * 1000))
        sig = hashlib.md5(  # noqa: S324 — API requires MD5
            (EmailMuxProvider._SECRET + email + ts).encode()
        ).hexdigest()
        return ts, sig

    def _init_session(self) -> Any:
        s = _cf_session()
        r = s.get(self.BASE, timeout=40)
        if r.status_code != 200:
            raise RuntimeError(f"EmailMux: page load failed ({r.status_code})")
        return s

    def create(self, domain: str) -> dict[str, Any]:
        s = self._init_session()
        r = s.post(
            f"{self.BASE}/generate-email", json={"domains": [domain]}, timeout=15
        )
        data = r.json()
        if data.get("status") != "success":
            raise RuntimeError(f"EmailMux: generate failed: {data}")
        email = data["email"]
        # Activate inbox with signed request
        ts, sig = self._sign(email)
        r2 = s.get(
            f"{self.BASE}/use-email",
            params={"email": email},
            headers={"X-API-Timestamp": ts, "X-API-Signature": sig},
            timeout=15,
        )
        d2 = r2.json()
        if d2.get("status") != "success":
            raise RuntimeError(f"EmailMux: use-email failed: {d2}")
        cookies = {k: v for k, v in s.cookies.items()}
        return {
            "email": email,
            "provider": self.name,
            "domain": domain,
            "cookies": cookies,
            "metadata": {},
        }

    def _restore(self, state: dict[str, Any]) -> Any:
        s = _cf_session()
        for k, v in state.get("cookies", {}).items():
            s.cookies.set(k, v)
        return s

    def inbox(self, state: dict[str, Any]) -> list[dict[str, str]]:
        s = self._restore(state)
        email = state["email"]
        ts, sig = self._sign(email)
        r = s.get(
            f"{self.BASE}/emails",
            params={"email": email},
            headers={"X-API-Timestamp": ts, "X-API-Signature": sig},
            timeout=15,
        )
        data = r.json()
        if not isinstance(data, list):
            return []
        return [
            {
                "id": m.get("uuid", m.get("id", "")),
                "from": m.get("sender", ""),
                "subject": m.get("subject", ""),
                "date": m.get("timestamp", ""),
            }
            for m in data
            if m.get("uuid") != "WelcomeToEmailMux"
        ]

    def message(self, state: dict[str, Any], msg_id: str) -> str:
        s = self._restore(state)
        r = s.get(f"{self.BASE}/email/{msg_id}", timeout=15)
        if r.status_code == 200:
            try:
                data = r.json()
                return str(data.get("body", data.get("html", r.text)))
            except Exception:
                return str(r.text)
        raise RuntimeError(f"EmailMux: message fetch failed ({r.status_code})")
