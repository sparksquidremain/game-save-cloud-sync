"""Conflict resolution. Policy: newest-mtime wins unless the remote is
strictly newer AND the local file is untouched since last push."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class ConflictVerdict:
    winner: str  # "local" | "remote"
    reason: str


def resolve_conflict(local_mtime: float, remote_mtime: float,
                     local_since_last_push: bool) -> ConflictVerdict:
    if local_since_last_push and remote_mtime > local_mtime:
        return ConflictVerdict("remote", "remote newer and local untouched")
    if local_mtime >= remote_mtime:
        return ConflictVerdict("local", "local newer or equal")
    return ConflictVerdict("remote", "remote strictly newer")