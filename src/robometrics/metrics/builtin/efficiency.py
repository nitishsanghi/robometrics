"""Efficiency-related metrics."""

from __future__ import annotations

import math

from robometrics.metrics.base import MetricContext, metric
from robometrics.model.metric_result import MetricResult


@metric(
    name="eff.path_efficiency",
    requires_streams=["state.pose2d", "mission.goal2d"],
    description="Straight-line distance to goal divided by path length.",
)
def eff_path_efficiency(ctx: MetricContext) -> MetricResult:
    pose = ctx.streams["state.pose2d"]
    goal = ctx.streams["mission.goal2d"]
    if len(pose.t) < 2:
        return MetricResult(
            value=None,
            units=None,
            direction="higher",
            valid=False,
            notes="insufficient pose samples",
        )

    path_length = _path_length(pose.data.get("x", []), pose.data.get("y", []))
    if path_length <= 0:
        return MetricResult(
            value=None,
            units=None,
            direction="higher",
            valid=False,
            notes="non-positive path length",
        )

    start_dist = _distance(
        pose.data.get("x", [0.0])[0],
        pose.data.get("y", [0.0])[0],
        goal.data.get("x", [0.0])[0],
        goal.data.get("y", [0.0])[0],
    )
    efficiency = max(0.0, min(1.0, start_dist / path_length))
    return MetricResult(
        value=efficiency,
        units=None,
        direction="higher",
        valid=True,
        notes=None,
    )


@metric(
    name="eff.stop_time_ratio",
    requires_streams=["state.twist2d"],
    description="Ratio of time with linear_speed < stop_speed_mps.",
)
def eff_stop_time_ratio(ctx: MetricContext) -> MetricResult:
    threshold = float(ctx.config.get("stop_speed_mps", 0.05))
    stream = ctx.streams["state.twist2d"]
    vx = stream.data.get("vx")
    vy = stream.data.get("vy")
    if vx is None or vy is None or len(stream.t) < 2:
        return MetricResult(
            value=None,
            units=None,
            direction="lower",
            valid=False,
            notes="insufficient samples",
        )

    duration = stream.t[-1] - stream.t[0]
    if duration <= 0:
        return MetricResult(
            value=None,
            units=None,
            direction="lower",
            valid=False,
            notes="non-positive duration",
        )

    stop_time = 0.0
    for i in range(1, len(stream.t)):
        dt = stream.t[i] - stream.t[i - 1]
        if dt <= 0:
            continue
        speed = math.hypot(float(vx[i]), float(vy[i]))
        if speed < threshold:
            stop_time += dt

    return MetricResult(
        value=stop_time / duration,
        units=None,
        direction="lower",
        valid=True,
        notes=None,
    )


def _distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(float(x2) - float(x1), float(y2) - float(y1))


def _path_length(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2 or len(ys) < 2:
        return 0.0
    length = 0.0
    for i in range(1, min(len(xs), len(ys))):
        length += _distance(xs[i - 1], ys[i - 1], xs[i], ys[i])
    return length
