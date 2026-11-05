from __future__ import annotations


from app.core.config import Settings


# ---------------------------------------------------------------------------
# Settings.parse_cors_origins — unit tests (no DB or network needed)
# ---------------------------------------------------------------------------

class TestParseCorsOrigins:
    """Tests for the Settings.parse_cors_origins classmethod."""

    def test_single_origin_string(self):
        """A single URL string is returned as a one-element list."""
        result = Settings.parse_cors_origins("http://localhost:3000")
        assert result == ["http://localhost:3000"]

    def test_multiple_origins_comma_separated(self):
        """Comma-separated origins are split into a list."""
        result = Settings.parse_cors_origins(
            "http://localhost:3000,https://dashboard.example.com"
        )
        assert result == ["http://localhost:3000", "https://dashboard.example.com"]

    def test_origins_with_surrounding_whitespace(self):
        """Whitespace around commas is stripped from each origin."""
        result = Settings.parse_cors_origins(
            "  http://localhost:3000 , https://dashboard.example.com  "
        )
        assert result == ["http://localhost:3000", "https://dashboard.example.com"]

    def test_empty_string_returns_empty_list(self):
        """An empty string produces an empty list (no origins)."""
        result = Settings.parse_cors_origins("")
        assert result == []

    def test_only_whitespace_returns_empty_list(self):
        """A string containing only whitespace/commas produces an empty list."""
        result = Settings.parse_cors_origins("  ,  ,  ")
        assert result == []

    def test_double_comma_skips_empty_segment(self):
        """Empty segments from double commas are filtered out."""
        result = Settings.parse_cors_origins(
            "http://localhost:3000,,https://example.com"
        )
        assert result == ["http://localhost:3000", "https://example.com"]

    def test_already_a_list_returned_unchanged(self):
        """When the value is already a list it is returned as-is."""
        origins = ["http://localhost:3000", "https://example.com"]
        result = Settings.parse_cors_origins(origins)
        assert result == origins

    def test_empty_list_returned_unchanged(self):
        """An empty list is returned unchanged."""
        result = Settings.parse_cors_origins([])
        assert result == []

    def test_three_origins(self):
        """Three comma-separated origins are all captured."""
        result = Settings.parse_cors_origins(
            "http://localhost:3000,http://localhost:3001,https://prod.example.com"
        )
        assert len(result) == 3
        assert "http://localhost:3000" in result
        assert "http://localhost:3001" in result
        assert "https://prod.example.com" in result

    def test_trailing_comma_ignored(self):
        """A trailing comma does not produce an empty string entry."""
        result = Settings.parse_cors_origins("http://localhost:3000,")
        assert result == ["http://localhost:3000"]

    def test_leading_comma_ignored(self):
        """A leading comma does not produce an empty string entry."""
        result = Settings.parse_cors_origins(",http://localhost:3000")
        assert result == ["http://localhost:3000"]


# ---------------------------------------------------------------------------
# Settings defaults and construction
# ---------------------------------------------------------------------------

class TestSettingsDefaults:
    """Tests for Settings field defaults related to CORS."""

    def test_cors_origins_default_value(self):
        """The default cors_origins contains http://localhost:3000."""
        # Instantiate without env overrides by passing explicit values for
        # required/defaulted fields to avoid picking up a stale .env file.
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
        )
        assert settings.cors_origins == ["http://localhost:3000"]

    def test_cors_origins_accepts_list_directly(self):
        """cors_origins can be overridden by passing a list."""
        settings = Settings(
            cors_origins=["http://localhost:3000", "https://example.com"],
            _env_file=None,  # type: ignore[call-arg]
        )
        assert "http://localhost:3000" in settings.cors_origins
        assert "https://example.com" in settings.cors_origins

    def test_cors_origins_single_item_default(self):
        """By default exactly one origin is configured."""
        settings = Settings(_env_file=None)  # type: ignore[call-arg]
        assert len(settings.cors_origins) == 1


class TestSecretKeyGuard:
    """Default SECRET_KEY must not survive into a non-development environment."""

    def test_default_key_allowed_in_development(self):
        settings = Settings(_env_file=None, environment="development")  # type: ignore[call-arg]
        assert settings.secret_key == "change-me-in-production"

    def test_default_key_rejected_in_production(self):
        import pytest

        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            Settings(_env_file=None, environment="production")  # type: ignore[call-arg]

    def test_custom_key_accepted_in_production(self):
        settings = Settings(  # type: ignore[call-arg]
            _env_file=None,
            environment="production",
            secret_key="a-long-random-secret-value",
        )
        assert settings.secret_key == "a-long-random-secret-value"

    def test_unknown_environment_rejected(self):
        import pytest

        with pytest.raises(ValueError):
            Settings(_env_file=None, environment="prod")  # type: ignore[call-arg]


class TestHashVerification:
    """A corrupt hash must return False rather than raising NameError."""

    def test_verify_password_with_corrupt_hash(self):
        from app.core.security import verify_password

        assert verify_password("whatever", "not-a-valid-argon2-hash") is False

    def test_verify_refresh_token_with_corrupt_hash(self):
        from app.core.security import verify_refresh_token

        assert verify_refresh_token("whatever", "$argon2id$broken") is False

    def test_verify_api_key_with_corrupt_hash(self):
        from app.core.security import verify_api_key

        assert verify_api_key("whatever", "garbage") is False

    def test_access_token_carries_token_version(self):
        from app.core.security import create_access_token, decode_access_token

        payload = decode_access_token(create_access_token(sub="u", org_id="o", role="owner", token_version=4))
        assert payload["tv"] == 4