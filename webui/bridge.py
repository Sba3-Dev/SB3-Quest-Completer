"""Small, allow-listed bridge for the HTML presentation layer.

The current Tk frontend remains the default until the HTML adapter is enabled and
verified on Windows. This module intentionally contains no filesystem or process
access; backend adapters are added in later migration slices.
"""
from __future__ import annotations

from typing import Any, Callable


class WebUiBridge:
    """Expose only presentation-safe callbacks to JavaScript."""

    def __init__(self, *, state_provider: Callable[[], dict[str, Any]] | None = None,
                 on_refresh: Callable[[], None] | None = None,
                 on_health: Callable[[], dict[str, Any]] | None = None,
                 on_login: Callable[[], None] | None = None,
                 on_support: Callable[[], None] | None = None,
                 on_membership: Callable[[], None] | None = None,
                 on_logout: Callable[[], None] | None = None,
                 on_update: Callable[[], None] | None = None,
                 on_add: Callable[[str], None] | None = None,
                 on_remove: Callable[[str], None] | None = None,
                 on_run: Callable[[str], None] | None = None,
                 on_stop: Callable[[str], None] | None = None,
                 on_stop_all: Callable[[], None] | None = None) -> None:
        self._state_provider = state_provider or (lambda: {})
        self._on_refresh = on_refresh
        self._on_health = on_health
        self._on_login, self._on_support = on_login, on_support
        self._on_membership, self._on_logout, self._on_update = on_membership, on_logout, on_update
        self._on_add, self._on_remove = on_add, on_remove
        self._on_run, self._on_stop, self._on_stop_all = on_run, on_stop, on_stop_all

    def bootstrap(self) -> dict[str, Any]:
        value = self._state_provider()
        return value if isinstance(value, dict) else {}

    def refresh_library(self) -> None:
        if self._on_refresh:
            self._on_refresh()

    def health_check(self) -> dict[str, Any]:
        if self._on_health:
            value = self._on_health()
            return value if isinstance(value, dict) else {}
        return {}

    def open_login(self) -> None:
        if self._on_login:
            self._on_login()

    def open_support(self) -> None:
        if self._on_support:
            self._on_support()

    def refresh_membership(self) -> None:
        if self._on_membership:
            self._on_membership()

    def logout(self) -> None:
        if self._on_logout:
            self._on_logout()

    def install_update(self) -> None:
        if self._on_update:
            self._on_update()

    def add_to_queue(self, game_id: str) -> None:
        if self._on_add and isinstance(game_id, str) and game_id.strip():
            self._on_add(game_id.strip())

    def remove_from_queue(self, game_id: str) -> None:
        if self._on_remove and isinstance(game_id, str) and game_id.strip():
            self._on_remove(game_id.strip())

    def run_quest(self, game_id: str) -> bool:
        if self._on_run and isinstance(game_id, str) and game_id.strip():
            result = self._on_run(game_id.strip())
            return result is not False
        return False

    def stop_quest(self, game_id: str) -> None:
        if self._on_stop and isinstance(game_id, str) and game_id.strip():
            self._on_stop(game_id.strip())

    def stop_all(self) -> None:
        if self._on_stop_all:
            self._on_stop_all()
