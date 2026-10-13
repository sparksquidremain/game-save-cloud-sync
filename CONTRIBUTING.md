# Contributing to game-save-cloud-sync

A Windows desktop tool that watches your game save folders and mirrors
them to cloud storage backends (S3-compatible, WebDAV, Google Drive,
OneDrive). Built service-oriented: thin handlers, business services,
data models, platform adapters.

## Ground rules

- Python 3.11+. Type hints are not optional — `mypy --strict` must pass.
- One concern per module. Handlers stay thin; logic lives in services.
- Every provider adapter implements `ProviderAdapter` from
  `game_save_cloud_sync/services/providers/base.py`. No exceptions.
- Never commit real tokens. Tokens live in Windows Credential Manager
  via `keyring`, referenced by name in `config/providers/*.toml`.

## Dev setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Running tests

```powershell
pytest -q
ruff check .
mypy game_save_cloud_sync
```

## Adding a cloud provider

1. Create `game_save_cloud_sync/services/providers/<name>_provider.py`.
2. Subclass `ProviderAdapter`, implement `push`, `pull`, `list_remote`.
3. Register it in `services/providers/registry.py`.
4. Add a config schema in `models/provider_config.py`.
5. Add a test under `tests/`.

## Commit style

Conventional commits: `feat(sync):`, `fix(watcher):`, `chore(deps):`.

## Code of conduct

Be decent. This is a hobbyist tool for backing up your own saves.