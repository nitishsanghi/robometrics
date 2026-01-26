"""Scenario model for robometrics."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Scenario:
    scenario_id: str
    run_id: str
    t0: float
    t1: float
    intent: str
    tags: dict[str, str] = field(default_factory=dict)
    eval_profile: str | None = None

    def __post_init__(self) -> None:
        if self.t1 <= self.t0:
            raise ValueError("Scenario t1 must be greater than t0")

    def to_dict(self) -> dict[str, object]:
        ordered_tags = {key: self.tags[key] for key in sorted(self.tags)}
        return {
            "scenario_id": self.scenario_id,
            "run_id": self.run_id,
            "t0": float(self.t0),
            "t1": float(self.t1),
            "intent": self.intent,
            "tags": ordered_tags,
            "eval_profile": self.eval_profile,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "Scenario":
        tags = payload.get("tags", {})
        if not isinstance(tags, dict):
            raise ValueError("Scenario tags must be a dict")
        eval_profile = payload.get("eval_profile")
        if eval_profile is not None:
            eval_profile = str(eval_profile)
        return cls(
            scenario_id=str(payload["scenario_id"]),
            run_id=str(payload["run_id"]),
            t0=float(payload["t0"]),
            t1=float(payload["t1"]),
            intent=str(payload["intent"]),
            tags={str(k): str(v) for k, v in tags.items()},
            eval_profile=eval_profile,
        )
