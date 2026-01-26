import json

from robometrics.validate.schema_report import SchemaReport


def test_schema_report_ok_and_adders() -> None:
    report = SchemaReport()

    assert report.ok()

    report.add_warning("warn")
    assert report.ok()

    report.add_error("err")
    assert not report.ok()


def test_schema_report_roundtrip() -> None:
    report = SchemaReport(errors=["bad"], warnings=["note"])

    payload = report.to_dict()
    restored = SchemaReport.from_dict(json.loads(json.dumps(payload)))

    assert restored.errors == ["bad"]
    assert restored.warnings == ["note"]
