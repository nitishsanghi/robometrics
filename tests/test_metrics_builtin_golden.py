import math

from robometrics.eval.engine import run_metric
from robometrics.model.event import Event
from robometrics.model.run import Run
from robometrics.model.scenario import Scenario
from robometrics.model.stream import Stream


def test_metrics_builtin_constant_velocity_jerk():
    t = [0.0, 1.0, 2.0, 3.0]
    stream = Stream(
        name="state.twist2d",
        t=t,
        data={"vx": [1.0, 1.0, 1.0, 1.0], "vy": [0.0, 0.0, 0.0, 0.0], "wz": [0.0, 0.0, 0.0, 0.0]},
    )
    run = Run(run_id="r1", streams={"state.twist2d": stream})
    scenario = Scenario(
        scenario_id="s1",
        run_id="r1",
        t0=0.0,
        t1=3.0,
        intent="test",
        tags={},
    )

    result_p95 = run_metric("motion.jerk_p95", run, scenario)
    result_p99 = run_metric("motion.jerk_p99", run, scenario)

    assert result_p95.valid is True
    assert result_p99.valid is True
    assert math.isclose(float(result_p95.value), 0.0, abs_tol=1e-9)
    assert math.isclose(float(result_p99.value), 0.0, abs_tol=1e-9)


def test_metrics_builtin_oscillation_score():
    t = [0.0, 0.5, 1.0, 1.5, 2.0]
    stream = Stream(
        name="command.twist2d",
        t=t,
        data={"vx": [1.0, -1.0, 1.0, -1.0, 1.0], "vy": [0.0] * 5, "wz": [0.0] * 5},
    )
    run = Run(run_id="r1", streams={"command.twist2d": stream})
    scenario = Scenario(
        scenario_id="s1",
        run_id="r1",
        t0=0.0,
        t1=2.0,
        intent="test",
        tags={},
    )

    result = run_metric("motion.oscillation_score", run, scenario)
    assert result.valid is True
    assert result.value is not None
    assert result.value > 0


def test_metrics_builtin_fallback_count():
    events = [
        Event(t=0.5, name="safety.fallback", attrs={}),
        Event(t=1.0, name="safety.fallback", attrs={}),
        Event(t=1.5, name="safety.fallback", attrs={}),
    ]
    run = Run(run_id="r1", events=events)
    scenario = Scenario(
        scenario_id="s1",
        run_id="r1",
        t0=0.0,
        t1=2.0,
        intent="test",
        tags={},
    )

    result = run_metric("safety.fallback_count", run, scenario)
    assert result.valid is True
    assert result.value == 3
