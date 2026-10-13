"""S3-compatible provider (AWS, MinIO, Backblaze B2, Wasabi)."""
from __future__ import annotations

from pathlib import Path

import httpx

from game_save_cloud_sync.config.schema import ProviderConfig
from game_save_cloud_sync.services.providers.base import ProviderAdapter
from game_save_cloud_sync.utils.secrets import get_token
from game_save_cloud_sync.utils.logging import get_logger

log = get_logger(__name__)


class S3Provider(ProviderAdapter):
    def __init__(self, cfg: ProviderConfig) -> None:
        self._cfg = cfg
        self._token = get_token(cfg.token_keyring_name)
        self._client = httpx.AsyncClient(base_url=cfg.endpoint, timeout=60.0)

    def _headers(self, digest: str | None = None) -> dict[str, str]:
        h = {"Authorization": f"Bearer {self._token}"}
        if digest:
            h["x-amz-meta-sha256"] = digest
        return h

    async def push(self, local: Path, remote_key: str, digest: str) -> None:
        body = local.read_bytes()
        resp = await self._client.put(
            f"/{self._cfg.bucket}/{remote_key}", content=body, headers=self._headers(digest))
        resp.raise_for_status()

    async def pull(self, remote_key: str, local: Path) -> None:
        resp = await self._client.get(f"/{self._cfg.bucket}/{remote_key}")
        resp.raise_for_status()
        local.write_bytes(resp.content)

    async def list_remote(self, prefix: str, game_id: str) -> dict[str, str]:
        resp = await self._client.get(
            f"/{self._cfg.bucket}", params={"prefix": f"{prefix}{game_id}/", "list-type": "2"},
            headers=self._headers())
        resp.raise_for_status()
        return {obj["Key"]: obj.get("Meta", {}).get("sha256", "") for obj in resp.json().get("Contents", [])}