# Metrics

This document describes the built-in metrics in Milestone 4 and their formulas.
All metrics operate on a `(Run, Scenario)` window and return a `MetricResult`.
If required inputs are missing, metrics return `valid=False` with a short note.

## Conventions

- Units are listed per metric; `units: null` means unitless.
- Directions are one of: `higher`, `lower`, `neutral`.
- Stream names are canonical (e.g., `state.twist2d`).
- Event counts are within the scenario window.

## Task metrics

### task.success
- Requires: `mission.status`
- Definition: `True` if final status in window is `succeeded`.
- Units: null
- Direction: higher

### task.time_to_goal
- Requires: `mission.status`
- Definition: seconds from first `active` to first `succeeded` (or window end).
- Units: s
- Direction: lower

### task.progress_rate
- Requires: `state.pose2d`, `mission.goal2d`
- Definition: `(start distance to goal - end distance) / duration`.
- Units: m/s
- Direction: higher

### task.recovery_count
- Requires: events named `task.recovery`
- Definition: count of recovery events in the window.
- Units: null
- Direction: lower

## Motion metrics

### motion.jerk_p95
- Requires: `state.twist2d` with `vx`, `vy`
- Definition: 95th percentile of linear jerk magnitude computed from velocity.
- Units: m/s^3
- Direction: lower

### motion.jerk_p99
- Requires: `state.twist2d` with `vx`, `vy`
- Definition: 99th percentile of linear jerk magnitude computed from velocity.
- Units: m/s^3
- Direction: lower

### motion.angular_jerk_p95
- Requires: `state.twist2d` with `wz`
- Definition: 95th percentile of angular jerk magnitude from `wz`.
- Units: rad/s^3
- Direction: lower

### motion.oscillation_score
- Requires: `command.twist2d` with `vx`
- Definition: sign-change rate of `vx` per second.
- Units: 1/s
- Direction: lower

## Safety metrics

### safety.fallback_count
- Requires: events named `safety.fallback`
- Definition: count of fallback events.
- Units: null
- Direction: lower

### safety.estop_count
- Requires: events named `safety.estop`
- Definition: count of estop events.
- Units: null
- Direction: lower

### safety.contact_count
- Requires: events named `safety.contact`
- Definition: count of contact events.
- Units: null
- Direction: lower

### safety.speed_limit_violations
- Requires: `state.twist2d` with `vx`, `vy`
- Config: `speed_limit_mps`
- Definition: number of samples where linear speed exceeds the limit.
- Units: null
- Direction: lower

### safety.min_clearance
- Requires: `obstacle` with `min_distance`
- Definition: minimum value of `min_distance`.
- Units: m
- Direction: higher

## Efficiency metrics

### eff.path_efficiency
- Requires: `state.pose2d`, `mission.goal2d`
- Definition: straight-line distance to goal divided by path length, clipped to [0,1].
- Units: null
- Direction: higher

### eff.stop_time_ratio
- Requires: `state.twist2d` with `vx`, `vy`
- Config: `stop_speed_mps` (default 0.05)
- Definition: fraction of time where linear speed < threshold.
- Units: null
- Direction: lower

## Reliability metrics

### sys.deadline_miss_count
- Requires: events named `sys.deadline_miss`
- Definition: count of deadline miss events.
- Units: null
- Direction: lower

### sys.sensor_degraded_count
- Requires: events named `sys.sensor_degraded`
- Definition: count of sensor degraded events.
- Units: null
- Direction: lower
