"""Stream primitives for robometrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class Stream:
    name: str = ""
    t: list[float] = field(default_factory=list)
    data: dict[str, list[float | int | str | bool | None]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._validate_lengths()
        self._validate_monotonic()

    def _validate_lengths(self) -> None:
        expected = len(self.t)
        for key, values in self.data.items():
            if len(values) != expected:
                raise ValueError(
                    f"Stream column '{key}' length {len(values)} != {expected}"
                )

    def _validate_monotonic(self) -> None:
        for i in range(1, len(self.t)):
            if self.t[i] < self.t[i - 1]:
                raise ValueError("Stream time values must be non-decreasing")

    def slice(self, t0: float, t1: float, *, inclusive: str = "left") -> "Stream":
        if inclusive not in {"left", "both"}:
            raise ValueError("inclusive must be 'left' or 'both'")

        if inclusive == "left":
            indices = [i for i, ti in enumerate(self.t) if t0 <= ti < t1]
        else:
            indices = [i for i, ti in enumerate(self.t) if t0 <= ti <= t1]

        sliced_t = [self.t[i] for i in indices]
        sliced_data = {
            key: [values[i] for i in indices] for key, values in self.data.items()
        }
        return Stream(name=self.name, t=sliced_t, data=sliced_data)

    def to_dict(self) -> dict[str, object]:
        ordered_data = {key: self.data[key] for key in sorted(self.data)}
        return {
            "name": self.name,
            "t": list(self.t),
            "data": ordered_data,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "Stream":
        name = str(payload.get("name", ""))
        t = list(payload.get("t", []))
        data = payload.get("data", {})
        if not isinstance(data, dict):
            raise ValueError("Stream data must be a dict")
        typed_data: dict[str, list[float | int | str | bool | None]] = {}
        for key, values in data.items():
            if not isinstance(values, Iterable):
                raise ValueError(f"Stream data column '{key}' must be iterable")
            typed_data[str(key)] = list(values)
        return cls(name=name, t=[float(x) for x in t], data=typed_data)
