"""Provider registry and base class."""

from __future__ import annotations

from tema.providers.base import Provider
from tema.providers.burner import BurnerMailboxProvider
from tema.providers.emailmux import EmailMuxProvider
from tema.providers.emailnator import EmailnatorProvider
from tema.providers.etempmail import EtempMailProvider
from tema.providers.privatix import PrivatixProvider
from tema.providers.smailpro import SmailProProvider
from tema.providers.tempmaili import TempMailiProvider

__all__ = ["Provider", "PROVIDERS", "DOMAIN_PROVIDERS", "get_provider"]

# Domain -> provider priority order
DOMAIN_PROVIDERS: dict[str, list[str]] = {
    "gmail": ["emailnator", "emailmux"],
    "googlemail": ["emailnator", "emailmux"],
    "outlook": ["emailmux"],
    "hotmail": ["emailmux"],
    "icloud": ["emailmux"],
    "edu": ["smailpro", "tempmaili", "etempmail"],
    "temp": ["privatix", "burner"],
}

PROVIDERS: dict[str, Provider] = {
    "emailmux": EmailMuxProvider(),
    "emailnator": EmailnatorProvider(),
    "smailpro": SmailProProvider(),
    "privatix": PrivatixProvider(),
    "burner": BurnerMailboxProvider(),
    "tempmaili": TempMailiProvider(),
    "etempmail": EtempMailProvider(),
}


def get_provider(name: str) -> Provider:
    """Look up a provider by name."""
    p = PROVIDERS.get(name)
    if not p:
        raise ValueError(f"Unknown provider: {name}. Available: {', '.join(PROVIDERS)}")
    return p
