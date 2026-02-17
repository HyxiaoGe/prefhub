# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is PrefHub

A shared Python library that provides unified user preferences management across multiple AI projects (ai-audio-assistant, idea-generator, prompthub). Projects extend a common `BasePreferences` schema with domain-specific fields and implement their own storage backend.

## Development Commands

```bash
pip install -e ".[dev]"        # Install with all deps (FastAPI, SQLAlchemy, pytest, ruff)
pytest tests/ -v               # Run all tests
pytest tests/test_preferences.py::TestDeepMerge -v  # Run single test class
ruff check .                   # Lint
ruff format .                  # Format
```

## Architecture

Four-layer design with optional dependencies (SQLAlchemy and FastAPI are extras, not required):

- **schemas/** — Pydantic models: `UIPreferences`, `NotificationPreferences`, `BasePreferences`, plus enums (`Language`, `Theme`, `HourCycle`) and API contracts (`PreferencesUpdateRequest`, `PreferencesResponse`)
- **services/** — Storage-agnostic business logic: abstract `PreferencesService` (subclass and implement `_load_raw`/`_save_raw`), `deep_merge` for incremental updates, `InMemoryPreferencesService` for tests
- **models/** — SQLAlchemy mixins: `PreferencesEmbeddedMixin` (Pattern A: prefs nested in `User.settings` JSONB) and `PreferencesTableMixin` (Pattern B: dedicated `user_settings` table with JSONB column)
- **api/** — `create_preferences_router()` factory that auto-generates GET/PATCH/DELETE FastAPI endpoints

## Key Patterns

- **Extension model**: Projects subclass `BasePreferences` to add domain-specific fields. An `extra` dict provides an escape hatch for ad-hoc preferences.
- **Deep merge on PATCH**: Only provided fields are changed; existing values are preserved via recursive dict merge.
- **Two storage patterns**: Pattern A embeds preferences inside a broader `settings` JSONB column; Pattern B uses a dedicated table. Both expose the same `get_preferences_dict`/`set_preferences_dict` interface.
- **Optional imports**: SQLAlchemy and FastAPI are guarded by try/except with `HAS_SQLALCHEMY`/`HAS_FASTAPI` flags so the core library works without them.

## Downstream Projects

- **idea-generator-web** — Pattern B (separate `user_settings` table), `UserPreferences` extends `BasePreferences` with `GenerationDefaults` and `ProviderPreferences`
- **ai-audio-assistant** — Pattern A (embedded in `User.settings` JSONB), see `examples/audio_assistant_integration.py`

When modifying schemas or service interfaces, check that downstream projects still import and function correctly.
