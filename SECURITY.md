# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.9.x   | yes       |
| < 0.9   | no        |

## Threat model

`game-save-cloud-sync` reads local game save directories and writes
them to a cloud backend you configure. It does not phone home, does not
collect telemetry, and does not run remote code.

Attack surface:

- **Provider tokens** — stored in Windows Credential Manager via
  `keyring`. Never written to disk in plaintext. If you find a path
  where a token lands in a log or config file, that is a P1.
- **Local config** — `config/local.toml` is gitignored. Do not commit it.
- **Save path traversal** — the watcher resolves paths from
  `models/save_profile.py`; symlink escapes are rejected.
- **Provider adapters** — HTTPS only; plaintext HTTP endpoints are
  refused at config validation.

## Reporting a vulnerability

Open a private security advisory on GitHub, or email the maintainers
listed in `pyproject.toml`. Include: version, OS build, provider,
reproduction steps. We aim to respond within 72 hours.

Do not open public issues for token-leak or path-traversal bugs.