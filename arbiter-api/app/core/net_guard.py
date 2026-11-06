"""Reject webhook targets that point back into the operator's own network."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit

LOCAL_HOST_NAMES = frozenset({"localhost", "ip6-localhost", "ip6-loopback"})
LOCAL_HOST_SUFFIXES = (".localhost", ".local", ".internal", ".localdomain", ".home.arpa")
LOCAL_TARGET_MESSAGE = "url must point at a public http or https host"


def _checked_host(url: str) -> str:
    """Return the host of a plain absolute HTTP or HTTPS endpoint."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError("url must be an absolute http or https endpoint")
    if " " in url:
        raise ValueError("url must not contain spaces")
    host = parts.hostname
    if not host:
        raise ValueError(LOCAL_TARGET_MESSAGE)
    return host


def check_stored_url(url: str) -> str:
    """Reject a target whose own name says it is local, before it is stored."""
    host = _checked_host(url)
    if host in LOCAL_HOST_NAMES or host.endswith(LOCAL_HOST_SUFFIXES):
        raise ValueError(LOCAL_TARGET_MESSAGE)
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return url
    if not address.is_global:
        raise ValueError(LOCAL_TARGET_MESSAGE)
    return url


async def check_reachable_url(url: str) -> str:
    """Reject a target whose address records are local, just before the request.

    A name that does not resolve is left alone: the request cannot reach a hidden
    address either, and it fails on its own at connect time.
    """
    host = _checked_host(check_stored_url(url))
    try:
        answers = await asyncio.get_running_loop().getaddrinfo(host, None)
    except (socket.gaierror, socket.herror, UnicodeError, OSError):
        return url
    for answer in answers:
        try:
            address = ipaddress.ip_address(str(answer[4][0]).split("%")[0])
        except ValueError:
            continue
        if not address.is_global:
            raise ValueError(LOCAL_TARGET_MESSAGE)
    return url
