import json

import pytest

from robometrics.model.stream import Stream


def test_stream_roundtrip_and_ordering() -> None:
    stream = Stream(
        name="pose",
        t=[0.0, 1.0],
        data={"z": [3, 4], "a": [1, 2]},
    )

    payload = stream.to_dict()
    restored = Stream.from_dict(json.loads(json.dumps(payload)))

    assert list(payload["data"].keys()) == ["a", "z"]
    assert restored.to_dict() == payload


def test_stream_allows_mixed_types() -> None:
    stream = Stream(
        name="mixed",
        t=[0.0, 1.0, 2.0],
        data={"x": [1, 2, 3], "flag": [True, False, True], "note": [None, "ok", ""]},
    )

    payload = stream.to_dict()

    assert payload["data"]["flag"] == [True, False, True]
    assert payload["data"]["note"] == [None, "ok", ""]


def test_stream_from_dict_rejects_string_column() -> None:
    payload = {
        "name": "bad",
        "t": [0.0],
        "data": {"x": "not-a-list"},
    }

    with pytest.raises(ValueError):
        Stream.from_dict(payload)
