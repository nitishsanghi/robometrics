import json

import pytest

from robometrics.model.scenario import Scenario


def test_scenario_roundtrip_and_ordering() -> None:
    scenario = Scenario(
        scenario_id="sc-1",
        run_id="run-1",
        t0=0.0,
        t1=1.0,
        intent="baseline",
        tags={"z": "last", "a": "first"},
        eval_profile="default",
    )

    payload = scenario.to_dict()
    restored = Scenario.from_dict(json.loads(json.dumps(payload)))

    assert list(payload["tags"].keys()) == ["a", "z"]
    assert restored.to_dict() == payload


def test_scenario_eval_profile_optional() -> None:
    scenario = Scenario(
        scenario_id="sc-2",
        run_id="run-2",
        t0=1.0,
        t1=2.0,
        intent="turn",
        tags={},
    )

    payload = scenario.to_dict()

    assert payload["eval_profile"] is None


def test_scenario_time_bounds_validation() -> None:
    with pytest.raises(ValueError):
        Scenario(
            scenario_id="sc-3",
            run_id="run-3",
            t0=1.0,
            t1=1.0,
            intent="bad",
            tags={},
        )
