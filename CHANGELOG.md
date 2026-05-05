# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-05-05

### Added
- `nbfoundry.config` module with `load(base_dir) -> Config` (stdlib `tomllib`); immutable nested `Config` dataclass covering `compile.default_out`, `exercise.markdown_flavor`, `environment.spec_path`, and `assets.{max_single_asset_mb, warn_single_asset_mb, allow_large_assets}`. Built-in defaults applied when the file or any key is absent.
- `merge_cli(config, **overrides)` stub for the Phase D CLI-flag merge layer; ignores `None` values so unset flags fall through to toml/defaults.

## [0.5.0] - 2026-05-05

### Added
- `nbfoundry.paths` module with `resolve_under(base_dir, candidate) -> Path` (SC-3): rejects absolute paths, `..` traversal, and symlinks that escape `base_dir`; resolves symlinks via `Path.resolve(strict=True)` before the containment check and raises `ExerciseError` with the offending candidate in the message.

## [0.4.0] - 2026-05-05

### Added
- `nbfoundry.logging_setup` module with `configure(level)` installing a stderr `StreamHandler` on the `nbfoundry` logger using the `"%(levelname)s %(name)s: %(message)s"` format. Library modules log to `logging.getLogger("nbfoundry.<module>")` (OR-4).

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
