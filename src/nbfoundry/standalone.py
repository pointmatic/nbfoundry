# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import shutil
import tempfile
from importlib.resources import files
from pathlib import Path

from nbfoundry import notebooks
from nbfoundry.errors import ExerciseError


def compile(notebook_or_dir: Path, out: Path) -> Path:
    if out.exists():
        raise ExerciseError(
            file_path=out,
            message=f"output path already exists, refusing to overwrite: {out}",
        )

    notebooks.discover_entry(notebook_or_dir)  # raises if ambiguous / wrong shape
    notebooks.parse_all(notebook_or_dir)  # aggregate parse failures → ExerciseError

    out.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(dir=out.parent))
    try:
        _populate(notebook_or_dir, staged)
        os.replace(str(staged), str(out))
    except Exception:
        shutil.rmtree(staged, ignore_errors=True)
        raise

    return out


_BASE_REQUIREMENTS = "requirements-base.txt"


def _populate(notebook_or_dir: Path, staged: Path) -> None:
    if notebook_or_dir.is_file():
        shutil.copy2(notebook_or_dir, staged / notebook_or_dir.name)
        req_src = notebook_or_dir.parent
    else:
        for src in sorted(notebook_or_dir.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(notebook_or_dir)
            dst = staged / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        req_src = notebook_or_dir

    _ensure_requirements(req_src, staged)

    launch = files("nbfoundry.templates.standalone").joinpath("launch.py")
    (staged / "launch.py").write_text(launch.read_text(encoding="utf-8"), encoding="utf-8")


def _ensure_requirements(req_src: Path, staged: Path) -> None:
    """Ensure the artifact ships installable venv/pip requirements (F.f.4).

    Preserves any `requirements*.txt` the source carries (already copied in the
    directory case; copied here for the single-file case). When the source ships
    none, falls back to the agnostic `requirements-base.txt` package data. A
    framework file (torch/tf) `-r`-includes the base, so the base is guaranteed
    alongside it.
    """
    for req in sorted(req_src.glob("requirements*.txt")):
        dst = staged / req.name
        if not dst.exists():
            shutil.copy2(req, dst)

    staged_reqs = list(staged.glob("requirements*.txt"))
    base_needed = not staged_reqs or any(r.name != _BASE_REQUIREMENTS for r in staged_reqs)
    if base_needed and not (staged / _BASE_REQUIREMENTS).exists():
        bundled = files("nbfoundry.templates").joinpath(_BASE_REQUIREMENTS)
        (staged / _BASE_REQUIREMENTS).write_text(
            bundled.read_text(encoding="utf-8"), encoding="utf-8"
        )
