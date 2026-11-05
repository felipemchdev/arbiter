import pytest
from collector.airflow import AirflowClient
from collector.main import to_duration_ms


class TestAirflowClient:
    def test_client_creation(self):
        client = AirflowClient("http://localhost:8080", "admin", "admin")
        assert client.base_url == "http://localhost:8080"
        assert client.username == "admin"

    def test_get_client_returns_same_instance(self):
        client = AirflowClient("http://localhost:8080", "user", "pass")
        c1 = client._client()
        c2 = client._client()
        assert c1 is c2
        client.close()


class TestToDurationMs:
    def test_duration_ms_is_not_rescaled(self):
        assert to_duration_ms({"duration_ms": 5000}) == 5000

    def test_duration_seconds_are_scaled(self):
        assert to_duration_ms({"duration": 5}) == 5000

    def test_duration_ms_wins_over_seconds(self):
        assert to_duration_ms({"duration_ms": 1200, "duration": 5}) == 1200

    def test_missing_duration_returns_none(self):
        assert to_duration_ms({}) is None

    def test_zero_duration_ms_is_preserved(self):
        assert to_duration_ms({"duration_ms": 0}) == 0
