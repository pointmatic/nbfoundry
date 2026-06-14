# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""End-to-end TensorFlow happy path on Apple Silicon (Story F.c).

Verifies the refreshed Phase F stack produces a working TF/MPS training run on
Apple Silicon.

The test is gated behind `@pytest.mark.hardware`, so `pyve test` skips it by
default (see pyproject.toml `addopts = "-m 'not hardware'"`).

Developer-hardware run procedure (one-time per release), on Apple Silicon:

    pyve test --env smoke-tensorflow tests/integration/test_e2e_tensorflow.py -m hardware

The `smoke-tensorflow` env (declared in `pyve.toml`, deps in
`tests/integration/env/tensorflow.txt`) is a lazy-provisioned venv that
pip-installs `tensorflow-macos` + `tensorflow-metal` on first targeted use. It
is the TensorFlow-family smoke env (no torch — the F.f.1 co-residence boundary;
no standalone keras — the F.f.2 hygiene boundary). Run one smoke file per
process. This test imports only `tensorflow`/`numpy` (via `importorskip`); it
does not import nbfoundry. See `docs/specs/env-dependencies.md` §5.3.

Budget: under 60s on M-series silicon.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.hardware]


def test_tensorflow_mps_loss_decreases() -> None:
    tf = pytest.importorskip("tensorflow")
    np = pytest.importorskip("numpy")

    gpus = tf.config.list_physical_devices("GPU")
    if not gpus:
        pytest.skip("No GPU device available — tensorflow-metal not active")

    rng = np.random.default_rng(seed=0)
    x = rng.standard_normal((100, 8)).astype("float32")
    y = (rng.standard_normal((100,)) > 0).astype("float32")

    with tf.device("/GPU:0"):
        model = tf.keras.Sequential(
            [
                tf.keras.layers.Input(shape=(8,)),
                tf.keras.layers.Dense(16, activation="relu"),
                tf.keras.layers.Dense(1, activation="sigmoid"),
            ]
        )
        model.compile(optimizer="adam", loss="binary_crossentropy")
        history = model.fit(x, y, epochs=3, batch_size=16, verbose=0)

    losses = history.history["loss"]
    assert losses[-1] < losses[0], (
        f"training loss did not decrease from epoch 0 to epoch {len(losses) - 1}: {losses}"
    )
    assert gpus[0].device_type == "GPU", f"unexpected device type: {gpus[0]}"
