"""Windows save-folder locator. Knows where Steam, Epic, and GOG stash
saves, and resolves %APPDATA% / %USERPROFILE% style paths."""
from __future__ import annotations

import os
from pathlib import Path

from game_save_cloud_sync.utils.logging import get_logger

log = get_logger(__name__)


class GameSaveLocator:
    """Resolves common Windows save locations for a game."""

    def __init__(self) -> None:
        self._appdata = Path(os.environ.get("APPDATA", ""))
        self._local = Path(os.environ.get("LOCALAPPDATA", ""))
        self._docs = Path(os.environ.get("USERPROFILE", "")) / "Documents"

    def steam_userdata(self, appid: str, steam_id: str | None = None) -> Path | None:
        base = Path(r"C:\Program Files (x86)\Steam\userdata")
        if not base.exists():
            return None
        candidates = [base / steam_id] if steam_id else list(base.iterdir())
        for user in candidates:
            target = user / appid / "remote"
            if target.exists():
                return target
        return None

    def epic_saved(self, game_id: str) -> Path | None:
        target = self._local / "EpicGamesLauncher" / "Saved" / "SaveGames" /