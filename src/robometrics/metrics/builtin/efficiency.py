"""Efficiency-related metrics."""

from __future__ import annotations

from robometrics.metrics.base import MetricContext, metric
from robometrics.metrics.util import distance
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

    pose_x = pose.data.get("x") or []
    pose_y = pose.data.get("y") or []
    goal_x = goal.data.get("x") or []
    goal_y = goal.data.get("y") or []
    if not pose_x or not pose_y or not goal_x or not goal_y:
        return MetricResult(
            value=None,
            units=None,
            direction="higher",
            valid=False,
            notes="missing pose or goal coordinates",
        )

    path_length = _path_length(pose_x, pose_y)
    if path_length <= 0:
        return MetricResult(
            value=None,
            units=None,
            direction="higher",
            valid=False,
            notes="non-positive path length",
        )

    start_dist = distance(pose_x[0], pose_y[0], goal_x[0], goal_y[0])
    ratio = start_dist / path_length
    efficiency = max(0.0, min(1.0, ratio))
    if ratio > 1.0:
        return MetricResult(
            value=efficiency,
            units=None,
            direction="higher",
            valid=False,
            notes="path shorter than start distance: run ended before reaching goal",
        )
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
        speed = distance(vx[i], vy[i], 0.0, 0.0)
        if speed < threshold:
            stop_time += dt

    return MetricResult(
        value=stop_time / duration,
        units=None,
        direction="lower",
        valid=True,
        notes=None,
    )


def _path_length(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2 or len(ys) < 2:
        return 0.0
    length = 0.0
    for i in range(1, min(len(xs), len(ys))):
        length += distance(xs[i - 1], ys[i - 1], xs[i], ys[i])
    return length
