# robometrics

[![CI](https://github.com/<ORG>/<REPO>/actions/workflows/ci.yml/badge.svg)](https://github.com/<ORG>/<REPO>/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

robometrics is a lightweight, scenario-based offline evaluation toolkit for robotics logs, designed to help teams compare model behavior across runs and environments before deploying changes to a robot.

## Features (Milestones 0-4)

- Canonical data model with JSON-serializable artifacts (Run, ScenarioSet, ScoreCard primitives).
- DemoLog format + adapter to ingest demo runs into reusable canonical run artifacts.
- Scenario mining from YAML rules (event windows + threshold-based triggers).
- Metrics engine + built-in metrics pack (task/motion/safety/efficiency/reliability).
- CLI workflows: `ingest` and `mine` with deterministic outputs and schema reporting.

## Reviewer Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
robometrics --help

# Generate demo logs and ingest them into canonical run artifacts
python examples/generate_demolog.py --out /tmp/robometrics-data --seed 0
robometrics ingest --adapter demolog --input /tmp/robometrics-data/baseline/run_000 --out /tmp/robometrics-runs
ls /tmp/robometrics-runs/run_000

# Mine scenarios from a run
robometrics mine --run /tmp/robometrics-runs/run_000 \
  --rules examples/configs/mining_rules.yaml \
  --out /tmp/robometrics-scenarios \
  --scenario-set-id demo
```

## Development

- Run tests: `pytest -q`
- Format code: `black .`
- Lint: `ruff check .`

## Metrics (optional)

See docs/metrics.md and examples/configs/metrics.yaml for available metrics.
