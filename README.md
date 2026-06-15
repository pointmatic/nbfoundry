# nbfoundry

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Marimo-based notebook framework for ML/DS work. One notebook source compiles into two
artifacts: a standalone runnable application and an `ExerciseBlock`-compatible artifact
that drops into a learningfoundry curriculum.

For the why, see [`docs/specs/concept.md`](docs/specs/concept.md). For the what, see
[`docs/specs/features.md`](docs/specs/features.md). For the how, see
[`docs/specs/tech-spec.md`](docs/specs/tech-spec.md).

## Installation

`nbfoundry` targets Python 3.12.13 with **Pyve + venv** (exclusively — no conda or
micromamba). The Metal ML stack is fully pip-installable on Apple Silicon, so each
scaffolded project ships per-stage pip requirements instead of a conda env file:

- [`requirements-base.txt`](src/nbfoundry/templates/requirements-base.txt) — framework-agnostic core (the `data_*` stages).
- [`requirements-torch.txt`](src/nbfoundry/templates/requirements-torch.txt) — torch-family stack (the `model_*` stages); `-r`-includes the base.
- [`requirements-tf.txt`](src/nbfoundry/templates/requirements-tf.txt) — TensorFlow-family option; `-r`-includes the base.

These ship as package data: `nbfoundry init` copies the **stage-appropriate** file into
every scaffolded project, and the standalone artifact emitter falls back to
`requirements-base.txt` when the source carries none.

### Apple Silicon quickstart

The stack defaults to Apple Silicon with Metal/MPS acceleration: PyTorch via the bare
`torch` MPS wheel, TensorFlow via `tensorflow-macos` + `tensorflow-metal`, and the
bundled Keras 3 namespace from TF 2.16+. The torch stack also ships the wider
cross-project set (HuggingFace `transformers` / `datasets` / `peft`, Optuna, the
plotly/seaborn/pyarrow utility set, and the Pointmatic-internal `ml-datarefinery`).

Scaffold a project and build its venv with plain pip — no micromamba:

```bash
nbfoundry init demo --template model_experimentation
cd demo
pyve init                                  # creates the project venv
pip install -r requirements-torch.txt      # torch + HuggingFace + Optuna on MPS
```

A `data_*` scaffold instead emits `requirements-base.txt` (no ML framework). Because
`torch` and `tensorflow` are never co-installed in one venv, a learner cannot hit the
PyTorch-MPS / TensorFlow-Metal co-residence crash.

> **Framework Metal verification** is done dev-side via the lazy named smoke envs
> (`pyve test --env smoke-torch …` / `--env smoke-tensorflow …`); see
> [`docs/specs/env-dependencies.md`](docs/specs/env-dependencies.md).

#### Cross-platform users (CUDA / CPU-only)

The requirements files ship comment-delimited swap guidance:

- **PyTorch CUDA:** install torch from the PyTorch index instead of the bare line, e.g.
  `pip install torch --index-url https://download.pytorch.org/whl/cu128` (`cpu` / `cu126`
  / `cu128`).
- **TensorFlow CPU-only or Linux+CUDA:** in `requirements-tf.txt`, replace the
  `tensorflow-macos` / `tensorflow-metal` lines with `tensorflow>=2.16` (CPU-only) or
  `tensorflow[and-cuda]>=2.16` (Linux + CUDA).

Both notes are documented inline at the top of the relevant requirements file.

### Development setup (Pyve two-env)

```bash
pyve init
pyve run pip install -e .
pyve env init
pyve env run pip install -e .
pyve env install -r requirements-dev.txt
```

Run the suite with `pyve test` (lint: `pyve env run ruff check .`; types:
`pyve env run mypy`). Hardware smokes are opt-in: `pyve test --env smoke-torch …`
/ `--env smoke-tensorflow … -m hardware`.

## Usage

`nbfoundry` exposes four commands. Compile and validate are **offline,
deterministic, and side-effect-free** — they read only the files you point them at
and never touch the network.

