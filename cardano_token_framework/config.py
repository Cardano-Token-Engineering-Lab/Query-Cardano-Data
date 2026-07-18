"""Shared configuration objects and environment helpers.

This module defines the two primary *inputs* to the framework described in
the Milestone 2 spec: token identifying information (policy ID / asset name)
and a time window to bound the extraction. Both are plain dataclasses so they
are easy to construct from a CLI, a JSON file, or directly in a notebook.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

from dotenv import load_dotenv


@dataclass(frozen=True)
class TokenIdentifier:
    """Identifies a single Cardano native asset.

    Attributes:
        policy_id: 56-character hex policy ID for the asset.
        asset_name: Hex-encoded asset name (the part after the policy ID in
            the asset fingerprint). May be empty for ADA-only contexts.
        display_name: Optional human-readable name, used only for file
            naming and chart labels. If not supplied, it is derived from
            ``asset_name`` by decoding it as ASCII when possible.
    """

    policy_id: str
    asset_name: str = ""
    display_name: str | None = None

    def __post_init__(self) -> None:
        if not self.policy_id or len(self.policy_id) != 56:
            raise ValueError(
                f"policy_id must be a 56-character hex string, got: {self.policy_id!r}"
            )
        if self.display_name is None:
            object.__setattr__(self, "display_name", self._decode_display_name())

    def _decode_display_name(self) -> str:
        if not self.asset_name:
            return self.policy_id[:8]
        try:
            return bytearray.fromhex(self.asset_name).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return self.asset_name

    @property
    def unit(self) -> str:
        """The concatenated policy_id + asset_name, as used by most APIs."""
        return f"{self.policy_id}{self.asset_name}"


@dataclass(frozen=True)
class TimeWindow:
    """A UTC time window used to bound a data extraction.

    Attributes:
        start: Inclusive start of the window. ``None`` means "no lower bound".
        end: Exclusive end of the window. ``None`` means "up to now".
    """

    start: datetime | None = None
    end: datetime | None = None

    def __post_init__(self) -> None:
        for field_name in ("start", "end"):
            value = getattr(self, field_name)
            if value is not None and value.tzinfo is None:
                object.__setattr__(
                    self, field_name, value.replace(tzinfo=timezone.utc)
                )
        if self.start and self.end and self.start > self.end:
            raise ValueError("TimeWindow start must be before end")

    @classmethod
    def from_strings(
        cls, start: str | None = None, end: str | None = None
    ) -> TimeWindow:
        """Build a window from ISO-8601 date/datetime strings (e.g. '2024-01-01')."""
        start_dt = datetime.fromisoformat(start) if start else None
        end_dt = datetime.fromisoformat(end) if end else None
        return cls(start=start_dt, end=end_dt)

    def contains(self, when: datetime) -> bool:
        """Return True if ``when`` falls within [start, end)."""
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        if self.start and when < self.start:
            return False
        return not (self.end and when >= self.end)


def get_env_var(name: str) -> str:
    """Load a required environment variable, raising a clear error if missing.

    Calls :func:`dotenv.load_dotenv` first so a local ``.env`` file (see
    ``.env.example``) is picked up automatically.
    """
    load_dotenv()
    value = os.getenv(name)
    if not value:
        raise OSError(
            f"Required environment variable '{name}' is not set. "
            "Copy .env.example to .env and fill in your API key(s)."
        )
    return value
