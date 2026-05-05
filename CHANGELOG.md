# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-05-05

### Added
- `nbfoundry.errors` module with `ExerciseError` (frozen dataclass inheriting `Exception`) and `ErrorDetail` (`section_index`, `field_name`, `yaml_pointer`) per BR-3.
- `errors.from_pydantic(yaml_path, ValidationError) -> list[ExerciseError]` helper that walks Pydantic `loc` tuples into `yaml_pointer` strings.
- `ExerciseError` re-exported from the package root: `from nbfoundry import ExerciseError`.

## [0.2.0] - 2026-05-05

### Added
- Minimal Typer CLI skeleton in `src/nbfoundry/cli.py` exposing `main()` as the console-script entry point.
- `--version` global flag printing `nbfoundry <version>` and exiting cleanly.

## [0.1.0] - 2026-05-05

### Added
- Initial project scaffolding: `pyproject.toml` with `hatchling` build backend and dynamic version, `src/nbfoundry/` package skeleton with `_version.py`, `requirements-dev.txt` for the pyve testenv, `README.md`, `CHANGELOG.md`, and Apache-2.0 LICENSE.
- Console script entry point `nbfoundry = "nbfoundry.cli:main"` declared in `pyproject.toml` (CLI module lands in Story A.b).
