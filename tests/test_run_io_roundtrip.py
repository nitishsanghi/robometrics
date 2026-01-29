import json

from robometrics.io.run_io import RunReader, RunWriter
from robometrics.model.event import Event
from robometrics.model.run import Run
from robometrics.model.stream import Stream
from robometrics.validate.schema_report import SchemaReport


def test_run_io_roundtrip(tmp_path):
    run = Run(
        run_id="run-1",
        meta={"operator": "tester"},
        streams={
            "state": Stream(name="state", t=[0.0, 1.0], data={"x": [1.0, 2.0]}),
            "command": Stream(name="command", t=[0.0, 1.0], data={"vx": [0.1, 0.2]}),
        },
        events=[Event(t=0.5, name="start", attrs={"ok": True})],
    )
    report = SchemaReport(warnings=["note"])

    out_dir = RunWriter.write(run, report, tmp_path)
    restored, restored_report = RunReader.read(out_dir)

    assert restored.run_id == run.run_id
    assert set(restored.streams.keys()) == set(run.streams.keys())
    assert len(restored.events) == len(run.events)
    assert restored_report.warnings == report.warnings
    assert restored.streams["state"].data["x"] == run.streams["state"].data["x"]
    assert restored.events[0].attrs == run.events[0].attrs

    meta_payload = json.loads((out_dir / "meta.json").read_text())
    assert meta_payload["run_id"] == run.run_id
