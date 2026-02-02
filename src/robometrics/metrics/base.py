"""Metric registry and core types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from robometrics.model.event import Event
from robometrics.model.metric_result import MetricResult
from robometrics.model.run import Run
from robometrics.model.scenario import Scenario
from robometrics.model.stream import Stream


@dataclass(frozen=True)
class MetricContext:
    run: Run
    scenario: Scenario
    streams: dict[str, Stream]
    events: list[Event]
    config: dict[str, object]


MetricFn = Callable[[MetricContext], MetricResult]


@dataclass(frozen=True)
class MetricSpec:
    name: str
    requires_streams: list[str] = field(default_factory=list)
    optional_streams: list[str] = field(default_factory=list)
    requires_events: list[str] = field(default_factory=list)
    optional_events: list[str] = field(default_factory=list)
    description: str | None = None
    fn: MetricFn | None = None


REGISTRY: dict[str, MetricSpec] = {}


def metric(
    *,
    name: str,
    requires_streams: list[str] | None = None,
    optional_streams: list[str] | None = None,
    requires_events: list[str] | None = None,
    optional_events: list[str] | None = None,
    description: str | None = None,
) -> Callable[[MetricFn], MetricFn]:
    """Register a metric in the global registry."""

    def decorator(fn: MetricFn) -> MetricFn:
        if name in REGISTRY:
            raise ValueError(f"Metric already registered: {name}")
        spec = MetricSpec(
            name=name,
            requires_streams=list(requires_streams or []),
            optional_streams=list(optional_streams or []),
            requires_events=list(requires_events or []),
            optional_events=list(optional_events or []),
            description=description,
            fn=fn,
        )
        REGISTRY[name] = spec
        return fn

    return decorator
