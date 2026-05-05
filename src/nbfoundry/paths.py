# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

from nbfoundry.errors import ExerciseError


def resolve_under(base_dir: Path, candidate: str | Path) -> Path:
    candidate_path = Path(candidate)

    if candidate_path.is_absolute():
        raise ExerciseError(
            file_path=base_dir,
            message=f"path escapes base directory: {candidate} (absolute paths not allowed)",
        )

    base_resolved = base_dir.resolve(strict=True)
    joined = base_resolved / candidate_path

    try:
        resolved = joined.resolve(strict=True)
    except FileNotFoundError as e:
        raise ExerciseError(
            file_path=base_dir,
            message=f"path does not exist: {candidate}",
        ) from e

    if resolved != base_resolved and base_resolved not in resolved.parents:
        raise ExerciseError(
            file_path=base_dir,
            message=f"path escapes base directory: {candidate}",
        )

    return resolved
