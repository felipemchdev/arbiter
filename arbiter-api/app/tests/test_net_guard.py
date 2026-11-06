from __future__ import annotations

import socket

import httpx
import pytest

import app.core.net_guard as net_guard
from app.core.net_guard import UNRESOLVED_TARGET_MESSAGE, check_stored_url, pin_target
from app.services import notification_service

PUBLIC_V4 = "93.184.216.34"
PUBLIC_V6 = "2606:2800:220:1:248:1893:25c8:1946"


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:6379",
        "https://127.0.0.1/hook",
        "https://10.0.0.5/hook",
        "https://172.16.0.9/hook",
        "https://192.168.1.10/hook",
        "https://169.254.169.254/latest/meta-data/",
        "https://[::1]/hook",
        "https://redis.internal/hook",
        "https://cache.local/hook",
        "https://metadata.google.internal/hook",
        "ftp://hook.example.test/x",
        "hook.example.test/x",
        "https://",
    ],
)
def test_check_stored_url_rejects_local_and_non_http_targets(url):
    with pytest.raises(ValueError):
        check_stored_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://hook.example.test/arbiter",
        "https://hooks.other.example/v1",
        "http://93.184.216.34/hook",
    ],
)
def test_check_stored_url_accepts_public_targets(url):
    assert check_stored_url(url) == url


class _FakeLoop:
    """Stand in for the resolver so a test can choose what a name answers with."""

    def __init__(self, answers=None, failure=None):
        self._answers = answers or []
        self._failure = failure
        self.lookups: list[tuple] = []

    async def getaddrinfo(self, host, port, type=None):
        self.lookups.append((host, port, type))
        if self._failure is not None:
            raise self._failure
        return self._answers


def _use_loop(monkeypatch, loop):
    monkeypatch.setattr(net_guard.asyncio, "get_running_loop", lambda: loop)
    return loop


def _answers(*addresses: str, port=443):
    return [(6 if ":" in address else 2, 1, 6, "", (address, port)) for address in addresses]


@pytest.mark.asyncio
async def test_pin_target_answers_with_the_address_it_validated(monkeypatch):
    """The connection uses the address, so a second, different answer moves nothing."""
    _use_loop(monkeypatch, _FakeLoop(answers=_answers(PUBLIC_V4)))

    target = await pin_target("https://collector.example.test/hook")

    assert target.url == f"https://{PUBLIC_V4}/hook"
    assert target.host_header == "collector.example.test"
    assert target.sni_hostname == "collector.example.test"


@pytest.mark.asyncio
async def test_pin_target_keeps_the_port_of_the_stored_url(monkeypatch):
    _use_loop(monkeypatch, _FakeLoop(answers=_answers(PUBLIC_V4, port=8443)))

    target = await pin_target("https://collector.example.test:8443/hook")

    assert target.url == f"https://{PUBLIC_V4}:8443/hook"
    assert target.host_header == "collector.example.test:8443"


@pytest.mark.asyncio
async def test_pin_target_wraps_an_ipv6_address_in_brackets(monkeypatch):
    _use_loop(monkeypatch, _FakeLoop(answers=_answers(PUBLIC_V6)))

    target = await pin_target("https://collector.example.test/hook")

    assert target.url == f"https://[{PUBLIC_V6}]/hook"


@pytest.mark.asyncio
async def test_pin_target_refuses_a_name_that_resolves_locally(monkeypatch):
    _use_loop(monkeypatch, _FakeLoop(answers=_answers("10.0.0.5")))

    with pytest.raises(ValueError, match="public http or https host"):
        await pin_target("https://collector.example.test/hook")


@pytest.mark.asyncio
async def test_pin_target_refuses_an_ipv6_record_that_is_not_public(monkeypatch):
    _use_loop(monkeypatch, _FakeLoop(answers=_answers("fe80::1")))

    with pytest.raises(ValueError, match="public http or https host"):
        await pin_target("https://collector.example.test/hook")


