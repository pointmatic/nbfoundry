# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""End-to-end Keras 3 happy path on Apple Silicon (Story F.e).

Verifies Keras 3 (the bundled `tf.keras` namespace from TF 2.16+) works
against the refreshed Phase F stack. No standalone `keras` install — F.b
explicitly dropped the standalone pin because TF re-exports the namespace,
and a parallel install silently fights TF's bundled copy.

This test also guards against accidental reintroduction of the standalone
pin: it asserts that the installed `keras` module resolves to the TF-bundled
namespace, not a separately-installed package. If a future env-edit puts
`keras` back in `templates/environment.yml`, this assertion fails loudly.

The test is gated behind `@pytest.mark.hardware`; `pyve test` skips it by
default (see pyproject.toml `addopts = "-m 'not hardware'"`). Run it
explicitly on developer Apple Silicon hardware:

    pyve test tests/integration/test_e2e_keras.py -m hardware

Developer-hardware run procedure (one-time per release):

    1. Build a fresh micromamba-backed env from the refreshed templates env:
           mkdir keras-smoke && cd keras-smoke
           cp <repo>/src/nbfoundry/templates/environment.yml .
           pyve init --backend micromamba

    2. Install nbfoundry from PyPI into that env (not editable from the
       working tree -- per project-essentials, F.c-F.j install from PyPI to
       validate the published surface):
           pyve run pip install nbfoundry==<latest-published>

    3. Run the smoke from inside the repo:
           pyve test tests/integration/test_e2e_keras.py -m hardware

Budget: under 60s on M-series silicon.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, distribution

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.hardware]


def test_keras_is_the_tf_bundled_namespace() -> None:
    """No separate `keras` distribution should be installed — TF re-exports it."""
    tf = pytest.importorskip("tensorflow")
    keras = pytest.importorskip("keras")

    try:
        dist = distribution("keras")
    except PackageNotFoundError:
        dist = None

    assert dist is None, (
        f"a standalone `keras` distribution is installed ({dist.version}); "
        "expected the TF-bundled namespace only. The standalone pin was dropped "
        "in F.b — re-adding it pulls a parallel Keras 3 minor that fights TF's bundled copy."
    )

    # The bundled namespace's __file__ should live inside the tensorflow install tree.
    assert keras.__file__ is not None
    tf_root = tf.__file__.rsplit("/", 1)[0]
    assert "tensorflow" in keras.__file__ or keras.__file__.startswith(tf_root), (
        f"`keras` module path {keras.__file__!r} does not resolve under "
        f"tensorflow ({tf.__file__!r}); a parallel install may be shadowing tf.keras."
    )


def test_keras_3_mps_loss_decreases() -> None:
    tf = pytest.importorskip("tensorflow")
    keras = pytest.importorskip("keras")
    np = pytest.importorskip("numpy")

    gpus = tf.config.list_physical_devices("GPU")
    if not gpus:
        pytest.skip("No GPU device available — tensorflow-metal not active")

    rng = np.random.default_rng(seed=0)
    x = rng.standard_normal((100, 8)).astype("float32")
    y = (rng.standard_normal((100,)) > 0).astype("float32")

    with tf.device("/GPU:0"):
        model = keras.Sequential(
            [
                keras.layers.Input(shape=(8,)),
                keras.layers.Dense(16, activation="relu"),
                keras.layers.Dense(1, activation="sigmoid"),
            ]
        )
        model.compile(optimizer="adam", loss="binary_crossentropy")
        history = model.fit(x, y, epochs=3, batch_size=16, verbose=0)

    losses = history.history["loss"]
    assert losses[-1] < losses[0], (
        f"training loss did not decrease from epoch 0 to epoch {len(losses) - 1}: {losses}"
    )
