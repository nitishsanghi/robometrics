# Contributing to robometrics

Thanks for your interest in contributing! We welcome issues, feature requests, and pull requests.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Style and linting

- Format: `black .`
- Lint: `ruff check .`

## Tests

```bash
pytest -q
```

## Issues and PRs

- Open an issue to discuss larger changes.
- Keep PRs focused and include tests when possible.
- Ensure CI is green before requesting review.

## Code of Conduct

This project follows the Contributor Covenant. By participating, you agree to abide by the Code of Conduct in `CODE_OF_CONDUCT.md`.
