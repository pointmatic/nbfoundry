# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Minimal reproducer for the silent Keras-on-Metal fit crash.

Run from an env-refresh-test directory built per the F.b verify procedure:

    pyve run python ../nbfoundry/scripts/keras_metal_fit_repro.py; echo "exit=$?"

Expected (working stack): prints "DONE" and exits 0.
Observed (broken stack):  exits 138 (SIGBUS) silently after the TF Metal
plugin-optimizer log line, with no traceback and no "DONE".

Deliberately imports *only* keras + numpy (no torch, no tensorflow preamble)
to isolate whether the crash needs the metal_smoke.py import order or fires
on a clean keras.fit() in isolation.
"""

from __future__ import annotations

import sys

import keras
import numpy as np

print(f"keras={keras.__version__}", flush=True)
print(f"backend={keras.backend.backend()}", flush=True)

model = keras.Sequential([
    keras.layers.Input(shape=(8,)),
    keras.layers.Dense(16, activation="relu"),
    keras.layers.Dense(1),
])
model.compile(optimizer="adam", loss="mse")

x = np.random.randn(64, 8).astype("float32")
y = np.random.randn(64, 1).astype("float32")

print("about to fit...", flush=True)
history = model.fit(x, y, epochs=1, verbose=0)
print(f"DONE loss={history.history['loss'][0]:.4f}", flush=True)
sys.exit(0)
