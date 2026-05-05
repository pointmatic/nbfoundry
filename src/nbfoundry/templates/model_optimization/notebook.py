# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""model_optimization lifecycle template — sweep → prune → quantize.

Reactive Marimo notebook scaffold for the *optimization* stage of the
modelfoundry/nbfoundry workflow. Runs a small grid search over learning
rate × hidden dimension, then applies an L1-unstructured pruning pass to
the best model. Modelfoundry primitives are reached only through
`nbfoundry._modelfoundry.get_adapter()`.
"""

import marimo

__generated_with = "0.23.5"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    mo.md("# Model optimization\nHyperparameter sweep, then pruning.")
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
    def build_mlp(in_dim: int, hidden: int, out_dim: int) -> torch.nn.Module:
        return torch.nn.Sequential(
            torch.nn.Linear(in_dim, hidden),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden, out_dim),
        )

    def train_one(model: torch.nn.Module, X, y, *, lr: float, epochs: int = 30) -> float:
        opt = torch.optim.Adam(model.parameters(), lr=lr)
        loss_fn = torch.nn.CrossEntropyLoss()
        for _ in range(epochs):
            opt.zero_grad()
            logits = model(X)
            loss = loss_fn(logits, y)
            loss.backward()
            opt.step()
        with torch.no_grad():
            return (logits.argmax(dim=1) == y).float().mean().item()

    return build_mlp, train_one


@app.cell
def _(X_t, build_mlp, device, train_one, y_t):
    X_d = X_t.to(device)
    y_d = y_t.to(device)
    grid: list[dict[str, float | int]] = []
    for lr in (1e-3, 1e-2, 5e-2):
        for hidden in (8, 32, 64):
            model = build_mlp(8, hidden, 2).to(device)
            acc = train_one(model, X_d, y_d, lr=lr, epochs=30)
            grid.append({"lr": lr, "hidden": hidden, "acc": acc})
    return X_d, grid, y_d


@app.cell
def _(grid, mo):
    import pandas as pd

    results = pd.DataFrame(grid).sort_values("acc", ascending=False).reset_index(drop=True)
    best = results.iloc[0]
    mo.md(
        f"**Best hyperparameters** — lr=`{best['lr']}`, hidden=`{int(best['hidden'])}`, "
        f"acc=`{best['acc']:.3f}`"
    )
    return best, pd, results


@app.cell
def _(results):
    results
    return


@app.cell
def _(X_d, best, build_mlp, device, mo, torch, train_one, y_d):
    from torch.nn.utils import prune

    final = build_mlp(8, int(best["hidden"]), 2).to(device)
    train_one(final, X_d, y_d, lr=float(best["lr"]), epochs=30)

    # Apply 30% L1-unstructured pruning to the first Linear layer's weights
    prune.l1_unstructured(final[0], name="weight", amount=0.3)
    sparsity = float((final[0].weight == 0).float().mean().item())

    with torch.no_grad():
        pruned_acc = (final(X_d).argmax(dim=1) == y_d).float().mean().item()

    mo.md(
        f"**Pruned model** — sparsity (layer 0): `{sparsity:.2f}`, "
        f"post-prune acc: `{pruned_acc:.3f}`"
    )
    return final, prune, pruned_acc, sparsity


if __name__ == "__main__":
    app.run()
