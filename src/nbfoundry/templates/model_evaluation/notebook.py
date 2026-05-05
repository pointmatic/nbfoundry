# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""model_evaluation lifecycle template — held-out → confusion → calibration.

Reactive Marimo notebook scaffold for the *evaluation* stage of the
modelfoundry/nbfoundry workflow. Trains a small classifier, evaluates on a
held-out test split, and produces a classification report, confusion matrix,
and a calibration curve. Modelfoundry primitives are reached only through
`nbfoundry._modelfoundry.get_adapter()`.
"""

import marimo

__generated_with = "0.23.5"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    mo.md("# Model evaluation\nHeld-out test set, confusion matrix, and calibration.")
    return (mo,)


@app.cell
def _():
    import torch

    device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
    return device, torch


@app.cell
def _(torch):
    import numpy as np
    from sklearn.model_selection import train_test_split

    rng = np.random.default_rng(seed=42)
    n, d = 1024, 8
    X = rng.normal(size=(n, d)).astype("float32")
    y = (X[:, 0] + X[:, 1] > 0).astype("int64")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    return (
        X,
        X_test,
        X_train,
        np,
        rng,
        torch.from_numpy(X_test),
        torch.from_numpy(X_train),
        torch.from_numpy(y_test),
        torch.from_numpy(y_train),
        y,
        y_test,
        y_train,
    )


@app.cell
def _(X_train, device, torch, y_train):
    model = torch.nn.Sequential(
        torch.nn.Linear(8, 32),
        torch.nn.ReLU(),
        torch.nn.Linear(32, 2),
    ).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    loss_fn = torch.nn.CrossEntropyLoss()

    Xtr = torch.from_numpy(X_train).to(device)
    ytr = torch.from_numpy(y_train).to(device)

    for _ in range(50):
        opt.zero_grad()
        loss = loss_fn(model(Xtr), ytr)
        loss.backward()
        opt.step()
    return Xtr, loss_fn, model, opt, ytr


@app.cell
def _(X_test, device, model, torch, y_test):
    Xte = torch.from_numpy(X_test).to(device)
    yte = torch.from_numpy(y_test).to(device)

    with torch.no_grad():
        logits = model(Xte)
        probs = torch.softmax(logits, dim=1)
        preds = logits.argmax(dim=1)

    y_true = yte.cpu().numpy()
    y_pred = preds.cpu().numpy()
    y_prob = probs[:, 1].cpu().numpy()
    return Xte, logits, preds, probs, y_pred, y_prob, y_true, yte


@app.cell
def _(mo, y_pred, y_true):
    from sklearn.metrics import classification_report

    report = classification_report(y_true, y_pred, digits=3)
    mo.md(f"### Classification report\n```\n{report}\n```")
    return classification_report, report


@app.cell
def _(y_pred, y_true):
    from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix
    import matplotlib.pyplot as plt

    cm = confusion_matrix(y_true, y_pred)
    fig_cm, ax_cm = plt.subplots(figsize=(4, 4))
    ConfusionMatrixDisplay(cm).plot(ax=ax_cm, colorbar=False)
    ax_cm.set_title("Confusion matrix")
    fig_cm
    return ConfusionMatrixDisplay, ax_cm, cm, confusion_matrix, fig_cm, plt


@app.cell
def _(plt, y_prob, y_true):
    from sklearn.calibration import calibration_curve

    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10, strategy="uniform")
    fig_cal, ax_cal = plt.subplots(figsize=(4, 4))
    ax_cal.plot([0, 1], [0, 1], "--", color="gray", label="perfectly calibrated")
    ax_cal.plot(prob_pred, prob_true, marker="o", label="model")
    ax_cal.set_xlabel("predicted probability (class 1)")
    ax_cal.set_ylabel("observed frequency")
    ax_cal.set_title("Reliability diagram")
    ax_cal.legend()
    fig_cal
    return ax_cal, calibration_curve, fig_cal, prob_pred, prob_true


@app.cell
def _(cm, mo, prob_pred, prob_true, report):
    diag = sum(cm[i, i] for i in range(len(cm)))
    accuracy = diag / cm.sum()
    mae = float(abs(prob_true - prob_pred).mean())
    mo.md(
        "### Final report\n"
        f"- **Test accuracy**: {accuracy:.3f}\n"
        f"- **Calibration MAE** (10 bins): {mae:.3f}\n"
        f"- See classification report above and confusion matrix / reliability diagram below."
    )
    return accuracy, diag, mae


if __name__ == "__main__":
    app.run()
