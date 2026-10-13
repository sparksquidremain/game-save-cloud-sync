"""Provider registry. Maps config kind -> adapter class."""
from __future__ import annotations

from game_save_cloud_sync.config.schema import ProviderConfig
from game_save_cloud_sync.services.providers.base import ProviderAdapter
from game_save_cloud_sync.services.providers.s3_provider import S3Provider
from game_save_cloud_sync.services.providers.webdav_provider import WebDAVProvider

_REGISTRY: dict[str, type[ProviderAdapter]] = {
    "s3": S3Provider,
    "webdav": WebDAVProvider,
}


def build_provider(cfg: ProviderConfig) -> ProviderAdapter:
    try:
        cls = _REGISTRY[cfg.kind]
    except KeyError as exc:
        raise ValueError(f"unknown provider kind: {cfg.kind!r}") from exc
    return cls(cfg)