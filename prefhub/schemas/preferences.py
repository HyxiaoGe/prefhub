"""
Core preference schemas.

These are the universal preferences shared across all projects.
Each project can extend these with domain-specific fields.

Usage:
    from prefhub.schemas.preferences import UIPreferences, NotificationPreferences

    # Extend for your project
    class AudioPreferences(UIPreferences):
        summary_style: str | None = None
        asr_provider: str | None = None
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from . import HourCycle, Language, Theme


# ──────────────────────────────────────────────
# Universal preferences (every project needs these)
# ──────────────────────────────────────────────


class UIPreferences(BaseModel):
    """Universal UI preferences. Extend this for project-specific needs."""

    language: Language = Field(
        default=Language.ZH_CN,
        description="UI display language",
    )
    theme: Theme = Field(
        default=Theme.SYSTEM,
        description="UI theme",
    )
    timezone: str = Field(
        default="Asia/Shanghai",
        description="User timezone (IANA format)",
    )
    hour_cycle: HourCycle = Field(
        default=HourCycle.AUTO,
        description="Hour display format",
    )

    # Derived helper (not stored, computed from language)
    @property
    def locale(self) -> str:
        """Get locale string from language setting."""
        return str(self.language)


class NotificationPreferences(BaseModel):
    """Universal notification preferences."""

    enabled: bool = Field(
        default=True,
        description="Master switch for notifications",
    )
    task_completed: bool = Field(
        default=True,
        description="Notify when tasks complete",
    )
    task_failed: bool = Field(
        default=True,
        description="Notify when tasks fail",
    )
    sound: bool = Field(
        default=False,
        description="Enable notification sounds",
    )


# ──────────────────────────────────────────────
# Composite preferences container
# ──────────────────────────────────────────────


class BasePreferences(BaseModel):
    """
    Base preferences container. Each project should subclass this
    and add domain-specific fields.

    Example:
        class AudioProjectPreferences(BasePreferences):
            task_defaults: AudioTaskDefaults = Field(default_factory=AudioTaskDefaults)
    """

    ui: UIPreferences = Field(default_factory=UIPreferences)
    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences)

    # Extensible: projects can store arbitrary extra prefs here
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Project-specific extra preferences (escape hatch)",
    )


# ──────────────────────────────────────────────
# API request/response schemas
# ──────────────────────────────────────────────


class PreferencesUpdateRequest(BaseModel):
    """
    Generic PATCH request for updating preferences.
    All fields are optional — only provided fields are merged.
    """

    ui: Optional[UIPreferences] = None
    notifications: Optional[NotificationPreferences] = None
    extra: Optional[dict[str, Any]] = None


class PreferencesResponse(BaseModel):
    """Generic response for preferences endpoints."""

    ui: UIPreferences
    notifications: NotificationPreferences
    extra: dict[str, Any] = Field(default_factory=dict)
