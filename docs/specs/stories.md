# stories.md -- nbfoundry (Python 3.12.13)

This document breaks the `nbfoundry` project into an ordered sequence of small, independently completable stories grouped into phases. Each story has a checklist of concrete tasks. Stories are organized by phase and reference modules defined in `tech-spec.md`.

Put **`vX.Y.Z` in the story title only when that story ships the package version bump** for that release. Doc-only or polish stories **omit the version from the title** (they share the release with the preceding code story, or use your project's doc-release policy). **One semver bump per owning story** — extra tasks on the *same* story share that bump; see `project-essentials.md`. Semantic versioning applies to the package. Stories are marked with `[Planned]` initially and changed to `[Done]` when completed.

For a high-level concept (why), see [`concept.md`](concept.md). For requirements and behavior (what), see [`features.md`](features.md). For implementation details (how), see [`tech-spec.md`](tech-spec.md). For project-specific must-know facts, see [`project-essentials.md`](project-essentials.md) (`plan_phase` appends new facts per phase). For the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), see [`docs/project-guide/go.md`](../project-guide/go.md) — re-read it whenever the mode changes or after context compaction.

---

## Phase A: Foundation

Scaffolding, the smallest runnable artifact, an end-to-end compile-path spike, and the cross-cutting primitives (errors, logging, path-escape protection, config) that every later phase depends on.

### Story A.a: v0.1.0 Project Scaffolding [Done]

Create the package skeleton, license, manifest, and developer-facing baseline. Executed in `scaffold_project` mode; marked `[Done]` by that mode upon completion.

- [x] LICENSE (Apache-2.0, copyright Pointmatic)
- [x] `pyproject.toml` with `hatchling` build backend, `requires-python = ">=3.12.13,<3.14"`, dynamic version from `src/nbfoundry/_version.py`, console script `nbfoundry = "nbfoundry.cli:main"`
- [x] `src/nbfoundry/__init__.py` and `src/nbfoundry/_version.py` (`__version__ = "0.1.0"`)
- [x] `requirements-dev.txt` (ruff, mypy, pytest, pytest-cov, types-PyYAML)
- [x] `README.md` (one-paragraph description + install stub)
- [x] `CHANGELOG.md` (Keep-a-Changelog format, `0.1.0` entry)
- [x] `.gitignore` (Python + venv + dist artifacts)
- [x] Apache-2.0 / Pointmatic header on every new source file
- [x] Verify: `pyve run pip install -e .` succeeds; `pyve testenv --install -r requirements-dev.txt` succeeds

### Story A.b: v0.2.0 Hello-World CLI entry point [Done]

Smallest runnable artifact proving the package + console script wiring works.

- [x] Add minimal Typer app skeleton in `src/nbfoundry/cli.py` exposing `main()`
- [x] Implement `--version` global flag reading from `_version.py`
- [x] Re-export `__version__` from `nbfoundry/__init__.py`
- [x] Bump version to v0.2.0
- [x] Update CHANGELOG.md
- [x] Verify: `pyve run nbfoundry --version` prints `nbfoundry 0.2.0`

### Story A.c: End-to-end compile-path spike [Done]

Throwaway script (in `scripts/`, not the package) that wires the critical YAML → BR-1 dict path end-to-end with a hand-written minimal exercise fixture, before any production module exists. De-risks the architecture; the script is **deleted** when Phase C lands.

- [x] Create `scripts/spike_compile_exercise.py` with Apache-2.0 / Pointmatic header
- [x] Hand-write a tiny `scripts/spike_fixtures/minimal.yaml` (one section, no submission, no assets)
- [x] Spike loads YAML, renders markdown via `markdown-it-py`, assembles a BR-1-shaped dict, prints JSON
- [x] Document in script docstring: "throwaway; superseded by `nbfoundry.compiler` in Phase C"
- [x] Verify: `pyve run python scripts/spike_compile_exercise.py` prints valid JSON matching the BR-1 contract from `learningfoundry-dependency-spec.md`

### Story A.d: v0.3.0 ExerciseError and ErrorDetail [Done]

Typed error contract per features.md BR-3; foundation for all later validation paths.

