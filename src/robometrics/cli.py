"""Command line interface for robometrics."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from robometrics import __version__
from robometrics.io.run_io import RunReader
from robometrics.io.run_io import RunWriter
from robometrics.mining.miner import mine_scenarios
from robometrics.mining.rules import load_rules


def _handle_placeholder(args: argparse.Namespace) -> int:
    print(f"Subcommand '{args.command}' is not implemented in bootstrap.")
    return 0


def _handle_ingest(args: argparse.Namespace) -> int:
    adapter_name = args.adapter.lower()
    if adapter_name != "demolog":
        print(f"Unsupported adapter: {args.adapter}", file=sys.stderr)
        return 2

    try:
        from robometrics.adapters.demolog import DemoLogAdapter

        run, report = DemoLogAdapter.read(Path(args.input))
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to read input: {exc}", file=sys.stderr)
        return 1
    if report.errors:
        for error in report.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    try:
        out_path = RunWriter.write(run, report, Path(args.out))
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to write output: {exc}", file=sys.stderr)
        return 1
    print(out_path)
    return 0


def _handle_mine(args: argparse.Namespace) -> int:
    try:
        rules = load_rules(args.rules)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load rules: {exc}", file=sys.stderr)
        return 1

    run_dir = Path(args.run)
    try:
        if (run_dir / "meta.json").exists() and (run_dir / "streams.parquet").exists():
            run, report = RunReader.read(run_dir)
        else:
            from robometrics.adapters.demolog import DemoLogAdapter

            run, report = DemoLogAdapter.read(run_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load run: {exc}", file=sys.stderr)
        return 1

    if report.errors:
        for error in report.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    run_warnings = list(report.warnings)
    scenario_set_id = args.scenario_set_id or f"{run.run_id}-scset"
    created_at = args.created_at or datetime.now(timezone.utc).isoformat()
    scenario_set, mine_report = mine_scenarios(
        run,
        rules,
        scenario_set_id=scenario_set_id,
        created_at=created_at,
    )

    if mine_report.errors:
        for error in mine_report.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    for warning in run_warnings + mine_report.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_id = _sanitize_filename(scenario_set_id)
    out_path = out_dir / f"{safe_id}.scset.json"
    out_path.write_text(
        json.dumps(scenario_set.to_dict(), sort_keys=True, indent=2),
        encoding="utf-8",
    )
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

    mine_parser = subparsers.add_parser("mine", help="mine scenarios")
    mine_parser.add_argument("--run", required=True)
    mine_parser.add_argument("--rules", required=True)
    mine_parser.add_argument("--out", required=True)
    mine_parser.add_argument("--scenario-set-id", default=None)
    mine_parser.add_argument("--created-at", default=None)
    mine_parser.set_defaults(func=_handle_mine)

    for name in ("eval", "compare"):
        subparser = subparsers.add_parser(name, help=f"{name} workflows")
        subparser.set_defaults(func=_handle_placeholder)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def _sanitize_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    safe = safe.strip("._-")
    return safe or "scset"


if __name__ == "__main__":
    raise SystemExit(main())
