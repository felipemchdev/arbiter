from __future__ import annotations

import pytest

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