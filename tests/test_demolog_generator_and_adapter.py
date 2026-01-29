import subprocess
import sys

from robometrics.adapters.demolog import DemoLogAdapter


def test_demolog_generator_and_adapter(tmp_path):
    out_dir = tmp_path / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    baseline_dir = out_dir / "baseline"
    candidate_dir = out_dir / "candidate"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            sys.executable,
            "examples/generate_demolog.py",
            "--out",
            str(out_dir),
            "--seed",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    run, report = DemoLogAdapter.read(baseline_dir / "run_000")
    assert report.ok()
    assert "state.pose2d" in run.streams
    assert "state.twist2d" in run.streams
    assert "command.twist2d" in run.streams
    assert "mission.goal2d" in run.streams
    assert "mission.status" in run.streams

    run_candidate, report_candidate = DemoLogAdapter.read(candidate_dir / "run_000")
    assert report_candidate.ok()
    event_names = {event.name for event in run_candidate.events}
    assert "safety.fallback" in event_names or "sys.deadline_miss" in event_names
