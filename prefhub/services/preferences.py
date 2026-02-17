"""
Storage-agnostic preferences service.

Handles the merge logic that's identical across projects.
Each project plugs in its own storage backend (JSONB column, separate table, Redis, etc.)

Usage:
    from prefhub.services.preferences import PreferencesService

    class MyPreferencesService(PreferencesService):
        async def _load_raw(self, user_id: str) -> dict:
            # Load from your DB
            row = await db.get(user_id)
            return row.preferences if row else {}

        async def _save_raw(self, user_id: str, data: dict) -> None:
            # Save to your DB
            await db.upsert(user_id, preferences=data)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

from prefhub.schemas.preferences import (
    BasePreferences,
    NotificationPreferences,
    PreferencesResponse,
    PreferencesUpdateRequest,
    UIPreferences,
)

T = TypeVar("T", bound=BasePreferences)


def deep_merge(base: dict, override: dict) -> dict:
    """
    Deep merge two dicts. override values take precedence.
    Nested dicts are merged recursively; other values are replaced.
    """
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class PreferencesService(ABC):
    """
    Abstract preferences service. Subclass and implement _load_raw / _save_raw
    to plug in your storage backend.
    """

    @abstractmethod
    async def _load_raw(self, user_id: str) -> dict[str, Any]:
        """Load raw preferences dict from storage. Return {} if not found."""
        ...

    @abstractmethod
    async def _save_raw(self, user_id: str, data: dict[str, Any]) -> None:
        """Persist raw preferences dict to storage."""
        ...

    async def get(self, user_id: str) -> PreferencesResponse:
        """Get user preferences with defaults applied."""
        raw = await self._load_raw(user_id)
        prefs = BasePreferences(**raw) if raw else BasePreferences()
        return PreferencesResponse(
            ui=prefs.ui,
            notifications=prefs.notifications,
            extra=prefs.extra,
        )

    async def update(
        self, user_id: str, request: PreferencesUpdateRequest
    ) -> PreferencesResponse:
        """
        Merge-update preferences. Only provided fields are changed.
        This is the core logic that every project repeats — now centralized.
        """
        current_raw = await self._load_raw(user_id)

        # Build the update dict from non-None fields
        update_dict: dict[str, Any] = {}
        if request.ui is not None:
            update_dict["ui"] = request.ui.model_dump(exclude_unset=True)
        if request.notifications is not None:
            update_dict["notifications"] = request.notifications.model_dump(exclude_unset=True)
        if request.extra is not None:
            update_dict["extra"] = request.extra

        # Deep merge current with updates
        merged = deep_merge(current_raw, update_dict)
        await self._save_raw(user_id, merged)

        # Return validated result
        prefs = BasePreferences(**merged)
        return PreferencesResponse(
            ui=prefs.ui,
            notifications=prefs.notifications,
            extra=prefs.extra,
        )

    async def reset(self, user_id: str) -> PreferencesResponse:
        """Reset to defaults."""
        defaults = BasePreferences()
        await self._save_raw(user_id, defaults.model_dump())
        return PreferencesResponse(
            ui=defaults.ui,
            notifications=defaults.notifications,
            extra=defaults.extra,
        )


class InMemoryPreferencesService(PreferencesService):
    """In-memory implementation for testing."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    async def _load_raw(self, user_id: str) -> dict[str, Any]:
        return dict(self._store.get(user_id, {}))

    async def _save_raw(self, user_id: str, data: dict[str, Any]) -> None:
        self._store[user_id] = dict(data)
