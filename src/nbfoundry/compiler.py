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


def _validate(
    yaml_path: Path,
    base_dir: Path,
    *,
    allow_large_assets: bool,
) -> tuple[RawExerciseModel | None, Path | None, list[ExerciseError]]:
    """Shared validation pipeline.

    Returns `(model, yaml_full, errors)`. `model` is `None` iff the YAML or
    Pydantic stage failed (no further checks possible). `yaml_full` is the
    resolved YAML path when available (used by callers that need it).
    Errors past the schema stage are accumulated, not raised, so callers can
    choose first-error or collect-all semantics.
    """
    errors: list[ExerciseError] = []

    try:
        yaml_full = paths.resolve_under(base_dir, yaml_path)
    except ExerciseError as e:
        return None, None, [e]

    try:
        with yaml_full.open("rb") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return None, yaml_full, [ExerciseError(yaml_full, f"YAML parse error: {e}")]
    except OSError as e:
        return None, yaml_full, [ExerciseError(yaml_full, f"could not read YAML: {e}")]

    if not isinstance(raw, dict):
        return None, yaml_full, [
            ExerciseError(yaml_full, "exercise YAML must be a mapping at the top level"),
        ]

    try:
        model = RawExerciseModel.model_validate(raw)
    except ValidationError as e:
        return None, yaml_full, from_pydantic(yaml_full, e)

    cfg = load_config(base_dir)

    # Path-escape checks for code_file references (no inlining here).
    for i, section in enumerate(model.sections):
        if section.code_file is None:
            continue
        try:
            paths.resolve_under(base_dir, section.code_file)
        except ExerciseError as e:
            errors.append(
                ExerciseError(
                    file_path=yaml_full,
                    message=f"sections[{i}].code_file: {e.message}",
                )
            )

    # Build an output-shape preview just for asset enumeration; this avoids
    # markdown rendering (FR-4: validation must not render).
    preview_outputs: list[dict[str, Any]] = []
    for o in model.expected_outputs:
        if o.type == "image" and o.path is not None:
            preview_outputs.append({"type": "image", "path": o.path.as_posix()})

    asset_paths = assets.enumerate(preview_outputs)

    try:
        assets.check_existence(base_dir, asset_paths)
    except ExerciseError as e:
        errors.append(ExerciseError(yaml_full, e.message))

    try:
        assets.check_size(
            base_dir,
            [p for p in asset_paths if (base_dir / p).is_file()],
            warn_mb=cfg.assets.warn_single_asset_mb,
            max_mb=cfg.assets.max_single_asset_mb,
            allow_large=allow_large_assets or cfg.assets.allow_large_assets,
        )
    except ExerciseError as e:
        errors.append(ExerciseError(yaml_full, e.message))

    return model, yaml_full, errors


def compile_exercise(
    yaml_path: Path,
    base_dir: Path,
    *,
    allow_large_assets: bool = False,
) -> dict[str, Any]:
    model, yaml_full, errors = _validate(
        yaml_path, base_dir, allow_large_assets=allow_large_assets
    )
    if errors:
        raise errors[0]
    assert model is not None and yaml_full is not None  # no errors → both present

    cfg = load_config(base_dir)
    flavor = cfg.exercise.markdown_flavor

    sections = [_compile_section(s, yaml_full, base_dir, flavor) for s in model.sections]
    expected_outputs = [_compile_expected_output(o) for o in model.expected_outputs]
    asset_paths = assets.enumerate(expected_outputs)

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


def validate_exercise(yaml_path: Path, base_dir: Path) -> list[str]:
    _, _, errors = _validate(yaml_path, base_dir, allow_large_assets=False)
    return [str(e) for e in errors]


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