- [x] `src/nbfoundry/errors.py` — `ExerciseError` frozen dataclass (file_path, message, detail) inheriting `Exception`
- [x] `ErrorDetail` frozen dataclass (section_index, field_name, yaml_pointer)
- [x] `__str__` formatting per tech-spec
- [x] Helper `from_pydantic(yaml_path, ValidationError) -> list[ExerciseError]` walking `loc` tuples into `yaml_pointer` strings
- [x] Re-export `ExerciseError` from `nbfoundry/__init__.py`
- [x] Bump version to v0.3.0
- [x] Update CHANGELOG.md
- [x] Verify: import path `from nbfoundry import ExerciseError` works; `str(ExerciseError(Path("x.yaml"), "bad"))` matches expected format

### Story A.e: v0.4.0 Logging setup [Done]

Leveled logging per OR-4; wired so CLI `--verbose` / `--quiet` map cleanly.

- [x] `src/nbfoundry/logging_setup.py` with `configure(level)` installing `StreamHandler` on stderr, format `%(levelname)s %(name)s: %(message)s`
- [x] Library modules log to `logging.getLogger("nbfoundry.<module>")`
- [x] Bump version to v0.4.0
- [x] Update CHANGELOG.md
- [x] Verify: calling `configure(logging.DEBUG)` then `getLogger("nbfoundry.test").debug("hi")` writes to stderr

### Story A.f: v0.5.0 Path-escape protection [Done]

SC-3 path containment guard, used by every subsequent file-reading code path.

- [x] `src/nbfoundry/paths.py` with `resolve_under(base_dir, candidate) -> Path`
- [x] Reject absolute paths, `..` traversal, symlinks-out-of-base
- [x] Resolve symlinks via `Path.resolve(strict=True)` before containment check
- [x] Raise `ExerciseError` on escape with the offending candidate in `message`
- [x] Bump version to v0.5.0
- [x] Update CHANGELOG.md
- [x] Verify: unit-level smoke — `resolve_under(tmp, "x.yaml")` succeeds; `resolve_under(tmp, "../x")` raises

### Story A.g: v0.6.0 Config loader [Done]

`nbfoundry.toml` + defaults precedence per features.md Configuration; immutable `Config` dataclass for downstream consumers.

- [x] `src/nbfoundry/config.py` with `load(base_dir) -> Config` using stdlib `tomllib`
- [x] `Config` frozen dataclass with `compile.default_out`, `exercise.markdown_flavor`, `environment.spec_path`, `assets.{max_single_asset_mb, warn_single_asset_mb, allow_large_assets}`
- [x] Built-in defaults applied when file or key absent
- [x] CLI flag merge stub (the merge function — flags wired in Phase D)
- [x] Bump version to v0.6.0
- [x] Update CHANGELOG.md
- [x] Verify: `load(tmp_with_no_toml)` returns defaults; `load(tmp_with_partial_toml)` overrides only listed keys

---

## Phase B: Schema and Primitives

The validated input model and the four primitive services the compiler orchestrates: schema, markdown, assets, notebook discovery, and the modelfoundry adapter.

### Story B.a: v0.7.0 Pydantic schema models [Planned]

Single source of truth for YAML input shape and BR-1/BR-4 wire shape per tech-spec Data Models.

- [ ] `src/nbfoundry/schema.py` with `RawSectionModel`, `RawExpectedOutputModel`, `ExpectedRule`, `SubmissionFieldModel`, `SubmissionModel`, `EnvironmentModel`, `RawExerciseModel`
- [ ] `code_xor_code_file` model validator on `RawSectionModel`
- [ ] `shape_by_type` validator on `RawExpectedOutputModel` (image requires `path`+`alt`; text/table require `content`)
- [ ] `ExpectedRule` validator: required keys per `type` (`range` needs `min`/`max`; `equals` needs `value`; `contains_all` needs `values`)
- [ ] `SubmissionFieldModel` validator: rule/type compat (`range`→number; `contains_all`→text; `equals`→number|text)
- [ ] `SubmissionModel` validator: unique field names, `pass_threshold ∈ [0.0, 1.0]`, `weight > 0`
- [ ] `CompiledExercise` and supporting `TypedDict`s for the BR-1 wire shape
- [ ] Bump version to v0.7.0
- [ ] Update CHANGELOG.md
- [ ] Verify: a hand-written valid dict round-trips `RawExerciseModel.model_validate(...)`; representative invalid permutations raise

