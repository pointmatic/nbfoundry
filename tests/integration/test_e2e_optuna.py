# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""End-to-end Optuna hyperparameter-search happy path (Story F.g).

Runs a small Optuna study whose objective trains a tiny PyTorch model on Apple
Silicon's MPS device, proving the optimization library drives a real torch/MPS
training loop end-to-end against the refreshed Phase F stack. Optuna rides the
torch family, so it lives in the `smoke-torch` env alongside PyTorch and
HuggingFace — there is no co-residence concern (Optuna is pure-Python).

The test is gated behind `@pytest.mark.hardware`, so `pyve test` skips it by
default (see pyproject.toml `addopts = "-m 'not hardware'"`).

Developer-hardware run procedure (one-time per release), on Apple Silicon:

    pyve test --env smoke-torch tests/integration/test_e2e_optuna.py -m hardware

The `smoke-torch` env (declared in `pyve.toml`, deps in
`tests/integration/env/torch.txt`) is a lazy-provisioned venv that pip-installs
the torch-family stack — including `optuna` — on first targeted use. Run one
smoke file per process. This test imports only `optuna`/`torch`/`numpy` (via
`importorskip`); it does not import nbfoundry. See
`docs/specs/env-dependencies.md` §5.2.

The study runs 5 trials, each tuning two hyperparameters (learning rate and
hidden width) of a tiny dense classifier trained on ~100 random samples; the
objective returns the final training loss. Budget: under 60s on M-series
silicon.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.hardware]


def test_optuna_study_optimizes_a_torch_mps_model() -> None:
    optuna = pytest.importorskip("optuna")
    torch = pytest.importorskip("torch")
    np = pytest.importorskip("numpy")

    if not torch.backends.mps.is_available():
        pytest.skip("torch.backends.mps.is_available() is False — MPS not built or no Metal GPU")

    device = torch.device("mps")
    rng = np.random.default_rng(seed=0)
    x = torch.from_numpy(rng.standard_normal((100, 8)).astype("float32")).to(device)
    y = torch.from_numpy((rng.standard_normal((100,)) > 0).astype("float32")).to(device)

    def objective(trial: optuna.Trial) -> float:
        lr = trial.suggest_float("lr", 1e-3, 1e-1, log=True)
        hidden = trial.suggest_int("hidden", 8, 32)

        torch.manual_seed(0)
        model = torch.nn.Sequential(
            torch.nn.Linear(8, hidden),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden, 1),
        ).to(device)
        loss_fn = torch.nn.BCEWithLogitsLoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)

        model.train()
        loss = torch.tensor(0.0)
        for _ in range(20):
            logits = model(x).squeeze(-1)
            loss = loss_fn(logits, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        return float(loss.detach().cpu())

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=5)

    assert len(study.trials) == 5
    assert all(t.state == optuna.trial.TrialState.COMPLETE for t in study.trials)
    # best_trial is populated and its value matches the best recorded objective.
    assert study.best_trial is not None
    assert study.best_value == min(t.value for t in study.trials)
    assert torch.backends.mps.is_available()
