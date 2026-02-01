"""Scenario mining implementation."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Iterable

from robometrics.mining.rules import RuleSpec, Ruleset, ThresholdSpec
from robometrics.model.run import Run
from robometrics.model.scenario import Scenario
from robometrics.model.scenarioset import ScenarioSet
from robometrics.model.spec import SPEC_VERSION
from robometrics.model.stream import Stream
from robometrics.validate.schema_report import SchemaReport


@dataclass(frozen=True)
class _Segment:
    start: float
    end: float


def mine_scenarios(
    run: Run,
    rules: Ruleset,
    *,
    scenario_set_id: str,
    created_at: str,
) -> tuple[ScenarioSet, SchemaReport]:
    report = SchemaReport()
    scenarios: list[Scenario] = []

    bounds = _run_time_bounds(run)

    for rule in rules.scenarios:
        if rule.event is not None:
            scenarios.extend(_mine_event_rule(run, rule, bounds, report))
        elif rule.threshold is not None:
            scenarios.extend(_mine_threshold_rule(run, rule, bounds, report))

    scenarios.sort(key=lambda s: (s.run_id, s.t0, s.t1, s.intent, s.scenario_id))

    scenario_set = ScenarioSet(
        spec_version=SPEC_VERSION,
        scenario_set_id=scenario_set_id,
        created_at=created_at,
        runs={run.run_id: {"run_id": run.run_id}},
        scenarios=scenarios,
    )

    return scenario_set, report


def _mine_event_rule(
    run: Run,
    rule: RuleSpec,
    bounds: tuple[float, float] | None,
    report: SchemaReport,
) -> list[Scenario]:
    assert rule.event is not None
    matches: list[Scenario] = []

    filtered = run.filter_events(name=rule.event.name)
    if rule.event.where:
        filtered = [
            event for event in filtered if _match_attrs(event.attrs, rule.event.where)
        ]

    for idx, event in enumerate(sorted(filtered, key=lambda e: e.t)):
        t0 = event.t - rule.window.pre_s
        t1 = event.t + rule.window.post_s
        t0, t1 = _clamp_window(t0, t1, bounds)
        scenario_id = _scenario_id(rule.rule_id, run.run_id, t0, t1, idx)
        if t1 <= t0:
            report.add_warning(
                "Rule '{rule_id}' run '{run_id}' scenario '{scenario_id}' "
                "skipped due to non-positive window ({t0:.3f}, {t1:.3f})".format(
                    rule_id=rule.rule_id,
                    run_id=run.run_id,
                    scenario_id=scenario_id,
                    t0=t0,
                    t1=t1,
                )
            )
            continue
        tags = {**rule.tags, "rule_id": rule.rule_id}
        matches.append(
            Scenario(
                scenario_id=scenario_id,
                run_id=run.run_id,
                t0=t0,
                t1=t1,
                intent=rule.intent,
                tags=tags,
            )
        )

    return matches


def _mine_threshold_rule(
    run: Run,
    rule: RuleSpec,
    bounds: tuple[float, float] | None,
    report: SchemaReport,
) -> list[Scenario]:
    assert rule.threshold is not None
    stream = run.get_stream(rule.threshold.stream)
    if stream is None:
        report.add_warning(
            f"Rule '{rule.rule_id}': stream '{rule.threshold.stream}' missing"
        )
        return []

    signal_values = _resolve_signal(stream, rule.threshold, report, rule.rule_id)
    if signal_values is None:
        return []

    condition = [
        _compare(value, rule.threshold.op, rule.threshold.value)
        for value in signal_values
    ]

    segments = _segments_from_condition(stream.t, condition)
    segments = _apply_min_duration(segments, rule.threshold.for_s)
    segments = _apply_min_gap(segments, rule.threshold.min_gap_s)
    segments = _apply_cooldown(segments, rule.threshold.cooldown_s)

    scenarios: list[Scenario] = []
    for idx, segment in enumerate(segments):
        t0 = segment.start - rule.window.pre_s
        t1 = segment.end + rule.window.post_s
        t0, t1 = _clamp_window(t0, t1, bounds)
        scenario_id = _scenario_id(rule.rule_id, run.run_id, t0, t1, idx)
        if t1 <= t0:
            report.add_warning(
                "Rule '{rule_id}' run '{run_id}' scenario '{scenario_id}' "
                "skipped due to non-positive window ({t0:.3f}, {t1:.3f})".format(
                    rule_id=rule.rule_id,
                    run_id=run.run_id,
                    scenario_id=scenario_id,
                    t0=t0,
                    t1=t1,
                )
            )
            continue
        tags = {**rule.tags, "rule_id": rule.rule_id}
        scenarios.append(
            Scenario(
                scenario_id=scenario_id,
                run_id=run.run_id,
                t0=t0,
                t1=t1,
                intent=rule.intent,
                tags=tags,
            )
        )

    return scenarios


def _match_attrs(attrs: dict[str, object], where: dict[str, object]) -> bool:
    for key, value in where.items():
        if attrs.get(key) != value:
            return False
    return True


def _run_time_bounds(run: Run) -> tuple[float, float] | None:
    all_times: list[float] = []
    for stream in run.streams.values():
        all_times.extend(stream.t)
    if not all_times:
        return None
    return min(all_times), max(all_times)


def _clamp_window(
    t0: float, t1: float, bounds: tuple[float, float] | None
) -> tuple[float, float]:
    if bounds is None:
        return t0, t1
    start, end = bounds
    return max(t0, start), min(t1, end)


def _scenario_id(rule_id: str, run_id: str, t0: float, t1: float, idx: int) -> str:
    payload = f"{rule_id}:{run_id}:{t0:.4f}:{t1:.4f}:{idx}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{rule_id}:{digest[:10]}"


def _resolve_signal(
    stream: Stream,
    threshold: ThresholdSpec,
    report: SchemaReport,
    rule_id: str,
) -> list[float] | None:
    if threshold.signal in stream.data:
        return [float(value) for value in stream.data[threshold.signal]]

    if threshold.signal == "linear_speed":
        if "vx" in stream.data and "vy" in stream.data:
            values: list[float] = []
            for vx, vy in zip(stream.data["vx"], stream.data["vy"], strict=True):
                values.append(math.hypot(float(vx), float(vy)))
            return values
        report.add_warning(f"Rule '{rule_id}': signal 'linear_speed' requires vx/vy")
        return None

    report.add_warning(f"Rule '{rule_id}': signal '{threshold.signal}' not found")
    return None


def _compare(value: float, op: str, target: float) -> bool:
    if op == "lt":
        return value < target
    if op == "le":
        return value <= target
    if op == "gt":
        return value > target
    if op == "ge":
        return value >= target
    raise ValueError(f"Unsupported operator: {op}")


def _segments_from_condition(
    times: Iterable[float], mask: Iterable[bool]
) -> list[_Segment]:
    segments: list[_Segment] = []
    start: float | None = None
    last_time: float | None = None
    for t, flag in zip(times, mask, strict=True):
        if flag and start is None:
            start = float(t)
        if not flag and start is not None:
            end = float(last_time if last_time is not None else t)
            segments.append(_Segment(start=start, end=end))
            start = None
        last_time = float(t)
    if start is not None and last_time is not None:
        segments.append(_Segment(start=start, end=last_time))
    return segments


def _apply_min_duration(segments: list[_Segment], for_s: float) -> list[_Segment]:
    if for_s <= 0:
        return segments
    return [segment for segment in segments if (segment.end - segment.start) >= for_s]


def _apply_min_gap(segments: list[_Segment], min_gap_s: float | None) -> list[_Segment]:
    if not segments or not min_gap_s or min_gap_s <= 0:
        return segments
    merged: list[_Segment] = []
    current = segments[0]
    for segment in segments[1:]:
        if segment.start - current.end <= min_gap_s:
            current = _Segment(start=current.start, end=max(current.end, segment.end))
        else:
            merged.append(current)
            current = segment
    merged.append(current)
    return merged


def _apply_cooldown(
    segments: list[_Segment], cooldown_s: float | None
) -> list[_Segment]:
    if not segments or not cooldown_s or cooldown_s <= 0:
        return segments
    filtered: list[_Segment] = []
    last_end: float | None = None
    for segment in segments:
        if last_end is None or segment.start - last_end >= cooldown_s:
            filtered.append(segment)
            last_end = segment.end
    return filtered
