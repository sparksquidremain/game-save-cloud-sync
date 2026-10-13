"""CLI handler. Parses subcommands and delegates to services."""
from __future__ import annotations

from pathlib import Path

from game_save_cloud_sync.bootstrap.app import build_app
from game_save_cloud_sync.utils.logging import get_logger

log = get_logger(__name__)


def handle_list_profiles(config_path: Path) -> int:
    ctx = build_app(config_path)
    for p in ctx.config.profiles:
        print(f"{p.name}\t{p.game_id}\t{p.save_dir}")
    return 0


def handle_sync_now(config_path: Path) -> int:
    ctx = build_app(config_path)
    return ctx.sync_service.run_once()