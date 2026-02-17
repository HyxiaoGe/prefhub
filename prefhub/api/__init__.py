"""
FastAPI router factory for preferences endpoints.

Generates a standard set of preference endpoints that each project
can mount directly. Projects only need to provide their PreferencesService
implementation and auth dependency.

Usage:
    from prefhub.api import create_preferences_router

    router = create_preferences_router(
        get_service=lambda: my_preferences_service,
        get_user_id=get_current_user_id,  # your auth dependency
        prefix="/api/v1/preferences",
    )
    app.include_router(router)
"""

from __future__ import annotations

from typing import Any, Callable

try:
    from fastapi import APIRouter, Depends

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

from prefhub.schemas.preferences import PreferencesResponse, PreferencesUpdateRequest
from prefhub.services.preferences import PreferencesService


def create_preferences_router(
    get_service: Callable[..., PreferencesService],
    get_user_id: Callable[..., str],
    prefix: str = "/preferences",
    tags: list[str] | None = None,
) -> Any:
    """
    Create a standard preferences router.

    Args:
        get_service: FastAPI dependency that returns a PreferencesService instance.
        get_user_id: FastAPI dependency that returns the current user's ID as string.
        prefix: URL prefix for the router.
        tags: OpenAPI tags.

    Returns:
        FastAPI APIRouter with GET, PATCH, DELETE /preferences endpoints.
    """
    if not HAS_FASTAPI:
        raise ImportError(
            "FastAPI is required for the router factory. "
            "Install with: pip install prefhub[fastapi]"
        )

    router = APIRouter(prefix=prefix, tags=tags or ["preferences"])

    @router.get("", response_model=PreferencesResponse)
    async def get_preferences(
        user_id: str = Depends(get_user_id),
        service: PreferencesService = Depends(get_service),
    ) -> PreferencesResponse:
        """Get current user preferences with defaults applied."""
        return await service.get(user_id)

    @router.patch("", response_model=PreferencesResponse)
    async def update_preferences(
        payload: PreferencesUpdateRequest,
        user_id: str = Depends(get_user_id),
        service: PreferencesService = Depends(get_service),
    ) -> PreferencesResponse:
        """Update user preferences. Only provided fields are merged."""
        return await service.update(user_id, payload)

    @router.delete("", response_model=PreferencesResponse)
    async def reset_preferences(
        user_id: str = Depends(get_user_id),
        service: PreferencesService = Depends(get_service),
    ) -> PreferencesResponse:
        """Reset preferences to defaults."""
        return await service.reset(user_id)

    return router
