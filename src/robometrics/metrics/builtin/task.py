"""Task-related metrics."""

from __future__ import annotations

from robometrics.metrics.base import MetricContext, metric
from robometrics.metrics.util import distance
from robometrics.model.metric_result import MetricResult


@metric(
    name="task.success",
    requires_streams=["mission.status"],
    description="Whether the mission status ends in succeeded.",
)
def task_success(ctx: MetricContext) -> MetricResult:
    stream = ctx.streams["mission.status"]
    statuses = stream.data.get("status", [])
    if not statuses:
        return MetricResult(
            value=None,
            units=None,
            direction="higher",
            valid=False,
            notes="missing status samples",
        )
    return MetricResult(
        value=str(statuses[-1]) == "succeeded",
        units=None,
        direction="higher",
        valid=True,
        notes=None,
    )


@metric(
    name="task.time_to_goal",
    requires_streams=["mission.status"],
    description="Seconds from first active to first succeeded.",
)
def task_time_to_goal(ctx: MetricContext) -> MetricResult:
    stream = ctx.streams["mission.status"]
    times = stream.t
    statuses = stream.data.get("status", [])
    if not times or not statuses:
        return MetricResult(
            value=None,
            units="s",
            direction="lower",
            valid=False,
            notes="missing status samples",
        )

    t_active = None
    for t, status in zip(times, statuses, strict=True):
        if str(status) == "active":
            t_active = float(t)
            break

    t_succeeded = None
    for t, status in zip(times, statuses, strict=True):
        if str(status) == "succeeded":
            t_succeeded = float(t)
            break

    if t_active is None:
        t_active = ctx.scenario.t0
    if t_succeeded is None:
        t_succeeded = ctx.scenario.t1

    return MetricResult(
        value=max(0.0, t_succeeded - t_active),
        units="s",
        direction="lower",
        valid=True,
        notes=None,
    )


@metric(
    name="task.progress_rate",
    requires_streams=["state.pose2d", "mission.goal2d"],
    description="(start distance - end distance) / duration.",
)
def task_progress_rate(ctx: MetricContext) -> MetricResult:
    state = ctx.streams["state.pose2d"]
    goal = ctx.streams["mission.goal2d"]
    if not state.t or not goal.t:
        return MetricResult(
            value=None,
            units="m/s",
            direction="higher",
            valid=False,
            notes="missing pose or goal samples",
        )
    state_x = state.data.get("x") or []
    state_y = state.data.get("y") or []
    goal_x = goal.data.get("x") or []
    goal_y = goal.data.get("y") or []
    if not state_x or not state_y or not goal_x or not goal_y:
        return MetricResult(
            value=None,
            units="m/s",
            direction="higher",
            valid=False,
            notes="missing pose or goal coordinates",
        )
    duration = state.t[-1] - state.t[0]
    if duration <= 0:
        return MetricResult(
            value=None,
            units="m/s",
            direction="higher",
            valid=False,
            notes="non-positive duration",
        )

    start_dist = distance(state_x[0], state_y[0], goal_x[0], goal_y[0])
    end_dist = distance(state_x[-1], state_y[-1], goal_x[-1], goal_y[-1])

    return MetricResult(
        value=(start_dist - end_dist) / duration,
        units="m/s",
        direction="higher",
        valid=True,
        notes=None,
    )


@metric(
    name="task.recovery_count",
    description="Count of task.recovery events.",
)
def task_recovery_count(ctx: MetricContext) -> MetricResult:
    count = sum(1 for event in ctx.events if event.name == "task.recovery")
    return MetricResult(
        value=count,
        units=None,
        direction="lower",
        valid=True,
        notes=None,
    )
