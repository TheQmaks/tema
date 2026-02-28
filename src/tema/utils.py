"""Shared utilities: HTTP sessions, HTML parsing, link extraction."""

from __future__ import annotations

import re
import secrets
import string
import sys
from html.parser import HTMLParser
from typing import Any

try:
    import requests  # noqa: F401 — re-exported for providers
except ImportError as _e:
    raise ImportError("requests is required. Install: pip install tema") from _e

try:
    from curl_cffi import requests as cf_requests  # noqa: F401

    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

__all__ = [
    "HAS_CURL_CFFI",
    "IMPERSONATE",
    "LinkExtractor",
    "extract_links",
    "find_verification_link",
    "gmail_alias",
    "_cf_session",
    "_log",
    "_random_username",
]

IMPERSONATE: Any = "chrome131"


class LinkExtractor(HTMLParser):
    """Extract href links from HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.links.append(value)


def extract_links(html_content: str) -> list[str]:
    """Extract all links from HTML."""
    parser = LinkExtractor()
    parser.feed(html_content)
    return parser.links


def find_verification_link(html_content: str) -> str | None:
    """Find verification/confirmation link in email HTML."""
    links = extract_links(html_content)
    verify_patterns = [
        r"verif",
        r"confirm",
        r"activate",
        r"validate",
        r"registration",
        r"auth",
        r"token=",
        r"code=",
        r"key=",
        r"click.here",
        r"email.confirm",
        r"signup",
        r"register",
    ]
    skip_patterns = [
        r"unsubscribe",
        r"privacy",
        r"terms",
        r"mailto:",
        r"facebook\.com",
        r"twitter\.com",
        r"instagram\.com",
        r"linkedin\.com",
        r"youtube\.com",
    ]

    def _should_skip(url: str) -> bool:
        return any(re.search(sp, url, re.IGNORECASE) for sp in skip_patterns)

    for link in links:
        if _should_skip(link):
            continue
        for pattern in verify_patterns:
            if re.search(pattern, link, re.IGNORECASE):
                return link
    for link in links:
        if not link.startswith("http"):
            continue
        if not _should_skip(link):
            return link
    return links[0] if links else None


def gmail_alias(base_email: str) -> str:
    """Generate unique Gmail +alias address."""
    if "@gmail.com" not in base_email.lower():
        raise ValueError("Must be a @gmail.com address")
    local, domain = base_email.rsplit("@", 1)
    chars = string.ascii_lowercase + string.digits
    suffix = "".join(secrets.choice(chars) for _ in range(8))
    return f"{local}+{suffix}@{domain}"


def _random_username(length: int = 12) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def _cf_session() -> Any:
    """Create a curl_cffi session with Chrome impersonation for Cloudflare bypass."""
    if not HAS_CURL_CFFI:
        raise RuntimeError(
            "curl_cffi required for this provider. Install: pip install curl_cffi"
        )
    return cf_requests.Session(impersonate=IMPERSONATE)


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)
