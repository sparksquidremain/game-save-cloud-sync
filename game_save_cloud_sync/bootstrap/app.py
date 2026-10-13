"""Application context. Constructs services once and hands them to
handlers. No business logic here — only wiring."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from game_save_cloud_sync.config.loader import load_config
from game_save_cloud_sync.config.schema import AppConfig
from game_save_cloud_sync.platform.windows.paths import GameSaveLocator
from game_save_cloud_sync.services.providers.registry import build_provider
from game_save_cloud_sync.services.sync_service import SyncService
from game_save_cloud_sync.services.watcher_service import WatcherService
from game_save_cloud_sync.utils.logging import get_logger

log = get_logger(__name__)


@dataclass(slots=True)
class AppContext:
    config: AppConfig
    sync_service: SyncService
    watcher_service: WatcherService

    def run_forever(self) -> int:
        log.info("app.start", profiles=len(self.config.profiles))
        self.watcher_service.start()
        try:
            self.watcher_service.join()
        except KeyboardInterrupt:
            log.info("app.shutdown_requested")
        finally:
            self.watcher_service.stop()
        return 0


def build_app(config_path: str | Path) -> AppContext:
    cfg = load_config(Path(config_path))
    provider = build_provider(cfg.provider)
    locator = GameSaveLocator()
    sync = SyncService(config=cfg, provider=provider, locator=locator)
    watch = WatcherService(config=cfg, sync=sync, locator=locator)
    return AppContext(config=cfg, sync_service=sync, watcher_service=watch)