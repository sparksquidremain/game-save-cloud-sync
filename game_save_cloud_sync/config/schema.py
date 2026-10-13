"""Typed config schema. Validated at load; a bad config fails fast."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ProviderConfig(BaseModel):
    kind: str = Field(..., description="s3 | webdav | gdrive | onedrive")
    endpoint: str | None = None
    bucket: str | None = None
    token_keyring_name: str = Field(..., description="keyring entry for the token")
    prefix: str = "saves/"

    @field_validator("endpoint")
    @classmethod
    def _no_plaintext_http(cls, v: str | None) -> str | None:
        if v and v.startswith("http://"):
            raise ValueError("plaintext HTTP endpoints are refused")
        return v


class SaveProfile(BaseModel):
    name: str
    game_id: str
    save_dir: str
    include_globs: list[str] = Field(default_factory=lambda: ["**/*"])
    exclude_globs: list[str] = Field(default_factory=lambda: ["**/*.tmp", "**/cache/**"])
    max_file_mb: int = 256


class AppConfig(BaseModel):
    provider: ProviderConfig
    profiles: list[SaveProfile]
    debounce_seconds: float = 2.0
    sync_interval_seconds: int = 300
    concurrency: int = 4