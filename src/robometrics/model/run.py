"""Run container for robometrics."""

from __future__ import annotations

from dataclasses import dataclass, field

from robometrics.model.event import Event
from robometrics.model.stream import Stream


@dataclass
class Run:
    run_id: str
    meta: dict[str, object] = field(default_factory=dict)
    streams: dict[str, Stream] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)

    def get_stream(self, name: str) -> Stream | None:
        return self.streams.get(name)

    def filter_events(
        self,
        name: str | None = None,
        t0: float | None = None,
        t1: float | None = None,
    ) -> list[Event]:
        filtered: list[Event] = []
        for event in self.events:
            if name is not None and event.name != name:
                continue
            if t0 is not None and event.t < t0:
                continue
            if t1 is not None and event.t >= t1:
                continue
            filtered.append(event)
        return filtered

    @staticmethod
    def _sort_structure(value: object) -> object:
        if isinstance(value, dict):
            return {key: Run._sort_structure(value[key]) for key in sorted(value)}
        if isinstance(value, list):
            return [Run._sort_structure(item) for item in value]
        if isinstance(value, tuple):
            return tuple(Run._sort_structure(item) for item in value)
        return value

    def to_dict(self) -> dict[str, object]:
        ordered_meta = Run._sort_structure(self.meta)
        ordered_streams = {
            key: self.streams[key].to_dict() for key in sorted(self.streams)
        }
        return {
            "run_id": self.run_id,
            "meta": ordered_meta,
            "streams": ordered_streams,
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "Run":
        run_id = str(payload["run_id"])
        meta = payload.get("meta", {})
        streams = payload.get("streams", {})
        events = payload.get("events", [])

        if not isinstance(meta, dict):
            raise ValueError("Run meta must be a dict")
        if not isinstance(streams, dict):
            raise ValueError("Run streams must be a dict")
        if not isinstance(events, list):
            raise ValueError("Run events must be a list")

        typed_streams = {
            str(name): Stream.from_dict(stream) for name, stream in streams.items()
        }
        typed_events = [Event.from_dict(event) for event in events]
        return cls(
            run_id=run_id,
            meta=dict(meta),
            streams=typed_streams,
            events=typed_events,
        )
