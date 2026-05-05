# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""data_preparation lifecycle template — clean → engineer → split.

Reactive Marimo notebook scaffold for the *preparation* stage of the
modelfoundry/nbfoundry workflow. Replace the synthetic dataset with your
real data, then iterate on cleaning rules, feature engineering, and the
train/test split. Modelfoundry primitives are reached only through
`nbfoundry._modelfoundry.get_adapter()`.
"""

import marimo

__generated_with = "0.23.5"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    mo.md("# Data preparation\nClean, engineer features, and split into train/test.")
    return (mo,)


@app.cell
def _():
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(seed=42)
    n = 200
    raw = pd.DataFrame(
        {
            "feature_a": rng.normal(loc=0.0, scale=1.0, size=n),
            "feature_b": rng.normal(loc=2.0, scale=0.5, size=n),
            "category": rng.choice(["alpha", "beta", "gamma"], size=n),
            "label": rng.integers(low=0, high=2, size=n),
        }
    )
    # Inject some NaNs to demonstrate cleaning
    raw.loc[rng.choice(raw.index, size=10, replace=False), "feature_a"] = np.nan
    return np, pd, raw, rng


@app.cell
def _(raw):
    cleaned = raw.dropna().reset_index(drop=True)
    cleaned["feature_a"] = cleaned["feature_a"].astype("float32")
    cleaned["feature_b"] = cleaned["feature_b"].astype("float32")
    cleaned
    return (cleaned,)


@app.cell
def _(cleaned, pd):
    encoded = pd.get_dummies(cleaned, columns=["category"], drop_first=False, dtype="float32")
    encoded["feature_a_x_b"] = encoded["feature_a"] * encoded["feature_b"]
    encoded
    return (encoded,)


@app.cell
def _(encoded):
    from sklearn.model_selection import train_test_split

    feature_cols = [c for c in encoded.columns if c != "label"]
    X = encoded[feature_cols]
    y = encoded["label"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    return X, X_test, X_train, feature_cols, y, y_test, y_train


@app.cell
def _(X_test, X_train, mo, y_test, y_train):
    mo.md(
        f"**Split sizes** — train: {len(X_train)} rows / {X_train.shape[1]} features; "
        f"test: {len(X_test)} rows. "
        f"Class balance — train: {y_train.value_counts().to_dict()}, "
        f"test: {y_test.value_counts().to_dict()}"
    )
    return


if __name__ == "__main__":
    app.run()
