"""Load and merge local.toml into AppConfig. Creates a default config
on first run if none exists."""
from __future__ import annotations

import tomllib
from pathlib import Path

import tomli_w

from game_save_cloud_sync.config.schema import AppConfig
from game_save_cloud_sync.utils.logging import get_logger

log = get_logger(__name__)

_DEFAULT = {
    "provider": {
        "kind": "s3",
        "endpoint": "https://s3.example.invalid",
        "bucket": "my-saves",
        "token_keyring_name": "gsync/s3",
        "prefix": "saves/",
    },
    "profiles": [
        {
            "name": "Elden Ring",
            "game_id": "1245620",
            "save_dir": r"%APPDATA%\EldenRing",
            "include_globs": ["**/*.sl2", "**/*.co2"],
            "exclude_globs": ["**/*.bak"],
            "max_file_mb": 128,
        }
    ],
    "debounce_seconds": 2.0,
    "sync_interval_seconds": 300,
    "concurrency": 4,
}


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as fh:
            tomli_w.dump(_DEFAULT, fh)
        log.info("config.created_default", path=str(path))
    with path.open("rb") as fh:
        raw = tomllib.load(fh)
    return AppConfig.model_validate(raw)