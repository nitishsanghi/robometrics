"""Plugin loader for external metrics."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_plugins(paths: list[str]) -> None:
    """Load metric plugins from file paths."""
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            raise FileNotFoundError(f"Plugin not found: {path}")
        module_name = f"robometrics_plugin_{path.stem}_{abs(hash(path))}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to load plugin: {path}")
        module = importlib.util.module_from_spec(spec)
        try:
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001
            raise ImportError(f"Failed to import plugin {path}: {exc}") from exc
