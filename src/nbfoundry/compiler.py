# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from nbfoundry import assets, paths
from nbfoundry.config import load as load_config
from nbfoundry.errors import ExerciseError, from_pydantic
from nbfoundry.markdown import render as render_markdown
from nbfoundry.schema import (
    ExpectedRule,
    RawExerciseModel,
    RawExpectedOutputModel,
    RawSectionModel,
    SubmissionFieldModel,
    SubmissionModel,
)

_logger = logging.getLogger("nbfoundry.compiler")


def compile_exercise(
    yaml_path: Path,
    base_dir: Path,
    *,
    allow_large_assets: bool = False,
) -> dict[str, Any]:
    cfg = load_config(base_dir)
    flavor = cfg.exercise.markdown_flavor

    yaml_full = paths.resolve_under(base_dir, yaml_path)

    try:
        with yaml_full.open("rb") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ExerciseError(file_path=yaml_full, message=f"YAML parse error: {e}") from e

    if not isinstance(raw, dict):
        raise ExerciseError(
            file_path=yaml_full,
            message="exercise YAML must be a mapping at the top level",
        )

    try:
        model = RawExerciseModel.model_validate(raw)
    except ValidationError as e:
        first = from_pydantic(yaml_full, e)[0]
        raise first from e

    sections = [_compile_section(s, yaml_full, base_dir, flavor) for s in model.sections]
    expected_outputs = [_compile_expected_output(o) for o in model.expected_outputs]

    asset_paths = assets.enumerate(expected_outputs)
    assets.check_existence(base_dir, asset_paths)
    assets.check_size(
        base_dir,
        asset_paths,
        warn_mb=cfg.assets.warn_single_asset_mb,
        max_mb=cfg.assets.max_single_asset_mb,
        allow_large=allow_large_assets or cfg.assets.allow_large_assets,
    )

    return {
        "type": "exercise",
        "source": "nbfoundry",
        "ref": str(yaml_path),
        "status": "ready",
        "title": model.title,
        "instructions": render_markdown(model.description, flavor),
        "sections": sections,
        "expected_outputs": expected_outputs,
        "assets": asset_paths,
        "hints": list(model.hints),
        "submission": _compile_submission(model.submission),
        "environment": _compile_environment(model.environment),
    }


def _compile_section(
    section: RawSectionModel,
    yaml_full: Path,
    base_dir: Path,
    flavor: str,
) -> dict[str, Any]:
    if section.code is not None:
        code = section.code
    else:
        assert section.code_file is not None  # schema validator guarantees this
        code_path = paths.resolve_under(base_dir, section.code_file)
        try:
            code = code_path.read_text(encoding="utf-8")
        except OSError as e:
            raise ExerciseError(
                file_path=yaml_full,
                message=f"could not read code_file {section.code_file}: {e}",
            ) from e

    return {
        "title": section.title,
        "description": render_markdown(section.description, flavor),  # type: ignore[arg-type]
        "code": code,
        "editable": section.editable,
    }


def _compile_expected_output(o: RawExpectedOutputModel) -> dict[str, Any]:
    if o.type == "image":
        assert o.path is not None and o.alt is not None
        return {
            "description": o.description,
            "type": "image",
            "path": o.path.as_posix(),
            "alt": o.alt,
        }
    assert o.content is not None
    return {
        "description": o.description,
        "type": o.type,
        "content": o.content,
    }


def _compile_submission(s: SubmissionModel | None) -> dict[str, Any] | None:
    if s is None:
        return None
    return {
        "pass_threshold": s.pass_threshold,
        "fields": [_compile_submission_field(f) for f in s.fields],
    }


def _compile_submission_field(f: SubmissionFieldModel) -> dict[str, Any]:
    out: dict[str, Any] = {
        "name": f.name,
        "type": f.type,
        "label": f.label,
        "expected": _compile_expected_rule(f.expected),
    }
    if f.placeholder is not None:
        out["placeholder"] = f.placeholder
    return out


def _compile_expected_rule(r: ExpectedRule) -> dict[str, Any]:
    out: dict[str, Any] = {"type": r.type, "weight": r.weight}
    if r.type == "range":
        if r.min is not None:
            out["min"] = r.min
        if r.max is not None:
            out["max"] = r.max
    elif r.type == "equals":
        out["value"] = r.value
    else:  # contains_all
        out["values"] = list(r.values or [])
    return out


def _compile_environment(e: Any) -> dict[str, Any] | None:
    if e is None:
        return None
    return {
        "python_version": e.python_version,
        "dependencies": list(e.dependencies),
        "setup_instructions": e.setup_instructions,
    }
