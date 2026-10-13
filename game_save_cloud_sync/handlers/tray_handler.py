"""System tray handler. Bridges the tray menu to the sync service.

Note: tray uses pystray which blocks; run in a daemon thread."""
from __future__ import annotations

import threading
from typing import Callable

from game_save_cloud_sync.utils.logging import get_logger

log = get_logger(__name__)


class TrayHandler:
    def __init__(self, on_sync: Callable[[], int], on_quit: Callable[[], None]) -> None:
        self._on_sync = on_sync
        self._on_quit = on_quit

    def start(self) -> None:
        t = threading.Thread(target=self._run, daemon=True, name="gsync-tray")
        t.start()

    def _run(self) -> None:
        try:
            import pystray  # optional dep; import lazily
            from PIL import Image
        except ImportError:
            log.warning("tray.unavailable", reason="pystray/Pillow not installed")
            return
        menu = pystray.Menu(
            pystray.MenuItem("Sync now", lambda *_: self._on_sync()),
            pystray.MenuItem("Quit", lambda *_: (self._on_quit(),)),
        )
        icon = pystray.Icon("gsync", Image.new("RGB", (16, 16), (60, 60, 60)),
                            "game-save-cloud-sync", menu)
        icon.run()