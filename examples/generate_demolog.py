"""Generate a deterministic DemoLog dataset."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

import pandas as pd

SPEC_VERSION = "0.1.0"


def _build_run_rows(seed: int, n: int, aggressive: bool) -> dict[str, list[object]]:
    if n <= 0:
        raise ValueError("n must be greater than 0")
    rng = random.Random(seed)
    t = [i * 0.1 for i in range(n)]

    def noise(scale: float) -> float:
        return (rng.random() - 0.5) * 2.0 * scale

    pose_x = []
    pose_y = []
    pose_yaw = []
    twist_vx = []
    twist_vy = []
    twist_wz = []

    cmd_vx = []
    cmd_vy = []
    cmd_wz = []

    goal_x = []
    goal_y = []
    goal_yaw = []

    mission_status = []
    obstacle_min_distance = []

    for i, ti in enumerate(t):
        base_vx = 0.8 + 0.1 * math.sin(ti)
        base_vy = 0.2 * math.cos(ti * 0.5)
        base_wz = 0.05 * math.sin(ti * 0.7)

        pose_x.append(0.9 * ti + noise(0.02))
        pose_y.append(0.4 * math.sin(ti * 0.3) + noise(0.02))
        pose_yaw.append(0.2 * math.sin(ti * 0.4) + noise(0.01))

        twist_vx.append(base_vx + noise(0.03))
        twist_vy.append(base_vy + noise(0.03))
        twist_wz.append(base_wz + noise(0.01))

        cmd_scale = 0.25 if aggressive else 0.08
        cmd_vx.append(base_vx + noise(cmd_scale))
        cmd_vy.append(base_vy + noise(cmd_scale))
        cmd_wz.append(base_wz + noise(cmd_scale / 3.0))

        goal_x.append(20.0)
        goal_y.append(0.0)
        goal_yaw.append(0.0)

        if ti < t[-1] * 0.1:
            mission_status.append("idle")
        elif ti < t[-1] * 0.9:
            mission_status.append("active")
        else:
            mission_status.append("succeeded")

        min_dist = 2.0 + 0.3 * math.sin(ti * 0.2) + noise(0.05)
        if aggressive and 0.45 * t[-1] < ti < 0.55 * t[-1]:
            min_dist = 0.25 + noise(0.02)
        obstacle_min_distance.append(max(min_dist, 0.05))

    return {
        "t": t,
        "state.pose2d.x": pose_x,
        "state.pose2d.y": pose_y,
        "state.pose2d.yaw": pose_yaw,
        "state.twist2d.vx": twist_vx,
        "state.twist2d.vy": twist_vy,
        "state.twist2d.wz": twist_wz,
        "command.twist2d.vx": cmd_vx,
        "command.twist2d.vy": cmd_vy,
        "command.twist2d.wz": cmd_wz,
        "mission.goal2d.x": goal_x,
        "mission.goal2d.y": goal_y,
        "mission.goal2d.yaw": goal_yaw,
        "mission.status": mission_status,
        "obstacle.min_distance": obstacle_min_distance,
    }


def _build_events(aggressive: bool) -> list[dict[str, object]]:
    events: list[dict[str, object]] = [
        {"t": 0.2, "name": "mission.start", "attrs": {"mode": "auto"}},
    ]
    if aggressive:
        events.extend(
            [
                {
                    "t": 4.2,
                    "name": "safety.fallback",
                    "attrs": {"mode": "slow", "reason": "clearance"},
                },
                {
                    "t": 6.4,
                    "name": "sys.deadline_miss",
                    "attrs": {"task": "planner", "dt_ms": 45},
                },
            ]
        )
    return events


def _write_run(out_dir: Path, seed: int, aggressive: bool) -> None:
    run_id = "run_000"
    run_dir = out_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "spec_version": SPEC_VERSION,
        "run_id": run_id,
        "created_at": "2026-01-22T00:00:00Z",
        "robot": {"name": "demo-bot", "model": "rbx-1"},
        "environment": {"site": "sim", "condition": "clear"},
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, sort_keys=True, indent=2))

    rows = _build_run_rows(seed, n=200, aggressive=aggressive)
    pd.DataFrame(rows).to_parquet(run_dir / "run.parquet", index=False)

    events = _build_events(aggressive)
    events_payload = [
        {
            "t": event["t"],
            "name": event["name"],
            "attrs_json": json.dumps(event["attrs"], sort_keys=True),
        }
        for event in events
    ]
    pd.DataFrame(events_payload).to_parquet(run_dir / "events.parquet", index=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic DemoLog dataset."
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    baseline_dir = args.out / "baseline"
    candidate_dir = args.out / "candidate"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir.mkdir(parents=True, exist_ok=True)

    _write_run(baseline_dir, seed=args.seed, aggressive=False)
    _write_run(candidate_dir, seed=args.seed + 1, aggressive=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
