from robometrics.mining.miner import mine_scenarios
from robometrics.mining.rules import Ruleset, RuleSpec, WindowSpec, EventSpec
from robometrics.model.event import Event
from robometrics.model.run import Run
from robometrics.model.stream import Stream


def test_mining_event_rule_windows():
    run = Run(
        run_id="run-1",
        streams={
            "clock": Stream(name="clock", t=[0.0, 5.0, 10.0], data={"x": [0, 1, 2]}),
        },
        events=[
            Event(t=2.0, name="safety.fallback", attrs={}),
            Event(t=8.0, name="safety.fallback", attrs={}),
        ],
    )

    rule = RuleSpec(
        rule_id="fallback",
        intent="fallback_event",
        tags={"source": "test"},
        window=WindowSpec(pre_s=1.0, post_s=2.0),
        event=EventSpec(name="safety.fallback"),
    )
    ruleset = Ruleset(version="0.1", scenarios=[rule])

    scenario_set, report = mine_scenarios(
        run,
        ruleset,
        scenario_set_id="set-1",
        created_at="2026-01-22T00:00:00Z",
    )

    assert report.ok()
    assert len(scenario_set.scenarios) == 2
    assert scenario_set.scenarios[0].t0 == 1.0
    assert scenario_set.scenarios[0].t1 == 4.0
    assert scenario_set.scenarios[1].t0 == 7.0
    assert scenario_set.scenarios[1].t1 == 10.0
    assert scenario_set.scenarios[0].tags["rule_id"] == "fallback"
