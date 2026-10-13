"""SyncService — the core. Walks a profile, diffs against the remote
manifest, uploads changed files, records a ledger entry per transfer.

Concurrency: bounded by AppConfig.concurrency. Each provider call is
awaited in a worker; the ledger write is serialized behind an asyncio
lock because SQLite is single-writer.
"""
from __future__ import annotations

import asyncio
import fnmatch
import hashlib
from pathlib import Path

from game_save_cloud_sync.config.schema import AppConfig
from game_save_cloud_sync.models.save_profile import ResolvedSaveProfile, is_within_root, resolve
from game_save_cloud_sync.models.transfer import TransferRecord, TransferState
from game_save_cloud_sync.services.ledger import Ledger
from game_save_cloud_sync.services.providers.base import ProviderAdapter
from game_save_cloud_sync.platform.windows.paths import GameSaveLocator
from game_save_cloud_sync.utils.logging import get_logger

log = get_logger(__name__)

_CHUNK = 1 << 20  # 1 MiB read chunk; keeps peak RSS bounded for big saves


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def _included(path: Path, profile: ResolvedSaveProfile) -> bool:
    rel = path.relative_to(profile.root).as_posix()
    if any(fnmatch.fnmatch(rel, g) for g in profile.exclude_globs):
        return False
    return any(fnmatch.fnmatch(rel, g) for g in profile.include_globs)


class SyncService:
    def __init__(self, config: AppConfig, provider: ProviderAdapter,
                 locator: GameSaveLocator) -> None:
        self._cfg = config
        self._provider = provider
        self._locator = locator
        self._ledger = Ledger()
        self._sem = asyncio.Semaphore(config.concurrency)
        self._ledger_lock = asyncio.Lock()

    async def sync_profile(self, profile: ResolvedSaveProfile) -> list[TransferRecord]:
        files = self._collect(profile)
        remote = await self._provider.list_remote(self._cfg.provider.prefix, profile.game_id)
        tasks = [self._upload_one(profile, f, remote) for f in files]
        return [r for r in await asyncio.gather(*tasks) if r is not None]

    def _collect(self, profile: ResolvedSaveProfile) -> list[Path]:
        if not profile.root.exists():
            log.warning("sync.profile_missing", profile=profile.name, root=str(profile.root))
            return []
        out: list[Path] = []
        for p in profile.root.rglob("*"):
            if not p.is_file() or not is_within_root(p, profile.root):
                continue
            if not _included(p, profile):
                continue
            if p.stat().st_size > profile.max_file_bytes:
                log.warning("sync.file_too_large", path=str(p))
                continue
            out.append(p)
        return out

    async def _upload_one(self, profile: ResolvedSaveProfile, local: Path,
                          remote: dict[str, str]) -> TransferRecord | None:
        rel = local.relative_to(profile.root).as_posix()
        key = f"{self._cfg.provider.prefix}{profile.game_id}/{rel}"
        digest = _sha256(local)
        if remote.get(key) == digest:
            rec = TransferRecord(profile.name, local, key, local.stat().st_size,
                                 local.stat().st_mtime, TransferState.SKIPPED)
            await self._record(rec)
            return rec
        rec = TransferRecord(profile.name, local, key, local.stat().st_size,
                             local.stat().st_mtime, TransferState.UPLOADING)
        async with self._sem:
            try:
                await self._provider.push(local, key, digest)
                rec.state = TransferState.DONE
            except Exception as exc:  # provider errors are recoverable; log + retry next pass
                rec.state = TransferState.FAILED
                rec.last_error = str(exc)
                log.error("sync.upload_failed", key=key, error=str(exc))
            finally:
                rec.finished_at = __import__("time").time()
        await self._record(rec)
        return rec

    async def _record(self, rec: TransferRecord) -> None:
        async with self._ledger_lock:
            self._ledger.append(rec)

    def run_once(self) -> int:
        profiles = [resolve(p) for p in self._cfg.profiles]
        results = asyncio.run(self._sync_all(profiles))
        failed = [r for r in results if r.state is TransferState.FAILED]
        log.info("sync.pass_done", total=len(results), failed=len(failed))
        return 1 if failed else 0

    async def _sync_all(self, profiles: list[ResolvedSaveProfile]) -> list[TransferRecord]:
        out: list[TransferRecord] = []
        for p in profiles:
            out.extend(await self.sync_profile(p))
        return out