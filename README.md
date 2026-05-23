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
TensorFlow (via `tensorflow-metal`), and Keras. To verify the stack on a clean Apple
Silicon machine, copy `environment.yml` and `scripts/metal_smoke.py` into a fresh
directory and let pyve build a micromamba-backed env from the spec:

```bash
mkdir nbfoundry-test && cd nbfoundry-test
mkdir scripts
cp <path-to-nbfoundry-root>/environment.yml .
cp <path-to-nbfoundry-root>/scripts/metal_smoke.py scripts/
pyve init --backend micromamba
pyve run python scripts/metal_smoke.py
```

`pyve init --backend micromamba` reads the local `environment.yml` and provisions the
runtime env from it. The smoke script doesn't import `nbfoundry` itself — it just
exercises PyTorch / TensorFlow / Keras against the MPS device — so no `pip install -e .`
step is required for the verify.

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
