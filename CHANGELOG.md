# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.47.0] - 2026-06-20

### Added
- Optional per-section `hide_code` flag in the `ExerciseDefinition` schema (Story I.g). When a section sets `hide_code: true`, `codegen.generate` emits that section's code cell as `@app.cell(hide_code=True)` instead of `@app.cell` — marimo's hidden-code state, so the learner sees the cell's output but not its source. Default `false` (code visible); the markdown description cell and byte-stable output for unflagged sections are unchanged. Additive and backward-compatible: existing definitions without `hide_code` produce identical `notebook_source`.

### Documentation
- Documented `hide_code` in [README.md](README.md) (`compile-exercise` section), [features.md](docs/specs/features.md) (Inputs), and [tech-spec.md](docs/specs/tech-spec.md) (`SectionModel`).

## [0.46.0] - 2026-06-18

**Phase I — LearningFoundry Integration Refactoring.** Migrates `compile_exercise` from the LearningFoundry Option-B (static-display) contract to Option C (banner + `learningfoundry launch` + notebook-emit). The compiled exercise dict is now an 8-key wire shape whose `notebook_source` field is itself a self-contained `marimo.App()` module the learner runs locally; the previous static-display fields (sections / expected_outputs / submission / assets / status / instructions) are gone. **This is a breaking output-shape change** — any consumer reading the v0.45.0 dict will see different keys after upgrading.

### Added
- `src/nbfoundry/codegen.py` (Story I.c): `generate(defn, base_dir) -> str` emits a self-contained `marimo.App()` module string from an `ExerciseDefinition`. Cell layout: one header cell + per-section `mo.md(...)` markdown cell + code cell. Framework imports (`import torch`, etc.) appear only as **source text** inside emitted cells; `codegen.py` imports no ML framework. Sibling helper `ensure_marimo_pinned(env)` appends `marimo>=<importlib.metadata.version("marimo")>` to `environment.dependencies` when the author omitted it, preserves existing marimo entries (including `marimo[lsp]>=…`), and does not misidentify lookalike package names. Byte-stable output (cross-process SHA-identical).
- `notebook_source` field in the `compile_exercise` dict — a complete `marimo.App()` module as a string; `learningfoundry launch <id>` materializes it on the learner's machine and spawns `marimo edit` against it.
- Option-C input schema (Story I.b): `ExerciseDefinition` (`title`, `description`, `sections[]`, optional `hints[]` markdown, optional `environment`) and `SectionModel` (`title`, `description`, `code` XOR `code_file`); Pydantic v2 with `extra="forbid"` rejects unknown fields including the retired Option-B keys.
- `tests/unit/test_build_time_purity.py` (Story I.e): authoritative parametrized AST scan over every module on the build-time compile path (`__init__.py`, `schema.py`, `compiler.py`, `codegen.py`, `cli.py`, `config.py`, `errors.py`, `logging_setup.py`, `markdown.py`, `notebooks.py`, `paths.py`, `standalone.py`) asserting that none imports `torch`, `tensorflow`, `keras`, `transformers`, `datasets`, `peft`, `sentencepiece`, `tiktoken`, `optuna`, `modelfoundry`, or `datarefinery`. Sibling test asserts none of those modules imports the `_modelfoundry.py` lazy-import boundary either.
- `tests/integration/test_marimo_loads_generated.py` (Story I.e): loads the compiled `notebook_source` via `importlib.util.spec_from_file_location` and asserts a top-level `marimo.App` instance — no subprocess, no marimo server, no ML deps.
- Option-C test fixtures: `tests/fixtures/exercises/valid_minimal.yaml` and `tests/fixtures/exercises/tree/exercise.yaml` + `tree/sections/{load,summarize}.py` (exercises `code_file` inlining). `tests/fixtures` excluded from `ruff` (`[tool.ruff] extend-exclude`) — the snippet files are intentionally cross-cell-stateful for marimo.
- "Retired in v0.46.0" subsection in [features.md](docs/specs/features.md) documenting BR-4 (graded submission), BR-5 (image assets), the retired wire fields, and the `editable` per-section flag, with a note that BR-1/BR-2/BR-3 are intentionally not renumbered.

### Changed (BREAKING)
- **`compile_exercise(yaml_path, base_dir) -> dict` returns the Option-C wire shape** (Story I.d): exactly 8 keys — `{type: "exercise", source: "nbfoundry", ref, title, description, hints, environment, notebook_source}`. `description` and each `hints[i]` are rendered HTML (markdown source from the YAML run through `markdown-it-py` per the `markdown_flavor` toggle). `environment` is `None` when the author omitted it; otherwise a `CompiledEnvironment` TypedDict with a guaranteed `marimo` pin in `dependencies`.
- **`compile_exercise` signature dropped the `allow_large_assets` kwarg** — the gate is meaningless once assets are gone.
- **`nbfoundry compile-exercise` CLI dropped the `--allow-large-assets` flag** — same reason.
- `validate_exercise(yaml_path, base_dir) -> list[str]` now validates against `ExerciseDefinition` (Option-C shape) and returns all errors with collect-all semantics; YAML parse / missing-file / non-mapping-top-level short-circuits unchanged. `validate_exercise` lives in `compiler.py` (no separate `validator.py`).
- The compile path no longer runs `notebooks.parse_all` on `code_file` references — under Option C those are plain code snippets inlined into a marimo cell, not whole marimo notebooks. Python / marimo syntax is evaluated at notebook run time on the learner's machine.
- All four specs reconciled to Option C: [features.md](docs/specs/features.md) (Stories I.f.2), [tech-spec.md](docs/specs/tech-spec.md) (I.f.3), [concept.md](docs/specs/concept.md) (I.f.4), [README.md](README.md) (I.f.5). The LearningFoundry consumer dependency-spec link target moved from `docs/specs/learningfoundry/dependency-spec.md` to `docs/specs/learningfoundry/consumer-dependency-spec.md` in all four places.

