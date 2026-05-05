# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from nbfoundry.errors import ExerciseError

_logger = logging.getLogger("nbfoundry.assets")
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_BYTES_PER_MB = 1024 * 1024


def _reject_url(path: str, base_dir: Path) -> None:
    if _URL_RE.match(path):
        raise ExerciseError(
            file_path=base_dir,
            message=f"asset paths must be relative file paths, not URLs: {path}",
        )


def enumerate(compiled_outputs: Iterable[Mapping[str, Any]]) -> list[str]:
    seen: set[str] = set()
    for entry in compiled_outputs:
        if entry.get("type") != "image":
            continue
        path = entry.get("path")
        if path is None:
            continue
        seen.add(str(path))
    return sorted(seen)


def check_existence(base_dir: Path, paths: Iterable[str]) -> None:
    for p in paths:
        _reject_url(p, base_dir)
        target = base_dir / p
        if not target.is_file():
            raise ExerciseError(
                file_path=base_dir,
                message=f"asset file does not exist: {p}",
            )


def check_size(
    base_dir: Path,
    paths: Iterable[str],
    *,
    warn_mb: int,
    max_mb: int,
    allow_large: bool,
) -> None:
    warn_bytes = warn_mb * _BYTES_PER_MB
    max_bytes = max_mb * _BYTES_PER_MB
    for p in paths:
        _reject_url(p, base_dir)
        size = (base_dir / p).stat().st_size
        if size >= max_bytes and not allow_large:
            raise ExerciseError(
                file_path=base_dir,
                message=(
                    f"asset {p} is {size / _BYTES_PER_MB:.1f} MB, exceeds "
                    f"max_single_asset_mb={max_mb} (override with allow_large_assets)"
                ),
            )
        if size >= warn_bytes:
            _logger.warning(
                "asset %s is %.1f MB (warn_single_asset_mb=%d)",
                p,
                size / _BYTES_PER_MB,
                warn_mb,
            )
