"""Provider abstract base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

__all__ = ["Provider"]


class Provider(ABC):
    """Base class for all email providers."""

    name: str
    domains: list[str]
    requires_curl_cffi: bool = False

    @abstractmethod
    def create(self, domain: str) -> dict[str, Any]:
        """Create email. Returns {email, provider, domain, cookies, metadata}."""

    @abstractmethod
    def inbox(self, state: dict[str, Any]) -> list[dict[str, str]]:
        """Get messages. Returns [{id, from, subject, date}]."""

    @abstractmethod
    def message(self, state: dict[str, Any], msg_id: str) -> str:
        """Get full message HTML body."""
