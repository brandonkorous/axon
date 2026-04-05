"""VaultWatcher — filesystem watcher that keeps VaultCache in sync with external edits."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from axon.logging import get_logger

if TYPE_CHECKING:
    from axon.vault.cache import VaultCache

logger = get_logger(__name__)

# Debounce window in seconds — batches rapid saves (Obsidian temp files, Windows duplicates)
DEBOUNCE_SECONDS = 0.2


class _VaultEventHandler(FileSystemEventHandler):
    """Handles filesystem events for .md files and updates the cache."""

    def __init__(self, vault_path: Path, cache: "VaultCache"):
        self._vault_path = vault_path
        self._cache = cache
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._schedule_update(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._schedule_update(event.src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._schedule_remove(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._schedule_remove(event.src_path)
            if hasattr(event, "dest_path"):
                self._schedule_update(event.dest_path)

    def _schedule_update(self, abs_path: str) -> None:
        """Debounced cache update for a file."""
        rel_path = self._to_relative(abs_path)
        if rel_path is None:
            return

        with self._lock:
            existing = self._timers.pop(rel_path, None)
            if existing:
                existing.cancel()

            timer = threading.Timer(DEBOUNCE_SECONDS, self._do_update, args=[rel_path])
            timer.daemon = True
            self._timers[rel_path] = timer
            timer.start()

    def _schedule_remove(self, abs_path: str) -> None:
        """Debounced cache removal for a file."""
        rel_path = self._to_relative(abs_path)
        if rel_path is None:
            return

        with self._lock:
            existing = self._timers.pop(rel_path, None)
            if existing:
                existing.cancel()

            timer = threading.Timer(DEBOUNCE_SECONDS, self._do_remove, args=[rel_path])
            timer.daemon = True
            self._timers[rel_path] = timer
            timer.start()

    def _do_update(self, rel_path: str) -> None:
        """Actually update the cache for a file."""
        logger.debug("Watcher: updating cache for %s", rel_path)
        try:
            self._cache.update(rel_path)
        except Exception:
            logger.warning("Watcher: failed to update %s", rel_path, exc_info=True)

    def _do_remove(self, rel_path: str) -> None:
        """Actually remove a file from the cache."""
        logger.debug("Watcher: removing %s from cache", rel_path)
        try:
            self._cache.remove(rel_path)
        except Exception:
            logger.warning("Watcher: failed to remove %s", rel_path, exc_info=True)

    def _to_relative(self, abs_path: str) -> str | None:
        """Convert absolute path to vault-relative path, filtering non-.md files."""
        path = Path(abs_path)
        if path.suffix != ".md" or path.name.startswith("."):
            return None
        try:
            return str(path.relative_to(self._vault_path)).replace("\\", "/")
        except ValueError:
            return None


class VaultWatcher:
    """Watches a vault directory for filesystem changes and updates the cache."""

    def __init__(self, vault_path: str | Path, cache: "VaultCache"):
        self._vault_path = Path(vault_path)
        self._cache = cache
        self._observer: Observer | None = None

    def start(self) -> None:
        """Start watching the vault directory."""
        if self._observer:
            return

        handler = _VaultEventHandler(self._vault_path, self._cache)
        self._observer = Observer()
        self._observer.schedule(handler, str(self._vault_path), recursive=True)
        self._observer.daemon = True
        self._observer.start()
        logger.info("VaultWatcher started for %s", self._vault_path)

    def stop(self) -> None:
        """Stop watching."""
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
            logger.info("VaultWatcher stopped for %s", self._vault_path)
