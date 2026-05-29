# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Apple Silicon Metal-acceleration smoke test (Story E.a / PE-4 / F.b / F.g).

Probes each of PyTorch, TensorFlow, and Keras for an MPS-backed device and
runs a small training step / matmul on it. Also imports every other package
added to the shared `templates/environment.yml` in Phase F (HuggingFace
stack, Optuna, plotly, seaborn, pyarrow, etc.) and asserts they load — per-
framework training for those tools is covered by the F.c-F.g per-tool smoke
stories. Exits 0 only if every framework ran on MPS *and* every additional
package imported cleanly.

Run from the repo root after `micromamba env create -f environment.yml`:

    pyve run python scripts/metal_smoke.py

Each framework probe runs in its OWN subprocess. This is load-bearing, not
tidiness: PyTorch's MPS backend and TensorFlow-Metal cannot coexist in a
single process — once torch.mps has claimed the system Metal device, a
later TF-Metal Grappler optimization (which Keras's TF backend triggers on
`fit()`) faults with SIGBUS (exit 138). The crash is native, so the old
in-process `try/except Exception` could not catch it and the run exited
silently mid-Keras. Isolating each probe means a crash in one is observed by
the parent as a non-zero child exit and reported loudly, and no two Metal
clients ever share a process. The driver process itself imports no framework.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from collections.abc import Callable


def _section(title: str) -> None:
    print(f"\n=== {title} ===")


def _ok(msg: str) -> None:
    print(f"  ok: {msg}")


def _fail(msg: str) -> str:
    print(f"  FAIL: {msg}")
    return msg


def _pytorch_smoke() -> str | None:
    _section("PyTorch")
    try:
        import torch
    except ImportError as e:
        return _fail(f"could not import torch: {e}")

    if not torch.backends.mps.is_available():
        return _fail("torch.backends.mps.is_available() is False — MPS not built or no Metal GPU")

    device = torch.device("mps")
    x = torch.randn(1024, 1024, device=device)
    y = torch.randn(1024, 1024, device=device)
    t0 = time.perf_counter()
    z = (x @ y).sum()
    torch.mps.synchronize()
    dt = time.perf_counter() - t0
    _ok(f"matmul + sum on {device}: {dt * 1000:.1f} ms (result≈{z.item():.2f})")
    return None


def _tensorflow_smoke() -> str | None:
    _section("TensorFlow")
    try:
        import tensorflow as tf
    except ImportError as e:
        return _fail(f"could not import tensorflow: {e}")

    gpus = tf.config.list_physical_devices("GPU")
    if not gpus:
        return _fail(
            "tf.config.list_physical_devices('GPU') is empty — tensorflow-metal not active"
        )

    with tf.device("/GPU:0"):
        x = tf.random.normal((1024, 1024))
        y = tf.random.normal((1024, 1024))
        t0 = time.perf_counter()
        z = tf.reduce_sum(tf.linalg.matmul(x, y))
        _ = float(z.numpy())
        dt = time.perf_counter() - t0
    _ok(f"matmul on {gpus[0].name}: {dt * 1000:.1f} ms (result≈{float(z):.2f})")
    return None


def _keras_smoke() -> str | None:
    _section("Keras")
    try:
        import keras
        import numpy as np
    except ImportError as e:
        return _fail(f"could not import keras/numpy: {e}")

    model = keras.Sequential([
        keras.layers.Input(shape=(8,)),
        keras.layers.Dense(16, activation="relu"),
        keras.layers.Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse")
    x = np.random.randn(64, 8).astype("float32")
    y = np.random.randn(64, 1).astype("float32")
    t0 = time.perf_counter()
    history = model.fit(x, y, epochs=1, verbose=0)
    dt = time.perf_counter() - t0
    _ok(f"fit 1 epoch: {dt * 1000:.1f} ms (loss≈{history.history['loss'][0]:.3f})")
    return None


_F_B_IMPORT_PROBES: list[tuple[str, str]] = [
    # (section, module name to import)
    ("core", "pyarrow"),
    ("core", "seaborn"),
    ("core", "plotly"),
    ("core", "PIL"),
    ("core", "h5py"),
    ("core", "yaml"),
    ("core", "click"),
    ("core", "rich"),
    ("core", "dotenv"),
    ("core", "conda_lock"),
    # PyPI distribution is `ml-datarefinery`; import name is `datarefinery`
    # (sklearn-style split).
    ("core", "datarefinery"),
    ("huggingface", "transformers"),
    ("huggingface", "datasets"),
    ("huggingface", "peft"),
    ("huggingface", "sentencepiece"),
    ("huggingface", "google.protobuf"),
    ("huggingface", "tiktoken"),
    ("optimization", "optuna"),
]


def _f_b_imports_smoke() -> list[str]:
    _section("F.b additional packages (import-only)")
    fails: list[str] = []
    for section, module in _F_B_IMPORT_PROBES:
        try:
            __import__(module)
            _ok(f"[{section}] {module}")
        except ImportError as e:
            fails.append(_fail(f"[{section}] could not import {module}: {e}"))
    return fails


# Probe name -> worker function. Order is the order the driver runs them in.
# Each runs in its own subprocess (see module docstring); the framework
# imports live inside these functions, never at module top level.
_PROBES = {
    "pytorch": _pytorch_smoke,
    "tensorflow": _tensorflow_smoke,
    "keras": _keras_smoke,
    "imports": _f_b_imports_smoke,
}
PROBE_ORDER: tuple[str, ...] = ("pytorch", "tensorflow", "keras", "imports")


def _run_probe(name: str) -> int:
    """Worker entry: run one probe in this (subprocess) interpreter."""
    probe = _PROBES[name]
    result = probe()
    failed = bool(result)  # str (single) or non-empty list (imports) == failure
    return 1 if failed else 0


def _verdict(rc: int) -> str:
    if rc == 0:
        return "PASS"
    if rc < 0:
        return f"CRASH (signal {-rc}, exit {128 - rc})"
    return f"FAIL (exit {rc})"


def _default_runner(name: str) -> int:
    """Spawn a fresh interpreter running just this probe, inheriting stdio.

    A native crash (e.g. SIGBUS from torch-MPS/TF-Metal co-residence in a
    framework that itself pulls multiple Metal clients) surfaces as a
    negative returncode the parent can report, rather than killing the driver.
    """
    proc = subprocess.run([sys.executable, __file__, "--probe", name])
    return proc.returncode


def drive(
    probes: tuple[str, ...] = PROBE_ORDER,
    runner: Callable[[str], int] = _default_runner,
) -> int:
    results: dict[str, int] = {}
    for name in probes:
        rc = runner(name)
        results[name] = rc
        print(f"\n[{name}] -> {_verdict(rc)}")

    print("\n=== summary ===")
    failures = {n: rc for n, rc in results.items() if rc != 0}
    if failures:
        for name, rc in failures.items():
            print(f"  - {name}: {_verdict(rc)}")
        return 1
    print("  all frameworks ran on MPS ✓")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--probe",
        choices=tuple(_PROBES),
        help="Internal: run a single probe in this process (used by the driver).",
    )
    args = parser.parse_args(argv)

    if args.probe is not None:
        return _run_probe(args.probe)
    return drive()


if __name__ == "__main__":
    sys.exit(main())
