# nbfoundry

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Marimo-based notebook framework for ML/DS work. One notebook source compiles into two
artifacts: a standalone runnable application and an `ExerciseBlock`-compatible artifact
that drops into a learningfoundry curriculum.

For the why, see [`docs/specs/concept.md`](docs/specs/concept.md). For the what, see
[`docs/specs/features.md`](docs/specs/features.md). For the how, see
[`docs/specs/tech-spec.md`](docs/specs/tech-spec.md).

## Installation

`nbfoundry` targets Python 3.12.13 with the pinned Pyve + micromamba environment defined
in [`environment.yml`](environment.yml).

### Apple Silicon quickstart

The pinned stack is tuned for Apple Silicon with Metal/MPS acceleration across PyTorch,
TensorFlow (via `tensorflow-metal`), and Keras. From a clean Apple Silicon machine:

```bash
# 1. Create the runtime environment from the pinned spec
micromamba env create -f environment.yml -n nbfoundry
micromamba activate nbfoundry

# 2. Install the package in editable mode
pip install -e .

# 3. Verify Metal acceleration on each framework
python scripts/metal_smoke.py
```

Successful output ends with `all frameworks ran on MPS ✓`. If any framework fails, the
script reports which one and why (no MPS device, plugin not installed, etc.).

### Development setup (Pyve two-env)

```bash
pyve init
pyve run pip install -e .
pyve testenv init
pyve testenv install -r requirements-dev.txt
```

## Usage

The CLI surface (`nbfoundry init`, `compile`, `compile-exercise`, `validate`) lands
across Phase D. See [`docs/specs/stories.md`](docs/specs/stories.md) for the
implementation roadmap.
