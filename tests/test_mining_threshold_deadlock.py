from robometrics.mining.miner import mine_scenarios
from robometrics.mining.rules import Ruleset, RuleSpec, WindowSpec, ThresholdSpec
from robometrics.model.run import Run
from robometrics.model.stream import Stream


def test_mining_threshold_deadlock():
    t = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    vx = [0.0, 0.0, 0.5, 0.5, 0.5, 0.0, 0.0]
    vy = [0.0] * len(t)

    run = Run(
        run_id="run-1",
        streams={
            "command.twist2d": Stream(
                name="command.twist2d",
                t=t,
                data={"vx": vx, "vy": vy},
            ),
        },
    )

    rule = RuleSpec(
        rule_id="deadlock",
        intent="deadlock",
        tags={},
        window=WindowSpec(pre_s=1.0, post_s=1.0),
        threshold=ThresholdSpec(
            stream="command.twist2d",
            signal="linear_speed",
            op="gt",
            value=0.3,
            for_s=2.0,
        ),
    )
    ruleset = Ruleset(version="0.1", scenarios=[rule])

    scenario_set, report = mine_scenarios(
        run,
        ruleset,
        scenario_set_id="set-1",
        created_at="2026-01-22T00:00:00Z",
    )

    assert report.ok()
    assert len(scenario_set.scenarios) == 1
    scenario = scenario_set.scenarios[0]
    assert scenario.t0 == 1.0
    assert scenario.t1 == 5.0
    assert scenario.scenario_id.startswith("deadlock:")
