# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import ValidationError


@dataclass(frozen=True, slots=True)
class ErrorDetail:
    section_index: int | None = None
    field_name: str | None = None
    yaml_pointer: str | None = None

    def __str__(self) -> str:
        parts: list[str] = []
        if self.yaml_pointer is not None:
            parts.append(self.yaml_pointer)
        if self.section_index is not None:
            parts.append(f"section={self.section_index}")
        if self.field_name is not None:
            parts.append(f"field={self.field_name}")
        return ", ".join(parts) if parts else "ErrorDetail()"


@dataclass(slots=True)
class ExerciseError(Exception):
    file_path: Path
    message: str
    detail: ErrorDetail | None = None

    def __str__(self) -> str:
        suffix = f" [{self.detail}]" if self.detail is not None else ""
        return f"{self.file_path}: {self.message}{suffix}"


def _loc_to_pointer(loc: tuple[str | int, ...]) -> str:
    parts: list[str] = []
    for item in loc:
        if isinstance(item, int):
            parts.append(f"[{item}]")
        else:
            parts.append(f".{item}" if parts else item)
    return "".join(parts)


def _section_index_from_loc(loc: tuple[str | int, ...]) -> int | None:
    for i, item in enumerate(loc):
        if item == "sections" and i + 1 < len(loc) and isinstance(loc[i + 1], int):
            return int(loc[i + 1])
    return None


def from_pydantic(yaml_path: Path, error: ValidationError) -> list[ExerciseError]:
    out: list[ExerciseError] = []
    for entry in error.errors():
        loc: tuple[str | int, ...] = tuple(entry.get("loc", ()))
        msg = str(entry.get("msg", "validation error"))
        message = _augment_with_input(msg, entry.get("input"))
        detail = ErrorDetail(
            section_index=_section_index_from_loc(loc),
            yaml_pointer=_loc_to_pointer(loc) if loc else None,
        )
        out.append(ExerciseError(file_path=yaml_path, message=message, detail=detail))
    return out


def _augment_with_input(msg: str, value: object) -> str:
    if isinstance(value, str | int | float | bool) and not isinstance(value, list | dict):
        return f"{msg} (got {value!r})"
    return msg
