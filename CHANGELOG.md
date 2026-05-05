# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.15.0] - 2026-05-05

### Added
- Aggregate notebook-tree compilation (FR-6): `compile_exercise` now validates that every `sections[i].code_file` ending in `.py` is a parseable Marimo notebook (via `notebooks.parse_all`) before inlining. A YAML pulling sections from multiple notebooks in the same tree compiles to one exercise dict — tree structure is invisible to the consumer. Tree-external references continue to be rejected by `paths.resolve_under` (FR-3 path-escape).

## [0.14.0] - 2026-05-05

### Changed
- BR-4 (FR-5) submission errors now include the offending value: `errors.from_pydantic` appends `(got <value>)` to messages whose underlying Pydantic error carries a primitive `input`. Rule/type-compat errors on `SubmissionFieldModel` now name the field (`field 'test_accuracy': ...`).

## [0.13.0] - 2026-05-05

### Added
- `nbfoundry.validate_exercise(yaml_path, base_dir) -> list[str]` — FR-4 collect-all-errors mode. Uses the same `_validate` core as `compile_exercise`, returning every error as a human-readable string (each prefixed with the YAML file path). YAML parse failure or missing file short-circuits to a single-element list.
- Public re-export `from nbfoundry import validate_exercise`.

### Changed
- Refactored `compile_exercise` onto a shared private `_validate` pipeline so compile (raise-on-first) and validate (collect-all) share schema, path-escape, and asset checks.

## [0.12.0] - 2026-05-05

### Added
- `nbfoundry.compiler.compile_exercise(yaml_path, base_dir, *, allow_large_assets=False)` — production FR-3 / BR-1 compiler. Pipeline: resolve YAML under `base_dir`, `yaml.safe_load`, Pydantic validate (first `ValidationError` → `ExerciseError`), inline `code_file` contents (path-escape protected), render markdown, enumerate / existence-check / size-check assets, and assemble the canonical-key-order dict.
- Public re-export `from nbfoundry import compile_exercise`.

### Removed
- `scripts/spike_compile_exercise.py` and `scripts/spike_fixtures/minimal.yaml` — superseded by the production compiler per Story A.c's throwaway contract.

## [0.11.0] - 2026-05-05

### Added
- `nbfoundry._modelfoundry` thin adapter module: `ModelfoundryAdapter` Protocol (`prepare_data`, `train`, `optimize`, `evaluate`) and `get_adapter()` that lazy-imports `modelfoundry` and raises `RuntimeError` with an install hint when the dependency is absent (FR-7 / AC-10).
- `tests/unit/test_modelfoundry_adapter.py` covering the missing-import error and an AST-scan asserting that `compiler.py`, `validator.py`, `schema.py`, and `cli.py` never import the adapter.

## [0.10.0] - 2026-05-05

### Added
- `nbfoundry.notebooks` module with `discover_entry(notebook_or_dir)` (single file → itself; directory → `notebook.py` if present, else the lone `*.py`) and `parse_all(entry)` returning a list of `ParsedNotebook` (path + Marimo serialization). Marimo parse failures are aggregated into one `ExerciseError` with one `file:line: description` per violation. No `exec`, `eval`, or `subprocess` (SC-4).

## [0.9.0] - 2026-05-05

### Added
- `nbfoundry.assets` module with `enumerate(compiled_outputs)` (sorted, deduplicated image paths), `check_existence(base_dir, paths)` (`Path.is_file()` only — no byte reads), and `check_size(base_dir, paths, *, warn_mb, max_mb, allow_large)` (warn at `warn_mb`, raise `ExerciseError` at `max_mb` unless `allow_large`). Paths matching `^https?://` are rejected.

## [0.8.0] - 2026-05-05

### Added
- `nbfoundry.markdown` module with `render(text, flavor)` wrapping `markdown-it-py`. The `commonmark` flavor uses the stock CommonMark preset; `gfm` enables GFM `table` and `strikethrough` rules on top of CommonMark (no extra runtime dependency).

## [0.7.0] - 2026-05-05

### Added
- `nbfoundry.schema` module: Pydantic v2 input models (`RawSectionModel`, `RawExpectedOutputModel`, `ExpectedRule`, `SubmissionFieldModel`, `SubmissionModel`, `EnvironmentModel`, `RawExerciseModel`) and `TypedDict`s for the BR-1 wire shape (`CompiledSection`, `CompiledExpectedImage`, `CompiledExpectedTextOrTable`, `CompiledSubmissionField`, `CompiledSubmission`, `CompiledEnvironment`, `CompiledExercise`).
- Schema validators: `code` xor `code_file` on sections; shape-by-type on expected outputs (image needs `path`+`alt`; text/table need `content`); per-rule key requirements on `ExpectedRule`; rule/type compatibility on submission fields; unique field names; `pass_threshold ∈ [0.0, 1.0]`; positive-integer `weight`.

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