### Story B.b: v0.8.0 Markdown renderer [Planned]

Markdown → HTML wrapper honoring the `markdown_flavor` toggle.

- [ ] `src/nbfoundry/markdown.py` with `render(text: str, flavor: Literal["commonmark", "gfm"]) -> str`
- [ ] `markdown-it-py` configured for CommonMark; GFM enabled via plugin set
- [ ] Bump version to v0.8.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `render("**bold**", "commonmark")` returns `<p><strong>bold</strong></p>`; GFM-only constructs render only under `gfm`

### Story B.c: v0.9.0 Asset handling [Planned]

BR-5 enumeration, existence checks, and size policy per tech-spec Cross-Cutting.

- [ ] `src/nbfoundry/assets.py` with `enumerate(compiled_outputs) -> list[str]` (sorted, deduplicated)
- [ ] `check_existence(base_dir, paths)` raising `ExerciseError` on missing files (no byte reads — `Path.is_file()` only)
- [ ] `check_size(base_dir, paths, *, warn_mb, max_mb, allow_large)` — warn ≥ `warn_mb`, raise `ExerciseError` ≥ `max_mb` unless `allow_large`
- [ ] Reject paths matching `^https?://`
- [ ] Bump version to v0.9.0
- [ ] Update CHANGELOG.md
- [ ] Verify: enumeration over a fixture with two image outputs (one duplicate) returns 1 entry, sorted

### Story B.d: v0.10.0 Notebook discovery and parsing [Planned]

Marimo notebook entry-point detection, parse, and tree walking per FR-2 / FR-6.

- [ ] `src/nbfoundry/notebooks.py` with `discover_entry(notebook_or_dir) -> Path` (single file → that file; dir → root-of-tree by convention)
- [ ] `parse_all(entry) -> list[ParsedNotebook]` aggregating Marimo parse failures with file/line info into `ExerciseError`
- [ ] No `exec`, no `eval`, no `subprocess` (SC-4)
- [ ] Bump version to v0.10.0
- [ ] Update CHANGELOG.md
- [ ] Verify: a tiny hand-written Marimo notebook parses; a deliberately broken one raises `ExerciseError` naming the file

### Story B.e: v0.11.0 Modelfoundry adapter [Planned]

Thin Protocol adapter per FR-7 / AC-10. Provisional method shape pending modelfoundry's contract.

- [ ] `src/nbfoundry/_modelfoundry.py` with `ModelfoundryAdapter` Protocol (`prepare_data`, `train`, `optimize`, `evaluate`)
- [ ] `get_adapter() -> ModelfoundryAdapter` lazy-imports `modelfoundry`; raises `RuntimeError("modelfoundry is required ...")` with install hint when import fails
- [ ] AST-scan test asserting the compiler core (`compiler.py`, `validator.py`, `schema.py`, `cli.py`) does not import `_modelfoundry`
- [ ] Bump version to v0.11.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `get_adapter()` raises with the expected message in an env where `modelfoundry` is absent

---

## Phase C: Compile and Validate Orchestration

Wire schema + primitives into the production compile/validate pipeline and the standalone artifact emitter. After this phase the spike script from A.c is deleted.

### Story C.a: v0.12.0 Compiler core [Planned]

`compile_exercise()` — FR-3 happy path and first-error semantics.

- [ ] `src/nbfoundry/compiler.py` with `compile_exercise(yaml_path, base_dir, *, allow_large_assets=False) -> dict`
- [ ] Pipeline: path-resolve → `yaml.safe_load` → reject URL-looking scalars → Pydantic validate → resolve `code_file` under `base_dir` → render markdown → enumerate assets → assemble dict in canonical key order
- [ ] No file writes, no network, no module imports beyond declared runtime deps
- [ ] Pydantic `ValidationError` → first `ExerciseError` via `errors.from_pydantic`
- [ ] Re-export `compile_exercise` from `nbfoundry/__init__.py`
- [ ] Delete `scripts/spike_compile_exercise.py` and its fixtures (superseded)
- [ ] Bump version to v0.12.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `from nbfoundry import compile_exercise` works; a minimal hand-written YAML produces a dict with `type=="exercise"`, `source=="nbfoundry"`, `status=="ready"`, `assets==[]`

