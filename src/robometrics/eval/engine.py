"""Metric evaluation engine."""

from __future__ import annotations

from robometrics.metrics.base import MetricContext, REGISTRY
from robometrics.model.event import Event
from robometrics.model.metric_result import MetricResult
from robometrics.model.run import Run
from robometrics.model.scenario import Scenario
from robometrics.model.stream import Stream


def run_metric(
    metric_name: str,
    run: Run,
    scenario: Scenario,
    *,
    config: dict[str, object] | None = None,
) -> MetricResult:
    spec = REGISTRY.get(metric_name)
    if spec is None or spec.fn is None:
        return MetricResult(
            value=None,
            units=None,
            direction="neutral",
            valid=False,
            notes=f"unknown metric: {metric_name}",
        )

    streams: dict[str, Stream] = {}
    for name in spec.requires_streams:
        stream = run.get_stream(name)
        if stream is None:
            return MetricResult(
                value=None,
                units=None,
                direction="neutral",
                valid=False,
                notes=f"missing required stream: {name}",
            )
        streams[name] = stream.slice(scenario.t0, scenario.t1, inclusive="left")

    for name in spec.optional_streams:
        stream = run.get_stream(name)
        if stream is not None:
            streams[name] = stream.slice(scenario.t0, scenario.t1, inclusive="left")

    events = _filter_events(run.events, scenario.t0, scenario.t1)
    for name in spec.requires_events:
        if not any(event.name == name for event in events):
            return MetricResult(
                value=None,
                units=None,
                direction="neutral",
                valid=False,
                notes=f"missing required event: {name}",
            )

    ctx = MetricContext(
        run=run,
        scenario=scenario,
        streams=streams,
        events=events,
        config=dict(config or {}),
    )

    try:
        return spec.fn(ctx)
    except Exception as exc:  # noqa: BLE001
        return MetricResult(
            value=None,
            units=None,
            direction="neutral",
            valid=False,
            notes=f"{type(exc).__name__}: {exc}",
        )


def run_metrics(
    metric_names: list[str],
    run: Run,
    scenario: Scenario,
    *,
    config: dict[str, dict[str, object]] | None = None,
) -> dict[str, MetricResult]:
    results: dict[str, MetricResult] = {}
    config = config or {}
    for name in metric_names:
        results[name] = run_metric(name, run, scenario, config=config.get(name))
    return results


def _filter_events(events: list[Event], t0: float, t1: float) -> list[Event]:
    return [event for event in events if t0 <= event.t < t1]
