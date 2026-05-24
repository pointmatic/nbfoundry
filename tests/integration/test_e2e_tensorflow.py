# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""End-to-end TensorFlow happy path on Apple Silicon (Story F.c).

Verifies the refreshed Phase F stack produces a working TF/MPS training run
when nbfoundry is installed from PyPI against the new shared
`src/nbfoundry/templates/environment.yml`.

The test is gated behind `@pytest.mark.hardware`, so `pyve test` skips it by
default (see pyproject.toml `addopts = "-m 'not hardware'"`). Run it
explicitly on developer Apple Silicon hardware:

    pyve test tests/integration/test_e2e_tensorflow.py -m hardware

Developer-hardware run procedure (one-time per release):

    1. Build a fresh micromamba-backed env from the refreshed templates env:
           mkdir tf-smoke && cd tf-smoke
           cp <repo>/src/nbfoundry/templates/environment.yml .
           pyve init --backend micromamba

    2. Install nbfoundry from PyPI into that env (not editable from the
       working tree -- per project-essentials, F.c-F.j install from PyPI to
       validate the published surface):
           pyve run pip install nbfoundry==<latest-published>

    3. Run the smoke from inside the repo:
           pyve test tests/integration/test_e2e_tensorflow.py -m hardware

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
