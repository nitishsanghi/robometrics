import json

import pytest

from robometrics.model.metric_result import MetricResult
from robometrics.model.scenario import Scenario
from robometrics.model.scenarioset import ScenarioSet
from robometrics.model.scorecard import ScoreCard
from robometrics.model.spec import SPEC_VERSION


def test_scenarioset_roundtrip() -> None:
    scenarios = [
        Scenario(
            scenario_id="sc-1",
            run_id="run-1",
            t0=0.0,
            t1=1.0,
            intent="baseline",
            tags={"scene": "indoor"},
        ),
        Scenario(
            scenario_id="sc-2",
            run_id="run-1",
            t0=1.0,
            t1=2.0,
            intent="turn",
            tags={"scene": "outdoor"},
            eval_profile="default",
        ),
    ]
    scenario_set = ScenarioSet(
        spec_version=SPEC_VERSION,
        scenario_set_id="set-1",
        created_at="2026-01-22T00:00:00Z",
        runs={"run-1": {"path": "runs/run-1"}},
        scenarios=scenarios,
    )

    payload = json.loads(json.dumps(scenario_set.to_dict()))
    restored = ScenarioSet.from_dict(payload)

    assert restored.spec_version == scenario_set.spec_version
    assert restored.scenario_set_id == scenario_set.scenario_set_id
    assert restored.created_at == scenario_set.created_at
    assert list(restored.runs.keys()) == ["run-1"]
    assert len(restored.scenarios) == 2
    assert restored.scenarios[0].scenario_id == "sc-1"
    assert restored.scenarios[1].eval_profile == "default"


def test_scorecard_roundtrip() -> None:
    scenario = Scenario(
        scenario_id="sc-1",
        run_id="run-1",
        t0=0.0,
        t1=1.0,
        intent="baseline",
        tags={"scene": "indoor"},
    )
    scorecard = ScoreCard(
        spec_version=SPEC_VERSION,
        scorecard_id="card-1",
        run_id="run-1",
        scenario=scenario,
        provenance={"source": "unit-test"},
        metrics={
            "latency": MetricResult(
                value=1.2,
                units="s",
                direction="lower",
                valid=True,
                notes=None,
            ),
            "success": MetricResult(
                value=0.95,
                units=None,
                direction="higher",
                valid=True,
                notes="ok",
            ),
        },
        created_at="2026-01-22T00:00:00Z",
    )

    payload = json.loads(json.dumps(scorecard.to_dict()))
    restored = ScoreCard.from_dict(payload)

    assert restored.spec_version == scorecard.spec_version
    assert restored.scorecard_id == scorecard.scorecard_id
    assert restored.run_id == scorecard.run_id
    assert restored.scenario.scenario_id == "sc-1"
    assert set(restored.metrics.keys()) == {"latency", "success"}
    assert restored.metrics["latency"].direction == "lower"


def test_spec_version_mismatch_raises() -> None:
    scenario_set_payload = {
        "spec_version": "9.9.9",
        "scenario_set_id": "set-1",
        "created_at": "2026-01-22T00:00:00Z",
        "runs": {},
        "scenarios": [],
    }
    with pytest.raises(ValueError):
        ScenarioSet.from_dict(scenario_set_payload)

    scorecard_payload = {
        "spec_version": "9.9.9",
        "scorecard_id": "card-1",
        "run_id": "run-1",
        "scenario": {
            "scenario_id": "sc-1",
            "run_id": "run-1",
            "t0": 0.0,
            "t1": 1.0,
            "intent": "baseline",
            "tags": {},
            "eval_profile": None,
        },
        "provenance": {},
        "metrics": {},
        "created_at": "2026-01-22T00:00:00Z",
    }
    with pytest.raises(ValueError):
        ScoreCard.from_dict(scorecard_payload)
