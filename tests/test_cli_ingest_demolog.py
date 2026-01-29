import subprocess
import sys


def test_cli_ingest_demolog(tmp_path):
    data_dir = tmp_path / "data"
    runs_dir = tmp_path / "runs"
    data_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            sys.executable,
            "examples/generate_demolog.py",
            "--out",
            str(data_dir),
            "--seed",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    run_dir = data_dir / "baseline" / "run_000"

    ingest = subprocess.run(
        [
            sys.executable,
            "-m",
            "robometrics",
            "ingest",
            "--adapter",
            "demolog",
            "--input",
            str(run_dir),
            "--out",
            str(runs_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert ingest.returncode == 0, ingest.stderr or ingest.stdout

    meta_path = runs_dir / "run_000" / "meta.json"
    assert meta_path.exists()
