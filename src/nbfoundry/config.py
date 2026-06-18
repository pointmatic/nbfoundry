# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import tomllib
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal

MarkdownFlavor = Literal["commonmark", "gfm"]


@dataclass(frozen=True, slots=True)
class CompileConfig:
    default_out: str = "dist/"


@dataclass(frozen=True, slots=True)
class ExerciseConfig:
    markdown_flavor: MarkdownFlavor = "commonmark"


@dataclass(frozen=True, slots=True)
class EnvironmentConfig:
    spec_path: str = "requirements-base.txt"


@dataclass(frozen=True, slots=True)
class Config:
    compile: CompileConfig = CompileConfig()
    exercise: ExerciseConfig = ExerciseConfig()
    environment: EnvironmentConfig = EnvironmentConfig()


CONFIG_FILENAME = "nbfoundry.toml"


def load(base_dir: Path) -> Config:
    toml_path = base_dir / CONFIG_FILENAME
    if not toml_path.is_file():
        return Config()

    with toml_path.open("rb") as f:
        data = tomllib.load(f)

    return _from_dict(data)


def _from_dict(data: dict[str, Any]) -> Config:
    defaults = Config()
    return Config(
        compile=_section(CompileConfig, defaults.compile, data.get("compile")),
        exercise=_section(ExerciseConfig, defaults.exercise, data.get("exercise")),
        environment=_section(EnvironmentConfig, defaults.environment, data.get("environment")),
    )


def _section[T](cls: type[T], default: T, raw: dict[str, Any] | None) -> T:
    if not raw:
        return default
    field_names = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
    overrides = {k: v for k, v in raw.items() if k in field_names}
    return replace(default, **overrides)  # type: ignore[type-var]


def merge_cli(config: Config, **overrides: Any) -> Config:
    """CLI-flag merge stub.

    Recognized keys: `default_out`, `markdown_flavor`, `spec_path`. Values
    that are `None` are treated as "flag not provided" and skipped.
    """

    def _picked(*keys: str) -> dict[str, Any]:
        return {k: overrides[k] for k in keys if overrides.get(k) is not None}

    out = config
    if compile_o := _picked("default_out"):
        out = replace(out, compile=replace(out.compile, **compile_o))
    if exercise_o := _picked("markdown_flavor"):
        out = replace(out, exercise=replace(out.exercise, **exercise_o))
    if env_o := _picked("spec_path"):
        out = replace(out, environment=replace(out.environment, **env_o))
    return out