### Removed (BREAKING)
- `src/nbfoundry/assets.py` (Story I.d) — image-asset enumeration, existence checks, size policy. The notebook renders its own outputs at run time; LearningFoundry no longer stages binary assets.
- `AssetsConfig` from `src/nbfoundry/config.py` (Story I.f.1) — `max_single_asset_mb`, `warn_single_asset_mb`, `allow_large_assets`. Also dropped the `[assets]` TOML section parse and the assets-group `merge_cli(...)` branch.
- Option-B schema models from `src/nbfoundry/schema.py` (Story I.b): `RawSectionModel`, `RawExerciseModel`, `RawExpectedOutputModel`, `ExpectedRule`, `SubmissionFieldModel`, `SubmissionModel`, `CompiledSection`, `CompiledExpectedImage`, `CompiledExpectedTextOrTable`, `CompiledExpectedOutput`, `CompiledSubmissionField`, `CompiledSubmission`. The per-section `editable` flag is gone — cell editability is LearningFoundry's `ExerciseBlock` concern under Option C.
- Wire-shape fields retired from the `compile_exercise` dict: `status`, `instructions`, `sections[]`, `expected_outputs[]`, `assets[]`, `submission`. The new shape has `description` (HTML) + `hints` (HTML list) + `notebook_source` (marimo module string) instead.
- BR-4 (graded submission schema with `pass_threshold` / `fields[]` / `expected` rules) and BR-5 (image-asset enumeration with `expected_outputs[i] of type: image`) are retired in the consumer dependency spec; see [features.md § "Retired in v0.46.0"](docs/specs/features.md). Graded submission is parked as a future marimo-cell-output concern in [stories.md § Future](docs/specs/stories.md).
- Option-B test files and fixtures (Story I.e): 11 retired test files under `tests/unit/` and `tests/integration/` (`test_assets.py`, `test_fixtures_corpus.py`, `test_aggregate_tree.py`, `test_schema_fidelity.py`, the legacy `test_compiler.py` / `test_validator.py` / `test_schema.py` / etc.); the `tests/fixtures/golden/` directory; 14 retired `*.yaml` corpus files; `tests/fixtures/exercises/assets/`; the Option-B `tree/notebooks/` (FR-6 multi-notebook tree).

### Documentation
- All four specs (features / tech-spec / concept / README) now describe the Option-C contract end-to-end with consistent vocabulary and a single shared link target (`learningfoundry/consumer-dependency-spec.md`).
- [Phase I plan](docs/specs/phase-i-learningfoundry-integration-refactoring-plan.md) carries a "Story I.a — Spike Findings" section documenting the cell-emission pattern, the marimo-version sourcing strategy, and one open design question for downstream codegen work (reactive dataflow between author-supplied code cells, intentionally deferred to a future story).

### Migration notes (for v0.45.0 consumers)
- The `compile_exercise` return-dict shape is **different**. Code reading `dict["sections"]`, `dict["expected_outputs"]`, `dict["assets"]`, `dict["submission"]`, `dict["status"]`, or `dict["instructions"]` will see `KeyError` after upgrading. Read `dict["notebook_source"]` (the marimo module to run) and the banner metadata (`title` / `description` / `hints` / `environment`) instead.
- Exercise YAML inputs must use the new `ExerciseDefinition` shape: drop top-level `expected_outputs`, `submission`, and the per-section `editable` flag. `ExerciseDefinition`'s `extra="forbid"` will reject the legacy keys with a clear error.
- The `compile_exercise(...)` Python call drops `allow_large_assets=True`; the CLI's `--allow-large-assets` flag is gone. Existing YAMLs that referenced large images via the retired `expected_outputs[i]` of `type: image` should remove those entries — the learner notebook now renders its own outputs at run time.

## [0.45.0] - 2026-06-15

### Added
- Coverage reporting to Codecov (Story H.b): `pyve test` now also writes `coverage.xml` (`--cov-report=xml` added to `pyproject.toml` `addopts`), and [.github/workflows/ci.yml](.github/workflows/ci.yml) uploads it via `codecov/codecov-action@v5` from the macOS primary leg only (single source of truth; `fail_ci_if_error: false` so reporting never gates the build). Works tokenless on the public repo; a `CODECOV_TOKEN` secret makes uploads reliable/rate-limit-free.
- Coverage badge in [README.md](README.md) header.
- [CONTRIBUTING.md](CONTRIBUTING.md): development setup, the four quality gates, and the ≥85% coverage gate (including the single-file `--no-cov` caveat).

## [0.44.0] - 2026-06-15

### Added
- CI workflow [.github/workflows/ci.yml](.github/workflows/ci.yml) (Story H.a): runs on every push and pull request across a `macos-latest` (Apple Silicon, primary) + `ubuntu-latest` (stretch, non-blocking) matrix. Steps bootstrap the project and dev environment with **pyve**, then run `ruff check`, `ruff format --check`, `mypy --strict`, and `pyve test` (with the coverage gate). Materialized `.pyve` environments are cached, keyed on the dependency manifests + the pinned pyve release.
- CI status badge in [README.md](README.md).

### Changed
- CI installs pyve by cloning the pinned release (`PYVE_REF`, `v3.0.7`) and running `pyve.sh self install` to `~/.local/bin`, bypassing Homebrew and the (name-conflicting) PyPI package. This keeps **one idiom** — CI runs the same `pyve` commands as local development — while staying reproducible and tap-independent. (The repo entry point is `pyve.sh` at the root; the `bin/pyve` wrapper only exists in the Homebrew layout. `self install` requires pyve ≥ v3.0.7, which fixed a v3.0.6 bug where the installer omitted `lib/ui/` and produced a broken install.)
- CI provides Python via **pyenv**, not `setup-python`: pyve's venv backend provisions the interpreter through a version manager (asdf/pyenv) — absent on GitHub runners — so CI installs pyenv and compiles the project Python (`3.12.13`, cached under `~/.pyenv`). `pyve init` is then run non-interactively (`PYVE_INIT_NONINTERACTIVE=1`, `--backend venv --python-version 3.12.13 --no-project-guide --no-direnv`); because that exact version is already installed, pyve uses it directly (no prompt, no per-run compile). The pin is `3.12.13` because the package requires `>=3.12.13,<3.14`, so pyve's default (3.14.x) would fail `pip install -e .`.
- Reformatted [src/nbfoundry/cli.py](src/nbfoundry/cli.py), [src/nbfoundry/compiler.py](src/nbfoundry/compiler.py), and [src/nbfoundry/config.py](src/nbfoundry/config.py) to satisfy `ruff format --check` (pure formatting; no behavior change), so the new format-check gate passes on a clean tree.

