"""Schema validation reporting for robometrics."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SchemaReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def ok(self) -> bool:
        return not self.errors

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def to_dict(self) -> dict[str, object]:
        return {
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "SchemaReport":
        errors = payload.get("errors", [])
        warnings = payload.get("warnings", [])
        if not isinstance(errors, list):
            raise ValueError("SchemaReport errors must be a list")
        if not isinstance(warnings, list):
            raise ValueError("SchemaReport warnings must be a list")
        return cls(
            errors=[str(item) for item in errors],
            warnings=[str(item) for item in warnings],
        )
