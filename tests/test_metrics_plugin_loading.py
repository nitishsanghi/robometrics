import textwrap

from robometrics.eval.engine import run_metric
from robometrics.metrics.base import REGISTRY
from robometrics.metrics.loader import load_plugins
from robometrics.model.metric_result import MetricResult
from robometrics.model.run import Run
from robometrics.model.scenario import Scenario


def test_metrics_plugin_loading(tmp_path):
    plugin_path = tmp_path / "plugin_metric.py"
    plugin_path.write_text(textwrap.dedent("""
            from robometrics.metrics.base import MetricContext, metric
            from robometrics.model.metric_result import MetricResult

            @metric(name="custom.constant_one")
            def custom_constant_one(ctx: MetricContext) -> MetricResult:
                return MetricResult(
                    value=1, units=None, direction="higher", valid=True, notes=None
                )
            """))

    load_plugins([str(plugin_path)])
    assert "custom.constant_one" in REGISTRY

    try:
        run = Run(run_id="r1")
        scenario = Scenario(
            scenario_id="s1",
            run_id="r1",
            t0=0.0,
            t1=1.0,
            intent="test",
            tags={},
        )
        result = run_metric("custom.constant_one", run, scenario)
        assert isinstance(result, MetricResult)
        assert result.valid is True
        assert result.value == 1
    finally:
        REGISTRY.pop("custom.constant_one", None)
