"""SaveProfile runtime representation. Resolves env vars, expands
Windows %APPDATA% style paths, and rejects symlink escapes."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from game_save_cloud_sync.config.schema import SaveProfile as SaveProfileCfg


@dataclass(slots=True, frozen=True)
class ResolvedSaveProfile:
    name: str
    game_id: str
    root: Path
    include_globs: tuple[str, ...]
    exclude_globs: tuple[str, ...]
    max_file_bytes: int


def _expand(raw: str) -> Path:
    expanded = os.path.expandvars(raw)
    return Path(expanded).expanduser()


def resolve(cfg: SaveProfileCfg) -> ResolvedSaveProfile:
    root = _expand(cfg.save_dir).resolve(strict=False)
    return ResolvedSaveProfile(
        name=cfg.name,
        game_id=cfg.game_id,
        root=root,
        include_globs=tuple(cfg.include_globs),
        exclude_globs=tuple(cfg.exclude_globs),
        max_file_bytes=cfg.max_file_mb * 1024 * 1024,
    )


def is_within_root(candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve().relative_to(root)
    except ValueError:
        return False
    return True