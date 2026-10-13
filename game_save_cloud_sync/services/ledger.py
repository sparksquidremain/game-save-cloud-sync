"""Ledger — append-only SQLite record of every transfer. Used by the UI
and by conflict resolution to know what we last pushed."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from game_save_cloud_sync.models.transfer import TransferRecord

_SCHEMA = """
CREATE TABLE IF NOT EXISTS transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile TEXT NOT NULL,
    local_path TEXT NOT NULL,
    remote_key TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    mtime REAL NOT NULL,
    state TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    started_at REAL NOT NULL,
    finished_at REAL
);
CREATE INDEX IF NOT EXISTS idx_transfers_key ON transfers(remote_key);
"""


class Ledger:
    def __init__(self, path: Path = Path("state/ledger.sqlite3")) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.executescript(_SCHEMA)

    def append(self, rec: TransferRecord) -> None:
        self._conn.execute(
            "INSERT INTO transfers (profile, local_path, remote_key, size_bytes, mtime, "
            "state, attempts, last_error, started_at, finished_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (rec.profile, str(rec.local_path), rec.remote_key, rec.size_bytes,
             rec.mtime, rec.state.value, rec.attempts, rec.last_error,
             rec.started_at, rec.finished_at or time.time()),
        )
        self._conn.commit()

    def last_remote_digest(self, remote_key: str) -> str | None:
        cur = self._conn.execute(
            "SELECT remote_key FROM transfers WHERE remote_key=? AND state='done' "
            "ORDER BY finished_at DESC LIMIT 1", (remote_key,))
        row = cur.fetchone()
        return row[0] if row else None