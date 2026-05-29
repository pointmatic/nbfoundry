# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Narrowing driver for the Keras-on-Metal SIGBUS (debug cycle, Phase F).

Runs four framework-coresidence permutations, each in its OWN subprocess, to
isolate which preceding GPU context triggers the crash inside `keras.fit()`:

    1. control      : bare keras.fit (no preamble)            -> expect exit 0
    2. tf->keras    : tf matmul on /GPU:0, then keras.fit
    3. torch->keras : torch.mps matmul, then keras.fit
    4. torch->tf->keras : the full metal_smoke.py order        -> known exit 138

Because each case is a separate process, a SIGBUS in one does not kill the
driver -- the parent observes the child's negative/exit return code and
reports it. (This is exactly the isolation property the future diagnostic
CLI will rely on; see the deferred spec/CLI discussion.)

Run from an env-refresh-test directory:

    pyve run python ../nbfoundry/scripts/keras_metal_narrow.py
"""

from __future__ import annotations

import subprocess
import sys

_TORCH = (
    "import torch;"
    "x=torch.randn(1024,1024,device='mps');y=torch.randn(1024,1024,device='mps');"
    "_=(x@y).sum();torch.mps.synchronize();"
)

_TF = (
    "import tensorflow as tf;"
    "d=tf.device('/GPU:0');d.__enter__();"
    "_=tf.reduce_sum(tf.linalg.matmul(tf.random.normal((1024,1024)),"
    "tf.random.normal((1024,1024)))).numpy();d.__exit__(None,None,None);"
)

_KERAS_FIT = (
    "import keras,numpy as np;"
    "m=keras.Sequential([keras.layers.Input(shape=(8,)),"
    "keras.layers.Dense(16,activation='relu'),keras.layers.Dense(1)]);"
    "m.compile(optimizer='adam',loss='mse');"
    "m.fit(np.random.randn(64,8).astype('float32'),"
    "np.random.randn(64,1).astype('float32'),epochs=1,verbose=0);"
    "print('FIT_OK')"
)

_CASES: list[tuple[str, str]] = [
    ("control      (keras only)", _KERAS_FIT),
    ("tf -> keras", _TF + _KERAS_FIT),
    ("torch -> keras", _TORCH + _KERAS_FIT),
    ("torch -> tf -> keras", _TORCH + _TF + _KERAS_FIT),
]


def _verdict(rc: int) -> str:
    if rc == 0:
        return "PASS (exit 0)"
    if rc < 0:
        return f"CRASH (signal {-rc}, i.e. exit {128 - rc})"
    return f"FAIL (exit {rc})"


def main() -> int:
    print(f"python: {sys.executable}\n")
    worst = 0
    for label, code in _CASES:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
        )
        rc = proc.returncode
        worst = worst or (rc != 0)
        print(f"{label:<28} -> {_verdict(rc)}")
        if rc != 0:
            tail = (proc.stderr or "").strip().splitlines()[-3:]
            for line in tail:
                print(f"      stderr| {line}")
    return 1 if worst else 0


if __name__ == "__main__":
    sys.exit(main())
