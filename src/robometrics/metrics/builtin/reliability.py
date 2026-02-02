"""Reliability-related metrics."""

from __future__ import annotations

from robometrics.metrics.base import MetricContext, metric
from robometrics.model.metric_result import MetricResult


@metric(
    name="sys.deadline_miss_count",
    description="Count of sys.deadline_miss events.",
)
def sys_deadline_miss_count(ctx: MetricContext) -> MetricResult:
    count = sum(1 for event in ctx.events if event.name == "sys.deadline_miss")
    return MetricResult(
        value=count,
        units=None,
        direction="lower",
        valid=True,
        notes=None,
    )


@metric(
    name="sys.sensor_degraded_count",
    description="Count of sys.sensor_degraded events.",
)
def sys_sensor_degraded_count(ctx: MetricContext) -> MetricResult:
    count = sum(1 for event in ctx.events if event.name == "sys.sensor_degraded")
    return MetricResult(
        value=count,
        units=None,
        direction="lower",
        valid=True,
        notes=None,
    )
