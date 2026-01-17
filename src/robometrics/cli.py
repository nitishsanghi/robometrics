"""Command line interface for robometrics."""

from __future__ import annotations

import argparse

from robometrics import __version__


def _handle_placeholder(args: argparse.Namespace) -> int:
    print(f"Subcommand '{args.command}' is not implemented in bootstrap.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="robometrics",
        description="Scenario-based offline evaluation for robotics logs.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"robometrics {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("ingest", "mine", "eval", "compare"):
        subparser = subparsers.add_parser(name, help=f"{name} workflows")
        subparser.set_defaults(func=_handle_placeholder)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
