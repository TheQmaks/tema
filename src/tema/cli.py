"""Command-line interface for tema."""

from __future__ import annotations

__all__ = ["main"]

import argparse
import json
import re
import sys

from tema.core import create_email, get_inbox, get_message_body, wait_for_message
from tema.providers import DOMAIN_PROVIDERS, PROVIDERS
from tema.utils import (
    HAS_CURL_CFFI,
    extract_links,
    find_verification_link,
    gmail_alias,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Temp Mail — multi-provider temporary email CLI with real domains"
    )
    sub = parser.add_subparsers(dest="command", help="Command")

    # create
    p_create = sub.add_parser("create", help="Create new temporary mailbox")
    p_create.add_argument(
        "--domain",
        "-d",
        default="gmail",
        choices=list(DOMAIN_PROVIDERS.keys()),
        help="Email domain (default: gmail)",
    )
    p_create.add_argument(
        "--provider",
        "-p",
        default=None,
        choices=list(PROVIDERS.keys()),
        help="Force specific provider (default: auto-fallback)",
    )

    # wait
    p_wait = sub.add_parser("wait", help="Wait for new message")
    p_wait.add_argument("--timeout", type=int, default=120)

    # read
    p_read = sub.add_parser("read", help="Read message")
    p_read.add_argument(
        "msg_id", nargs="?", default=None, help="Message ID (default: latest)"
    )

    # links
    sub.add_parser("links", help="Extract links from latest message")

    # verify
    sub.add_parser("verify", help="Find verification link")

    # gmail-alias
    p_gmail = sub.add_parser("gmail-alias", help="Generate Gmail +alias")
    p_gmail.add_argument("email", help="Base Gmail address")

    # list
    sub.add_parser("list", help="List all messages")

    # domains
    sub.add_parser("domains", help="List available domains with providers")

    # providers
    sub.add_parser("providers", help="List all providers and status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        _dispatch(args)
    except (ValueError, RuntimeError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


def _dispatch(args: argparse.Namespace) -> None:
    if args.command == "create":
        state = create_email(domain=args.domain, provider_name=args.provider)
        print(
            json.dumps(
                {
                    "email": state["email"],
                    "provider": state["provider"],
                    "domain": state["domain"],
                },
                indent=2,
            )
        )

    elif args.command == "wait":
        msg = wait_for_message(timeout=args.timeout)
        if msg:
            print(
                json.dumps(
                    {
                        "id": msg.get("id", ""),
                        "from": msg.get("from", ""),
                        "subject": msg.get("subject", ""),
                        "has_html": bool(msg.get("html")),
                        "text_preview": (msg.get("html", "") or "")[:500],
                    },
                    indent=2,
                )
            )
        else:
            print(json.dumps({"error": "timeout"}))
            sys.exit(1)

    elif args.command == "read":
        if args.msg_id:
            html = get_message_body(args.msg_id)
            print(
                json.dumps(
                    {"id": args.msg_id, "html": html},
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            messages, state = get_inbox()
            if not messages:
                print(json.dumps({"error": "no messages"}))
                sys.exit(1)
            msg = messages[0]
            html = get_message_body(msg["id"], state)
            print(
                json.dumps(
                    {
                        "id": msg["id"],
                        "from": msg.get("from", ""),
                        "subject": msg.get("subject", ""),
                        "html": html,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )

    elif args.command == "links":
        messages, state = get_inbox()
        if not messages:
            print(json.dumps({"error": "no messages"}))
            sys.exit(1)
        html = get_message_body(messages[0]["id"], state)
        links = extract_links(html or "")
        text_links = re.findall(r"https?://[^\s<>\"')\]]+", html or "")
        all_links = list(dict.fromkeys(links + text_links))
        print(json.dumps({"links": all_links}, indent=2))

    elif args.command == "verify":
        messages, state = get_inbox()
        if not messages:
            print(json.dumps({"error": "no messages"}))
            sys.exit(1)
        html = get_message_body(messages[0]["id"], state)
        link = find_verification_link(html or "")
        if link:
            print(json.dumps({"verification_link": link}))
        else:
            print(
                json.dumps(
                    {
                        "error": "no verification link found",
                        "subject": messages[0].get("subject", ""),
                    }
                )
            )
            sys.exit(1)

    elif args.command == "gmail-alias":
        alias = gmail_alias(args.email)
        print(json.dumps({"alias": alias}))

    elif args.command == "list":
        messages, _ = get_inbox()
        print(json.dumps(messages, indent=2))

    elif args.command == "domains":
        print(json.dumps(DOMAIN_PROVIDERS, indent=2))

    elif args.command == "providers":
        result = []
        for name, p in PROVIDERS.items():
            result.append(
                {
                    "name": name,
                    "domains": p.domains,
                    "needs_curl_cffi": p.requires_curl_cffi,
                    "available": HAS_CURL_CFFI if p.requires_curl_cffi else True,
                }
            )
        print(json.dumps(result, indent=2))
