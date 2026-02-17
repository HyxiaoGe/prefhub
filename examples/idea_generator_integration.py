"""
Example: How idea-generator-web integrates prefhub.

This replaces:
  - api/schemas/settings.py (preference parts)
  - api/routers/settings.py (preference CRUD)
  - database/repositories/settings_repo.py (partially)
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, Field

# ──────────────────────────────────────────────
# 1. Extend schemas for image-generation-specific preferences
# ──────────────────────────────────────────────
from prefhub.schemas.preferences import (
    BasePreferences,
    PreferencesResponse,
    PreferencesUpdateRequest,
    UIPreferences,
)
from prefhub.services.preferences import PreferencesService


class RoutingStrategy(StrEnum):
    PRIORITY = "priority"
    COST = "cost"
    QUALITY = "quality"
    SPEED = "speed"
    ROUND_ROBIN = "round_robin"
    ADAPTIVE = "adaptive"


class GenerationDefaults(BaseModel):
    """Image generation specific defaults."""

    default_aspect_ratio: Optional[str] = Field(default=None)
    default_resolution: Optional[str] = Field(default=None)
    default_provider: Optional[str] = Field(default=None)
    routing_strategy: Optional[RoutingStrategy] = Field(default=None)


class ProviderPreference(BaseModel):
    provider: str
    enabled: bool = True
    priority: int = Field(default=100, ge=1)
    max_daily_usage: Optional[int] = Field(default=None, ge=0)


class ProviderPreferences(BaseModel):
    providers: list[ProviderPreference] = Field(default_factory=list)
    fallback_enabled: bool = True


class IdeaGeneratorPreferences(BasePreferences):
    """Idea generator preferences = universal + generation-specific."""

    generation: GenerationDefaults = Field(default_factory=GenerationDefaults)
    providers: ProviderPreferences = Field(default_factory=ProviderPreferences)


# ──────────────────────────────────────────────
# 2. Implement storage backend (Pattern B: separate table)
# ──────────────────────────────────────────────


class IdeaGeneratorPreferencesService(PreferencesService):
    """
    Storage backend using the existing user_settings table.
    """

    def __init__(self, settings_repo, user_repo):
        self.settings_repo = settings_repo
        self.user_repo = user_repo

    async def _load_raw(self, user_id: str) -> dict[str, Any]:
        from uuid import UUID

        settings = await self.settings_repo.get_by_user_id(UUID(user_id))
        if not settings:
            return {}
        return settings.preferences or {}

    async def _save_raw(self, user_id: str, data: dict[str, Any]) -> None:
        from uuid import UUID

        await self.settings_repo.upsert(
            user_id=UUID(user_id),
            preferences=data,
        )


# ──────────────────────────────────────────────
# 3. Mount the router
# ──────────────────────────────────────────────

"""
from prefhub.api import create_preferences_router

preferences_router = create_preferences_router(
    get_service=lambda: IdeaGeneratorPreferencesService(settings_repo, user_repo),
    get_user_id=get_current_user_id,
    prefix="/api/settings/preferences",
)
app.include_router(preferences_router)
"""
