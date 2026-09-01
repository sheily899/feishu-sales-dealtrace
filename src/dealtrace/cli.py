"""Command-line entry point for the Feishu sales workbench."""
from __future__ import annotations

import argparse

from . import __version__


def cmd_workbench(args) -> int:
    from .workbench import run_workbench

    feishu_config = None
    if args.feishu:
        from dotenv import load_dotenv

        from .feishu import FeishuConfig

        load_dotenv(override=False)
        feishu_config = FeishuConfig.from_env()
    run_workbench(host=args.host, port=args.port, feishu_config=feishu_config)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dealtrace", description="Feishu sales conversation workbench.")
    parser.add_argument("--version", action="version", version=f"dealtrace {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    workbench = sub.add_parser("workbench", help="run the local Feishu sales workbench")
    workbench.add_argument("--host", default="127.0.0.1")
    workbench.add_argument("--port", type=int, default=8765)
    workbench.add_argument("--feishu", action="store_true", help="receive Feishu group messages")
    workbench.set_defaults(func=cmd_workbench)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
