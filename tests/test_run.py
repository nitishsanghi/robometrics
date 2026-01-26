import json

from robometrics.model.event import Event
from robometrics.model.run import Run
from robometrics.model.stream import Stream


def test_run_roundtrip() -> None:
    stream = Stream(
        name="pose",
        t=[0.0, 1.0],
        data={"x": [1.0, 2.0]},
    )
    events = [
        Event(t=0.5, name="start", attrs={"ok": True}),
        Event(t=1.5, name="stop", attrs={"reason": "done"}),
    ]
    run = Run(
        run_id="run-1",
        meta={"operator": "unit-test", "trial": 1},
        streams={"pose": stream},
        events=events,
    )

    payload = run.to_dict()
    restored = Run.from_dict(json.loads(json.dumps(payload)))

    assert restored.to_dict() == payload


def test_run_get_stream() -> None:
    stream = Stream(name="pose", t=[0.0], data={"x": [1.0]})
    run = Run(run_id="run-1", streams={"pose": stream})

    assert run.get_stream("pose") is stream
    assert run.get_stream("missing") is None


def test_run_filter_events() -> None:
    events = [
        Event(t=0.5, name="start", attrs={}),
        Event(t=1.0, name="mark", attrs={}),
        Event(t=1.5, name="start", attrs={}),
    ]
    run = Run(run_id="run-1", events=events)

    by_name = run.filter_events(name="start")
    assert [event.t for event in by_name] == [0.5, 1.5]

    by_time = run.filter_events(t0=0.75, t1=1.5)
    assert [event.t for event in by_time] == [1.0]

    by_both = run.filter_events(name="start", t0=0.0, t1=1.0)
    assert [event.t for event in by_both] == [0.5]
