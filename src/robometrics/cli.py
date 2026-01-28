"""Command line interface for robometrics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from robometrics import __version__
from robometrics.adapters.demolog import DemoLogAdapter
from robometrics.io.run_io import RunWriter


def _handle_placeholder(args: argparse.Namespace) -> int:
    print(f"Subcommand '{args.command}' is not implemented in bootstrap.")
    return 0


def _handle_ingest(args: argparse.Namespace) -> int:
    adapter_name = args.adapter.lower()
    if adapter_name != "demolog":
        print(f"Unsupported adapter: {args.adapter}", file=sys.stderr)
        return 2

    run, report = DemoLogAdapter.read(Path(args.input))
    if report.errors:
        for error in report.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    out_path = RunWriter.write(run, report, Path(args.out))
    print(out_path)
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

    ingest_parser = subparsers.add_parser("ingest", help="ingest workflows")
    ingest_parser.add_argument("--adapter", required=True)
    ingest_parser.add_argument("--input", required=True)
    ingest_parser.add_argument("--out", required=True)
    ingest_parser.set_defaults(func=_handle_ingest)

    for name in ("mine", "eval", "compare"):
        subparser = subparsers.add_parser(name, help=f"{name} workflows")
        subparser.set_defaults(func=_handle_placeholder)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
