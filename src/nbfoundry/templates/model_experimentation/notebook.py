# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""model_experimentation lifecycle template — define → train → capture metrics.

Reactive Marimo notebook scaffold for the *experimentation* stage of the
modelfoundry/nbfoundry workflow. Defines a small PyTorch classifier, runs a
few epochs on Apple Silicon's MPS device, and records per-epoch loss / accuracy.
Modelfoundry primitives are reached only through `nbfoundry._modelfoundry.get_adapter()`.
"""

import marimo

__generated_with = "0.23.5"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    mo.md("# Model experimentation\nDefine a PyTorch model, train on MPS, capture metrics.")
    return (mo,)


@app.cell
def _():
    import torch

    device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
    return device, torch


@app.cell
def _(torch):
    import numpy as np

    rng = np.random.default_rng(seed=42)
    n, d = 1024, 8
    X = rng.normal(size=(n, d)).astype("float32")
    y = (X[:, 0] + X[:, 1] > 0).astype("int64")

    X_t = torch.from_numpy(X)
    y_t = torch.from_numpy(y)
    return X_t, n, np, rng, y_t


@app.cell
def _(torch):
    class MLP(torch.nn.Module):
        def __init__(self, in_dim: int = 8, hidden: int = 32, out_dim: int = 2) -> None:
            super().__init__()
            self.net = torch.nn.Sequential(
                torch.nn.Linear(in_dim, hidden),
                torch.nn.ReLU(),
                torch.nn.Linear(hidden, out_dim),
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.net(x)

    return (MLP,)


@app.cell
def _(MLP, X_t, device, torch, y_t):
    import time

    model = MLP().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    loss_fn = torch.nn.CrossEntropyLoss()

    X_d = X_t.to(device)
    y_d = y_t.to(device)

    history: list[dict[str, float]] = []
    epochs = 10
    for epoch in range(epochs):
        t0 = time.perf_counter()
        model.train()
        opt.zero_grad()
        logits = model(X_d)
        loss = loss_fn(logits, y_d)
        loss.backward()
        opt.step()

        with torch.no_grad():
            pred = logits.argmax(dim=1)
            acc = (pred == y_d).float().mean().item()
        history.append(
            {"epoch": epoch, "loss": loss.item(), "acc": acc, "secs": time.perf_counter() - t0}
        )

    return acc, epoch, epochs, history, loss, model, opt, time


@app.cell
def _(history, mo):
    import pandas as pd

    metrics = pd.DataFrame(history)
    last = metrics.iloc[-1]
    mo.md(
        f"**Trained {len(metrics)} epochs.** "
        f"Final loss: `{last['loss']:.4f}` · acc: `{last['acc']:.3f}` · "
        f"avg epoch: `{metrics['secs'].mean() * 1000:.1f} ms`"
    )
    return metrics, pd


@app.cell
def _(metrics):
    metrics
    return


if __name__ == "__main__":
    app.run()