### Story C.b: v0.13.0 Validator core [Planned]

`validate_exercise()` — FR-4 collect-all-errors mode sharing the C.a pipeline.

- [ ] Refactor C.a's pipeline into a private `_validate(...) -> tuple[Model | None, list[ExerciseError]]` core
- [ ] `compile_exercise` raises on first; `validate_exercise(yaml_path, base_dir) -> list[str]` formats and returns the full list
- [ ] YAML parse failure or missing file short-circuits to a single-element list
- [ ] Re-export `validate_exercise` from `nbfoundry/__init__.py`
- [ ] Bump version to v0.13.0
- [ ] Update CHANGELOG.md
- [ ] Verify: a YAML with three independent rejections returns three error strings, each with file path

### Story C.c: v0.14.0 Submission / BR-4 validation [Planned]

FR-5 enforcement of every §BR-4 validator requirement.

- [ ] Pydantic-driven enforcement of: `pass_threshold ∈ [0.0, 1.0]`, non-empty `fields`, rule/type compat, `weight > 0`, unique `name`, required keys per rule
- [ ] Each rejection produces a human-readable string with the offending field name and value
- [ ] Bump version to v0.14.0
- [ ] Update CHANGELOG.md
- [ ] Verify: a fixture exercising each BR-4 rejection returns a distinct, recognizable error message

### Story C.d: v0.15.0 Aggregate tree compilation [Planned]

FR-6 — a tree of notebooks compiles to a single exercise dict; structure is invisible to learningfoundry.

- [ ] Compiler accepts a YAML whose `sections[i].code_file` references notebooks within a tree
- [ ] Tree-internal references inline via `notebooks.parse_all`
- [ ] Tree-external references rejected by `paths.resolve_under` (FR-3 path-escape)
- [ ] Output dict shape unchanged from single-notebook case
- [ ] Bump version to v0.15.0
- [ ] Update CHANGELOG.md
- [ ] Verify: a 3-notebook tree fixture compiles to one dict whose `sections` reflect the inlined references

### Story C.e: v0.16.0 Standalone artifact emitter [Planned]

FR-2 — `nbfoundry compile <notebook-or-dir>` produces a self-contained runnable directory.

- [ ] `src/nbfoundry/standalone.py` with `compile(notebook_or_dir, out) -> Path`
- [ ] Atomic write: stage into `tempfile.mkdtemp(dir=out.parent)` → `os.replace` on success
- [ ] Emit notebooks, `environment.yml` copy, and `launch.py` (shipped from `templates/standalone/launch.py`)
- [ ] `launch.py` shells out to `marimo edit` against the entry-point notebook
- [ ] Aggregate parse failures with file/line info → `ExerciseError`
- [ ] Bump version to v0.16.0
- [ ] Update CHANGELOG.md
- [ ] Verify: compiling a single hand-written Marimo notebook produces a directory whose `python launch.py` boots Marimo

---

## Phase D: CLI and Library API

User-facing surface: Typer subcommands, global flags, exit codes, and the public library re-exports.

### Story D.a: v0.17.0 CLI scaffold and global flags [Planned]

Typer app shell with shared flags wired to logging and config.

