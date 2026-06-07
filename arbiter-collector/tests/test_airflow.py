import pytest
from collector.airflow import AirflowClient


class TestAirflowClient:
    def test_client_creation(self):
        client = AirflowClient("http://localhost:8080", "admin", "admin")
        assert client.base_url == "http://localhost:8080"
        assert client.username == "admin"

    def test_get_client_returns_same_instance(self):
        client = AirflowClient("http://localhost:8080", "user", "pass")
        c1 = client._get_client()
        c2 = client._get_client()
        assert c1 is c2
