"""tema — Multi-provider temporary email CLI with real domain support."""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = [
    "create_email",
    "get_inbox",
    "get_message_body",
    "wait_for_message",
    "PROVIDERS",
    "DOMAIN_PROVIDERS",
]

from tema.core import create_email, get_inbox, get_message_body, wait_for_message
from tema.providers import DOMAIN_PROVIDERS, PROVIDERS
