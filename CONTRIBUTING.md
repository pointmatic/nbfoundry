<!-- Copyright (c) 2026 Pointmatic -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Contributing to nbfoundry

Thanks for contributing! This project uses **Pyve + venv** exclusively (no conda
or micromamba). The full environment topology is documented in
[`docs/specs/env-dependencies.md`](docs/specs/env-dependencies.md).

## Development setup

```bash
pyve init                                    # root venv (.pyve/envs/root/venv/)
pyve run pip install -e .
pyve env init                                # dev/test env (.pyve/envs/testenv/venv/)
pyve env run pip install -e .                # entry-point registration for CLI tests
pyve env install -r requirements-dev.txt     # ruff, mypy, pytest, pytest-cov, + light template-smoke deps
```

## Quality gates (the same four CI enforces)

| Gate | Command | Notes |
|------|---------|-------|
| Lint | `pyve env run ruff check .` | Rule set E, F, W, B, I, UP, SIM, RUF |
| Format | `pyve env run ruff format --check .` | Run `ruff format .` to fix |
| Types | `pyve env run mypy` | `mypy --strict`; `src/nbfoundry/templates/` excluded |
| Tests + coverage | `pyve test` | See the coverage gate below |

All four run on every push and PR via [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
across macOS (primary) and Linux (stretch).

## Coverage gate

`pyve test` enforces **≥ 85% line coverage** on the `nbfoundry` public modules
(`--cov-fail-under=85` in `pyproject.toml`'s `addopts`); the template notebooks
under `src/nbfoundry/templates/` are omitted from measurement. The suite also
writes `coverage.xml`, which CI uploads to
[Codecov](https://codecov.io/gh/pointmatic/nbfoundry) from the primary leg (the
README badge reflects the latest result). Current coverage is ~95%.

A new change should not drop coverage below the gate — add tests for new
branches. The report's `term-missing` output lists uncovered lines.

> **Single-file runs under-report.** Because `--cov-fail-under` lives in the
> default `addopts`, running `pyve test <one_file>` measures only that file and
> will fail the gate. Pass `--no-cov` for focused runs:
> `pyve test tests/unit/test_schema.py --no-cov`.

## Hardware smokes (optional, Apple Silicon)

The `@pytest.mark.hardware` smokes are deselected by default and run in the lazy
per-framework envs:

```bash
pyve test --env smoke-torch      tests/integration/test_e2e_pytorch.py -m hardware
pyve test --env smoke-tensorflow tests/integration/test_e2e_keras.py   -m hardware
```

## Pull requests

Keep CI green (all four gates) and coverage at or above the gate. Match the
surrounding code style and add tests with behavior changes.
