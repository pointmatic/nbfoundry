# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""End-to-end Keras 3 happy path on Apple Silicon (Story F.e).

Verifies Keras 3 (the bundled `tf.keras` namespace from TF 2.16+) works
against the refreshed Phase F stack. No standalone `keras` install — F.b
explicitly dropped the standalone pin because TF re-exports the namespace,
and a parallel install silently fights TF's bundled copy.

This test also guards against accidental reintroduction of the standalone
pin: it asserts that the installed `keras` module resolves to the TF-bundled
namespace, not a separately-installed package. Under the named-env reframe
(F.f.3) this guard passes *by construction*: `smoke-tensorflow` ships
TensorFlow only — no HuggingFace — so the transitive that used to pull a
standalone `keras` is simply not present.

The test is gated behind `@pytest.mark.hardware`; `pyve test` skips it by
default (see pyproject.toml `addopts = "-m 'not hardware'"`).

Developer-hardware run procedure (one-time per release), on Apple Silicon:

    pyve test --env smoke-tensorflow tests/integration/test_e2e_keras.py -m hardware

The `smoke-tensorflow` env (declared in `pyve.toml`, deps in
`tests/integration/env/tensorflow.txt`) is a lazy-provisioned venv that
pip-installs `tensorflow-macos` + `tensorflow-metal` on first targeted use —
no torch, no HuggingFace, no standalone keras. Run one smoke file per process.
This test imports only the `keras`/`tensorflow` namespace (via `importorskip`);
it does not import nbfoundry. See `docs/specs/env-dependencies.md` §5.3.

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
