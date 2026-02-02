from robometrics.eval.engine import run_metric
from robometrics.model.run import Run
from robometrics.model.scenario import Scenario


def test_metrics_missing_inputs():
    run = Run(run_id="r1")
    scenario = Scenario(
        scenario_id="s1",
        run_id="r1",
        t0=0.0,
        t1=1.0,
        intent="test",
        tags={},
    )
    result = run_metric("motion.jerk_p95", run, scenario)
    assert result.valid is False
    assert result.value is None
    assert result.notes is not None
    assert "missing required stream" in result.notes
