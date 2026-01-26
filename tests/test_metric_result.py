import json

import pytest

from robometrics.model.metric_result import MetricResult


def test_metric_result_roundtrip() -> None:
    metric = MetricResult(
        value=0.9,
        units="ratio",
        direction="higher",
        valid=True,
        notes="ok",
    )

    payload = metric.to_dict()
    restored = MetricResult.from_dict(json.loads(json.dumps(payload)))

    assert restored.to_dict() == payload


def test_metric_result_optional_fields() -> None:
    metric = MetricResult(
        value=None,
        units=None,
        direction="neutral",
        valid=False,
        notes=None,
    )

    payload = metric.to_dict()

    assert payload["value"] is None
    assert payload["units"] is None
    assert payload["notes"] is None


def test_metric_result_direction_validation() -> None:
    with pytest.raises(ValueError):
        MetricResult(
            value=1,
            units=None,
            direction="up",
            valid=True,
            notes=None,
        )
