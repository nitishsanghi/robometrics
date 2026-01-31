import json
import subprocess
import sys

from robometrics.io.run_io import RunWriter
from robometrics.model.event import Event
from robometrics.model.run import Run
from robometrics.model.stream import Stream
from robometrics.validate.schema_report import SchemaReport


def test_cli_mine(tmp_path):
    run = Run(
        run_id="run-1",
        streams={
            "command.twist2d": Stream(
                name="command.twist2d",
                t=[0.0, 1.0, 2.0, 3.0],
                data={"vx": [0.0, 0.5, 0.5, 0.0], "vy": [0.0, 0.0, 0.0, 0.0]},
            )
        },
        events=[Event(t=1.5, name="safety.fallback", attrs={})],
    )
    report = SchemaReport()

    run_dir = RunWriter.write(run, report, tmp_path / "runs")

    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text(
        """version: '0.1'\nscenarios:\n  - id: fallback\n    intent: fallback_event\n    window:\n      pre_s: 1.0\n      post_s: 1.0\n    event:\n      name: safety.fallback\n"""
    )

    out_dir = tmp_path / "scenarios"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "robometrics",
            "mine",
            "--run",
            str(run_dir),
            "--rules",
            str(rules_path),
            "--out",
            str(out_dir),
            "--scenario-set-id",
            "testset",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    output_path = out_dir / "testset.scset.json"
    assert output_path.exists()
    payload = json.loads(output_path.read_text())
    assert "spec_version" in payload
    assert "scenarios" in payload
