"""Entry point. Boots the desktop app: parses args, loads config,
starts the watcher service and the sync scheduler."""
from __future__ import annotations

import argparse
import sys

from game_save_cloud_sync.bootstrap.app import AppContext, build_app
from game_save_cloud_sync.utils.logging import configure_logging


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="gsync", description="Game save cloud-backup sync")
    parser.add_argument("--config", default="config/local.toml", help="path to local config")
    parser.add_argument("--once", action="store_true", help="run one sync pass and exit")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    configure_logging(verbose=args.verbose)
    ctx: AppContext = build_app(config_path=args.config)
    if args.once:
        return ctx.sync_service.run_once()
    return ctx.run_forever()


if __name__ == "__main__":
    raise SystemExit(main())