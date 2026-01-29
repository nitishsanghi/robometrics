"""DemoLog adapter for robometrics."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from robometrics.model.event import Event
from robometrics.model.run import Run
from robometrics.model.stream import Stream
from robometrics.validate.schema_report import SchemaReport


class DemoLogAdapter:
    REQUIRED_COLUMNS = {
        "t",
        "state.pose2d.x",
        "state.pose2d.y",
        "state.pose2d.yaw",
        "state.twist2d.vx",
        "state.twist2d.vy",
        "state.twist2d.wz",
        "command.twist2d.vx",
        "command.twist2d.vy",
        "command.twist2d.wz",
        "mission.goal2d.x",
        "mission.goal2d.y",
        "mission.goal2d.yaw",
        "mission.status",
    }
    OPTIONAL_COLUMNS = {
        "obstacle.min_distance",
    }

    @classmethod
    def read(cls, path: str | Path) -> tuple[Run, SchemaReport]:
        run_dir = Path(path)
        report = SchemaReport()

        meta = _load_meta(run_dir, report)
        run_id = str(meta.get("run_id", run_dir.name))

        run_df = _load_parquet(run_dir / "run.parquet", report, "run.parquet")
        events_df = _load_parquet(run_dir / "events.parquet", report, "events.parquet")

        streams: dict[str, Stream] = {}
        events: list[Event] = []

        if run_df is not None:
            missing = cls.REQUIRED_COLUMNS - set(run_df.columns)
            if missing:
                report.add_error(
                    f"run.parquet missing required columns: {sorted(missing)}"
                )
            else:
                t_values = _series_to_floats(run_df["t"], report, "t")
                if t_values is not None:
                    streams.update(
                        _build_streams(run_df, t_values, report, cls.OPTIONAL_COLUMNS)
                    )

                for col in cls.OPTIONAL_COLUMNS:
                    if col not in run_df.columns:
                        report.add_warning(
                            f"run.parquet missing optional column: {col}"
                        )

        if events_df is not None:
            events = _build_events(events_df, report)

        run = Run(run_id=run_id, meta=dict(meta), streams=streams, events=events)
        return run, report


def _load_meta(run_dir: Path, report: SchemaReport) -> dict[str, Any]:
    meta_path = run_dir / "meta.json"
    if not meta_path.exists():
        report.add_error("meta.json not found")
        return {}
    try:
        payload = json.loads(meta_path.read_text())
    except json.JSONDecodeError as exc:
        report.add_error(f"meta.json is invalid JSON: {exc}")
        return {}
    if not isinstance(payload, dict):
        report.add_error("meta.json must contain a JSON object")
        return {}
    return payload


def _load_parquet(path: Path, report: SchemaReport, label: str) -> pd.DataFrame | None:
    if not path.exists():
        report.add_error(f"{label} not found")
        return None
    try:
        return pd.read_parquet(path)
    except Exception as exc:  # noqa: BLE001
        report.add_error(f"{label} could not be read: {exc}")
        return None


def _series_to_floats(
    series: pd.Series, report: SchemaReport, label: str
) -> list[float] | None:
    try:
        values = [float(value) for value in series.tolist()]
    except Exception as exc:  # noqa: BLE001
        report.add_error(f"{label} column cannot be converted to float: {exc}")
        return None
    if any(not math.isfinite(value) for value in values):
        report.add_warning(f"{label} column contains non-finite values")
    return values


def _build_streams(
    run_df: pd.DataFrame,
    t_values: list[float],
    report: SchemaReport,
    optional_columns: set[str],
) -> dict[str, Stream]:
    streams: dict[str, Stream] = {}

    def build(name: str, columns: dict[str, str]) -> None:
        data: dict[str, list[object]] = {}
        for key, col in columns.items():
            if col not in run_df.columns:
                report.add_error(f"run.parquet missing required column: {col}")
                return
            data[key] = run_df[col].tolist()
            _warn_if_non_numeric(run_df[col], report, col)
        try:
            streams[name] = Stream(name=name, t=t_values, data=data)
        except ValueError as exc:
            report.add_error(str(exc))

    build(
        "state.pose2d",
        {"x": "state.pose2d.x", "y": "state.pose2d.y", "yaw": "state.pose2d.yaw"},
    )
    build(
        "state.twist2d",
        {"vx": "state.twist2d.vx", "vy": "state.twist2d.vy", "wz": "state.twist2d.wz"},
    )
    build(
        "command.twist2d",
        {
            "vx": "command.twist2d.vx",
            "vy": "command.twist2d.vy",
            "wz": "command.twist2d.wz",
        },
    )
    build(
        "mission.goal2d",
        {"x": "mission.goal2d.x", "y": "mission.goal2d.y", "yaw": "mission.goal2d.yaw"},
    )

    if "mission.status" in run_df.columns:
        streams["mission.status"] = Stream(
            name="mission.status",
            t=t_values,
            data={
                "status": [str(value) for value in run_df["mission.status"].tolist()]
            },
        )

    if "obstacle.min_distance" in run_df.columns:
        streams["obstacle"] = Stream(
            name="obstacle",
            t=t_values,
            data={"min_distance": run_df["obstacle.min_distance"].tolist()},
        )
        _warn_if_non_numeric(
            run_df["obstacle.min_distance"], report, "obstacle.min_distance"
        )

    return streams


def _warn_if_non_numeric(series: pd.Series, report: SchemaReport, label: str) -> None:
    if not pd.api.types.is_numeric_dtype(series):
        report.add_warning(f"{label} column is not numeric")
        return
    values = [float(value) for value in series.tolist()]
    if any(not math.isfinite(value) for value in values):
        report.add_warning(f"{label} column contains non-finite values")


def _build_events(events_df: pd.DataFrame, report: SchemaReport) -> list[Event]:
    required = {"t", "name"}
    missing = required - set(events_df.columns)
    if missing:
        report.add_error(f"events.parquet missing required columns: {sorted(missing)}")
        return []

    attrs_column = None
    if "attrs_json" in events_df.columns:
        attrs_column = "attrs_json"
    elif "attrs" in events_df.columns:
        attrs_column = "attrs"
    else:
        report.add_error("events.parquet missing attrs_json or attrs column")
        return []

    events: list[Event] = []
    for _, row in events_df.iterrows():
        attrs_value = row.get(attrs_column)
        attrs: dict[str, Any] = {}
        if attrs_value is not None and not pd.isna(attrs_value):
            if isinstance(attrs_value, dict):
                attrs = attrs_value
            else:
                try:
                    attrs = json.loads(str(attrs_value))
                except json.JSONDecodeError:
                    report.add_warning(
                        f"event at t={row['t']} attrs could not be parsed as JSON"
                    )
                    attrs = {}
        events.append(Event(t=float(row["t"]), name=str(row["name"]), attrs=attrs))
    return events
