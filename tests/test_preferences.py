"""Tests for the preferences service core logic."""

from __future__ import annotations

import pytest

from prefhub.schemas import Language, Theme
from prefhub.schemas.preferences import PreferencesUpdateRequest, UIPreferences, NotificationPreferences
from prefhub.services.preferences import InMemoryPreferencesService, deep_merge


@pytest.fixture
def service() -> InMemoryPreferencesService:
    return InMemoryPreferencesService()


class TestDeepMerge:
    def test_flat_merge(self):
        assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_override(self):
        assert deep_merge({"a": 1}, {"a": 2}) == {"a": 2}

    def test_nested_merge(self):
        base = {"ui": {"language": "zh-CN", "theme": "dark"}}
        override = {"ui": {"theme": "light"}}
        result = deep_merge(base, override)
        assert result == {"ui": {"language": "zh-CN", "theme": "light"}}

    def test_empty_override(self):
        base = {"a": 1}
        assert deep_merge(base, {}) == {"a": 1}


class TestPreferencesService:
    @pytest.mark.asyncio
    async def test_get_defaults(self, service: InMemoryPreferencesService):
        """New user should get defaults."""
        result = await service.get("user-1")
        assert result.ui.language == Language.ZH_CN
        assert result.ui.theme == Theme.SYSTEM
        assert result.ui.timezone == "Asia/Shanghai"
        assert result.notifications.enabled is True

    @pytest.mark.asyncio
    async def test_update_partial(self, service: InMemoryPreferencesService):
        """Partial update should only change specified fields."""
        request = PreferencesUpdateRequest(
            ui=UIPreferences(theme=Theme.DARK),
        )
        result = await service.update("user-1", request)
        assert result.ui.theme == Theme.DARK
        # Other fields should remain defaults
        assert result.ui.language == Language.ZH_CN
        assert result.notifications.enabled is True

    @pytest.mark.asyncio
    async def test_update_preserves_previous(self, service: InMemoryPreferencesService):
        """Second update should not lose first update's values."""
        # First update: change theme
        await service.update(
            "user-1",
            PreferencesUpdateRequest(ui=UIPreferences(theme=Theme.DARK)),
        )
        # Second update: change language
        result = await service.update(
            "user-1",
            PreferencesUpdateRequest(ui=UIPreferences(language=Language.EN)),
        )
        # Both should be preserved
        assert result.ui.theme == Theme.DARK
        assert result.ui.language == Language.EN

    @pytest.mark.asyncio
    async def test_update_notifications(self, service: InMemoryPreferencesService):
        request = PreferencesUpdateRequest(
            notifications=NotificationPreferences(sound=True, task_failed=False),
        )
        result = await service.update("user-1", request)
        assert result.notifications.sound is True
        assert result.notifications.task_failed is False
        assert result.notifications.task_completed is True  # default preserved

    @pytest.mark.asyncio
    async def test_update_extra(self, service: InMemoryPreferencesService):
        """Projects can store domain-specific prefs in extra."""
        request = PreferencesUpdateRequest(
            extra={"default_resolution": "2K", "asr_provider": "tencent"},
        )
        result = await service.update("user-1", request)
        assert result.extra["default_resolution"] == "2K"
        assert result.extra["asr_provider"] == "tencent"

    @pytest.mark.asyncio
    async def test_reset(self, service: InMemoryPreferencesService):
        """Reset should restore defaults."""
        await service.update(
            "user-1",
            PreferencesUpdateRequest(ui=UIPreferences(theme=Theme.DARK)),
        )
        result = await service.reset("user-1")
        assert result.ui.theme == Theme.SYSTEM

    @pytest.mark.asyncio
    async def test_isolation_between_users(self, service: InMemoryPreferencesService):
        """Different users should have independent preferences."""
        await service.update(
            "user-1",
            PreferencesUpdateRequest(ui=UIPreferences(theme=Theme.DARK)),
        )
        result = await service.get("user-2")
        assert result.ui.theme == Theme.SYSTEM  # user-2 still has defaults
