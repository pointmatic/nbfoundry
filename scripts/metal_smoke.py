# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Apple Silicon Metal-acceleration smoke test (Story E.a / PE-4 / F.b).

Probes each of PyTorch, TensorFlow, and Keras for an MPS-backed device and
runs a small training step / matmul on it. Also imports every other package
added to the shared `templates/environment.yml` in Phase F (HuggingFace
stack, Optuna, plotly, seaborn, pyarrow, etc.) and asserts they load — per-
framework training for those tools is covered by the F.c-F.g per-tool smoke
stories. Exits 0 only if every framework ran on MPS *and* every additional
package imported cleanly.

Run from the repo root after `micromamba env create -f environment.yml`:

    pyve run python scripts/metal_smoke.py
"""

from __future__ import annotations

import sys
import time


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
    ("core", "ml_datarefinery"),
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


def main() -> int:
    failures: list[str] = []
    for label, probe in [
        ("pytorch", _pytorch_smoke),
        ("tensorflow", _tensorflow_smoke),
        ("keras", _keras_smoke),
    ]:
        try:
            err = probe()
        except Exception as e:
            err = _fail(f"unexpected error: {e!r}")
        if err is not None:
            failures.append(f"{label}: {err}")

    extra_fails = _f_b_imports_smoke()
    failures.extend(f"imports: {m}" for m in extra_fails)

    print("\n=== summary ===")
    if failures:
        for f in failures:
            print(f"  - {f}")
        return 1
    print("  all frameworks ran on MPS ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
