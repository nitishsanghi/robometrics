"""Metric result model for robometrics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MetricResult:
    value: object | None
    units: str | None
    direction: str
    valid: bool
    notes: str | None

    def __post_init__(self) -> None:
        if self.direction not in {"higher", "lower", "neutral"}:
            raise ValueError("MetricResult direction must be higher, lower, or neutral")

    def to_dict(self) -> dict[str, object]:
        return {
            "value": self.value,
            "units": self.units,
            "direction": self.direction,
            "valid": self.valid,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "MetricResult":
        direction = str(payload["direction"])
        units = str(payload["units"]) if payload.get("units") is not None else None
        notes = str(payload["notes"]) if payload.get("notes") is not None else None
        return cls(
            value=payload.get("value"),
            units=units,
            direction=direction,
            valid=bool(payload["valid"]),
            notes=notes,
        )
