"""Keep webhook targets in the public network and bind the send to one address."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

LOCAL_HOST_NAMES = frozenset({"localhost", "ip6-localhost", "ip6-loopback"})
LOCAL_HOST_SUFFIXES = (".localhost", ".local", ".internal", ".localdomain", ".home.arpa")
LOCAL_TARGET_MESSAGE = "url must point at a public http or https host"
UNRESOLVED_TARGET_MESSAGE = "url host does not resolve to a public address"
DEFAULT_PORTS = {"http": 80, "https": 443}


@dataclass(frozen=True)
class PinnedTarget:
    """One validated address to connect to, and the name the request keeps using."""

    url: str
    host_header: str
    sni_hostname: str


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


def _public_address(answer) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """The address of one resolver answer, refused when it is not public."""
    try:
        address = ipaddress.ip_address(str(answer[4][0]).split("%")[0])
    except ValueError as exc:
        raise ValueError(UNRESOLVED_TARGET_MESSAGE) from exc
    if not address.is_global:
        raise ValueError(LOCAL_TARGET_MESSAGE)
    return address


async def pin_target(url: str) -> PinnedTarget:
    """Resolve a target and return the request that connects to that answer.

    The address, not the name, goes into the URL, so a record that changes
    between the check and the connection cannot move the request into a private
    network. A name that does not resolve, or that answers with nothing, is
    refused: the sender cannot know where such a request would arrive.
    """
    host = _checked_host(check_stored_url(url))
    parts = urlsplit(url)
    port = parts.port or DEFAULT_PORTS[parts.scheme]
    try:
        answers = await asyncio.get_running_loop().getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except (socket.gaierror, socket.herror, UnicodeError, OSError) as exc:
        raise ValueError(UNRESOLVED_TARGET_MESSAGE) from exc
    if not answers:
        raise ValueError(UNRESOLVED_TARGET_MESSAGE)
    addresses = [_public_address(answer) for answer in answers]
    literal = f"[{addresses[0]}]" if addresses[0].version == 6 else str(addresses[0])
    authority = literal if parts.port is None else f"{literal}:{parts.port}"
    credentials, _, _ = parts.netloc.rpartition("@")
    netloc = f"{credentials}@{authority}" if credentials else authority
    return PinnedTarget(
        url=urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment)),
        host_header=host if parts.port is None else f"{host}:{parts.port}",
        sni_hostname=host,
    )