### 1. Scaffold a notebook — `init`

```bash
nbfoundry init demo --template data_exploration
```

`--template` is one of the five lifecycle stages: `data_exploration`,
`data_preparation`, `model_experimentation`, `model_optimization`,
`model_evaluation` (defaults to `data_exploration`). The scaffold contains a
reactive Marimo `notebook.py` plus the stage-appropriate `requirements-*.txt`.

### 2. Run it as a standalone app — `compile`

```bash
nbfoundry compile demo --out dist
```

Produces a self-contained artifact directory (the compiled notebook(s), the
`requirements-*.txt`, and a `launch.py` entry point) that runs locally with no
server or cloud dependency.

### 3. Compile to a learningfoundry exercise — `compile-exercise`

Author an exercise YAML whose sections carry (or reference, via `code_file`) the
notebook code, plus instructional metadata:

```yaml
# exercise.yaml
title: Explore a dataset
description: Load, describe, and visualize the data.
sections:
  - title: Load
    description: Read the CSV into a DataFrame.
    code: |
      import pandas as pd
      df = pd.read_csv("data.csv")
```

```bash
nbfoundry compile-exercise exercise.yaml --out exercise.json   # or omit --out for stdout
```

The output is an `ExerciseBlock`-compatible dict (the BR-1 wire shape) that drops
into a learningfoundry curriculum. The full schema — instructions, hints,
expected outputs, and the BR-4 `submission` block with client-side grading — is
defined in [`docs/specs/learningfoundry/dependency-spec.md`](docs/specs/learningfoundry/dependency-spec.md).

### 4. Validate without compiling — `validate`

```bash
nbfoundry validate exercise.yaml   # exit 0 when clean; exit 1 with all errors on stdout
```

### Two surfaces from one source (AC-3)

The same notebook source feeds **both** outputs: `compile` turns it into a
runnable standalone app, while `compile-exercise` (whose sections reference that
same notebook via `code_file`) turns it into an embeddable curriculum exercise —
no rewrite when the purpose shifts. That dual-surface compile is the core of
nbfoundry's value (see [`docs/specs/concept.md`](docs/specs/concept.md)).

## Further reading

- [`docs/specs/concept.md`](docs/specs/concept.md) — why nbfoundry exists (problem/solution space).
- [`docs/specs/features.md`](docs/specs/features.md) — what it does (requirements, behavior, acceptance criteria).
- [`docs/specs/tech-spec.md`](docs/specs/tech-spec.md) — how it is built (architecture, dependencies, testing strategy).
- [`docs/specs/learningfoundry/dependency-spec.md`](docs/specs/learningfoundry/dependency-spec.md) — the `ExerciseBlock` contract the compiled exercise targets.
- [`docs/specs/env-dependencies.md`](docs/specs/env-dependencies.md) — the dev/test environment topology.

## Releasing to PyPI

Releases ship through [`.github/workflows/publish.yml`](.github/workflows/publish.yml),
which is triggered by pushing a `v*` tag. The workflow builds an sdist + wheel with
`hatch build` and publishes via PyPI [trusted publishing](https://docs.pypi.org/trusted-publishers/)
(OIDC, no long-lived API tokens).

One-time PyPI setup: register `nbfoundry` on PyPI and add a pending trusted publisher
under the project's *Publishing* settings — owner `pointmatic`, repository `nbfoundry`,
workflow `publish.yml`, environment `pypi`.

Per-release procedure:

1. Land the version-bump story on `main` (package version in `src/nbfoundry/_version.py`
   and a matching `CHANGELOG.md` entry).
2. Tag the commit with the matching `v<version>` (e.g. `git tag v0.29.0 && git push origin v0.29.0`).
3. The workflow verifies the tag matches `hatch version`, builds the distributions, and
   publishes to PyPI under the `pypi` GitHub environment.

The workflow refuses to publish if the tag and `hatch version` disagree, so the only way
to ship a release is to tag the same commit that owns the version bump.
