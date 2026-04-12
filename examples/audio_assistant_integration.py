"""
Example: How ai-audio-assistant-web integrates prefhub.

This replaces:
  - app/schemas/user.py (preference parts)
  - app/services/user_preferences.py
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ──────────────────────────────────────────────
# 1. Extend schemas for audio-specific preferences
# ──────────────────────────────────────────────
from prefhub.schemas.preferences import (
    BasePreferences,
)
from prefhub.services.preferences import PreferencesService


class AudioTaskDefaults(BaseModel):
    """Audio-assistant specific task defaults."""

    language: str = Field(default="auto", description="Transcription language")
    summary_style: str = Field(default="meeting", description="Summary style")
    enable_speaker_diarization: bool = Field(default=True)
    enable_visual_summary: bool | None = None
    visual_types: list[str] | None = None
    asr_provider: str | None = None
    asr_variant: str | None = None
    llm_provider: str | None = None
    llm_model_id: str | None = None


class AudioPreferences(BasePreferences):
    """Audio assistant preferences = universal + audio-specific."""

    task_defaults: AudioTaskDefaults = Field(default_factory=AudioTaskDefaults)


# ──────────────────────────────────────────────
# 2. Implement storage backend (Pattern A: embedded JSONB)
# ──────────────────────────────────────────────


class AudioPreferencesService(PreferencesService):
    """
    Storage backend using the existing User.settings JSONB column.
    Minimal change to existing code.
    """

    def __init__(self, db_session):
        self.db = db_session

    async def _load_raw(self, user_id: str) -> dict[str, Any]:
        # Reuse existing pattern: user.settings["preferences"]
        user = await self._get_user(user_id)
        if not user:
            return {}
        settings = user.settings if isinstance(user.settings, dict) else {}
        return settings.get("preferences", {})

    async def _save_raw(self, user_id: str, data: dict[str, Any]) -> None:
        user = await self._get_user(user_id)
        if not user:
            return
        settings = dict(user.settings) if isinstance(user.settings, dict) else {}
        settings["preferences"] = data
        user.settings = settings
        # flag_modified(user, "settings")  # needed for SQLAlchemy JSONB
        await self.db.commit()

    async def _get_user(self, user_id: str):
        # Your existing user query logic
        ...


# ──────────────────────────────────────────────
# 3. Mount the router (in app/main.py or app/api/router.py)
# ──────────────────────────────────────────────

"""
from prefhub.api import create_preferences_router

preferences_router = create_preferences_router(
    get_service=lambda: AudioPreferencesService(db),
    get_user_id=get_current_user_id,
    prefix="/api/v1/users/me/preferences",
)
app.include_router(preferences_router)
"""
