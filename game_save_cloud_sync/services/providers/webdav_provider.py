"""WebDAV provider (Nextcloud, ownCloud, generic WebDAV)."""
from __future__ import annotations

from pathlib import Path

import httpx

from game_save_cloud_sync.config.schema import ProviderConfig
from game_save_cloud_sync.services.providers.base import ProviderAdapter
from game_save_cloud_sync.utils.secrets import get_token


class WebDAVProvider(ProviderAdapter):
    def __init__(self, cfg: ProviderConfig) -> None:
        self._cfg = cfg
        self._token = get_token(cfg.token_keyring_name)
        self._client = httpx.AsyncClient(base_url=cfg.endpoint, timeout=60.0,
                                         auth=(cfg.bucket or "user", self._token))

    async def push(self, local: Path, remote_key: str, digest: str) -> None:
        resp = await self._client.put(f"/{remote_key}", content=local.read_bytes())
        resp.raise_for_status()

    async def pull(self, remote_key: str, local: Path) -> None:
        resp = await self._client.get(f"/{remote_key}")
        resp.raise_for_status()
        local.write_bytes(resp.content)

    async def list_remote(self, prefix: str, game_id: str) -> dict[str, str]:
        resp = await self._client.request("PROPFIND", f"/{prefix}{game_id}/",
                                          headers={"Depth": "1"})
        resp.raise_for_status()
        return {elem.text or "": "" for elem in resp.iter("href")}