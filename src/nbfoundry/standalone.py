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


def _populate(notebook_or_dir: Path, staged: Path) -> None:
    if notebook_or_dir.is_file():
        shutil.copy2(notebook_or_dir, staged / notebook_or_dir.name)
        env_src = notebook_or_dir.parent / "environment.yml"
    else:
        for src in sorted(notebook_or_dir.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(notebook_or_dir)
            dst = staged / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        env_src = notebook_or_dir / "environment.yml"

    if env_src.is_file() and not (staged / "environment.yml").exists():
        shutil.copy2(env_src, staged / "environment.yml")
    elif not (staged / "environment.yml").exists():
        bundled_env = files("nbfoundry.templates").joinpath("environment.yml")
        (staged / "environment.yml").write_text(
            bundled_env.read_text(encoding="utf-8"), encoding="utf-8"
        )

    launch = files("nbfoundry.templates.standalone").joinpath("launch.py")
    (staged / "launch.py").write_text(launch.read_text(encoding="utf-8"), encoding="utf-8")