- [ ] Flesh out `src/nbfoundry/cli.py`: Typer app, `--verbose`/`--quiet` → `logging_setup.configure(...)`
- [ ] Each subcommand thin-wraps a library call; maps `ExerciseError` → exit code 1, message on stderr
- [ ] Exit codes: `0` success, `1` `ExerciseError`/validation/parse/asset-oversize, `2` Typer misuse
- [ ] Load `nbfoundry.toml` via `config.load(base_dir)` and merge with parsed flags
- [ ] Bump version to v0.17.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve run nbfoundry --help` lists all four subcommand names; `--version` still prints

### Story D.b: v0.18.0 `nbfoundry init` subcommand [Planned]

FR-1 scaffold from five-stage templates (templates themselves arrive in Phase E; this story validates the wiring against a placeholder template).

- [ ] `init <name> [--template <stage>]` Typer command in `cli.py`
- [ ] Default `--template` to `data_exploration`
- [ ] Use `importlib.resources.files("nbfoundry.templates")` to read template directory
- [ ] Copy template files into `<name>/` under cwd; preserve Apache-2.0 / Pointmatic header
- [ ] Reject existing `<name>` (no overwrite); reject unknown stage
- [ ] Print created path on stdout
- [ ] Add a placeholder `src/nbfoundry/templates/data_exploration/notebook.py` (real five-stage content lands in Phase E)
- [ ] Bump version to v0.18.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve run nbfoundry init demo` creates `demo/` with the template file; rerunning errors

### Story D.c: v0.19.0 `nbfoundry compile` subcommand [Planned]

FR-2 wire-up of `standalone.compile` to the CLI.

- [ ] `compile <notebook-or-dir> [--out <path>]` Typer command
- [ ] Default `--out` from `Config.compile.default_out` (i.e., `dist/`)
- [ ] Print output directory path on success
- [ ] Bump version to v0.19.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve run nbfoundry compile demo/notebook.py` writes to `dist/` and prints the path

### Story D.d: v0.20.0 `nbfoundry compile-exercise` subcommand [Planned]

FR-3 CLI: writes JSON to `--out` if given, else stdout.

- [ ] `compile-exercise <yaml-path> [--base-dir <path>] [--out <path>] [--allow-large-assets]` Typer command
- [ ] Default `--base-dir` to YAML's parent directory
- [ ] Serialize via `json.dumps(d, sort_keys=False, ensure_ascii=False, separators=(",", ": "), indent=2)` for OR-5 stability
- [ ] Atomic write when `--out` is given
- [ ] Bump version to v0.20.0
- [ ] Update CHANGELOG.md
- [ ] Verify: piping output of a fixture run into `python -c "import json,sys;json.load(sys.stdin)"` succeeds

### Story D.e: v0.21.0 `nbfoundry validate` subcommand [Planned]

FR-4 CLI: prints each error on its own line; exit `0` empty, `1` otherwise.

- [ ] `validate <yaml-path> [--base-dir <path>]` Typer command
- [ ] Bump version to v0.21.0
- [ ] Update CHANGELOG.md
- [ ] Verify: validating a YAML with two errors prints two lines on stdout and exits `1`; a clean YAML exits `0` silently

### Story D.f: v0.22.0 Public library API surface [Planned]

Lock down the `from nbfoundry import compile_exercise, validate_exercise, ExerciseError, __version__` contract per OR-2 / AC-1.

- [ ] Tighten `nbfoundry/__init__.py` re-exports, set `__all__`
- [ ] Type-stub the public functions to match BR-1 / BR-2 / BR-3 signatures verbatim
- [ ] Add a public-API smoke test asserting names and signatures
- [ ] Bump version to v0.22.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve run python -c "from nbfoundry import compile_exercise, validate_exercise, ExerciseError, __version__; print(__version__)"` prints `0.22.0`

---

## Phase E: Pinned ML Stack and Five-Stage Templates

Major new integration boundary: the pinned Apple Silicon Metal stack plus the five lifecycle templates that ride on top of it. Phase opens with a spike per the Story Writing Rules.

### Story E.a: v0.23.0 Pinned environment + Metal acceleration spike [Planned]

CR-10 / AC-5 — verified Pyve + micromamba environment with Metal-compatible PyTorch / TensorFlow / Keras / scikit-learn on Python 3.12.13. Validated by a Metal smoke benchmark per PE-4.

- [ ] Author `environment.yml` pinning `python=3.12.13` and the highest stable Metal-compatible versions of PyTorch, TensorFlow (+ `tensorflow-metal` plugin), Keras, scikit-learn, NumPy, SciPy, Matplotlib, Pandas, Marimo
- [ ] Channels: `conda-forge`, `pypi`, with `pytorch` / `apple` channels where they bring stability
- [ ] Document the one-step install in `README.md` ("Apple Silicon quickstart")
- [ ] Add `scripts/metal_smoke.py` running a small training step on each of PyTorch / TensorFlow / Keras and asserting non-trivial GPU/MPS utilization
- [ ] Ship `environment.yml` as package data so `init` and `compile` can copy it
- [ ] Bump version to v0.23.0
- [ ] Update CHANGELOG.md
- [ ] Verify: on a clean Apple Silicon machine, `pyve` + micromamba install reproduces the env; `pyve run python scripts/metal_smoke.py` reports MPS device used for each framework

