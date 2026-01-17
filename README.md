# robometrics

[![CI](https://github.com/<ORG>/<REPO>/actions/workflows/ci.yml/badge.svg)](https://github.com/<ORG>/<REPO>/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

robometrics is a lightweight, scenario-based offline evaluation toolkit for robotics logs, designed to help teams compare model behavior across runs and environments before deploying changes to a robot.

## Reviewer Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
robometrics --help
```

## Development

- Run tests: `pytest -q`
- Format code: `black .`
- Lint: `ruff check .`
