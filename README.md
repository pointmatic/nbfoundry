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
in [`environment.yml`](environment.yml). The full Apple Silicon Metal acceleration story
arrives in Phase E; pre-Phase-E development uses the bare environment.

```bash
# Set up the runtime environment
pyve init
pip install -e .

# Set up the dev tools (separate environment)
pyve testenv --install -r requirements-dev.txt
```

## Usage

The CLI surface (`nbfoundry init`, `compile`, `compile-exercise`, `validate`) lands
across Phase D. See [`docs/specs/stories.md`](docs/specs/stories.md) for the
implementation roadmap.
