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

> **Versioning — phase-bundled.** The contract only becomes Option-C-compliant once I.d flips `compile_exercise`, so intermediate stories (spike, schema, generator) land unversioned; the phase ships a single **v0.46.0** at I.f (minor — pre-1.0, breaking output-shape change). See `phase-i-learningfoundry-integration-refactoring-plan.md`.

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

### Story I.e: Test-suite rebuild for Option C [Planned]

Replace the static-path suite with codegen coverage.

- [ ] **Remove** the retired static-path tests (submission matrix, assets, expected-output / image, static-dict fidelity) and the `tests/fixtures/golden/valid_graded.json` golden + submission/asset fixtures
- [ ] Unit: `schema` accept/reject for the new definition; `codegen.generate()` produces a parseable marimo module; determinism (byte-stable); banner markdown → HTML
- [ ] Integration: `compile-exercise` CLI end-to-end → dict with `notebook_source`; **marimo-loads-the-generated-module smoke** (load the generated `marimo.App()` — light, no ML deps)
- [ ] Extend the no-ML-import AST scan to cover `codegen.py` and the compile path (AC-10 carried forward)
- [ ] New fixtures: a minimal Option-C definition YAML + a `sections`-with-`code_file` tree
- [ ] Apache-2.0 / Pointmatic header on new test files
- [ ] Verify: `pyve test` green; coverage gate (≥85%) satisfied on the new surface; `ruff` clean

### Story I.f: v0.46.0 — Spec + docs reconciliation to Option C [Planned]

Reconcile nbfoundry's own specs (still Option B) and ship the phase release.

- [ ] `features.md`: rewrite CR-3 / CR-6 + FR-3 / FR-5 + data models + AC-2 / AC-3 from static-display to notebook-emit; remove BR-4 / BR-5 references; move graded-submission to a deferred note
- [ ] `tech-spec.md`: compiler design, data models, package structure (drop `assets.py`, add `codegen.py`), CLI output
- [ ] `concept.md`: two-surface framing — the LF embed surface is now banner + launch, not static render
- [ ] `README.md`: `compile-exercise` usage + example reflect `notebook_source` output
- [ ] Bump version to **v0.46.0** (`_version.py`); update `CHANGELOG.md` (note the breaking output-shape change)
- [ ] Verify: dogfood `compile-exercise` against a sample definition → runnable notebook; full suite + mypy + ruff + coverage green

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
