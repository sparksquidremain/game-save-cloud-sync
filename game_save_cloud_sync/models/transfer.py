"""Transfer records — one per file per sync pass. Used by the ledger
and by the UI to show progress."""
from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from pathlib import Path


class TransferState(enum.StrEnum):
    PENDING = "pending"
    UPLOADING = "uploading"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(slots=True)
class TransferRecord:
    profile: str
    local_path: Path
    remote_key: str
    size_bytes: int
    mtime: float
    state: TransferState = TransferState.PENDING
    attempts: int = 0
    last_error: str | None = None
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    @property
    def elapsed(self) -> float:
        return (self.finished_at or time.time()) - self.started_at