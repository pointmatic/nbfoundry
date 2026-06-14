# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
