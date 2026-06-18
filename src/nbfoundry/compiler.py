# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Option-C compile / validate pipeline (Story I.d).

`compile_exercise` reads an exercise definition YAML, validates it
against `ExerciseDefinition`, renders the banner markdown
(`description` + `hints`) to HTML, calls `codegen.generate()` to emit
the marimo notebook source, and assembles the wire dict:

    {type, source, ref, title, description, hints, environment, notebook_source}

`validate_exercise` shares the validation core and returns all
accumulated errors as strings (collect-all-errors semantics, FR-4).

Build-time purity: this module imports no ML framework. The codegen
output bakes `import torch` / etc. as source text inside emitted cells.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from nbfoundry import codegen, paths
from nbfoundry.config import load as load_config
from nbfoundry.errors import ExerciseError, from_pydantic
from nbfoundry.markdown import render as render_markdown
from nbfoundry.schema import CompiledExercise, ExerciseDefinition

_logger = logging.getLogger("nbfoundry.compiler")


def _validate(
    yaml_path: Path,
    base_dir: Path,
) -> tuple[ExerciseDefinition | None, Path | None, list[ExerciseError]]:
    """Shared validation pipeline.

    Returns `(model, yaml_full, errors)`. `model` is `None` iff the YAML or
    Pydantic stage failed (no further checks possible). Path-escape and
    parseability checks for `code_file` references are accumulated, not
    raised, so callers can choose first-error or collect-all semantics.
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
        return (
            None,
            yaml_full,
            [ExerciseError(yaml_full, "exercise YAML must be a mapping at the top level")],
        )

    try:
        model = ExerciseDefinition.model_validate(raw)
    except ValidationError as e:
        return None, yaml_full, from_pydantic(yaml_full, e)

    # Path-escape + existence checks for code_file references (no
    # inlining here — codegen.generate handles that). Under Option C the
    # `code_file` is a plain code-snippet inlined into a marimo cell; it
    # is NOT a complete marimo notebook, so the old `notebooks.parse_all`
    # whole-notebook check is gone. Marimo/Python syntax is evaluated at
    # notebook run time on the learner's machine.
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

    return model, yaml_full, errors


def compile_exercise(yaml_path: Path, base_dir: Path) -> dict[str, Any]:
    model, yaml_full, errors = _validate(yaml_path, base_dir)
    if errors:
        raise errors[0]
    assert model is not None and yaml_full is not None  # no errors → both present

    cfg = load_config(base_dir)
    flavor = cfg.exercise.markdown_flavor

    notebook_source = codegen.generate(model, base_dir=base_dir)
    environment = codegen.ensure_marimo_pinned(model.environment)

    compiled: CompiledExercise = {
        "type": "exercise",
        "source": "nbfoundry",
        "ref": str(yaml_path),
        "title": model.title,
        "description": render_markdown(model.description, flavor),
        "hints": [render_markdown(h, flavor) for h in model.hints],
        "environment": environment,
        "notebook_source": notebook_source,
    }
    return dict(compiled)


def validate_exercise(yaml_path: Path, base_dir: Path) -> list[str]:
    _, _, errors = _validate(yaml_path, base_dir)
    return [str(e) for e in errors]
