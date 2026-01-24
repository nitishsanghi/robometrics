"""ScenarioSet artifact for robometrics."""

from __future__ import annotations

from dataclasses import dataclass, field

from robometrics.model.scenario import Scenario
from robometrics.model.spec import SPEC_VERSION


@dataclass
class ScenarioSet:
    spec_version: str
    scenario_set_id: str
    created_at: str
    runs: dict[str, dict[str, object]] = field(default_factory=dict)
    scenarios: list[Scenario] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.spec_version != SPEC_VERSION:
            raise ValueError(
                f"ScenarioSet spec_version {self.spec_version} != {SPEC_VERSION}"
            )

    def to_dict(self) -> dict[str, object]:
        ordered_runs = {key: self.runs[key] for key in sorted(self.runs)}
        return {
            "spec_version": self.spec_version,
            "scenario_set_id": self.scenario_set_id,
            "created_at": self.created_at,
            "runs": ordered_runs,
            "scenarios": [scenario.to_dict() for scenario in self.scenarios],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ScenarioSet":
        spec_version = str(payload["spec_version"])
        if spec_version != SPEC_VERSION:
            raise ValueError(
                f"ScenarioSet spec_version {spec_version} != {SPEC_VERSION}"
            )
        runs = payload.get("runs", {})
        scenarios = payload.get("scenarios", [])
        if not isinstance(runs, dict):
            raise ValueError("ScenarioSet runs must be a dict")
        if not isinstance(scenarios, list):
            raise ValueError("ScenarioSet scenarios must be a list")
        return cls(
            spec_version=spec_version,
            scenario_set_id=str(payload["scenario_set_id"]),
            created_at=str(payload["created_at"]),
            runs=dict(runs),
            scenarios=[Scenario.from_dict(item) for item in scenarios],
        )
