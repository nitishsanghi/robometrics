"""Mining rules schema and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass(frozen=True)
class WindowSpec:
    pre_s: float
    post_s: float


@dataclass(frozen=True)
class EventSpec:
    name: str
    where: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ThresholdSpec:
    stream: str
    signal: str
    op: str
    value: float
    for_s: float = 0.0
    min_gap_s: float | None = None
    cooldown_s: float | None = None


@dataclass(frozen=True)
class RuleSpec:
    rule_id: str
    intent: str
    tags: dict[str, str]
    window: WindowSpec
    event: EventSpec | None = None
    threshold: ThresholdSpec | None = None


@dataclass(frozen=True)
class Ruleset:
    version: str
    scenarios: list[RuleSpec]


def load_rules(path: str) -> Ruleset:
    with open(path, "r", encoding="utf-8") as handle:
        try:
            payload = yaml.safe_load(handle)
        except yaml.YAMLError as exc:  # pragma: no cover - rare
            raise ValueError(f"Invalid YAML: {exc}") from exc
    return _parse_rules(payload)


def _parse_rules(payload: Any) -> Ruleset:
    if not isinstance(payload, dict):
        raise ValueError("Rules file must contain a top-level mapping")

    version = payload.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("Rules file must specify a non-empty version")

    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValueError("Rules file must include a scenarios list")

    rules: list[RuleSpec] = []
    seen_ids: set[str] = set()
    for idx, item in enumerate(scenarios):
        if not isinstance(item, dict):
            raise ValueError(f"Rule at index {idx} must be a mapping")
        rule_id = _require_str(item, "id")
        if rule_id in seen_ids:
            raise ValueError(_fmt(rule_id, "duplicate rule id"))
        seen_ids.add(rule_id)
        intent = _require_str(item, "intent", rule_id)
        tags = item.get("tags", {})
        if tags is None:
            tags = {}
        if not isinstance(tags, dict):
            raise ValueError(_fmt(rule_id, "tags must be a mapping"))
        tags = {str(key): str(value) for key, value in tags.items()}

        window = _parse_window(item.get("window"), rule_id)

        event_spec = item.get("event")
        threshold_spec = item.get("threshold")
        if (event_spec is None) == (threshold_spec is None):
            raise ValueError(
                _fmt(rule_id, "must define exactly one of event or threshold")
            )

        event = _parse_event(event_spec, rule_id) if event_spec else None
        threshold = (
            _parse_threshold(threshold_spec, rule_id) if threshold_spec else None
        )

        rules.append(
            RuleSpec(
                rule_id=rule_id,
                intent=intent,
                tags=tags,
                window=window,
                event=event,
                threshold=threshold,
            )
        )

    return Ruleset(version=str(version), scenarios=rules)


def _parse_window(value: Any, rule_id: str) -> WindowSpec:
    if not isinstance(value, dict):
        raise ValueError(_fmt(rule_id, "window must be a mapping"))
    pre_s = _require_float(value, "pre_s", rule_id)
    post_s = _require_float(value, "post_s", rule_id)
    if pre_s < 0 or post_s < 0:
        raise ValueError(_fmt(rule_id, "window values must be >= 0"))
    return WindowSpec(pre_s=pre_s, post_s=post_s)


def _parse_event(value: Any, rule_id: str) -> EventSpec:
    if not isinstance(value, dict):
        raise ValueError(_fmt(rule_id, "event must be a mapping"))
    name = _require_str(value, "name", rule_id)
    where = value.get("where", {})
    if where is None:
        where = {}
    if not isinstance(where, dict):
        raise ValueError(_fmt(rule_id, "event.where must be a mapping"))
    return EventSpec(name=name, where=dict(where))


def _parse_threshold(value: Any, rule_id: str) -> ThresholdSpec:
    if not isinstance(value, dict):
        raise ValueError(_fmt(rule_id, "threshold must be a mapping"))
    stream = _require_str(value, "stream", rule_id)
    signal = _require_str(value, "signal", rule_id)
    op = _require_str(value, "op", rule_id)
    if op not in {"lt", "le", "gt", "ge"}:
        raise ValueError(_fmt(rule_id, "threshold.op must be one of lt/le/gt/ge"))
    threshold_value = _require_float(value, "value", rule_id)

    for_s = _optional_float(value, "for_s", rule_id, default=0.0)
    if for_s < 0:
        raise ValueError(_fmt(rule_id, "threshold.for_s must be >= 0"))

    min_gap_s = _optional_float(value, "min_gap_s", rule_id, default=None)
    if min_gap_s is not None and min_gap_s < 0:
        raise ValueError(_fmt(rule_id, "threshold.min_gap_s must be >= 0"))

    cooldown_s = _optional_float(value, "cooldown_s", rule_id, default=None)
    if cooldown_s is not None and cooldown_s < 0:
        raise ValueError(_fmt(rule_id, "threshold.cooldown_s must be >= 0"))

    return ThresholdSpec(
        stream=stream,
        signal=signal,
        op=op,
        value=threshold_value,
        for_s=for_s,
        min_gap_s=min_gap_s,
        cooldown_s=cooldown_s,
    )


def _require_str(value: dict[str, Any], key: str, rule_id: str | None = None) -> str:
    raw = value.get(key)
    if not isinstance(raw, str) or not raw:
        if rule_id:
            raise ValueError(_fmt(rule_id, f"{key} must be a non-empty string"))
        raise ValueError(f"{key} must be a non-empty string")
    return raw


def _require_float(value: dict[str, Any], key: str, rule_id: str) -> float:
    raw = value.get(key)
    try:
        return float(raw)
    except (TypeError, ValueError):
        raise ValueError(_fmt(rule_id, f"{key} must be a float")) from None


def _optional_float(
    value: dict[str, Any], key: str, rule_id: str, default: float | None
) -> float | None:
    if key not in value:
        return default
    raw = value.get(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        raise ValueError(_fmt(rule_id, f"{key} must be a float")) from None


def _fmt(rule_id: str, message: str) -> str:
    return f"Rule '{rule_id}': {message}"
