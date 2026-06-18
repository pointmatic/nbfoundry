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

## Phase I: LearningFoundry Integration Refactoring

An embedded Marimo notebook in a WASM container doesn't work. It renders just the application Python rather than run the Python. Even if there were a way to run the Python, there are problems with running PyTorch in a WASM container, and that is a common dependency for machine learning workflows. 

LearningFoundry revised the consumer contract from the static-display API (Option B) to a **notebook-emit API (Option C)**: LearningFoundry references an external exercise and the learner runs it locally via a `learningfoundry launch <notebook_id>` command that owns marimo's lifecycle (spawn, track, kill on relaunch), while the SvelteKit app renders a banner that links to the live notebook.

**That launch CLI, the manifest sidecar, and the banner are LearningFoundry's repo.** NbFoundry's part of this refactor is the `compile_exercise` API: emit a runnable **marimo notebook** — `notebook_source`, a self-contained `marimo.App()` module as a string — plus banner metadata (`title` / `description` / `hints` / `environment`), instead of the static-display dict, and retire the BR-4 submission and BR-5 asset paths. The build-time no-`torch`/no-`modelfoundry` constraint is already met by nbfoundry's ML-free compiler (FR-7/AC-10); imports become source text in generated cells.

See [consumer-dependency-spec.md](./learningfoundry/consumer-dependency-spec.md) (the revised Option-C contract) and [phase-i-learningfoundry-integration-refactoring-plan.md](phase-i-learningfoundry-integration-refactoring-plan.md) (gap analysis, technical changes, out-of-scope).

---

> **Versioning — phase-bundled.** The contract only becomes Option-C-compliant once I.d flips `compile_exercise`, so intermediate stories (spike, schema, generator) land unversioned; the phase ships a single **v0.46.0** at I.f.6 (minor — pre-1.0, breaking output-shape change). See `phase-i-learningfoundry-integration-refactoring-plan.md`.

### Story I.a: Codegen spike — runnable marimo module from a definition [Done]

Throwaway architectural/integration spike proving the one genuinely unproven piece of Option C: that `compile_exercise` can emit a self-contained `marimo.App()` module **as a string** that `marimo run` / `marimo edit` executes cleanly, deterministically, with **zero ML imports at generation time**. Deliverable is the documented cell-emission pattern + a marimo-version target — not production code — and it de-risks I.c.

- [x] Prototype: hand-assemble a `marimo.App()` module string (header cell `import marimo` + `mo`, one `mo.md(...)` cell, one code cell that `import`s a third-party package **as text**) — built at `scripts/spike_codegen.py`; generated module is syntactically valid (`ast.parse` clean)
- [x] Confirm determinism: same input → byte-identical module string across runs (fixed cell order, formatting, no timestamps) — cross-process SHA-256 identical across three separate invocations
- [x] Confirm build-time purity: the generator emits `import torch` as **text** and itself imports no ML framework (sanity AST scan) — spike's AST self-scan against the forbidden set (`torch`, `tensorflow`, `keras`, `transformers`, `datasets`, `peft`, `sentencepiece`, `tiktoken`, `optuna`, `modelfoundry`, `datarefinery`) finds zero hits; `import torch` appears only as source text inside emitted cells
- [x] Pin the target marimo-module shape (decorator form, `mo.md` cells, header) and the marimo version surfaced in `environment.dependencies` — documented in `docs/specs/phase-i-learningfoundry-integration-refactoring-plan.md` § "Story I.a — Spike Findings"; version sourced at gen time via `importlib.metadata.version("marimo")` (no hard-coding in `codegen.py`)
- [x] Capture the chosen cell-emission pattern in the phase plan doc (or a short spike note) — feeds I.b/I.c
- [ ] Throwaway: delete prototype scratch once the pattern is captured (regression coverage lands in I.e) — **deferred until after the developer-hardware marimo round-trip below; delete in a follow-up turn once that verify lands**
- [ ] Verify: the captured pattern round-trips through marimo on developer hardware (no nbfoundry code ships this story) — **deferred to developer hardware.** Procedure: `pyve run python scripts/spike_codegen.py` prints a tempfile path; run `marimo run <path>` and `marimo edit <path>` and confirm both load without error