### Story E.b: v0.24.0 `data_exploration` lifecycle template [Planned]

First real five-stage template; replaces the Phase-D placeholder.

- [ ] `src/nbfoundry/templates/data_exploration/notebook.py` Marimo notebook with reactive cells covering load → describe → visualize
- [ ] Imports modelfoundry primitives only via `_modelfoundry.get_adapter()`
- [ ] Apache-2.0 / Pointmatic header
- [ ] Bump version to v0.24.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve run nbfoundry init demo --template data_exploration && pyve run nbfoundry compile demo/notebook.py` produces a runnable artifact

### Story E.c: v0.25.0 `data_preparation` lifecycle template [Planned]

- [ ] `src/nbfoundry/templates/data_preparation/notebook.py` with cleaning / feature engineering / split scaffolding
- [ ] Apache-2.0 / Pointmatic header
- [ ] Bump version to v0.25.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve run nbfoundry init demo --template data_preparation` succeeds and the resulting notebook runs end-to-end on Apple Silicon

### Story E.d: v0.26.0 `model_experimentation` lifecycle template [Planned]

- [ ] `src/nbfoundry/templates/model_experimentation/notebook.py` with model definition / training loop / metric capture scaffolding
- [ ] Apache-2.0 / Pointmatic header
- [ ] Bump version to v0.26.0
- [ ] Update CHANGELOG.md
- [ ] Verify: scaffolded template trains a small model on MPS with sub-second per-epoch time

### Story E.e: v0.27.0 `model_optimization` lifecycle template [Planned]

- [ ] `src/nbfoundry/templates/model_optimization/notebook.py` with hyperparameter search / pruning / quantization scaffolding
- [ ] Apache-2.0 / Pointmatic header
- [ ] Bump version to v0.27.0
- [ ] Update CHANGELOG.md
- [ ] Verify: scaffolded template runs a parameter sweep producing a results table

### Story E.f: v0.28.0 `model_evaluation` lifecycle template [Planned]

- [ ] `src/nbfoundry/templates/model_evaluation/notebook.py` with held-out evaluation / confusion matrix / calibration scaffolding
- [ ] Apache-2.0 / Pointmatic header
- [ ] Bump version to v0.28.0
- [ ] Update CHANGELOG.md
- [ ] Verify: scaffolded template emits an evaluation report; AC-4 (all five templates scaffold and run) is satisfied

---

## Phase F: Testing, Quality, and Documentation

Hardening: fixtures, comprehensive test suite, type strictness, coverage target, and docs polish.

### Story F.a: v0.29.0 Test fixtures [Planned]

Establish the fixture corpus that downstream test stories consume.

- [ ] `tests/fixtures/exercises/valid_minimal.yaml` — smallest passing exercise
- [ ] `tests/fixtures/exercises/valid_graded.yaml` — full BR-4 submission block
- [ ] `tests/fixtures/exercises/valid_with_assets.yaml` — image expected_outputs (path-only, BR-5)
- [ ] One `invalid_<reason>.yaml` per validator rejection (named per `tech-spec.md` Testing Strategy)
- [ ] `tests/fixtures/exercises/tree/` — multi-notebook tree fixture
- [ ] `tests/fixtures/golden/valid_graded.json` — TR-2 byte-for-byte golden
- [ ] `tests/conftest.py` shared fixtures: `tmp_base_dir`, `sample_yaml`, `golden_dict`
- [ ] Bump version to v0.29.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test tests/fixtures/` discovers fixture files; conftest fixtures importable from a smoke test

### Story F.b: v0.30.0 Unit test sweep [Planned]

TR-1 / TR-8 — exhaustive unit coverage of the public API and primitives.

- [ ] `tests/unit/test_schema.py` — every Pydantic accept/reject permutation; BR-4 rule/type matrix
- [ ] `tests/unit/test_compiler.py` — FR-3 happy path; markdown rendering; code/code_file mutual exclusion
- [ ] `tests/unit/test_validator.py` — collects all errors; YAML-parse short-circuit
- [ ] `tests/unit/test_assets.py` — BR-5 enumeration; missing-asset rejection; size warn/error thresholds; `--allow-large-assets`
- [ ] `tests/unit/test_paths.py` — SC-3: `..`, absolute, symlinks, mixed separators
- [ ] `tests/unit/test_errors.py` — `ExerciseError` shape; Pydantic → ExerciseError mapping
- [ ] `tests/unit/test_modelfoundry_adapter.py` — raises when missing; AST-scan asserts compiler core does not import the adapter
- [ ] `tests/unit/test_config.py` — precedence; missing toml; bad keys
- [ ] `tests/unit/test_markdown.py` — commonmark vs gfm divergence
- [ ] Bump version to v0.30.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test tests/unit/` passes