@pytest.mark.asyncio
async def test_pin_target_refuses_answers_that_mix_public_and_private(monkeypatch):
    """One private record in the set is enough to reach the operator's network."""
    _use_loop(monkeypatch, _FakeLoop(answers=_answers(PUBLIC_V4, "192.168.1.10")))

    with pytest.raises(ValueError, match="public http or https host"):
        await pin_target("https://collector.example.test/hook")


@pytest.mark.asyncio
async def test_pin_target_refuses_a_name_that_does_not_resolve(monkeypatch):
    _use_loop(monkeypatch, _FakeLoop(failure=socket.gaierror("Name or service not known")))

    with pytest.raises(ValueError, match=UNRESOLVED_TARGET_MESSAGE):
        await pin_target("https://hook.example.test/arbiter")


@pytest.mark.asyncio
async def test_pin_target_refuses_an_answer_with_no_records(monkeypatch):
    _use_loop(monkeypatch, _FakeLoop(answers=[]))

    with pytest.raises(ValueError, match=UNRESOLVED_TARGET_MESSAGE):
        await pin_target("https://hook.example.test/arbiter")


@pytest.mark.asyncio
async def test_pin_target_refuses_a_local_name_before_it_asks_the_resolver(monkeypatch):
    loop = _use_loop(monkeypatch, _FakeLoop(answers=_answers(PUBLIC_V4)))

    with pytest.raises(ValueError, match="public http or https host"):
        await pin_target("https://cache.local/hook")

    assert loop.lookups == []


class _RecordedSend:
    """Stand in for the HTTP client, so a test reads the request that was built."""

    def __init__(self) -> None:
        self.factory_kwargs: dict = {}
        self.requests: list[dict] = []

    def factory(self, **kwargs):
        self.factory_kwargs = kwargs
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc) -> bool:
        return False

    async def post(self, url, content=None, headers=None, extensions=None, follow_redirects=None):
        self.requests.append({"url": url, "headers": headers, "extensions": extensions, "redirects": follow_redirects})
        return httpx.Response(200, request=httpx.Request("POST", url))


@pytest.mark.asyncio
async def test_send_webhook_connects_to_the_pinned_address(monkeypatch):
    """The name stays in Host, SNI and the certificate check; the URL carries the address."""
    _use_loop(monkeypatch, _FakeLoop(answers=_answers(PUBLIC_V4)))
    sent = _RecordedSend()
    monkeypatch.setattr(notification_service, "async_client_factory", sent.factory)

    status_code, error, delivered = await notification_service.send_webhook(
        "https://collector.example.test/hook",
        "s",
        {"a": 1},
        delivery_id="00000000-0000-0000-0000-000000000001",
        attempt=1,
    )

    assert (status_code, error, delivered) == (200, None, True)
    assert sent.factory_kwargs["trust_env"] is False
    request = sent.requests[0]
    assert request["url"] == f"https://{PUBLIC_V4}/hook"
    assert request["headers"]["Host"] == "collector.example.test"
    assert request["extensions"] == {"sni_hostname": "collector.example.test"}
    assert request["redirects"] is False


@pytest.mark.asyncio
async def test_send_webhook_refuses_a_private_target_before_any_request(monkeypatch):
    calls = []

    def _factory(*args, **kwargs):
        calls.append(args)
        raise AssertionError("no client is built for a refused target")

    _use_loop(monkeypatch, _FakeLoop(answers=_answers("127.0.0.1")))
    monkeypatch.setattr(notification_service, "async_client_factory", _factory)

    status_code, error, delivered = await notification_service.send_webhook(
        "http://collector.example.test:3924/hook",
        "s",
        {"a": 1},
        delivery_id="00000000-0000-0000-0000-000000000001",
        attempt=1,
    )

    assert delivered is False
    assert status_code is None
    assert "public http or https host" in error
    assert calls == []
