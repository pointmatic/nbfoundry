# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""End-to-end PyTorch happy path on Apple Silicon (Story F.d).

Verifies the refreshed Phase F stack produces a working PyTorch/MPS training
run on Apple Silicon.

The test is gated behind `@pytest.mark.hardware`, so `pyve test` skips it by
default (see pyproject.toml `addopts = "-m 'not hardware'"`).

Developer-hardware run procedure (one-time per release), on Apple Silicon:

    pyve test --env smoke-torch tests/integration/test_e2e_pytorch.py -m hardware

The `smoke-torch` env (declared in `pyve.toml`, deps in
`tests/integration/env/torch.txt`) is a lazy-provisioned venv that pip-installs
the torch-family stack on first targeted use. It is the torch-family smoke env
(no TensorFlow — the F.f.1 co-residence boundary). Run one smoke file per
process. This test imports only `torch`/`numpy` (via `importorskip`); it does
not import nbfoundry. See `docs/specs/env-dependencies.md` §5.2.

The test trains a tiny dense classifier on ~100 random samples for 1 epoch
(batch_size=16, ~6 optimizer steps), records the loss at each step, and
asserts the last-batch loss is below the first-batch loss and that
`torch.backends.mps.is_available()` is True. Budget: under 60s on M-series
silicon.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.hardware]


def test_pytorch_mps_loss_decreases() -> None:
    torch = pytest.importorskip("torch")
    np = pytest.importorskip("numpy")

    if not torch.backends.mps.is_available():
        pytest.skip("torch.backends.mps.is_available() is False — MPS not built or no Metal GPU")

    device = torch.device("mps")
    rng = np.random.default_rng(seed=0)
    x = torch.from_numpy(rng.standard_normal((100, 8)).astype("float32")).to(device)
    y = torch.from_numpy((rng.standard_normal((100,)) > 0).astype("float32")).to(device)

    torch.manual_seed(0)
    model = torch.nn.Sequential(
        torch.nn.Linear(8, 16),
        torch.nn.ReLU(),
        torch.nn.Linear(16, 1),
    ).to(device)
    loss_fn = torch.nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-2)

    batch_size = 16
    indices = torch.arange(x.shape[0])
    losses: list[float] = []
    model.train()
    for start in range(0, x.shape[0], batch_size):
        batch = indices[start : start + batch_size]
        logits = model(x[batch]).squeeze(-1)
        loss = loss_fn(logits, y[batch])
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu()))

    assert len(losses) >= 2, f"too few batches to assert decrease: {losses}"
    assert losses[-1] < losses[0], (
        f"training loss did not decrease from batch 0 to batch {len(losses) - 1}: {losses}"
    )
    assert torch.backends.mps.is_available()
