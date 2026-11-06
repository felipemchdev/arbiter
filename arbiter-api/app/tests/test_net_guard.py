from __future__ import annotations

import socket

import pytest

import app.core.net_guard as net_guard
from app.core.net_guard import check_reachable_url, check_stored_url
from app.models.notification_channel import NotificationChannel
from app.services import notification_service


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

    async def getaddrinfo(self, host, port):
        if self._failure is not None:
            raise self._failure
        return self._answers


def _use_loop(monkeypatch, loop):
    monkeypatch.setattr(net_guard.asyncio, "get_running_loop", lambda: loop)


@pytest.mark.asyncio
async def test_check_reachable_url_rejects_a_name_that_resolves_locally(monkeypatch):
    _use_loop(monkeypatch, _FakeLoop(answers=[(2, 1, 6, "", ("10.0.0.5", 443))]))

    with pytest.raises(ValueError):
        await check_reachable_url("https://collector.example.test/hook")


@pytest.mark.asyncio
async def test_check_reachable_url_accepts_a_name_that_resolves_publicly(monkeypatch):
    _use_loop(monkeypatch, _FakeLoop(answers=[(2, 1, 6, "", ("93.184.216.34", 443))]))

    url = "https://collector.example.test/hook"
    assert await check_reachable_url(url) == url


@pytest.mark.asyncio
async def test_check_reachable_url_leaves_an_unresolved_name_alone(monkeypatch):
    _use_loop(monkeypatch, _FakeLoop(failure=socket.gaierror("Name or service not known")))

    url = "https://hook.example.test/arbiter"
    assert await check_reachable_url(url) == url


@pytest.mark.asyncio
async def test_send_webhook_refuses_a_private_target_before_any_request(monkeypatch):
    calls = []

    def _factory(*args, **kwargs):
        calls.append(args)
        raise AssertionError("no client is built for a refused target")

    monkeypatch.setattr(notification_service, "async_client_factory", _factory)
    channel = NotificationChannel(
        name="internal", url="http://127.0.0.1:3924/hook", signing_secret="s", enabled=True
    )

    status_code, error, delivered = await notification_service.send_webhook(
        channel, {"a": 1}, delivery_id="00000000-0000-0000-0000-000000000001", attempt=1
    )

    assert delivered is False
    assert status_code is None
    assert "public http or https host" in error
    assert calls == []
