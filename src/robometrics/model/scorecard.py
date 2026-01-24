"""ScoreCard artifact for robometrics."""

from __future__ import annotations

from dataclasses import dataclass, field

from robometrics.model.metric_result import MetricResult
from robometrics.model.scenario import Scenario
from robometrics.model.spec import SPEC_VERSION


@dataclass
class ScoreCard:
    spec_version: str
    scorecard_id: str
    run_id: str
    scenario: Scenario
    provenance: dict[str, object] = field(default_factory=dict)
    metrics: dict[str, MetricResult] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.spec_version != SPEC_VERSION:
            raise ValueError(
                f"ScoreCard spec_version {self.spec_version} != {SPEC_VERSION}"
            )

    def to_dict(self) -> dict[str, object]:
        ordered_metrics = {
            key: self.metrics[key].to_dict() for key in sorted(self.metrics)
        }
        ordered_provenance = {
            key: self.provenance[key] for key in sorted(self.provenance)
        }
        return {
            "spec_version": self.spec_version,
            "scorecard_id": self.scorecard_id,
            "run_id": self.run_id,
            "scenario": self.scenario.to_dict(),
            "provenance": ordered_provenance,
            "metrics": ordered_metrics,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ScoreCard":
        spec_version = str(payload["spec_version"])
        if spec_version != SPEC_VERSION:
            raise ValueError(f"ScoreCard spec_version {spec_version} != {SPEC_VERSION}")
        metrics = payload.get("metrics", {})
        provenance = payload.get("provenance", {})
        if not isinstance(metrics, dict):
            raise ValueError("ScoreCard metrics must be a dict")
        if not isinstance(provenance, dict):
            raise ValueError("ScoreCard provenance must be a dict")
        return cls(
            spec_version=spec_version,
            scorecard_id=str(payload["scorecard_id"]),
            run_id=str(payload["run_id"]),
            scenario=Scenario.from_dict(payload["scenario"]),
            provenance=dict(provenance),
            metrics={
                str(key): MetricResult.from_dict(value)
                for key, value in metrics.items()
            },
            created_at=str(payload["created_at"]),
        )