## [0.43.0] - 2026-06-15

### Added
- **Coverage gate ≥85%** (Story G.e, TR-6). `[tool.pytest.ini_options] addopts` now includes `--cov=nbfoundry --cov-report=term-missing --cov-fail-under=85`, with `[tool.coverage.run] omit` excluding the author notebook templates + embedded launcher (mirroring the ruff/mypy template excludes). Public-module coverage is **94.57%**.
- `tests/unit/test_notebooks.py`: discovery + parse coverage for `notebooks.py` (entry-point resolution: file / conventional `notebook.py` / single-`.py` / ambiguous / nonexistent; `parse_all`: single file, directory, syntax-error rejection) — lifting the weakest module from 65% to 92%.

### Note
- Because `--cov-fail-under` is in the default `addopts`, a single-file `pyve test <one_file>` run will under-report total coverage and fail the gate; pass `--no-cov` for focused single-file runs.

### Documentation
- Expanded `README.md` (Story G.f): replaced the stale "CLI lands across Phase D" placeholder with a real four-command quickstart (`init` / `compile` / `compile-exercise` / `validate`), an example exercise YAML, and the AC-3 two-surface demonstration (one notebook source → standalone app **and** embeddable exercise). Added a "Further reading" cross-link block (concept / features / tech-spec / learningfoundry dependency-spec / env-dependencies) and refreshed the dev-setup commands to the non-deprecated `pyve env` forms. All documented commands were dogfooded end-to-end.

## [0.42.0] - 2026-06-15

### Changed
- **`mypy --strict` now passes clean on nbfoundry's typed surface** (Story G.d, QR-4/TR-5). Added a `templates/` exclude to `[tool.mypy]` (`exclude = '^src/nbfoundry/templates/'`, mirroring `[tool.ruff] extend-exclude`) so the author notebook scaffolds — ML example code with intentional unannotated marimo cells — are not strict-typed; their correctness is covered by the F.h–F.j template smokes. The typecheck stays ML-free and runs in the light `testenv`.
- Resolved the two real strict-mode errors that the exclude surfaced on the package modules:
  - [markdown.py](src/nbfoundry/markdown.py): annotate the `markdown_it` render result (`html: str = …`) before `.rstrip()` to fix `no-any-return`.
  - Added a `[[tool.mypy.overrides]]` for the optional, stub-less `modelfoundry` import (`ignore_missing_imports = true`) — it is reached only through the `_modelfoundry.get_adapter()` adapter and is not installed.

## [0.41.0] - 2026-06-14

### Added
- **Integration test sweep** (Story G.c, TR-2/TR-3/OR-5/AC-9) — eight modules exercising the CLI + library surface end-to-end:
  - `test_cli_init.py` — scaffolds each of the five templates (+ default template, unknown-template error, existing-path error).
  - `test_cli_compile.py` — standalone artifact emits `notebook.py` + `launch.py` + `requirements-base.txt` (no `environment.yml`); refuses existing output.
  - `test_cli_compile_exercise.py` — JSON to stdout; `--out` writes a file; invalid input exits non-zero.
  - `test_cli_validate.py` — exit 0/clean on valid, exit 1 with errors on invalid, all errors reported.
  - `test_determinism.py` — repeated and fresh-base compiles are byte-stable (OR-5).
  - `test_no_network.py` — socket-level sandbox (`socket.socket.connect`/`connect_ex` patched to raise) fails closed, and `compile_exercise`/`validate_exercise` succeed under it (AC-9/SC-2).
  - `test_aggregate_tree.py` — a notebook-tree exercise compiles to a single dict with tree-internal notebooks inlined; a tree-external (`..`) reference is rejected (FR-6).
  - `test_schema_fidelity.py` — `valid_graded.yaml` compiles to `golden/valid_graded.json` both as a dict and byte-for-byte via the CLI `--out` path (TR-2/QR-5).

## [0.40.0] - 2026-06-14

### Added
- **Unit test sweep** (Story G.b, TR-1/TR-8) — nine modules under `tests/unit/`, ~70 new tests covering the public API and primitives:
  - `test_schema.py` — every Pydantic accept/reject permutation + the full BR-4 rule/type compatibility matrix (range/equals/contains_all × number/text), weight positivity, pass_threshold bounds, duplicate-field detection.
  - `test_compiler.py` — `compile_exercise` happy-path wire shape, markdown rendering, code_file inlining, section-indexed errors, asset enumeration.
  - `test_validator.py` — `validate_exercise` collect-all semantics, empty-on-valid, YAML-parse / non-mapping / missing-file short-circuits.
  - `test_assets.py` — BR-5 enumeration (sorted/unique/image-only), missing-asset + URL rejection, size warn/error thresholds, `allow_large` bypass.
  - `test_paths.py` — SC-3 path-escape: absolute, `..`, symlink-escape, mixed-separator, nonexistent.
  - `test_errors.py` — `ExerciseError` / `ErrorDetail` string shapes; `from_pydantic` loc→pointer/section-index mapping + scalar-input augmentation.
  - `test_config.py` — defaults, toml load, CLI>toml>defaults precedence, unknown-key tolerance, `merge_cli` None-skip.
  - `test_markdown.py` — commonmark vs gfm divergence (tables, strikethrough) + rstrip.
  - `test_modelfoundry_adapter.py` — extended: `get_adapter` returns the module when importable, and the Protocol is runtime-checkable (in addition to the existing raises-when-missing + AST no-import-in-core checks).

## [0.39.0] - 2026-06-14