### Story F.c: v0.31.0 Integration test sweep [Planned]

TR-2 / TR-3 / OR-5 / AC-9 — end-to-end behaviors via the CLI and library surface.

- [ ] `tests/integration/test_cli_init.py` — scaffolds each of the five templates
- [ ] `tests/integration/test_cli_compile.py` — standalone artifact end-to-end
- [ ] `tests/integration/test_cli_compile_exercise.py` — JSON to stdout / `--out`
- [ ] `tests/integration/test_cli_validate.py` — exit codes
- [ ] `tests/integration/test_determinism.py` — two runs produce byte-identical JSON
- [ ] `tests/integration/test_no_network.py` — monkey-patched `socket.socket.connect` raises; compile/validate succeed
- [ ] `tests/integration/test_aggregate_tree.py` — tree → single dict; tree-external references reject
- [ ] `tests/integration/test_schema_fidelity.py` — `valid_graded.yaml` round-trips to `valid_graded.json` byte-for-byte (modulo path normalization)
- [ ] Bump version to v0.31.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test tests/integration/` passes; AC-9 sandbox test fails-closed if a network call sneaks in

### Story F.d: v0.32.0 mypy --strict pass [Planned]

QR-4 / TR-5 — strict typing across the whole package.

- [ ] Configure `[tool.mypy]` in `pyproject.toml` with `strict = true`, `mypy_path = "src"`, `packages = ["nbfoundry"]`
- [ ] Resolve every strict-mode error in `src/nbfoundry/`
- [ ] Add `types-PyYAML` (already in `requirements-dev.txt`); add any further `types-*` stubs the strict pass surfaces
- [ ] Bump version to v0.32.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve testenv run mypy src/nbfoundry/` reports zero errors

### Story F.e: v0.33.0 Coverage target ≥85% [Planned]

TR-6 — `pytest-cov --cov-fail-under=85` on `nbfoundry` public modules.

