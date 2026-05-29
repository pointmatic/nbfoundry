# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the framework-isolation driver in `scripts/metal_smoke.py`.

These tests are hardware-independent: they exercise the subprocess-isolation
*mechanism*, not the Metal probes themselves. The regression they guard is the
Phase F debug finding that PyTorch-MPS and TensorFlow-Metal cannot coexist in
one process (SIGBUS, exit 138), which means (a) each framework must run in its
own subprocess and (b) a native crash in any one must be surfaced loudly, not
swallowed by the old in-process `try/except Exception`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

_SMOKE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "metal_smoke.py"


def _load_smoke() -> ModuleType:
    spec = importlib.util.spec_from_file_location("metal_smoke", _SMOKE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_driver_module_imports_without_any_framework() -> None:
    """Importing the driver must not pull torch/tf/keras into the process.

    If a framework is imported at module top level, the driver process itself
    becomes a co-residence crash risk — the exact bug we're fixing.
    """
    before = set(sys.modules)
    _load_smoke()
    newly = set(sys.modules) - before
    assert not {m.split(".")[0] for m in newly} & {"torch", "tensorflow", "keras"}


def test_each_probe_runs_in_its_own_subprocess() -> None:
    smoke = _load_smoke()
    calls: list[str] = []

    def fake_runner(name: str) -> int:
        calls.append(name)
        return 0

    smoke.drive(runner=fake_runner)
    # every probe in the canonical order got its own isolated runner call
    assert calls == list(smoke.PROBE_ORDER)
    assert "pytorch" in calls and "keras" in calls


def test_native_crash_is_reported_not_swallowed(capsys) -> None:
    smoke = _load_smoke()

    def crashing_runner(name: str) -> int:
        return -10 if name == "keras" else 0  # -10 == SIGBUS

    rc = smoke.drive(runner=crashing_runner)
    out = capsys.readouterr().out

    assert rc != 0, "a crashed probe must make the overall run fail"
    assert "keras" in out
    assert "10" in out, "the crash signal/exit should be visible in the report"


def test_all_probes_passing_exits_zero(capsys) -> None:
    smoke = _load_smoke()
    rc = smoke.drive(runner=lambda name: 0)
    assert rc == 0
    assert "✓" in capsys.readouterr().out
