"""ProviderAdapter — the contract every cloud backend implements.
Adapters are stateless w.r.t. sync; they only move bytes and list keys."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ProviderAdapter(ABC):
    @abstractmethod
    async def push(self, local: Path, remote_key: str, digest: str) -> None:
        """Upload local to remote_key. digest is the sha256 of the file.
        Must be idempotent: re-pushing the same digest is a no-op."""

    @abstractmethod
    async def pull(self, remote_key: str, local: Path) -> None:
        """Download remote_key to local. Overwrites."""

    @abstractmethod
    async def list_remote(self, prefix: str, game_id: str) -> dict[str, str]:
        """Return {remote_key: sha256_digest} for all keys under prefix/game_id."""