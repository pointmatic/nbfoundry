# stories.md -- nbfoundry (python)

This document breaks the `nbfoundry` project into an ordered sequence of small, independently completable stories grouped into phases. Each story has a checklist of concrete tasks. Stories are organized by phase and reference modules defined in `tech-spec.md`.

Put **`vX.Y.Z` in the story title only when that story ships the package version bump** for that release. Doc-only or polish stories **omit the version from the title** (they share the release with the preceding code story, or use your project’s doc-release policy). **One semver bump per owning story** — extra tasks on the *same* story share that bump; see `project-essentials.md`. Semantic versioning applies to the package. Stories are marked with `[Planned]` initially and changed to `[Done]` when completed.

For a high-level concept (why), see [`concept.md`](concept.md). For requirements and behavior (what), see [`features.md`](features.md). For implementation details (how), see [`tech-spec.md`](tech-spec.md). For project-specific must-know facts, see [`project-essentials.md`](project-essentials.md) (`plan_phase` appends new facts per phase). For the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), see [`docs/project-guide/go.md`](../project-guide/go.md) — re-read it whenever the mode changes or after context compaction.

---

## Version Cadence

Standard semantic versioning, with these conventions:

- **Every story belongs to a phase.** Bugfix stories included. No orphan stories.
- **Per-story bumping** (when a story owns its own release):
  - Bugfix or trivial change → **patch** (`vX.Y.Z+1`)
  - Feature or improvement → **minor** (`vX.Y+1.0`)
  - Breaking change → **major** (`vX+1.0.0`). Post-1.0 only, and only via the `plan_production_phase` mode, which negotiates with the developer about whether the breakage is substantively user-facing or technically-but-trivially breaking (example: a log-format change is technically breaking, but if logs aren't a core consumer capability, the developer may judge it minor or even patch).
- **Phase-bundling option:** a phase can run unversioned during work and ship a single release/tag at end-of-phase. Stories within the phase carry no version in their title; the phase's last story owns the bump (magnitude determined by the highest-impact change in the bundle).
- **No out-of-order implementation.** Story order in this file is the order of execution. If work order needs to change, **reorganize/renumber here first** — don't skip ahead and create version-number gaps.
- **Pre-1.0:** standard semver applies; version starts at `v0.1.0` (Story A.a).
- **Post-1.0:** every phase must go through `plan_production_phase` (the lighter `plan_phase` is pre-1.0 only). Major bumps only happen through that mode's negotiation step.

This is the authoritative cadence rule. **Do not extrapolate the bump magnitude from `pyproject.toml`'s current version** — re-read this section whenever you're about to assign a version to a story.

---

## Phase F: PyPI Distribution and Stack Refresh

Establish nbfoundry as a real PyPI-installable package, refresh the template ML stack from the narrow Apple-only PyTorch+TF+Keras pinning to a broader cross-project stack (HuggingFace, Optuna, expanded utilities) derived from the proven sentiment-poc environment, and demonstrate per-tool and per-template happy paths on developer Apple Silicon hardware. Phase G is then free to focus on edges, quality, and documentation against a known-working stack. See `docs/specs/phase-f-pypi-distribution-and-stack-refresh-plan.md` for the full phase plan, gap analysis, and out-of-scope items.

### Story F.a: v0.29.0 PyPI publish workflow [Done]

Manual-tag → automated-build → trusted-publish pipeline. Lands first because every per-tool / per-template smoke story below installs nbfoundry from PyPI to validate the real install path.

- [x] `.github/workflows/publish.yml` triggered on `v*` tag push
- [x] Build sdist + wheel via `hatch build`
- [x] Trusted publishing via PyPI OIDC (no long-lived tokens)
- [x] Document tag-and-release procedure in `README.md`
- [x] Bump version to v0.29.0
- [x] Update CHANGELOG.md
- [ ] Verify: tagging `v0.29.0` triggers the workflow and the package appears on PyPI under `nbfoundry` — **deferred to developer (requires one-time PyPI trusted-publisher registration for `pointmatic/nbfoundry` → `publish.yml` → `pypi` environment, plus the developer's `git tag v0.29.0 && git push origin v0.29.0`)**

### Story F.b: v0.30.0 Pinned ML stack refresh + sectioned env.yml [Done]

Rewrite the template env as a single sectioned cross-platform stack derived from the proven sentiment-poc environment. Defaults to the proven Apple Silicon path (`tensorflow-macos` + `tensorflow-metal`, bundled Keras 3 from TF 2.16+, MPS PyTorch); cross-platform users follow documented comment-block swaps. Per-template env files are removed in favor of one shared file. Includes `ml-datarefinery` in the env (integration deferred to a future Phase I per the phase plan; package availability is the only F.b commitment).

- [x] Rewrite `src/nbfoundry/templates/environment.yml` as a single sectioned file with comment-delimited sections (`# core`, `# framework`, `# huggingface`, `# optimization`, `# dev tooling`) — section names refined from the original `# data_*` / `# model_*` lifecycle labels to match how packages actually group by role (the env is shared across all five lifecycle templates, so per-stage section names don't fit a single file)
- [x] Core section: `numpy`, `scipy`, `pandas`, `pyarrow`, `matplotlib`, `seaborn`, `plotly`, `scikit-learn`, `pillow`, `h5py`, `pyyaml`, `click`, `rich`, `python-dotenv`, `marimo`, `conda-lock`, `ml-datarefinery`
- [x] Framework section: `pytorch` (MPS index URL default; `cu126` / `cu128` swap documented in comment block), `tensorflow-macos` + `tensorflow-metal` (default Apple Silicon path; `tensorflow` / `tensorflow[and-cuda]` swap documented)
- [x] HuggingFace section: `transformers`, `datasets`, `peft`, `sentencepiece`, `protobuf`, `tiktoken`
- [x] Optimization section: `optuna`
- [x] Dev tooling section: `ruff`, `mypy`, `pytest`, `pytest-cov` (so a scaffolded student project is dev-tool-complete out of the box)
- [x] **Drops:** remove `jupyterlab`, `ipykernel`, `ipywidgets` (marimo replaces them); remove standalone `keras>=3.5` (Keras 3 is the bundled `tf.keras` in TF 2.16+; standalone install starts version-fighting)
- [x] Delete `src/nbfoundry/templates/{data_exploration,data_preparation,model_experimentation,model_optimization,model_evaluation}/environment.yml` (per-template copies superseded by the shared file)
- [x] Update `src/nbfoundry/templates/__init__.py` (or scaffolder code path) so `nbfoundry init` copies the single shared `environment.yml` into the scaffolded project alongside the notebook — implemented as `_emit_shared_env()` in `src/nbfoundry/cli.py`'s `cmd_init`
- [x] Update `src/nbfoundry/standalone.py` so `nbfoundry compile` emits the same shared `environment.yml` into the standalone artifact — fallback logic already routes to the shared bundled env; added clarifying comment that per-template envs no longer exist
- [x] Extend `scripts/metal_smoke.py` to import every new package (HuggingFace, Optuna, plotly, seaborn, etc.) and assert basic availability — framework training stays in F.c–F.g per-tool stories
- [x] Refresh `docs/specs/tech-spec.md` dependency table, env-management section, and "Pinned ML stack" subsection to match the new env.yml
- [x] Refresh `README.md` Apple Silicon quickstart to reflect the new env (single-file path, swap-point documentation pointer)
- [x] Apache-2.0 / Pointmatic header on `environment.yml` (YAML `#` comments) and any new files
- [x] Bump version to v0.30.0
- [x] Update CHANGELOG.md
- [ ] Verify: `mkdir env-refresh-test && cd env-refresh-test && cp <repo>/src/nbfoundry/templates/environment.yml . && pyve init --backend micromamba && pyve run python <repo>/scripts/metal_smoke.py` reports all packages import cleanly on Apple Silicon — **deferred to developer hardware**

### Story F.c: v0.31.0 TensorFlow happy path [Planned]

End-to-end smoke proving the refreshed stack produces a working TF/MPS training run on Apple Silicon, installed from PyPI against the new env.

- [ ] `tests/integration/test_e2e_tensorflow.py` marked `@pytest.mark.slow` and `@pytest.mark.hardware` (opt-in in CI, runs locally)
- [ ] Test procedure: build a fresh env from `templates/environment.yml`; install `nbfoundry==<latest-published>` from PyPI; scaffold synthetic data (~100 samples); train a tiny TF model for 1 epoch on MPS; assert loss decreases and MPS device is reported in use
- [ ] Budget: under 60s on M-series silicon (tiny model, tiny dataset)
- [ ] Apache-2.0 / Pointmatic header
- [ ] Document the run procedure in the story body for the developer-hardware verify
- [ ] Bump version to v0.31.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test tests/integration/test_e2e_tensorflow.py -m hardware` passes on developer Apple Silicon — **deferred to developer hardware**

### Story F.d: v0.32.0 PyTorch happy path [Planned]

End-to-end smoke proving the refreshed stack produces a working PyTorch/MPS training run on Apple Silicon.

- [ ] `tests/integration/test_e2e_pytorch.py` marked `@pytest.mark.slow` and `@pytest.mark.hardware`
- [ ] Test procedure: same env-and-install pattern as F.c; train a tiny PyTorch model for 1 epoch on MPS; assert loss decreases and `torch.backends.mps.is_available()` is True
- [ ] Budget: under 60s on M-series silicon
- [ ] Apache-2.0 / Pointmatic header
- [ ] Document the run procedure in the story body
- [ ] Bump version to v0.32.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test tests/integration/test_e2e_pytorch.py -m hardware` passes on developer Apple Silicon — **deferred to developer hardware**

### Story F.e: v0.33.0 Keras 3 happy path [Planned]

End-to-end smoke proving Keras 3 (the bundled `tf.keras` from TF 2.16+) works in the refreshed env. No standalone `keras` install — exercising what users actually consume.

- [ ] `tests/integration/test_e2e_keras.py` marked `@pytest.mark.slow` and `@pytest.mark.hardware`
- [ ] Test procedure: build a Keras 3 model via `from tensorflow import keras` (the bundled namespace); train 1 epoch on tiny synthetic data; assert loss decreases
- [ ] Explicitly assert no separate `keras` package is installed (`import keras` resolves to the TF-bundled module, not a parallel install) — catches accidental reintroduction of the standalone pin
- [ ] Budget: under 60s on M-series silicon
- [ ] Apache-2.0 / Pointmatic header
- [ ] Document the run procedure in the story body
- [ ] Bump version to v0.33.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test tests/integration/test_e2e_keras.py -m hardware` passes on developer Apple Silicon — **deferred to developer hardware**

### Story F.f: v0.34.0 HuggingFace stack happy path [Planned]

End-to-end smoke covering `transformers` + `datasets` + `peft` against a small pretrained model and a tiny dataset.

- [ ] `tests/integration/test_e2e_huggingface.py` marked `@pytest.mark.slow` and `@pytest.mark.hardware`
- [ ] Test procedure: load a small pretrained model (e.g. `distilbert-base-uncased` or `sshleifer/tiny-gpt2`) via `transformers`; load a tiny synthetic dataset via `datasets`; apply a `peft` LoRA wrapper; run one forward pass; assert tokenizer round-trip, model output shape, and PEFT parameter count is materially smaller than full-model parameter count
- [ ] Budget: under 90s on M-series silicon (model download cached on first run)
- [ ] Apache-2.0 / Pointmatic header
- [ ] Document the run procedure in the story body, including the cache-warmup caveat
- [ ] Bump version to v0.34.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test tests/integration/test_e2e_huggingface.py -m hardware` passes on developer Apple Silicon — **deferred to developer hardware**

### Story F.g: v0.35.0 Optuna hyperparameter search happy path [Planned]

End-to-end smoke running a small `optuna` study against one of the framework models from F.c–F.f.

- [ ] `tests/integration/test_e2e_optuna.py` marked `@pytest.mark.slow` and `@pytest.mark.hardware`
- [ ] Test procedure: define a small objective (1–2 hyperparameters) wrapping a tiny PyTorch or TF model; run a 5-trial Optuna study; assert study completes, `study.best_trial` is populated, and trial history is accessible
- [ ] Budget: under 60s on M-series silicon (5 tiny trials)
- [ ] Apache-2.0 / Pointmatic header
- [ ] Document the run procedure in the story body
- [ ] Bump version to v0.35.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test tests/integration/test_e2e_optuna.py -m hardware` passes on developer Apple Silicon — **deferred to developer hardware**

### Story F.h: v0.36.0 data_exploration template happy path [Planned]

End-to-end smoke against the scaffolded `data_exploration` template, exercising the framework-agnostic load → describe → visualize flow on synthetic data.

- [ ] `tests/integration/test_e2e_template_data_exploration.py` marked `@pytest.mark.slow` and `@pytest.mark.hardware`
- [ ] Test procedure: `nbfoundry init demo --template data_exploration` in a temp dir; create synthetic input data the template expects; run the scaffolded notebook end-to-end (via `marimo edit --headless` or equivalent); assert each cell completes and the expected describe/visualize outputs are produced
- [ ] Budget: under 60s on M-series silicon
- [ ] Apache-2.0 / Pointmatic header
- [ ] Document the run procedure in the story body
- [ ] Bump version to v0.36.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test tests/integration/test_e2e_template_data_exploration.py -m hardware` passes on developer Apple Silicon — **deferred to developer hardware**

### Story F.i: v0.37.0 data_preparation template happy path [Planned]

End-to-end smoke against the scaffolded `data_preparation` template, exercising the cleaning → feature engineering → split scaffolding.

- [ ] `tests/integration/test_e2e_template_data_preparation.py` marked `@pytest.mark.slow` and `@pytest.mark.hardware`
- [ ] Test procedure: `nbfoundry init demo --template data_preparation` in a temp dir; create synthetic input data; run the scaffolded notebook end-to-end; assert clean splits are produced with the expected shapes and class balance
- [ ] Budget: under 60s on M-series silicon
- [ ] Apache-2.0 / Pointmatic header
- [ ] Document the run procedure in the story body
- [ ] Bump version to v0.37.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test tests/integration/test_e2e_template_data_preparation.py -m hardware` passes on developer Apple Silicon — **deferred to developer hardware**

### Story F.j: v0.38.0 model_evaluation template happy path [Planned]

End-to-end smoke against the scaffolded `model_evaluation` template, exercising the held-out evaluation → confusion matrix → calibration scaffolding.

- [ ] `tests/integration/test_e2e_template_model_evaluation.py` marked `@pytest.mark.slow` and `@pytest.mark.hardware`
- [ ] Test procedure: `nbfoundry init demo --template model_evaluation` in a temp dir; provide a pre-trained tiny model + holdout split (synthetic); run the scaffolded notebook end-to-end; assert confusion matrix is rendered and calibration plot is produced
- [ ] Budget: under 60s on M-series silicon
- [ ] Apache-2.0 / Pointmatic header
- [ ] Document the run procedure in the story body
- [ ] Bump version to v0.38.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test tests/integration/test_e2e_template_model_evaluation.py -m hardware` passes on developer Apple Silicon — **deferred to developer hardware**

Phase-level acceptance check (covers AC-4 / AC-5 / CR-10 against the refreshed stack): a clean Apple Silicon machine can `pyve init --backend micromamba` against the new `environment.yml`, `pip install nbfoundry==v0.38.0` from PyPI, `nbfoundry init demo --template <each>` for all five templates, and run each scaffolded notebook to completion with the relevant tool exercised. Each story above carries its own minimal pass/fail check; the phase-level acceptance is the integral of those.

---

## Phase G: Testing, Quality, and Documentation

Hardening: fixtures, comprehensive test suite, type strictness, coverage target, and docs polish. DataRefinery bugs or small improvements that surface during Phase G testing work (Phase F adds `ml-datarefinery` to the template env but no nbfoundry-side integration code) may be addressed as additional G.* stories at the developer's discretion — Phase G is the quality phase and DataRefinery quality issues that span the nbfoundry boundary are in scope here. Full DataRefinery adapter + template integration remains deferred to a future Phase I.

### Story G.a: v0.39.0 Test fixtures [Planned]

Establish the fixture corpus that downstream test stories consume.

- [ ] `tests/fixtures/exercises/valid_minimal.yaml` — smallest passing exercise
- [ ] `tests/fixtures/exercises/valid_graded.yaml` — full BR-4 submission block
- [ ] `tests/fixtures/exercises/valid_with_assets.yaml` — image expected_outputs (path-only, BR-5)
- [ ] One `invalid_<reason>.yaml` per validator rejection (named per `tech-spec.md` Testing Strategy)
- [ ] `tests/fixtures/exercises/tree/` — multi-notebook tree fixture
- [ ] `tests/fixtures/golden/valid_graded.json` — TR-2 byte-for-byte golden
- [ ] `tests/conftest.py` shared fixtures: `tmp_base_dir`, `sample_yaml`, `golden_dict`
- [ ] Bump version to v0.39.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test tests/fixtures/` discovers fixture files; conftest fixtures importable from a smoke test

### Story G.b: v0.40.0 Unit test sweep [Planned]

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
- [ ] Bump version to v0.40.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test tests/unit/` passes

### Story G.c: v0.41.0 Integration test sweep [Planned]

TR-2 / TR-3 / OR-5 / AC-9 — end-to-end behaviors via the CLI and library surface.

- [ ] `tests/integration/test_cli_init.py` — scaffolds each of the five templates
- [ ] `tests/integration/test_cli_compile.py` — standalone artifact end-to-end
- [ ] `tests/integration/test_cli_compile_exercise.py` — JSON to stdout / `--out`
- [ ] `tests/integration/test_cli_validate.py` — exit codes
- [ ] `tests/integration/test_determinism.py` — two runs produce byte-identical JSON
- [ ] `tests/integration/test_no_network.py` — monkey-patched `socket.socket.connect` raises; compile/validate succeed
- [ ] `tests/integration/test_aggregate_tree.py` — tree → single dict; tree-external references reject
- [ ] `tests/integration/test_schema_fidelity.py` — `valid_graded.yaml` round-trips to `valid_graded.json` byte-for-byte (modulo path normalization)
- [ ] Bump version to v0.41.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test tests/integration/` passes; AC-9 sandbox test fails-closed if a network call sneaks in

### Story G.d: v0.42.0 mypy --strict pass [Planned]

QR-4 / TR-5 — strict typing across the whole package.

- [ ] Configure `[tool.mypy]` in `pyproject.toml` with `strict = true`, `mypy_path = "src"`, `packages = ["nbfoundry"]`
- [ ] Resolve every strict-mode error in `src/nbfoundry/`
- [ ] Add `types-PyYAML` (already in `requirements-dev.txt`); add any further `types-*` stubs the strict pass surfaces
- [ ] Bump version to v0.42.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve testenv run mypy src/nbfoundry/` reports zero errors

### Story G.e: v0.43.0 Coverage target ≥85% [Planned]

TR-6 — `pytest-cov --cov-fail-under=85` on `nbfoundry` public modules.

- [ ] Configure `[tool.pytest.ini_options]` with `--cov=nbfoundry --cov-report=term-missing --cov-fail-under=85`
- [ ] Exclude `src/nbfoundry/templates/**` and `src/nbfoundry/templates/standalone/launch.py` via `[tool.coverage.run] omit = [...]`
- [ ] Add tests to close any gaps surfaced by the report
- [ ] Bump version to v0.43.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve test` passes with coverage gate satisfied; the report shows ≥85% on public modules

### Story G.f: Documentation polish [Planned]

Doc-only — no version bump; ships under v0.43.0.

- [ ] Expand `README.md` with: install, scaffold, compile, embed-into-learningfoundry quickstart; AC-3 two-surface demonstration
- [ ] Cross-link `concept.md`, `features.md`, `tech-spec.md`, `learningfoundry-dependency-spec.md`
- [ ] Update `CHANGELOG.md` with documentation entry under `0.43.0`
- [ ] Verify: a fresh reader following only `README.md` on Apple Silicon can scaffold and compile a template within UR-3's "minutes" budget

---

## Phase H: CI/CD

Automation. Add lint/test to CI; add coverage badge. A v1.0.0 production release is intentionally not scheduled here — it lives in `## Future` as a deferred story, to be promoted to its own phase if/when project posture warrants.

### Story H.a: v0.44.0 CI lint + test workflow [Planned]

Added later per project direction — runs `ruff`, `mypy`, and `pytest` on every push and PR.

- [ ] `.github/workflows/ci.yml` triggered on push and pull_request
- [ ] Matrix: macOS-latest (Apple Silicon runner) primary; ubuntu-latest stretch
- [ ] Steps: install pyve + testenv, `ruff check`, `ruff format --check`, `mypy src/nbfoundry/`, `pyve test`
- [ ] Cache the testenv to keep CI under a few minutes
- [ ] Status badges in `README.md` for the `ci` workflow
- [ ] Bump version to v0.44.0
- [ ] Update CHANGELOG.md
- [ ] Verify: a deliberately broken commit fails CI; a clean commit passes on both runners

### Story H.b: v0.45.0 Coverage badge [Planned]

Code coverage reporting + README badge — required before the v1.0.0 production release per project direction.

- [ ] Add coverage upload step to `ci.yml` (Codecov or Coveralls; default Codecov)
- [ ] Add coverage badge to `README.md` header
- [ ] Document the coverage gate in `CONTRIBUTING.md` (or README dev section)
- [ ] Bump version to v0.45.0
- [ ] Update CHANGELOG.md
- [ ] Verify: a CI run uploads coverage and the README badge resolves to a current percentage

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
- **Modelfoundry contract finalization** — when modelfoundry's interface is published, harden `_modelfoundry.py` from the provisional Protocol to the real signatures; pin `nbfoundry[modelfoundry]` extra in `pyproject.toml`. Per the Phase F plan, modelfoundry and DataRefinery **coexist**: modelfoundry continues to own modeling primitives (training loops, optimizers, eval), DataRefinery owns data prep.
- **Phase I: DataRefinery integration** — wire `src/nbfoundry/_datarefinery.py` adapter (mirrors `_modelfoundry.py` pattern), add `[datarefinery]` optional extra in `pyproject.toml`, update lifecycle templates to load / inspect / materialize DataRefinery `Instance` objects, and extend per-template smokes to exercise an Instance end-to-end. Phase F only adds `ml-datarefinery` to `templates/environment.yml` so the package is installable alongside nbfoundry; the actual adapter and template wiring lives here. See `docs/specs/phase-f-pypi-distribution-and-stack-refresh-plan.md` § Out of Scope for the Coexist-vs-Subsume design decision (Coexist locked).
- **Windows CI** — out of v1 cross-platform scope (QR-3 limits CI to macOS primary, Linux stretch).
- **Concurrency / parallel parse** — `notebooks.parse_all` parallelization via `concurrent.futures` if curriculum-scale performance bites (tech-spec.md Performance).
- **Pre-commit hooks** — declined for v1 (tech-spec.md Runtime & Tooling); reconsider if CI-gates-only causes friction.
- **CUDA/Linux acceleration tuning** — best-effort only in v1 (NG-9); promote if user demand warrants.
- **Non-ML/DS exercise flavors** — owned by other tools (NG-8); not an nbfoundry concern.
- **Hosted runtime / managed cloud** — out of scope (NG-4); local-first is the v1 contract.

### (Future) Story ?.?: v1.0.0 Production release

Cut the stable, production-quality, feature-complete release per the versioning rule in `tech-spec.md` and the v1 acceptance criteria AC-1..AC-10.

- [ ] Walk every AC-1..AC-10 in `features.md` and confirm each is satisfied
- [ ] Final `CHANGELOG.md` entry under `1.0.0` summarizing the v1 surface
- [ ] Update `README.md` to remove pre-1.0 caveats
- [ ] Bump version to v1.0.0
- [ ] Tag `v1.0.0`; `publish.yml` ships the release to PyPI
- [ ] Verify: `pip install nbfoundry==1.0.0` from PyPI on a clean Apple Silicon machine; `nbfoundry init`, `compile`, `compile-exercise`, and `validate` all run successfully against the documented sample
