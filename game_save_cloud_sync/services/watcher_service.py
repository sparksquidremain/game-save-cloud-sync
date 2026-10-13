"""WatcherService — wraps watchdog to debounce filesystem events and
kick off a sync pass. Debounce matters: games write saves in bursts."""
from __future__ import annotations

import threading
import time

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from game_save_cloud_sync.config.schema import AppConfig
from game_save_cloud_sync.models.save_profile import ResolvedSaveProfile, resolve
from game_save_cloud_sync.services.sync_service import SyncService
from game_save_cloud_sync.platform.windows.paths import GameSaveLocator
from game_save_cloud_sync.utils.logging import get_logger

log = get_logger(__name__)


class _DebouncedHandler(FileSystemEventHandler):
    def __init__(self, debounce: float, on_flush) -> None:
        self._debounce = debounce
        self._on_flush = on_flush
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce, self._flush)
            self._timer.daemon = True
            self._timer.start()

    def _flush(self) -> None:
        log.info("watcher.flush", ts=time.time())
        self._on_flush()


class WatcherService:
    def __init__(self, config: AppConfig, sync: SyncService,
                 locator: GameSaveLocator) -> None:
        self._cfg = config
        self._sync = sync
        self._locator = locator
        self._observer = Observer()
        self._profiles: list[ResolvedSaveProfile] = [resolve(p) for p in config.profiles]

    def start(self) -> None:
        for profile in self._profiles:
            if not profile.root.exists():
                log.warning("watcher.root_missing", root=str(profile.root))
                continue
            handler = _DebouncedHandler(self._cfg.debounce_seconds, self._trigger_sync)
            self._observer.schedule(handler, str(profile.root), recursive=True)
            log.info("watcher.scheduled", profile=profile.name, root=str(profile.root))
        self._observer.start()

    def _trigger_sync(self) -> None:
        self._sync.run_once()

    def join(self) -> None:
        self._observer.join()

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join(timeout=5)