import json

from robometrics.model.event import Event


def test_event_roundtrip_and_ordering() -> None:
    event = Event(
        t=1.25,
        name="tag",
        attrs={"z": 3, "a": True, "m": None},
    )

    payload = event.to_dict()
    restored = Event.from_dict(json.loads(json.dumps(payload)))

    assert payload["t"] == 1.25
    assert payload["name"] == "tag"
    assert list(payload["attrs"].keys()) == ["a", "m", "z"]
    assert restored.to_dict() == payload


def test_event_attribute_types() -> None:
    event = Event(
        t=0.0,
        name="mixed",
        attrs={"flag": False, "count": 2, "note": "ok", "ratio": 0.5},
    )

    payload = event.to_dict()

    assert payload["attrs"] == {
        "count": 2,
        "flag": False,
        "note": "ok",
        "ratio": 0.5,
    }