- [ ] Configure `[tool.pytest.ini_options]` with `--cov=nbfoundry --cov-report=term-missing --cov-fail-under=85`
- [ ] Exclude `src/nbfoundry/templates/**` and `src/nbfoundry/templates/standalone/launch.py` via `[tool.coverage.run] omit = [...]`
- [ ] Add tests to close any gaps surfaced by the report
- [ ] Bump version to v0.33.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test` passes with coverage gate satisfied; the report shows ≥85% on public modules

### Story F.f: Documentation polish [Planned]

Doc-only — no version bump; ships under v0.33.0.

- [ ] Expand `README.md` with: install, scaffold, compile, embed-into-learningfoundry quickstart; AC-3 two-surface demonstration
- [ ] Cross-link `concept.md`, `features.md`, `tech-spec.md`, `learningfoundry-dependency-spec.md`
- [ ] Update `CHANGELOG.md` with documentation entry under `0.33.0`
- [ ] Verify: a fresh reader following only `README.md` on Apple Silicon can scaffold and compile a template within UR-3's "minutes" budget

---

## Phase G: CI/CD and Release

Automation. Per project direction: PyPI publish first; lint/test CI added later; coverage badge precedes the v1.0.0 production release.

### Story G.a: v0.34.0 PyPI publish workflow [Planned]

Manual-tag → automated-build → trusted-publish pipeline; the only CI in place initially per project direction.

- [ ] `.github/workflows/publish.yml` triggered on `v*` tag push
- [ ] Build sdist + wheel via `hatch build`
- [ ] Trusted publishing via PyPI OIDC (no long-lived tokens)
- [ ] Document tag-and-release procedure in `README.md`
- [ ] Bump version to v0.34.0
- [ ] Update CHANGELOG.md
- [ ] Verify: tagging `v0.34.0` triggers the workflow and the package appears on PyPI under `nbfoundry`

### Story G.b: v0.35.0 CI lint + test workflow [Planned]

Added later per project direction — runs `ruff`, `mypy`, and `pytest` on every push and PR.

- [ ] `.github/workflows/ci.yml` triggered on push and pull_request
- [ ] Matrix: macOS-latest (Apple Silicon runner) primary; ubuntu-latest stretch
- [ ] Steps: install pyve + testenv, `ruff check`, `ruff format --check`, `mypy src/nbfoundry/`, `pyve test`
- [ ] Cache the testenv to keep CI under a few minutes
- [ ] Status badges in `README.md` for the `ci` workflow
- [ ] Bump version to v0.35.0
- [ ] Update CHANGELOG.md
- [ ] Verify: a deliberately broken commit fails CI; a clean commit passes on both runners

### Story G.c: v0.36.0 Coverage badge [Planned]

Code coverage reporting + README badge — required before the v1.0.0 production release per project direction.

- [ ] Add coverage upload step to `ci.yml` (Codecov or Coveralls; default Codecov)
- [ ] Add coverage badge to `README.md` header
- [ ] Document the coverage gate in `CONTRIBUTING.md` (or README dev section)
- [ ] Bump version to v0.36.0
- [ ] Update CHANGELOG.md
- [ ] Verify: a CI run uploads coverage and the README badge resolves to a current percentage

### Story G.d: v1.0.0 Production release [Planned]

Cut the stable, production-quality, feature-complete release per the versioning rule in `tech-spec.md` and the v1 acceptance criteria AC-1..AC-10.

- [ ] Walk every AC-1..AC-10 in `features.md` and confirm each is satisfied
- [ ] Final `CHANGELOG.md` entry under `1.0.0` summarizing the v1 surface
- [ ] Update `README.md` to remove pre-1.0 caveats
- [ ] Bump version to v1.0.0
- [ ] Tag `v1.0.0`; `publish.yml` ships the release to PyPI
- [ ] Verify: `pip install nbfoundry==1.0.0` from PyPI on a clean Apple Silicon machine; `nbfoundry init`, `compile`, `compile-exercise`, and `validate` all run successfully against the documented sample

---

## Future

<!--
This section captures items intentionally deferred from the active phases above:
- Stories not yet planned in detail
- Phases beyond the current scope
- Project-level out-of-scope items
The `archive_stories` mode preserves this section verbatim when archiving stories.md.
-->

- **Marimo WASM (Option A) embed surface** — deferred per concept.md Scope and features.md NG-2; revisit post-v1 when the in-browser execution path becomes worthwhile.
- **Modelfoundry contract finalization** — when modelfoundry's interface is published, harden `_modelfoundry.py` from the provisional Protocol to the real signatures; pin `nbfoundry[modelfoundry]` extra in `pyproject.toml`.
- **Windows CI** — out of v1 cross-platform scope (QR-3 limits CI to macOS primary, Linux stretch).
- **Concurrency / parallel parse** — `notebooks.parse_all` parallelization via `concurrent.futures` if curriculum-scale performance bites (tech-spec.md Performance).
- **Pre-commit hooks** — declined for v1 (tech-spec.md Runtime & Tooling); reconsider if CI-gates-only causes friction.
- **CUDA/Linux acceleration tuning** — best-effort only in v1 (NG-9); promote if user demand warrants.
- **Non-ML/DS exercise flavors** — owned by other tools (NG-8); not an nbfoundry concern.
- **Hosted runtime / managed cloud** — out of scope (NG-4); local-first is the v1 contract.
