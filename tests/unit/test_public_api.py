# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import inspect
from pathlib import Path

import nbfoundry


def test_public_names_present() -> None:
    expected = {"ExerciseError", "__version__", "compile_exercise", "validate_exercise"}
    assert expected <= set(nbfoundry.__all__)
    for name in expected:
        assert hasattr(nbfoundry, name), name


def test_compile_exercise_signature_matches_br1() -> None:
    sig = inspect.signature(nbfoundry.compile_exercise, eval_str=True)
    params = list(sig.parameters.values())
    # First two positional params per BR-1: yaml_path: Path, base_dir: Path
    assert params[0].name == "yaml_path"
    assert params[0].annotation is Path
    assert params[1].name == "base_dir"
    assert params[1].annotation is Path
    # Any extra params must be keyword-only (extension, not BR-1 violation)
    assert all(p.kind == inspect.Parameter.KEYWORD_ONLY for p in params[2:])


def test_validate_exercise_signature_matches_br2() -> None:
    sig = inspect.signature(nbfoundry.validate_exercise, eval_str=True)
    params = list(sig.parameters.values())
    assert params[0].name == "yaml_path"
    assert params[0].annotation is Path
    assert params[1].name == "base_dir"
    assert params[1].annotation is Path
    assert sig.return_annotation == list[str]


def test_exercise_error_shape_matches_br3() -> None:
    err = nbfoundry.ExerciseError(Path("x.yaml"), "bad")
    assert isinstance(err, Exception)
    assert err.file_path == Path("x.yaml")
    assert err.message == "bad"
    assert err.detail is None
    assert str(err) == "x.yaml: bad"


def test_version_string() -> None:
    assert isinstance(nbfoundry.__version__, str)
    assert nbfoundry.__version__.count(".") == 2
