"""Event primitives for robometrics."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Event:
    t: float
    name: str
    attrs: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        ordered_attrs = {key: self.attrs[key] for key in sorted(self.attrs)}
        return {
            "t": float(self.t),
            "name": self.name,
            "attrs": ordered_attrs,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "Event":
        t = float(payload["t"])
        name = str(payload["name"])
        attrs = payload.get("attrs", {})
        if not isinstance(attrs, dict):
            raise ValueError("Event attrs must be a dict")
        return cls(t=t, name=name, attrs=dict(attrs))
