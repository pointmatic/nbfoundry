# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""data_exploration lifecycle template — load → describe → visualize.

Reactive Marimo notebook scaffold for the *exploration* stage of the
modelfoundry/nbfoundry workflow. Replace the synthetic dataset in the load
cell with your real data, then iterate. Modelfoundry primitives (used in
later-stage templates) are reached only through `nbfoundry._modelfoundry.get_adapter()`.
"""

import marimo

__generated_with = "0.23.5"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    mo.md("# Data exploration\nLoad, describe, and visualize a dataset.")
    return (mo,)


@app.cell
def _():
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(seed=42)
    n = 200
    df = pd.DataFrame(
        {
            "feature_a": rng.normal(loc=0.0, scale=1.0, size=n),
            "feature_b": rng.normal(loc=2.0, scale=0.5, size=n),
            "label": rng.integers(low=0, high=3, size=n),
        }
    )
    return df, np, pd


@app.cell
def _(df):
    summary = df.describe(include="all")
    summary
    return (summary,)


@app.cell
def _(df, mo):
    mo.md(f"**Class balance** (`label`): {df['label'].value_counts().to_dict()}")
    return


@app.cell
def _(df):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4))
    for label, group in df.groupby("label"):
        ax.scatter(group["feature_a"], group["feature_b"], label=f"class {label}", alpha=0.6)
    ax.set_xlabel("feature_a")
    ax.set_ylabel("feature_b")
    ax.set_title("feature_a vs feature_b by class")
    ax.legend()
    fig
    return ax, fig, plt


if __name__ == "__main__":
    app.run()