### Story I.b: Option C schema — definition input + notebook/banner output [Done]

Replace the static-display data models with the Option-C shapes.

- [x] New input models in `schema.py`: `ExerciseDefinition` (`title`, `description`, `sections[]`, optional `hints[]`, `environment`) + `SectionModel` (`title`, `description`, `code` XOR `code_file`)
- [x] New output `TypedDict` `CompiledExercise` = `{type, source, ref, title, description, hints, environment, notebook_source}`
- [x] **Delete** the retired models: `SubmissionModel`, `SubmissionFieldModel`, `ExpectedRule`, `RawExpectedOutputModel`, and the `CompiledSubmission*` / `CompiledExpected*` / static `CompiledExercise` fields — also removed `RawSectionModel`, `RawExerciseModel`, `CompiledSection`
- [x] Drop the `editable` flag (editability is LF's `ExerciseBlock` concern per the contract) and `expected_outputs` from the input
- [x] `mypy --strict` clean on the new shapes — `schema.py` + the I.b transition stub `compiler.py` both pass strict
- [x] Verify: schema unit tests (added in I.e) accept the new definition and reject malformed input; the old submission/asset models are gone — covered now by `tests/unit/test_schema_option_c.py` (21 tests, all green) as TDD red-green for I.b; the authoritative sweep still lands in I.e

**Transition state (a-pragmatic — see Phase I plan doc).** `compiler.py` is stubbed: `compile_exercise` and `validate_exercise` raise `NotImplementedError` so the package still imports. Two test files import retired schema names at module top and are temporarily collect-ignored via `tests/conftest.py`: `tests/unit/test_schema.py`, `tests/unit/test_errors.py`. **Suite baseline:** 99 pass / 30 fail / 2 collect-ignored / 7 deselected — every failure is a call into the stubbed compiler/validator. Story I.d restores the entry points; Story I.e removes the collect_ignore and replaces the legacy test files.

### Story I.c: Marimo notebook generator (`codegen.py`) [Done]

New module that turns an `ExerciseDefinition` into `notebook_source`, per the I.a pattern.

- [x] New `src/nbfoundry/codegen.py` (Apache-2.0 / Pointmatic header): `generate(defn, *, base_dir) -> str` emits a self-contained `marimo.App()` module — header cell, one `mo.md(...)` cell per section description, one code cell per section's `code` / inlined `code_file` (signature includes `base_dir` per the developer-chosen approach **A**: generator owns path resolution via `paths.resolve_under`)
- [x] Imports emitted as **source text** only; `codegen.py` imports no ML framework — covered by a build-time AST self-scan test against the forbidden set (`torch`, `tensorflow`, `keras`, `transformers`, `datasets`, `peft`, `sentencepiece`, `tiktoken`, `optuna`, `modelfoundry`, `datarefinery`)
- [x] Byte-stable output (fixed cell order, deterministic formatting) — covered by a same-input-twice equality test
- [x] `environment.dependencies` guarantees `marimo` is present (add if the author omitted it); surface the target marimo version — `ensure_marimo_pinned(env)` helper appends `marimo>=<importlib.metadata.version("marimo")>` when absent, preserves existing marimo entries (including `marimo[lsp]>=…`), does not misidentify `marimo-extension` / `marimo_helper`, and passes through `None` when the author opted out of declaring an environment
- [x] Reuse marimo-module conventions from `notebooks.py` / `standalone.py` where they fit — the shape mirrors the existing template `data_exploration/notebook.py` (decorator form, header cell exports `(mo,)`, `__generated_with` from installed marimo, footer `app.run()` guarded by `__main__`)
- [x] `ruff` + `mypy --strict` clean
- [ ] Verify: a generated sample opens under `marimo edit` (full smoke lands in I.e) — **deferred to developer hardware / Story I.e.** The hardware-side `marimo run|edit` round-trip is covered by the I.e smoke (light, no ML deps); the codegen unit suite proves the generated module is valid Python (`ast.parse` clean) and shape-correct.

**Cycle impact.** New file: `src/nbfoundry/codegen.py`. New tests: `tests/unit/test_codegen_option_c.py` (17 tests, all green). Suite baseline now **116 pass / 30 fail / 2 collect-ignored / 7 deselected** — the 30 failures are unchanged (still the I.d-stubbed `compile_exercise` / `validate_exercise` call sites). No regressions in the green surface.

### Story I.d: Rewire compile_exercise/validate_exercise → Option C; retire the static path [Done]

Flip the public API to Option C and remove the static-display machinery. **This story flips the contract** (phase-bundle release rides I.f).

- [x] Rewrite `compiler.py` `compile_exercise`: read YAML → validate → render banner markdown (`description`, `hints`) → `codegen.generate()` → assemble the Option-C dict (no `status` / `instructions` / `sections` / `expected_outputs` / `assets` / `submission`) — signature also dropped `allow_large_assets=False` (per dev sign-off, meaningless under Option C)
- [x] Update `validate_exercise` (lives in `compiler.py`, not a separate `validator.py` — original task wording was inaccurate) to validate the new definition shape (collect all errors); YAML-parse / missing-file short-circuit unchanged
- [x] **Delete** `src/nbfoundry/assets.py` (BR-5 removed) and its references — `assets.py` removed; `compiler.py` no longer imports it; `cli.py`'s `--allow-large-assets` flag removed; `config.py`'s `AssetsConfig` left in place as dormant config (referenced by `test_config.py`; will be pruned in I.f's spec / docs reconciliation)
- [x] Remove BR-4 submission validation and image-asset / expected-output handling from the compile + validate paths — already gone with the I.b schema redline; this story confirms there are no surviving references in the compile path
- [x] Update `cli.py` `compile-exercise`: emit the new dict to stdout / `--out` (JSON including `notebook_source`); `validate` shape unchanged — `--allow-large-assets` flag dropped, JSON output now includes `notebook_source`
- [x] Keep `paths.py` (code_file escape guard), `markdown.py`, `errors.py`, and the `_modelfoundry.py` boundary intact; `init` / `compile` (standalone) surfaces untouched — all five modules unchanged this cycle
- [x] `ruff` + `mypy --strict` clean
- [x] Verify: `compile_exercise` returns the Option-C dict for a well-formed definition; no ML framework imported at build time (AST scan + no-network sandbox still pass) — Option-C dict shape covered by `tests/unit/test_compiler_option_c.py` (18 tests, all green); the build-time AST scan in that file confirms `compiler.py` imports nothing from the forbidden ML set (`torch`, `tensorflow`, …); the no-network sandbox itself (`tests/integration/test_no_network.py`) still relies on the Option-B fixture corpus and goes green in I.e once the fixtures are replaced

**Sub-decision (also removed `notebooks.parse_all` from `_validate` for `code_file` refs).** Under Option B, each `code_file` was a complete marimo notebook (FR-6 tree compile). Under Option C, `code_file` is a plain `.py` snippet inlined into a marimo code cell by `codegen.generate`. The whole-notebook parse check is therefore obsolete; only the path-escape / existence guards remain. Marimo / Python syntax is evaluated at notebook run time on the learner's machine.

**Cycle impact.** New file: `tests/unit/test_compiler_option_c.py` (18 tests, all green). Deleted: `src/nbfoundry/assets.py`. Updated: `src/nbfoundry/compiler.py` (full Option-C pipeline replacing the I.b stub), `src/nbfoundry/cli.py` (drop `--allow-large-assets`), `tests/conftest.py` (collect-ignore extended to `tests/unit/test_assets.py`). Suite baseline now **138 pass / 16 fail / 3 collect-ignored / 7 deselected** — 14 tests went red → green (validators / CLI-validate / no-network validate, etc.), no regressions. The 16 remaining failures are all integration tests using the Option-B fixture corpus (`valid_graded.yaml` etc. still carry `editable`/`expected_outputs`/`submission`), which Story I.e replaces with Option-C fixtures.

### Story I.e: Test-suite rebuild for Option C [Done]

Replace the static-path suite with codegen coverage.

- [x] **Remove** the retired static-path tests (submission matrix, assets, expected-output / image, static-dict fidelity) and the `tests/fixtures/golden/valid_graded.json` golden + submission/asset fixtures — deleted 11 test files (unit: `test_schema.py`/`test_assets.py`/`test_compiler.py`/`test_validator.py`/`test_fixtures_corpus.py`; integration: `test_aggregate_tree.py`/`test_cli_compile_exercise.py`/`test_cli_validate.py`/`test_determinism.py`/`test_no_network.py`/`test_schema_fidelity.py`) and the entire `tests/fixtures/golden/` directory plus 14 retired `*.yaml` corpus files + `assets/` + old `tree/notebooks/` (Option-B FR-6 tree). Also dropped the `collect_ignore` from `tests/conftest.py` and rewrote `test_errors.py` against `ExerciseDefinition` (Option-C-clean)
- [x] Unit: `schema` accept/reject for the new definition; `codegen.generate()` produces a parseable marimo module; determinism (byte-stable); banner markdown → HTML — covered by renamed `test_schema.py` (21), `test_codegen.py` (16), `test_compiler.py` (18, includes `description`/`hints` HTML rendering)
- [x] Integration: `compile-exercise` CLI end-to-end → dict with `notebook_source`; **marimo-loads-the-generated-module smoke** (load the generated `marimo.App()` — light, no ML deps) — new `tests/integration/test_cli_compile_exercise.py` (stdout, `--out`, tree fixture) and `tests/integration/test_marimo_loads_generated.py` (loads via `importlib.util.spec_from_file_location`, asserts `module.app` is `marimo.App`)
- [x] Extend the no-ML-import AST scan to cover `codegen.py` and the compile path (AC-10 carried forward) — new authoritative `tests/unit/test_build_time_purity.py` parametrizes the scan over 12 modules on the build-time compile path (`__init__.py`, `schema.py`, `compiler.py`, `codegen.py`, `cli.py`, `config.py`, `errors.py`, `logging_setup.py`, `markdown.py`, `notebooks.py`, `paths.py`, `standalone.py`) against the full forbidden set, plus a sibling test asserting none of those modules import the `_modelfoundry` lazy-import boundary. Per-file scans removed from `test_codegen.py` and `test_compiler.py`
- [x] New fixtures: a minimal Option-C definition YAML + a `sections`-with-`code_file` tree — `tests/fixtures/exercises/valid_minimal.yaml` (Option-C) and `tests/fixtures/exercises/tree/exercise.yaml` + `tree/sections/{load,summarize}.py`. Tests/fixtures excluded from ruff via `pyproject.toml`'s `[tool.ruff] extend-exclude` (fixture files are code-snippet inlines for marimo cells, not stand-alone modules — `df` is intentionally cross-cell)
- [x] Apache-2.0 / Pointmatic header on new test files
- [x] Verify: `pyve test` green; coverage gate (≥85%) satisfied on the new surface; `ruff` clean

**Cycle impact.** **150 passed / 0 failed / 7 deselected — coverage 93.13%** (gate ≥85% satisfied; per-module coverage: `schema.py` 100%, `compiler.py` 92%, `codegen.py` 94%, `cli.py` 85%). Ruff clean across `src/` and `tests/`. Mypy strict clean on `src/nbfoundry/` (the configured scope). All Phase I (a-pragmatic) baseline failures resolved: the 16 stub-related failures inherited from I.d, the 3 collect-ignored files, and the Option-B fixture corpus are all gone. Also re-added new test files: `tests/integration/test_cli_validate.py`, `tests/integration/test_no_network.py`, `tests/integration/test_determinism.py`.

### Story I.f: v0.46.0 — Spec + docs reconciliation to Option C

Reconcile nbfoundry's own specs (still Option B) and ship the phase release. Split into six sub-stories — five small documentation/code reconciliations followed by the v0.46.0 release at I.f.6 — so each lands as its own commit and gates independently.

### Story I.f.1: Prune dormant `AssetsConfig` (BR-5 follow-through) [Done]

I.d removed `assets.py` and the `--allow-large-assets` kwarg/CLI flag, but `config.py`'s `AssetsConfig` (with `max_single_asset_mb` / `warn_single_asset_mb` / `allow_large_assets`) and its `merge_cli(...)` plumbing survived as dormant state. Removing it now keeps the v0.46.0 ship internally consistent with the tech-spec rewrite (I.f.3), which will say assets are gone.

- [x] Remove `AssetsConfig` from `src/nbfoundry/config.py` (the dataclass, the `Config.assets` field, the `[assets]` TOML section parse, and the related `merge_cli(...)` keyword arguments) — also updated `merge_cli` docstring's recognized-keys list to drop the assets group
- [x] Update `tests/unit/test_config.py`: remove the lines exercising `allow_large_assets` / `max_single_asset_mb` (currently 2 assertions) — also deleted `test_merge_cli_assets_group` (the dedicated test for the assets branch of `merge_cli`)
- [x] Verify: `pyve test` green, ruff clean, mypy strict clean (`src/nbfoundry/` scope) — **149 passed / 0 failed / 7 deselected**; coverage 93.02%; mypy and ruff both clean

### Story I.f.2: `features.md` → Option C [Done]

Rewrite the static-display passages in `docs/specs/features.md` to the notebook-emit contract; document BR-4/BR-5 retirement without renumbering the surviving BR-1/BR-2/BR-3.

- [x] Rewrite CR-3 / CR-6 from static-display rendering to notebook-emit (banner + `notebook_source`) — CR-3 now describes the 8-key Option-C wire shape; CR-6 retheme to "Generated marimo notebook (Option C)" describing the codegen contract (byte-stable, framework imports as text, cell layout)
- [x] Rewrite FR-3 / FR-5 to describe the Option-C `compile_exercise` pipeline (read YAML → validate → render banner markdown → `codegen.generate()` → assemble 8-key dict) — FR-3 rewritten end-to-end as a 7-step Option-C pipeline; FR-5 retheme from "Submission schema validation (BR-4)" to "Notebook source generation (Option C)" describing `codegen.generate()` + `ensure_marimo_pinned()` with explicit invariants (byte-stable / build-time pure / valid Python)
- [x] Rewrite the Data Models section: remove static `CompiledExercise` / `CompiledSection` / `CompiledSubmission*` / `CompiledExpected*` rows; add `ExerciseDefinition` / `SectionModel` / `CompiledExercise` (8 keys) / `CompiledEnvironment` — the Inputs / Outputs sections (which serve as the features-level data-model surface) now describe `ExerciseDefinition` + `SectionModel` (with code XOR code_file) and the 8-key `CompiledExercise`. The detailed model code lives in `tech-spec.md` (rewritten in I.f.3) and `src/nbfoundry/schema.py`
- [x] Rewrite AC-2 / AC-3 acceptance criteria for the new wire shape — AC-2 now "Generated notebook is marimo-loadable" (importlib.util smoke); AC-3 reframed for the two-surface compile under Option C
- [x] Add a short "Retired in v0.46.0" subsection recording BR-4 (graded submission) and BR-5 (image assets) as retired with the LF Option-C contract revision as the reason — preserves BR-1/BR-2/BR-3 numbering and AC-* / CR-* cross-references — added at lines 254-263 with four bullets (BR-4, BR-5, the retired wire fields, the `editable` per-section flag) plus a note that BR-1/BR-2/BR-3 are intentionally not renumbered
- [x] Sweep `features.md` for stray `expected_outputs` / `submission` / `editable` mentions and reconcile — all hits accounted for: NG-2 + the Retired section + TR-2's explanatory note are the only surviving references, each explicitly framed as retired-context
- [x] Verify: `features.md` internally consistent; no surviving Option-B vocabulary in normative passages — also caught and updated 4 cross-section refs (Project Goal, CR-1, QR-5, UR-4) that referenced `learningfoundry-dependency-spec.md` / "ExerciseBlock-compatible dict" / "byte-for-byte" — repointed to `learningfoundry/consumer-dependency-spec.md` and reframed for Option C

**Cycle impact.** Pure documentation story; no code changes. No new tests; full suite + ruff + mypy unchanged from I.f.1 baseline (149 pass / 0 fail / 7 deselected / coverage 93.02%).

### Story I.f.3: `tech-spec.md` → Option C [Done]

Reconcile the implementation-level spec with the shipped Option-C code.

- [x] Rewrite Compiler design section: pipeline shape, no asset enumeration, banner-markdown render, codegen handoff — `compile_exercise` rewritten as a 9-step Option-C pipeline (path-resolve → YAML → `ExerciseDefinition.model_validate` → code_file path-escape → render `description` + `hints` markdown → `codegen.generate()` → `codegen.ensure_marimo_pinned()` → assemble 8-key dict); `validate_exercise` notes single-`_validate` core and explicitly debunks the `validator.py` myth
- [x] Rewrite Data Models section to mirror `src/nbfoundry/schema.py` (post-I.b) — input now `_StrictModel` + `SectionModel` (code XOR code_file) + `EnvironmentModel` + `ExerciseDefinition`; output now `CompiledEnvironment` + 8-key `CompiledExercise`; retired-name list cited with link to features.md Retired section
- [x] Update Package structure: drop `assets.py`, add `codegen.py`, note `AssetsConfig` removed (per I.f.1) — package tree updated; `assets.py` and `validator.py` gone; `codegen.py` added with one-liner; `compiler.py` one-liner reframed for Option C
- [x] Update CLI output section: `compile-exercise` JSON shape (8 keys including `notebook_source`); `--allow-large-assets` flag gone — subcommand row updated; exit-code row updated to drop "asset oversize" trigger
- [x] Update Testing Strategy: remove Option-B fixture / golden references; reflect the I.e suite (Option-C fixtures, marimo-loads-generated smoke, authoritative build-time purity AST scan) — Testing Strategy table fully rewritten; new "Unit — codegen" + "Unit — build-time purity" + "Integration — marimo loads the generated module" rows; "Unit — schema" / "Unit — compiler core" / "Integration — determinism" rewritten for Option C; Option-B-only rows dropped ("Unit — assets" / "Unit — validator" / "Integration — schema fidelity" / "Integration — tree"); fixture-organization paragraph rewritten for the smaller Option-C corpus
- [x] Sweep `tech-spec.md` for stray Option-B vocabulary (asset enumeration, submission validators, expected-output handling, etc.) and reconcile — also caught and updated: Dependencies table (`markdown-it-py` no longer renders `instructions`; `pydantic` no longer cited for BR-4 errors); Cross-Cutting Concerns table (added "Build-time purity" row; added "Codegen byte-stability" row; rewrote "No code execution at compile time" for Option C; dropped "Asset size policy"); Modelfoundry-adapter section (`(compiler.py, validator.py)` → build-time compile path with link to test_build_time_purity); ErrorDetail example pointer; Performance Implementation I/O row; Public API line (`learningfoundry-dependency-spec.md` → `learningfoundry/consumer-dependency-spec.md`); Configuration section retains an explicit "AssetsConfig retired in v0.46.0" note
- [x] Verify: `tech-spec.md` internally consistent with `src/nbfoundry/`'s current code — package-tree and test-tree listings match the actual files post-I.e + I.f.1; retired-name set matches features.md's Retired section

**Cycle impact.** Pure documentation story; no code or test changes. Suite + ruff + mypy unchanged from I.f.1 baseline (149 pass / 0 fail / 7 deselected / coverage 93.02%).

### Story I.f.4: `concept.md` → two-surface framing [Planned]

Reframe the LF embed surface from static display to banner + launch.

- [ ] Rewrite the LearningFoundry embed surface description: banner + `learningfoundry launch <id>` instead of static-display render
- [ ] Note the Option-C contract revision and reference `learningfoundry/consumer-dependency-spec.md`
- [ ] Sweep `concept.md` for stray Option-B framing (e.g., "in-browser static render", "graded submission inline")
- [ ] Verify: `concept.md` internally consistent; the two surfaces (standalone marimo notebook + LF embed banner) are clearly delineated

### Story I.f.5: `README.md` → `compile-exercise` + `notebook_source` [Planned]

Update the user-facing README to show Option-C output.

- [ ] Update the `compile-exercise` example block to show the Option-C JSON output (8 keys including `notebook_source`)
- [ ] Update any "embed into learningfoundry" language to match the banner-and-launch flow
- [ ] Remove `--allow-large-assets` mentions
- [ ] Sweep for stray Option-B references (assets, expected outputs, graded submission)
- [ ] Verify: README accurately reflects the public API on `main`

### Story I.f.6: v0.46.0 release — version bump + CHANGELOG + dogfood [Planned]

Ship the Phase I bundle. **This story carries the v0.46.0 version bump for the entire phase.**

- [ ] Bump version to **v0.46.0** in `src/nbfoundry/_version.py`
- [ ] Add `CHANGELOG.md` v0.46.0 entry: breaking output-shape change (8-key Option-C dict with `notebook_source`); `compile_exercise` lost `allow_large_assets` kwarg + `--allow-large-assets` CLI flag; `assets.py` removed; `AssetsConfig` removed; BR-4 (graded submission) + BR-5 (image assets) retired
- [ ] Dogfood: `pyve run nbfoundry compile-exercise tests/fixtures/exercises/valid_minimal.yaml` succeeds and prints a JSON dict with `notebook_source` (the marimo-loads-the-generated-module smoke from I.e already covers runtime validity)
- [ ] Verify: full suite green; coverage gate (≥85%) satisfied; mypy strict clean; ruff clean

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
- **Phase J: DataRefinery integration** — wire `src/nbfoundry/_datarefinery.py` adapter (mirrors `_modelfoundry.py` pattern), add `[datarefinery]` optional extra in `pyproject.toml`, update lifecycle templates to load / inspect / materialize DataRefinery `Instance` objects, and extend per-template smokes to exercise an Instance end-to-end. Phase F only adds `ml-datarefinery` to `templates/environment.yml` so the package is installable alongside nbfoundry; the actual adapter and template wiring lives here. See `docs/specs/phase-f-pypi-distribution-and-stack-refresh-plan.md` § Out of Scope for the Coexist-vs-Subsume design decision (Coexist locked). *(Renumbered I→J: Phase I is the LearningFoundry Option-C refactor above.)*
- **NbFoundry scaffold-template injection (notebook codegen)** — extend Phase I's `codegen.py` so `compile_exercise` can emit data-load / train / eval **scaffold cells as source text** (not just author-supplied cells), sourced from the five-stage templates and — once their interfaces finalize — the modelfoundry / DataRefinery adapters. **Groups with the two entries above** (Modelfoundry contract finalization + Phase J DataRefinery integration): all three share the *emit framework scaffold as text, never import at build time* mechanism. Phase I ships author-supplied-cell assembly only.
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
