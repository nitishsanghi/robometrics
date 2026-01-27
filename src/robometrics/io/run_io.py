"""Canonical run artifact IO helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from robometrics.io.parquet import read_parquet, write_parquet
from robometrics.model.event import Event
from robometrics.model.run import Run
from robometrics.model.spec import SPEC_VERSION
from robometrics.model.stream import Stream
from robometrics.validate.schema_report import SchemaReport


class RunWriter:
    @staticmethod
    def write(run: Run, report: SchemaReport, out_dir: Path) -> Path:
        run_dir = out_dir / run.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        meta_payload = {
            "run_id": run.run_id,
            "spec_version": SPEC_VERSION,
            "meta": Run._sort_structure(run.meta),
        }
        _write_json(run_dir / "meta.json", meta_payload)
        _write_json(run_dir / "schema_report.json", report.to_dict())

        streams_df = _streams_to_frame(run)
        write_parquet(streams_df, run_dir / "streams.parquet")

        events_df = _events_to_frame(run.events)
        write_parquet(events_df, run_dir / "events.parquet")

        return run_dir


class RunReader:
    @staticmethod
    def read(run_dir: Path) -> tuple[Run, SchemaReport]:
        meta_payload = _read_json(run_dir / "meta.json")
        run_id = str(meta_payload.get("run_id", ""))
        meta = meta_payload.get("meta", {})
        if not isinstance(meta, dict):
            raise ValueError("Run meta must be a dict")

        streams_df = read_parquet(run_dir / "streams.parquet")
        events_df = read_parquet(run_dir / "events.parquet")

        streams = _frame_to_streams(streams_df)
        events = _frame_to_events(events_df)

        report_payload = _read_json(run_dir / "schema_report.json")
        report = SchemaReport.from_dict(report_payload)

        return (
            Run(run_id=run_id, meta=dict(meta), streams=streams, events=events),
            report,
        )


def _streams_to_frame(run: Run) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for name in sorted(run.streams):
        stream = run.streams[name]
        for idx, t_value in enumerate(stream.t):
            row = {
                "stream": name,
                "t": float(t_value),
                "data_json": json.dumps(
                    {key: stream.data[key][idx] for key in sorted(stream.data)},
                    sort_keys=True,
                ),
            }
            rows.append(row)
    return pd.DataFrame(rows, columns=["stream", "t", "data_json"])


def _frame_to_streams(frame: pd.DataFrame) -> dict[str, Stream]:
    streams: dict[str, Stream] = {}
    if frame.empty:
        return streams

    required = {"stream", "t", "data_json"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"streams.parquet missing columns: {sorted(missing)}")

    for stream_name, group in frame.groupby("stream", sort=False):
        t_values = [float(value) for value in group["t"].tolist()]
        data_items = [json.loads(item) for item in group["data_json"].tolist()]
        data: dict[str, list[object]] = {}
        for item in data_items:
            for key, value in item.items():
                data.setdefault(str(key), []).append(value)
        streams[str(stream_name)] = Stream(
            name=str(stream_name),
            t=t_values,
            data=data,
        )
    return streams


def _events_to_frame(events: list[Event]) -> pd.DataFrame:
    rows = [
        {
            "t": float(event.t),
            "name": event.name,
            "attrs_json": json.dumps(event.attrs, sort_keys=True),
        }
        for event in events
    ]
    return pd.DataFrame(rows, columns=["t", "name", "attrs_json"])


def _frame_to_events(frame: pd.DataFrame) -> list[Event]:
    if frame.empty:
        return []

    required = {"t", "name", "attrs_json"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"events.parquet missing columns: {sorted(missing)}")

    events: list[Event] = []
    for _, row in frame.iterrows():
        attrs = json.loads(row["attrs_json"]) if row["attrs_json"] else {}
        events.append(Event(t=float(row["t"]), name=str(row["name"]), attrs=attrs))
    return events


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2))


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())
