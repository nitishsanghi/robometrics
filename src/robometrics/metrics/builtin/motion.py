"""Motion-related metrics."""

from __future__ import annotations

import math

from robometrics.metrics.base import MetricContext, metric
from robometrics.model.metric_result import MetricResult


@metric(
    name="motion.jerk_p95",
    requires_streams=["state.twist2d"],
    description="95th percentile of linear jerk magnitude from vx/vy.",
)
def motion_jerk_p95(ctx: MetricContext) -> MetricResult:
    return _linear_jerk_percentile(ctx, 95.0)


@metric(
    name="motion.jerk_p99",
    requires_streams=["state.twist2d"],
    description="99th percentile of linear jerk magnitude from vx/vy.",
)
def motion_jerk_p99(ctx: MetricContext) -> MetricResult:
    return _linear_jerk_percentile(ctx, 99.0)


@metric(
    name="motion.angular_jerk_p95",
    requires_streams=["state.twist2d"],
    description="95th percentile of angular jerk magnitude from wz.",
)
def motion_angular_jerk_p95(ctx: MetricContext) -> MetricResult:
    stream = ctx.streams["state.twist2d"]
    wz = stream.data.get("wz")
    if wz is None:
        return MetricResult(
            value=None,
            units="rad/s^3",
            direction="lower",
            valid=False,
            notes="missing wz",
        )
    jerks = _scalar_jerk(stream.t, [float(value) for value in wz])
    if not jerks:
        return MetricResult(
            value=None,
            units="rad/s^3",
            direction="lower",
            valid=False,
            notes="insufficient samples",
        )
    return MetricResult(
        value=_percentile(jerks, 95.0),
        units="rad/s^3",
        direction="lower",
        valid=True,
        notes=None,
    )


@metric(
    name="motion.oscillation_score",
    requires_streams=["command.twist2d"],
    description="Sign-change rate of command.vx per second.",
)
def motion_oscillation_score(ctx: MetricContext) -> MetricResult:
    stream = ctx.streams["command.twist2d"]
    vx = stream.data.get("vx")
    if vx is None or len(stream.t) < 2:
        return MetricResult(
            value=None,
            units="1/s",
            direction="lower",
            valid=False,
            notes="insufficient samples",
        )
    duration = stream.t[-1] - stream.t[0]
    if duration <= 0:
        return MetricResult(
            value=None,
            units="1/s",
            direction="lower",
            valid=False,
            notes="non-positive duration",
        )
    changes = _sign_changes([float(value) for value in vx])
    return MetricResult(
        value=changes / duration,
        units="1/s",
        direction="lower",
        valid=True,
        notes=None,
    )


def _linear_jerk_percentile(ctx: MetricContext, percentile: float) -> MetricResult:
    stream = ctx.streams["state.twist2d"]
    vx = stream.data.get("vx")
    vy = stream.data.get("vy")
    if vx is None or vy is None:
        return MetricResult(
            value=None,
            units="m/s^3",
            direction="lower",
            valid=False,
            notes="missing vx/vy",
        )
    jerks = _vector_jerk(
        stream.t, [float(value) for value in vx], [float(value) for value in vy]
    )
    if not jerks:
        return MetricResult(
            value=None,
            units="m/s^3",
            direction="lower",
            valid=False,
            notes="insufficient samples",
        )
    return MetricResult(
        value=_percentile(jerks, percentile),
        units="m/s^3",
        direction="lower",
        valid=True,
        notes=None,
    )


def _vector_jerk(times: list[float], vx: list[float], vy: list[float]) -> list[float]:
    accelerations: list[tuple[float, float, float]] = []
    for i in range(1, len(times)):
        dt = times[i] - times[i - 1]
        if dt <= 0:
            continue
        ax = (vx[i] - vx[i - 1]) / dt
        ay = (vy[i] - vy[i - 1]) / dt
        accelerations.append((times[i], ax, ay))

    jerks: list[float] = []
    for i in range(1, len(accelerations)):
        t, ax, ay = accelerations[i]
        _, prev_ax, prev_ay = accelerations[i - 1]
        dt = t - accelerations[i - 1][0]
        if dt <= 0:
            continue
        jx = (ax - prev_ax) / dt
        jy = (ay - prev_ay) / dt
        jerks.append(math.hypot(jx, jy))

    return jerks


def _scalar_jerk(times: list[float], values: list[float]) -> list[float]:
    accelerations: list[tuple[float, float]] = []
    for i in range(1, len(times)):
        dt = times[i] - times[i - 1]
        if dt <= 0:
            continue
        accel = (values[i] - values[i - 1]) / dt
        accelerations.append((times[i], accel))

    jerks: list[float] = []
    for i in range(1, len(accelerations)):
        t, accel = accelerations[i]
        prev_t, prev_accel = accelerations[i - 1]
        dt = t - prev_t
        if dt <= 0:
            continue
        jerks.append((accel - prev_accel) / dt)
    return [abs(value) for value in jerks]


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = int(math.ceil((percentile / 100.0) * len(ordered))) - 1
    rank = max(0, min(rank, len(ordered) - 1))
    return float(ordered[rank])


def _sign_changes(values: list[float]) -> int:
    last_sign = 0
    changes = 0
    for value in values:
        sign = 0
        if value > 0:
            sign = 1
        elif value < 0:
            sign = -1
        if sign == 0:
            continue
        if last_sign != 0 and sign != last_sign:
            changes += 1
        last_sign = sign
    return changes
