from __future__ import annotations

from arbiter.decorator import Arbiter


def test_monitor_returns_function_result(monkeypatch):
    sent = []

    class DummyClient:
        def send_run(self, payload):
            sent.append(payload)

    arbiter = Arbiter(api_key="arb_x", pipeline="helios", api_url="http://localhost:8000")
    arbiter.client = DummyClient()

    @arbiter.monitor
    def add(a, b):
        return a + b

    assert add(1, 2) == 3
    assert sent == [] or sent[0].pipeline == "helios"