"""
SQLAlchemy mixins for storing user preferences.

Supports two patterns your projects already use:

Pattern A (audio-assistant style): Preferences embedded in User.settings JSONB
    class User(PreferencesEmbeddedMixin, Base):
        __tablename__ = "users"
        id = mapped_column(...)

Pattern B (idea-generator style): Separate UserSettings table
    class UserSettings(PreferencesTableMixin, Base):
        __tablename__ = "user_settings"
        user_id = mapped_column(ForeignKey("users.id"), primary_key=True)

Both patterns store preferences as JSONB, so the service layer works identically.
"""

from __future__ import annotations

from typing import Any

try:
    from sqlalchemy import text
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.orm import Mapped, mapped_column

    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False


def _check_sqlalchemy() -> None:
    if not HAS_SQLALCHEMY:
        raise ImportError(
            "SQLAlchemy is required for model mixins. "
            "Install with: pip install prefhub[sqlalchemy]"
        )


class PreferencesEmbeddedMixin:
    """
    Pattern A: Preferences stored inside a `settings` JSONB column on the User table.
    (Like ai-audio-assistant-web)

    The `settings` column holds: {"preferences": {...}, ...other stuff...}
    """

    if HAS_SQLALCHEMY:
        settings: Mapped[dict[str, Any]] = mapped_column(
            JSONB,
            default=dict,
            server_default=text("'{}'::jsonb"),
            nullable=False,
        )

    def get_preferences_dict(self) -> dict[str, Any]:
        """Extract preferences sub-dict from settings."""
        settings = self.settings if isinstance(self.settings, dict) else {}  # type: ignore[attr-defined]
        prefs = settings.get("preferences", {})
        return prefs if isinstance(prefs, dict) else {}

    def set_preferences_dict(self, prefs: dict[str, Any]) -> None:
        """Write preferences back into settings."""
        settings = dict(self.settings) if isinstance(self.settings, dict) else {}  # type: ignore[attr-defined]
        settings["preferences"] = prefs
        self.settings = settings  # type: ignore[attr-defined]


class PreferencesTableMixin:
    """
    Pattern B: Preferences in a dedicated table with a JSONB column.
    (Like idea-generator-web)

    The `preferences` column holds the full preferences dict directly.
    """

    if HAS_SQLALCHEMY:
        preferences: Mapped[dict[str, Any]] = mapped_column(
            JSONB,
            default=dict,
            server_default=text("'{}'::jsonb"),
            nullable=False,
        )

    def get_preferences_dict(self) -> dict[str, Any]:
        """Get preferences dict."""
        prefs = self.preferences  # type: ignore[attr-defined]
        return prefs if isinstance(prefs, dict) else {}

    def set_preferences_dict(self, prefs: dict[str, Any]) -> None:
        """Set preferences dict."""
        self.preferences = prefs  # type: ignore[attr-defined]