### Added
- **Test fixture corpus** under `tests/fixtures/` (Story G.a, start of Phase G) — the shared inputs the G.b/G.c sweeps consume:
  - Valid exercises: `valid_minimal.yaml`, `valid_graded.yaml` (full BR-4 submission: all three rule types, both field types, weight/placeholder, plus text expected-output, hints, environment), `valid_with_assets.yaml` (image expected-output, BR-5) + a real 1×1 `assets/plot.png`.
  - 12 `invalid_<reason>.yaml` fixtures, one per validator rejection (missing title, unknown key, empty sections, code/code_file XOR, image-missing-alt, pass_threshold out of range, duplicate field name, range-rule-on-text-field, YAML syntax error, top-level-not-mapping, missing asset, SC-3 path escape).
  - `tree/` multi-notebook fixture (FR-6): an exercise YAML pulling section code from two tree-internal marimo notebooks.
  - `golden/valid_graded.json` — byte-for-byte golden generated from the real compiler (TR-2).
  - `tests/conftest.py` shared fixtures: `tmp_base_dir` (writable copy of the corpus as a compile base), `sample_yaml`, `golden_dict` (+ `fixtures_dir`/`exercises_dir` helpers).
- `tests/unit/test_fixtures_corpus.py`: G.a verify smoke — asserts the corpus is real (valid fixtures compile clean, all invalid fixtures reject, the tree inlines, and `compile_exercise(sample_yaml)` equals the golden) and the conftest fixtures are usable.

## [0.38.0] - 2026-06-14

### Changed
- **Reshaped the `model_evaluation` template from a PyTorch example to a scikit-learn example** ([src/nbfoundry/templates/model_evaluation/notebook.py](src/nbfoundry/templates/model_evaluation/notebook.py)). Evaluation is the most framework-agnostic stage — the metrics (`classification_report`, `confusion_matrix`, `calibration_curve`) operate on plain `y_true`/`y_pred`/`y_prob` arrays — so the example model is now a `LogisticRegression` rather than a torch NN. The eval cells are unchanged; only the model/predict cells differ. This keeps the template (and its smoke) light, hardware-free, and CI-runnable, and better embodies the "evaluation doesn't bind to a framework" contract.
- `model_evaluation` now maps to `requirements-base.txt` (no torch) instead of `requirements-torch.txt` in the scaffolder ([cli.py](src/nbfoundry/cli.py) `_STAGE_REQUIREMENTS`); docs (tech-spec stage table, stories F.f.4 mapping) updated to match.

### Added
- model_evaluation template end-to-end smoke at [tests/integration/test_e2e_template_model_evaluation.py](tests/integration/test_e2e_template_model_evaluation.py): scaffolds the template via `nbfoundry init`, runs the generated marimo notebook end-to-end (`app.run()`), and asserts the held-out evaluation → confusion matrix → calibration flow (a fitted `LogisticRegression`, a 2×2 confusion matrix covering all 256 held-out rows, a confusion-matrix `Figure`, a calibration `Figure`, and a sane accuracy). Runs in the default `testenv`, no `@pytest.mark.hardware`.

### Note
- This completes Phase F. The phase-level acceptance check in `stories.md` was refreshed off the deleted conda `environment.yml` / micromamba flow onto the per-stage venv/pip path.

## [0.37.0] - 2026-06-14

