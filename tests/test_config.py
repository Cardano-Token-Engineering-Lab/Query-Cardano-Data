from datetime import datetime, timezone

import pytest

from cardano_token_framework.config import TimeWindow, TokenIdentifier, get_env_var


class TestTokenIdentifier:
    def test_unit_concatenates_policy_and_asset(self):
        token = TokenIdentifier(policy_id="a" * 56, asset_name="4c51")
        assert token.unit == "a" * 56 + "4c51"

    def test_display_name_decodes_hex_ascii(self):
        # "4c51" decodes to "LQ"
        token = TokenIdentifier(policy_id="a" * 56, asset_name="4c51")
        assert token.display_name == "LQ"

    def test_display_name_falls_back_to_hex_when_not_decodable(self):
        token = TokenIdentifier(policy_id="a" * 56, asset_name="ff")
        assert token.display_name == "ff"

    def test_explicit_display_name_is_respected(self):
        token = TokenIdentifier(
            policy_id="a" * 56, asset_name="4c51", display_name="Custom"
        )
        assert token.display_name == "Custom"

    def test_invalid_policy_id_length_raises(self):
        with pytest.raises(ValueError):
            TokenIdentifier(policy_id="too_short")

    def test_empty_policy_id_raises(self):
        with pytest.raises(ValueError):
            TokenIdentifier(policy_id="")


class TestTimeWindow:
    def test_naive_datetimes_are_assumed_utc(self):
        window = TimeWindow(start=datetime(2024, 1, 1))
        assert window.start.tzinfo == timezone.utc

    def test_start_after_end_raises(self):
        with pytest.raises(ValueError):
            TimeWindow(start=datetime(2024, 2, 1), end=datetime(2024, 1, 1))

    def test_from_strings_parses_iso_dates(self):
        window = TimeWindow.from_strings("2024-01-01", "2024-02-01")
        assert window.start == datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert window.end == datetime(2024, 2, 1, tzinfo=timezone.utc)

    def test_from_strings_with_no_bounds(self):
        window = TimeWindow.from_strings()
        assert window.start is None
        assert window.end is None

    @pytest.mark.parametrize(
        "when,expected",
        [
            (datetime(2024, 1, 15, tzinfo=timezone.utc), True),
            (datetime(2023, 12, 31, tzinfo=timezone.utc), False),
            (datetime(2024, 2, 1, tzinfo=timezone.utc), False),  # end is exclusive
            (datetime(2024, 1, 1, tzinfo=timezone.utc), True),  # start is inclusive
        ],
    )
    def test_contains(self, when, expected):
        window = TimeWindow.from_strings("2024-01-01", "2024-02-01")
        assert window.contains(when) is expected

    def test_contains_with_no_bounds_always_true(self):
        window = TimeWindow()
        assert window.contains(datetime(2000, 1, 1, tzinfo=timezone.utc)) is True

    def test_contains_handles_naive_datetime_input(self):
        window = TimeWindow.from_strings("2024-01-01", "2024-02-01")
        assert window.contains(datetime(2024, 1, 15)) is True


class TestGetEnvVar:
    def test_returns_value_when_set(self, monkeypatch):
        monkeypatch.setenv("SOME_TEST_VAR", "secret-value")
        assert get_env_var("SOME_TEST_VAR") == "secret-value"

    def test_raises_clear_error_when_missing(self, monkeypatch):
        monkeypatch.delenv("SOME_MISSING_VAR", raising=False)
        with pytest.raises(OSError, match="SOME_MISSING_VAR"):
            get_env_var("SOME_MISSING_VAR")
