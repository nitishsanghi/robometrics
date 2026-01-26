import pytest

from robometrics.model.stream import Stream


def test_stream_slice_left_inclusive() -> None:
    stream = Stream(
        name="demo",
        t=[0.0, 0.5, 1.0, 1.5, 2.0],
        data={"x": [0, 1, 2, 3, 4]},
    )

    sliced = stream.slice(0.5, 1.5)

    assert sliced.t == [0.5, 1.0]
    assert sliced.data["x"] == [1, 2]


def test_stream_slice_both_inclusive() -> None:
    stream = Stream(
        name="demo",
        t=[0.0, 0.5, 1.0, 1.5, 2.0],
        data={"x": [0, 1, 2, 3, 4]},
    )

    sliced = stream.slice(0.5, 1.5, inclusive="both")

    assert sliced.t == [0.5, 1.0, 1.5]
    assert sliced.data["x"] == [1, 2, 3]


def test_stream_slice_empty() -> None:
    stream = Stream(
        name="demo",
        t=[0.0, 0.5, 1.0, 1.5, 2.0],
        data={"x": [0, 1, 2, 3, 4]},
    )

    sliced = stream.slice(3.0, 4.0)

    assert sliced.t == []
    assert sliced.data["x"] == []


def test_stream_non_monotonic_raises() -> None:
    with pytest.raises(ValueError):
        Stream(
            name="bad",
            t=[0.0, 1.0, 0.5],
            data={"x": [0, 1, 2]},
        )


def test_stream_length_mismatch_raises() -> None:
    with pytest.raises(ValueError):
        Stream(
            name="bad",
            t=[0.0, 1.0],
            data={"x": [0, 1, 2]},
        )
