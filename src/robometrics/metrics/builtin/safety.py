"""Safety-related metrics."""

from __future__ import annotations

import math

from robometrics.metrics.base import MetricContext, metric
from robometrics.model.metric_result import MetricResult


@metric(
    name="safety.fallback_count",
    description="Count of safety.fallback events.",
)
def safety_fallback_count(ctx: MetricContext) -> MetricResult:
    count = sum(1 for event in ctx.events if event.name == "safety.fallback")
    return MetricResult(
        value=count,
        units=None,
        direction="lower",
        valid=True,
        notes=None,
    )


@metric(
    name="safety.estop_count",
    description="Count of safety.estop events.",
)
def safety_estop_count(ctx: MetricContext) -> MetricResult:
    count = sum(1 for event in ctx.events if event.name == "safety.estop")
    return MetricResult(
        value=count,
        units=None,
        direction="lower",
        valid=True,
        notes=None,
    )


@metric(
    name="safety.contact_count",
    description="Count of safety.contact events.",
)
def safety_contact_count(ctx: MetricContext) -> MetricResult:
    count = sum(1 for event in ctx.events if event.name == "safety.contact")
    return MetricResult(
        value=count,
        units=None,
        direction="lower",
        valid=True,
        notes=None,
    )


@metric(
    name="safety.speed_limit_violations",
    requires_streams=["state.twist2d"],
    description="Count of samples exceeding configured speed limit.",
)
def safety_speed_limit_violations(ctx: MetricContext) -> MetricResult:
    speed_limit = float(ctx.config.get("speed_limit_mps", 0.0))
    if speed_limit <= 0:
        return MetricResult(
            value=None,
            units=None,
            direction="lower",
            valid=False,
            notes="missing speed_limit_mps config",
        )

    stream = ctx.streams["state.twist2d"]
    vx = stream.data.get("vx")
    vy = stream.data.get("vy")
    if vx is None or vy is None:
        return MetricResult(
            value=None,
            units=None,
            direction="lower",
            valid=False,
            notes="missing vx/vy",
        )

    count = 0
    for x, y in zip(vx, vy, strict=True):
        speed = (float(x) ** 2 + float(y) ** 2) ** 0.5
        if speed > speed_limit:
            count += 1

    return MetricResult(
        value=count,
        units=None,
        direction="lower",
        valid=True,
        notes=None,
    )


@metric(
    name="safety.min_clearance",
    requires_streams=["obstacle"],
    description="Minimum obstacle clearance.",
)
def safety_min_clearance(ctx: MetricContext) -> MetricResult:
    stream = ctx.streams["obstacle"]
    distances = stream.data.get("min_distance")
    if not distances:
        return MetricResult(
            value=None,
            units="m",
            direction="higher",
            valid=False,
            notes="missing min_distance",
        )
    try:
        value = _min_valid_distance(distances)
    except ValueError:
        return MetricResult(
            value=None,
            units="m",
            direction="higher",
            valid=False,
            notes="no valid min_distance samples",
        )
    return MetricResult(
        value=value,
        units="m",
        direction="higher",
        valid=True,
        notes=None,
    )


def _min_valid_distance(distances: list[object]) -> float:
    values: list[float] = []
    for value in distances:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(numeric):
            continue
        values.append(numeric)
    if not values:
        raise ValueError("no valid min_distance samples")
    return min(values)