### Added
- data_preparation template end-to-end smoke at [tests/integration/test_e2e_template_data_preparation.py](tests/integration/test_e2e_template_data_preparation.py): scaffolds the template via `nbfoundry init`, runs the generated marimo notebook end-to-end (`app.run()`), and asserts the clean → engineer → split flow produces clean stratified splits (200 → 190 after NaN drop; 152/38 train/test; one-hot + interaction features; both label classes present in each split).
- `scikit-learn` added to the template-smoke deps in [requirements-dev.txt](requirements-dev.txt) (the template's split cell uses `sklearn.model_selection.train_test_split`).

## [0.36.0] - 2026-06-14

### Added
- data_exploration template end-to-end smoke at [tests/integration/test_e2e_template_data_exploration.py](tests/integration/test_e2e_template_data_exploration.py): scaffolds the template via `nbfoundry init`, runs the generated marimo notebook end-to-end (`app.run()`), and asserts the load → describe → visualize flow produces its outputs (synthetic 200×3 DataFrame, `describe()` summary, 3-class label balance, and a matplotlib `Figure`). Also checks the scaffolder emits `requirements-base.txt`. This is the first smoke that exercises the packaged template + `nbfoundry init` surface.
- Framework-agnostic template-smoke deps (`numpy`, `pandas`, `matplotlib`) added to [requirements-dev.txt](requirements-dev.txt).

### Note
- **Env/marker decision (F.h gate):** the framework-agnostic template smokes (F.h–F.j) run in the default `testenv` with **no** `@pytest.mark.hardware` — they execute on every `pyve test` run and in CI, rather than in a per-framework smoke env. They are pure-CPU and need no Metal hardware.

## [0.35.0] - 2026-06-14

### Added
- Optuna hyperparameter-search end-to-end happy-path smoke at [tests/integration/test_e2e_optuna.py](tests/integration/test_e2e_optuna.py): one hardware-gated test (`test_optuna_study_optimizes_a_torch_mps_model`) that runs a 5-trial Optuna study whose objective trains a tiny PyTorch dense classifier on the MPS device (tuning `lr` + `hidden`), then asserts all 5 trials complete, `study.best_trial` is populated, and `best_value` matches the minimum recorded objective.
- `optuna` added to the `smoke-torch` dev requirements ([tests/integration/env/torch.txt](tests/integration/env/torch.txt)); Optuna is pure-Python and rides the torch family, so no new env (per `env-dependencies.md` §6).

### Note
- Hardware verification (`pyve test --env smoke-torch tests/integration/test_e2e_optuna.py -m hardware` on Apple Silicon) is deferred to developer hardware; the test is deselected by the default `-m 'not hardware'`.

## [0.34.3] - 2026-06-14

### Changed
- **The learner-facing stack is now exclusively venv/pip — conda/micromamba fully eliminated.** The bundled conda manifest `src/nbfoundry/templates/environment.yml` is replaced by three composable per-stage pip requirements files shipped as package data:
  - [requirements-base.txt](src/nbfoundry/templates/requirements-base.txt) — framework-agnostic core (`data_*` stages).
  - [requirements-torch.txt](src/nbfoundry/templates/requirements-torch.txt) — torch-family stack (`model_*` stages); `-r`-includes the base.
  - [requirements-tf.txt](src/nbfoundry/templates/requirements-tf.txt) — TensorFlow-family option; `-r`-includes the base.
- `nbfoundry init` now emits the **stage-appropriate** requirements file(s) (`requirements-base.txt` for `data_*`, `requirements-torch.txt` + base for `model_*`) instead of the shared `environment.yml` ([cli.py](src/nbfoundry/cli.py) `_emit_stage_requirements`). The per-stage split makes the F.f.1 torch+TF co-residence SIGBUS impossible by construction for learners — the two frameworks are never co-installed.
- `nbfoundry compile` now emits venv/pip requirements into the standalone artifact (preserving any `requirements*.txt` the source ships, falling back to `requirements-base.txt`) instead of `environment.yml` ([standalone.py](src/nbfoundry/standalone.py) `_ensure_requirements`).
- `EnvironmentConfig.spec_path` default changed `environment.yml` → `requirements-base.txt` ([config.py](src/nbfoundry/config.py)).
- Reversed the micromamba constraint across the foundational specs (`concept.md`, `features.md` CR-10/QR-1/AC-5/PE-3, `tech-spec.md` env-management + Pinned ML stack, `README.md` quickstart): Pyve + micromamba → Pyve + venv.

### Removed
- `src/nbfoundry/templates/environment.yml` (the conda bundled payload) and `conda-lock` from the stack.
- `scripts/metal_smoke.py` and `tests/unit/test_metal_smoke.py` — the full-stack micromamba diagnostic is retired in favor of the named smoke envs (`smoke-torch` / `smoke-tensorflow`), which validate each framework on Metal via pytest (Story F.f.4 decision: retire over rework).

## [0.34.2] - 2026-06-14

### Added
- Per-framework smoke-env pip requirements for the Pyve v3.0.6 named test environments declared in `pyve.toml`:
  - [tests/integration/env/torch.txt](tests/integration/env/torch.txt) — the `smoke-torch` torch-family env (`torch` + `transformers`/`datasets`/`peft` + tokenizer deps + `numpy`/`pytest`); serves the F.d PyTorch, F.f HuggingFace, and (later) F.g Optuna smokes. No TensorFlow / standalone keras.
  - [tests/integration/env/tensorflow.txt](tests/integration/env/tensorflow.txt) — the `smoke-tensorflow` TensorFlow-family env (`tensorflow-macos`/`tensorflow-metal` + `numpy`/`pytest`); serves the F.c TensorFlow and F.e Keras smokes. No torch/HuggingFace/standalone keras.
- [tests/unit/test_smoke_env_requirements.py](tests/unit/test_smoke_env_requirements.py): hardware-independent regression tests locking the env-isolation invariants — torch.txt never declares TensorFlow/keras (F.f.1 co-residence boundary), tensorflow.txt never declares torch/HuggingFace/standalone keras (F.f.2 keras-hygiene boundary).

### Changed
- Migrated the hardware-smoke run procedures from the old single-bundled-env recipe (`mkdir <fw>-smoke && cp environment.yml && pyve init --backend micromamba && pip install nbfoundry==… && pyve test --env main …`) to the named-env one-liner (`pyve test --env smoke-<fw> tests/integration/test_e2e_<fw>.py -m hardware`) in the F.c/F.d/F.e/F.f story bodies and the four `test_e2e_*.py` module docstrings.

### Removed
- Throwaway debug scratch `scripts/keras_metal_fit_repro.py` and `scripts/keras_metal_narrow.py` (F.f.1 reproduction scripts; the regression is now covered by [tests/unit/test_metal_smoke.py](tests/unit/test_metal_smoke.py)).

## [0.34.1] - 2026-05-29

### Fixed
- [scripts/metal_smoke.py](scripts/metal_smoke.py) no longer exits silently (SIGBUS, `exit=138`) partway through the Keras section on Apple Silicon. Root cause: PyTorch's MPS backend and TensorFlow-Metal cannot coexist in one process — once `torch.mps` claims the Metal device, the later TF-Metal Grappler optimization that Keras's TF backend triggers on `fit()` faults on misaligned memory. The script ran all frameworks in one process and wrapped each probe in `try/except Exception`, which cannot catch native (signal) termination, so the only failure mode that occurs was invisible. Fix: each framework probe now runs in its own subprocess (`--probe <name>`); the driver imports no ML framework, collects each child's exit code, and reports `PASS` / `FAIL (exit N)` / `CRASH (signal N, exit 128+N)`. Process isolation makes the co-residence crash impossible and any native crash loud. Verified on developer M3 Max: all probes `PASS`, `exit=0`.
- The `ml-datarefinery` import probe in [scripts/metal_smoke.py](scripts/metal_smoke.py) used the wrong module name (`ml_datarefinery`); the PyPI distribution is `ml-datarefinery` but the import name is `datarefinery` (sklearn-style). The bug was previously masked by the SIGBUS, which crashed before the import-probe section ran.

### Added
- [tests/unit/test_metal_smoke.py](tests/unit/test_metal_smoke.py): hardware-independent regression tests for the subprocess-isolation driver — each framework runs in its own subprocess, and a native crash in one is reported rather than swallowed.

## [0.34.0] - 2026-05-23

### Added
- HuggingFace end-to-end happy-path smoke at [tests/integration/test_e2e_huggingface.py](tests/integration/test_e2e_huggingface.py): two hardware-gated tests against `sshleifer/tiny-gpt2` (~5MB).
  - `test_tokenizer_round_trip` — loads the tokenizer via `AutoTokenizer.from_pretrained`, encodes "the quick brown fox", decodes back, asserts the round-trip matches.
  - `test_peft_lora_shrinks_trainable_params_and_forward_pass_works` — loads the base causal LM via `AutoModelForCausalLM`, builds a 3-example `datasets.Dataset.from_dict`, wraps the model with `peft.LoraConfig(task_type=CAUSAL_LM, r=4, lora_alpha=8, target_modules=["c_attn"])`, asserts LoRA-trainable params are materially smaller than the base model total (< base_total / 10), and runs one forward pass asserting the logits shape is `(1, seq_len, vocab_size)`.

### Note
- Budget bumped to 90s (story spec) because the first run downloads the model into `~/.cache/huggingface/hub`; subsequent runs read from cache and finish in well under 30s.
- Hardware verification (`pyve test tests/integration/test_e2e_huggingface.py -m hardware` against a fresh micromamba env with `nbfoundry` installed from PyPI, network access to HF Hub on first run) is deferred to developer Apple Silicon hardware.

## [0.33.0] - 2026-05-23

### Added
- Keras 3 end-to-end happy-path smoke at [tests/integration/test_e2e_keras.py](tests/integration/test_e2e_keras.py): two hardware-gated tests.
  - `test_keras_is_the_tf_bundled_namespace` — guards against accidental reintroduction of the standalone `keras` pin that F.b dropped. Asserts `importlib.metadata.distribution("keras")` raises `PackageNotFoundError` (i.e. no separate distribution is installed) and that the `keras` module's `__file__` resolves under the TensorFlow install tree.
  - `test_keras_3_mps_loss_decreases` — builds a `Dense(16, relu) → Dense(1, sigmoid)` model via `keras.Sequential` (resolving to the TF-bundled namespace), trains 3 epochs on `(100, 8)` random data under `tf.device("/GPU:0")`, and asserts `history.history["loss"][-1] < losses[0]`.

### Note
- Same per-epoch loss-decrease adaptation as F.c (3 epochs rather than 1) — required because Keras' `model.fit` returns one loss value per epoch, and asserting a decrease needs ≥2 measurements.
- Hardware verification (`pyve test tests/integration/test_e2e_keras.py -m hardware` against a fresh micromamba env with `nbfoundry` installed from PyPI) is deferred to developer Apple Silicon hardware.

## [0.32.0] - 2026-05-23

### Added
- PyTorch end-to-end happy-path smoke at [tests/integration/test_e2e_pytorch.py](tests/integration/test_e2e_pytorch.py): builds a tiny `Linear(8,16) → ReLU → Linear(16,1)` classifier on `(100, 8)` random data, trains 1 epoch with `batch_size=16` (≈6 optimizer steps) on `torch.device("mps")`, records the BCE-with-logits loss at each batch, and asserts `losses[-1] < losses[0]` plus `torch.backends.mps.is_available()`. Gated behind `@pytest.mark.slow` and `@pytest.mark.hardware`; opt-in via `pyve test -m hardware`. Budget: under 60s on M-series silicon.

### Note
- Mirrors the F.c TensorFlow smoke's structure (module-level `pytestmark = [slow, hardware]`, `pytest.importorskip`, run-procedure in the module docstring), but tracks loss **per batch within 1 epoch** rather than per epoch — that matches the story's literal "1 epoch on MPS" wording while still providing the ≥2 measurements the loss-decrease assertion needs.
- Hardware verification (`pyve test tests/integration/test_e2e_pytorch.py -m hardware` against a fresh micromamba env with `nbfoundry` installed from PyPI) is deferred to developer Apple Silicon hardware.

## [0.31.0] - 2026-05-23

### Added
- TensorFlow end-to-end happy-path smoke at [tests/integration/test_e2e_tensorflow.py](tests/integration/test_e2e_tensorflow.py): trains a tiny dense classifier (`Dense(16, relu) → Dense(1, sigmoid)`) on ~100 synthetic samples for 3 epochs under `tf.device("/GPU:0")` and asserts training loss decreases epoch-over-epoch and that `tf.config.list_physical_devices("GPU")` reports an Apple Silicon GPU. Gated behind `@pytest.mark.slow` and `@pytest.mark.hardware`; opt-in via `pyve test -m hardware`. Budget: under 60s on M-series silicon.
- `[tool.pytest.ini_options]` in [pyproject.toml](pyproject.toml) now registers `slow` and `hardware` markers and defaults to `addopts = "-ra -m 'not hardware'"` so `pyve test` skips hardware-gated tests in routine runs; developers run them explicitly with `pyve test -m hardware`.
- `tests/integration/` package initialized with an `__init__.py` carrying the Apache-2.0 / Pointmatic header — this is the home for the F.c-F.j per-tool and per-template end-to-end smokes.

### Note
- The story body deviates from the literal "1 epoch" wording: asserting loss *decreases* requires at least two measurements, so the smoke trains 3 epochs and compares `losses[0]` vs `losses[-1]`. Wall-clock impact is negligible (tiny model, 100 samples, batch_size=16).
- Hardware verification (`pyve test tests/integration/test_e2e_tensorflow.py -m hardware` against a fresh micromamba env with `nbfoundry` installed from PyPI) is deferred to developer Apple Silicon hardware.

## [0.30.0] - 2026-05-23

### Added
- Sectioned cross-project ML stack at [src/nbfoundry/templates/environment.yml](src/nbfoundry/templates/environment.yml): single shared file with comment-delimited `# core`, `# framework`, `# huggingface`, `# optimization`, `# dev tooling` sections. Defaults to the proven Apple Silicon path (`tensorflow-macos` + `tensorflow-metal`, bundled Keras 3 from TF 2.16+, MPS PyTorch) with inline swap blocks for CUDA (`cu126` / `cu128`) and generic Linux/CPU (`tensorflow` / `tensorflow[and-cuda]`).
- Core section additions: `pyarrow`, `seaborn`, `plotly`, `pillow`, `h5py`, `click`, `rich`, `python-dotenv`, `conda-lock`, and the Pointmatic-internal `ml-datarefinery` (package availability only — adapter and template wiring are deferred to a future Phase I per the phase plan).
- HuggingFace section: `transformers`, `datasets`, `peft`, `sentencepiece`, `protobuf`, `tiktoken`.
- Optimization section: `optuna`.
- Dev-tooling section: `ruff`, `mypy`, `pytest`, `pytest-cov` (so a scaffolded student project ships dev-tool-complete out of the box).
- `_emit_shared_env()` in [src/nbfoundry/cli.py](src/nbfoundry/cli.py): `nbfoundry init` now copies the single shared `environment.yml` into every scaffolded project alongside the template notebook.
- [scripts/metal_smoke.py](scripts/metal_smoke.py) extended to import every new package after the framework MPS probes and assert basic availability — framework training for HuggingFace / Optuna stays in the F.c–F.g per-tool smoke stories.

### Changed
- [src/nbfoundry/standalone.py](src/nbfoundry/standalone.py) clarifies that the bundled-env fallback now resolves to the single shared sectioned file (per-template envs no longer exist).
- [docs/specs/tech-spec.md](docs/specs/tech-spec.md) "Pinned ML stack" subsection rewritten to describe the new sectioned file and its by-section package list; package-structure block updated to show the shared `templates/environment.yml` and to note that lifecycle-template directories no longer carry their own env file.
- [README.md](README.md) Apple Silicon quickstart updated to point at `src/nbfoundry/templates/environment.yml` (the shared spec) and to describe the new cross-platform CUDA / CPU swap blocks.

### Removed
- Per-template `environment.yml` copies under `src/nbfoundry/templates/{data_exploration,data_preparation,model_experimentation,model_optimization,model_evaluation}/` — superseded by the single shared file. `nbfoundry init` now sources the env from the templates root.
- `jupyterlab`, `ipykernel`, `ipywidgets` from the env (Marimo replaces them).
- Standalone `keras>=3.x` pin from the env. Keras 3 ships bundled inside TF 2.16+ and is exposed as both `tf.keras` and the bare `keras` namespace; a separate pin pulls a parallel minor and silently fights TF's bundled copy.

### Note
- Hardware verification (`mkdir env-refresh-test && cd env-refresh-test && cp <repo>/src/nbfoundry/templates/environment.yml . && pyve init --backend micromamba && pyve run python <repo>/scripts/metal_smoke.py`) is deferred to developer Apple Silicon hardware; the env solve isn't reproducible from CI.

## [0.29.0] - 2026-05-23

### Added
- PyPI publish workflow ([.github/workflows/publish.yml](.github/workflows/publish.yml)): triggered on `v*` tag push, builds sdist + wheel via `hatch build`, and uploads to PyPI through trusted publishing (OIDC; no long-lived API tokens). A pre-build guard fails the run if the pushed tag and `hatch version` disagree, so the only way to ship a release is to tag the commit that owns the matching version bump.
- README "Releasing to PyPI" section documenting the one-time PyPI trusted-publisher setup (owner `pointmatic`, repo `nbfoundry`, workflow `publish.yml`, environment `pypi`) and the per-release tag-and-push procedure.

### Note
- This is the first story in Phase F. The trusted-publisher binding on PyPI must be created before the first tag is pushed; until then the workflow will run the build but the publish step will fail closed. Phase F's per-tool and per-template end-to-end smokes (F.c–F.j) depend on this pipeline because they install `nbfoundry==<published-version>` from PyPI rather than from the working tree.

## [0.28.0] - 2026-05-05

### Added
- `model_evaluation` lifecycle template ([src/nbfoundry/templates/model_evaluation/notebook.py](src/nbfoundry/templates/model_evaluation/notebook.py)): 9-cell reactive Marimo scaffold covering MPS device selection, train/test split via `sklearn.model_selection.train_test_split`, small MLP training, `sklearn.metrics.classification_report` rendered in markdown, `ConfusionMatrixDisplay`, `sklearn.calibration.calibration_curve` reliability diagram, and a final markdown report with accuracy + calibration MAE. Bundled `environment.yml` mirrors the pinned ML stack.
- AC-4 satisfied: all five lifecycle templates (`data_exploration`, `data_preparation`, `model_experimentation`, `model_optimization`, `model_evaluation`) now scaffold via `nbfoundry init` and parse via `notebooks.parse_all`.

## [0.27.0] - 2026-05-05

### Added
- `model_optimization` lifecycle template ([src/nbfoundry/templates/model_optimization/notebook.py](src/nbfoundry/templates/model_optimization/notebook.py)): 8-cell reactive Marimo scaffold covering MPS device selection, synthetic dataset, `build_mlp` / `train_one` helpers, a 3×3 grid sweep over `lr × hidden`, sorted results table, and an L1-unstructured `torch.nn.utils.prune` pass on the best model with sparsity / post-prune accuracy reported. Bundled `environment.yml` mirrors the pinned ML stack.

## [0.26.0] - 2026-05-05

### Added
- `model_experimentation` lifecycle template ([src/nbfoundry/templates/model_experimentation/notebook.py](src/nbfoundry/templates/model_experimentation/notebook.py)): 7-cell reactive Marimo scaffold covering MPS device selection, synthetic 1024×8 dataset, PyTorch `MLP(nn.Module)` definition, 10-epoch training loop with per-epoch loss / accuracy / wall-clock capture, and a metrics summary. Bundled `environment.yml` mirrors the pinned ML stack.

## [0.25.0] - 2026-05-05

### Added
- `data_preparation` lifecycle template ([src/nbfoundry/templates/data_preparation/notebook.py](src/nbfoundry/templates/data_preparation/notebook.py)): 6-cell reactive Marimo scaffold covering load → clean (drop NaNs, cast dtypes) → engineer (one-hot encode `category`, interaction term) → split (`sklearn.model_selection.train_test_split` with stratification) → summary. Bundled `environment.yml` mirrors the pinned ML stack.

## [0.24.0] - 2026-05-05

### Changed
- Replaced the [data_exploration template placeholder](src/nbfoundry/templates/data_exploration/notebook.py) with a real reactive Marimo notebook covering load → describe → visualize: synthetic-data load via numpy/pandas, `DataFrame.describe()` summary, class-balance markdown, and a per-class matplotlib scatter. Pure scientific-Python imports — modelfoundry primitives (only relevant in later-stage templates) are reached through `nbfoundry._modelfoundry.get_adapter()` per FR-7 / AC-10.
- `[tool.ruff] extend-exclude` now skips `src/nbfoundry/templates`. Marimo cells idiomatically use bare expressions as display directives (B018), and templates ship verbatim to user projects — they aren't first-party code to lint.

## [0.23.0] - 2026-05-05

### Added
- Pinned ML stack ([environment.yml](environment.yml) at the repo root, mirrored as package data at [src/nbfoundry/templates/environment.yml](src/nbfoundry/templates/environment.yml)): `python=3.12.13`, scikit-learn ≥ 1.5, pytorch ≥ 2.5 (MPS), marimo, and the Apple Silicon TensorFlow stack via pip (`tensorflow-macos`, `tensorflow-metal`, `keras`).
- [scripts/metal_smoke.py](scripts/metal_smoke.py): probes PyTorch / TensorFlow / Keras for MPS-backed devices and runs a small matmul / fit on each. Exits 0 only if every framework runs on MPS.
- README "Apple Silicon quickstart" section walking the `micromamba env create` → `pip install -e .` → `python scripts/metal_smoke.py` sequence.
- `nbfoundry compile` now falls back to the bundled `templates/environment.yml` when no `environment.yml` sits next to the source notebook tree, so every standalone artifact ships with the pinned spec.
- A copy of `environment.yml` ships with the `data_exploration` template so `nbfoundry init demo` produces a reproducible project skeleton.

### Note
- The hardware verification step (Apple Silicon MPS smoke) requires a clean Apple Silicon machine and a fresh `micromamba env create` against `environment.yml`. Versions in the spec are floors (`>=`) rather than exact pins for v1; tighten to `==` once the lockfile workflow lands in Phase G.

## [0.22.0] - 2026-05-05

### Added
- Public-API smoke test ([tests/unit/test_public_api.py](tests/unit/test_public_api.py)) asserting the four `from nbfoundry import ...` names are present, signatures of `compile_exercise` / `validate_exercise` match BR-1 / BR-2 verbatim (positional `yaml_path: Path`, `base_dir: Path`; any extras are keyword-only), and `ExerciseError` carries the BR-3 fields.

### Changed
- Locked the public API surface (OR-2 / AC-1): `nbfoundry.__all__` is `["ExerciseError", "__version__", "compile_exercise", "validate_exercise"]`. The signatures already matched the spec; this story formalizes the contract via the smoke test.

## [0.21.0] - 2026-05-05

### Added
- `nbfoundry validate <yaml-path> [--base-dir <path>]` — FR-4 CLI contract finalized: prints each error returned by `validate_exercise` on its own line on stdout; exits `0` silently for clean YAML, `1` otherwise. The wrapper itself was scaffolded in D.a; this story owns the version bump and the formal exit-code contract.

## [0.20.0] - 2026-05-05

### Changed
- `nbfoundry compile-exercise --out <path>` now writes atomically: serialize to a sibling temp file via `tempfile.mkstemp(dir=out.parent)`, then `os.replace` into `out`. Partial output is never visible (OR-5). The default cwd-relative behavior, `--base-dir` defaulting to the YAML's parent, and the deterministic `json.dumps` settings (`sort_keys=False`, `ensure_ascii=False`, `separators=(",", ": ")`, `indent=2`) carry over from D.a.

## [0.19.0] - 2026-05-05

### Changed
- `nbfoundry compile` now resolves `Config.compile.default_out` (default `dist/`) relative to the current working directory rather than the notebook's parent. Matches CLI ergonomics: `nbfoundry compile demo/notebook.py` writes to `./dist/`, not `./demo/dist/`. Loads `nbfoundry.toml` from cwd. `--out` overrides the default; user-supplied relative paths still resolve from cwd via Python's normal `Path` semantics.

## [0.18.0] - 2026-05-05

### Added
- `nbfoundry init <name> [--template <stage>]` subcommand (FR-1): scaffolds a new project directory from `nbfoundry.templates.<stage>` via `importlib.resources`. Default template is `data_exploration`. Rejects existing `<name>` and unknown stages (with the available list in the error). Prints the created path on stdout.
- Placeholder `src/nbfoundry/templates/data_exploration/notebook.py` so `init` has a template to copy. Real five-stage content arrives in Story E.b.

## [0.17.0] - 2026-05-05

### Added
- CLI scaffold ([src/nbfoundry/cli.py](src/nbfoundry/cli.py)): four subcommands registered (`init`, `compile`, `compile-exercise`, `validate`); `--verbose` / `--quiet` map to `logging_setup.configure(...)` (DEBUG / ERROR; default WARNING); `compile`, `compile-exercise`, `validate` are now thin wrappers over the library functions; `init` is a stub until Story D.b lands. Per-base-dir `nbfoundry.toml` is loaded via `config.load(base_dir)` and merged with parsed flags via `config.merge_cli`. `ExerciseError` raised by library calls maps to exit code 1 with the message on stderr.

### Changed
- `ExerciseError` is no longer `frozen=True` (kept `slots=True`). The CPython combination of `frozen=True`, `slots=True`, and `Exception` inheritance breaks Click's traceback assignment (`super(type, obj): obj must be an instance or subtype of type` from the dataclass-generated `__setattr__`), preventing clean error mapping in the CLI. Spec mismatch noted; semantics unchanged in code that doesn't mutate the exception.

## [0.16.0] - 2026-05-05

### Added
- `nbfoundry.standalone.compile(notebook_or_dir, out) -> Path` — FR-2 standalone artifact emitter. Validates notebook parse (`notebooks.parse_all` aggregates failures), stages into `tempfile.mkdtemp(dir=out.parent)`, copies the notebook tree (or single file) and an adjacent `environment.yml` if present, writes `launch.py` from the bundled template, and atomically `os.replace`s the staged dir into `out`. Refuses to overwrite an existing `out` (CLI may add `--force` later).
- `src/nbfoundry/templates/standalone/launch.py` package data: minimal launcher that resolves its own entry-point and runs `marimo edit` against it.

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
