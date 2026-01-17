import subprocess
import sys


def test_cli_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "robometrics", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "robometrics" in result.stdout.lower()


def test_cli_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "robometrics", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "robometrics 0.1.0"
