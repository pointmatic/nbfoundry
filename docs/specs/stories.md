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
- [x] Verify: tagging `v0.29.0` triggers the workflow and the package appears on PyPI under `nbfoundry` — **deferred to developer (requires one-time PyPI trusted-publisher registration for `pointmatic/nbfoundry` → `publish.yml` → `pypi` environment, plus the developer's `git tag v0.29.0 && git push origin v0.29.0`)**

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
- [x] Verify: `mkdir env-refresh-test && cd env-refresh-test && cp <repo>/src/nbfoundry/templates/environment.yml . && pyve init --backend micromamba && pyve run python <repo>/scripts/metal_smoke.py` reports all packages import cleanly on Apple Silicon — **deferred to developer hardware**

### Story F.c: v0.31.0 TensorFlow happy path [Done]

End-to-end smoke proving the refreshed stack produces a working TF/MPS training run on Apple Silicon, installed from PyPI against the new env.

- [x] `tests/integration/test_e2e_tensorflow.py` marked `@pytest.mark.slow` and `@pytest.mark.hardware` (opt-in in CI, runs locally)
- [x] Test procedure: build a fresh env from `templates/environment.yml`; install `nbfoundry==<latest-published>` from PyPI; scaffold synthetic data (~100 samples); train a tiny TF model for 1 epoch on MPS; assert loss decreases and MPS device is reported in use — **trains 3 epochs rather than 1**, because asserting "loss decreases" requires ≥2 measurements; the wall-clock impact is negligible (tiny model, 100 samples, batch_size=16) and the assertion semantics match the story's intent
- [x] Budget: under 60s on M-series silicon (tiny model, tiny dataset)
- [x] Apache-2.0 / Pointmatic header
- [x] Document the run procedure in the story body for the developer-hardware verify (procedure embedded in the test module docstring at [tests/integration/test_e2e_tensorflow.py](../../tests/integration/test_e2e_tensorflow.py))
- [x] Bump version to v0.31.0
- [x] Update CHANGELOG.md
- [x] Verify: `pyve test <repo>/tests/integration/test_e2e_tensorflow.py -m hardware` passes on developer Apple Silicon — verified 2026-05-29 on M3 Max (1 passed in 8.41s); actual invocation used `--env main` per the testenv-trap doc

**Run procedure (one-time per release, on developer Apple Silicon):**

```bash
# 1. Build a fresh micromamba-backed env from the refreshed templates env.
mkdir tf-smoke && cd tf-smoke
cp <repo>/src/nbfoundry/templates/environment.yml .
pyve init --backend micromamba --no-lock

# 2. Install nbfoundry from PyPI into that env (not editable from the working
#    tree -- per project-essentials, F.c-F.j install from PyPI to validate
#    the published surface):
pyve run pip install nbfoundry==<latest-published>

# 3. Run the smoke from inside the repo.
pyve test tests/integration/test_e2e_tensorflow.py -m hardware
```

The `@pytest.mark.hardware` marker is gated out by default via the new `addopts = "-ra -m 'not hardware'"` in `pyproject.toml`, so routine `pyve test` runs skip it; the developer opts in with `-m hardware`.

### Story F.d: v0.32.0 PyTorch happy path [Done]

End-to-end smoke proving the refreshed stack produces a working PyTorch/MPS training run on Apple Silicon.

- [x] `tests/integration/test_e2e_pytorch.py` marked `@pytest.mark.slow` and `@pytest.mark.hardware`
- [x] Test procedure: same env-and-install pattern as F.c; train a tiny PyTorch model for 1 epoch on MPS; assert loss decreases and `torch.backends.mps.is_available()` is True — loss is tracked **per batch within the 1 epoch** (not per epoch), matching the story's literal "1 epoch" while still giving the ≥2 measurements the assertion needs
- [x] Budget: under 60s on M-series silicon
- [x] Apache-2.0 / Pointmatic header
- [x] Document the run procedure in the story body (procedure embedded in the test module docstring at [tests/integration/test_e2e_pytorch.py](../../tests/integration/test_e2e_pytorch.py))
- [x] Bump version to v0.32.0
- [x] Update CHANGELOG.md
- [x] Verify: `pyve test <repo>/tests/integration/test_e2e_pytorch.py -m hardware` activates test outside the repo, skips without `--env` flag. — verified 2026-05-29 on M3 Max (1 skipped; `could not import 'torch'`); pyve's silent-skip advisory fired with the corrective hint
- [x] Verify: `pyve test --env root <repo>/tests/integration/test_e2e_pytorch.py -m hardware` passes on developer Apple Silicon — verified 2026-05-29 on M3 Max (1 passed in 25.79s; torch trained on MPS, loss decreased)

**Run procedure** — identical to F.c with the test path swapped:

```bash
mkdir torch-smoke && cd torch-smoke
cp <repo>/src/nbfoundry/templates/environment.yml .
pyve init --backend micromamba
pyve run pip install nbfoundry==<latest-published>
pyve test --env root <repo>/tests/integration/test_e2e_pytorch.py -m hardware
```

### Story F.e: v0.33.0 Keras 3 happy path [Done]

End-to-end smoke proving Keras 3 (the bundled `tf.keras` from TF 2.16+) works in the refreshed env. No standalone `keras` install — exercising what users actually consume.

- [x] `tests/integration/test_e2e_keras.py` marked `@pytest.mark.slow` and `@pytest.mark.hardware`
- [x] Test procedure: build a Keras 3 model via `import keras` (the TF-bundled namespace); train 3 epochs on tiny synthetic data; assert loss decreases — trains **3 epochs rather than 1** for the same reason as F.c: Keras' `model.fit` reports one loss per epoch, and asserting a decrease needs ≥2 measurements
- [x] Explicitly assert no separate `keras` package is installed (`importlib.metadata.distribution("keras")` raises `PackageNotFoundError`; `keras.__file__` resolves under the tensorflow install tree) — catches accidental reintroduction of the standalone pin
- [x] Budget: under 60s on M-series silicon
- [x] Apache-2.0 / Pointmatic header
- [x] Document the run procedure in the story body (embedded in the test module docstring at [tests/integration/test_e2e_keras.py](../../tests/integration/test_e2e_keras.py))
- [x] Bump version to v0.33.0
- [x] Update CHANGELOG.md
- [ ] Verify: `pyve test --env main <repo>/tests/integration/test_e2e_keras.py -m hardware` passes on developer Apple Silicon — **attempted 2026-05-29 on M3 Max: 1 failed, 1 passed.** `test_keras_3_mps_loss_decreases` passed (Keras trained on MPS). `test_keras_is_the_tf_bundled_namespace` failed: `a standalone keras distribution is installed (3.14.1)` — exactly the env-hygiene regression F.b dropped and F.e's guard was authored to catch. **Blocked by F.f.1 env-hygiene housekeeping** (constrain transitive pulls of `keras` / conda-forge `tensorflow` via `transformers`/`datasets`/`peft`).

**Run procedure** — identical to F.c/F.d with the test path swapped:

```bash
mkdir keras-smoke && cd keras-smoke
cp <repo>/src/nbfoundry/templates/environment.yml .
pyve init --backend micromamba
pyve run pip install nbfoundry==<latest-published>
pyve test tests/integration/test_e2e_keras.py -m hardware
```

### Story F.f: v0.34.0 HuggingFace stack happy path [Done]

End-to-end smoke covering `transformers` + `datasets` + `peft` against a small pretrained model and a tiny dataset.

- [x] `tests/integration/test_e2e_huggingface.py` marked `@pytest.mark.slow` and `@pytest.mark.hardware`
- [x] Test procedure: load `sshleifer/tiny-gpt2` (~5MB) via `transformers.AutoModelForCausalLM`; build a 3-example synthetic `datasets.Dataset.from_dict`; wrap with `peft.LoraConfig(task_type=CAUSAL_LM, r=4, lora_alpha=8, target_modules=["c_attn"])`; run one forward pass; assert tokenizer round-trip, logits shape `(1, seq_len, vocab_size)`, and LoRA-trainable params are materially smaller than base model total (< base_total / 10)
- [x] Budget: under 90s on M-series silicon (model download cached on first run)
- [x] Apache-2.0 / Pointmatic header
- [x] Document the run procedure in the story body, including the cache-warmup caveat (embedded in the test module docstring at [tests/integration/test_e2e_huggingface.py](../../tests/integration/test_e2e_huggingface.py))
- [x] Bump version to v0.34.0
- [x] Update CHANGELOG.md
- [x] Verify: `pyve test --env main <repo>/tests/integration/test_e2e_huggingface.py -m hardware` passes on developer Apple Silicon — verified 2026-05-30 on M3 Max (2 passed in 26.78s; tokenizer round-trip + LoRA forward pass; 6 deprecation warnings from `transformers`/`huggingface_hub`/`peft`, no failures)

**Run procedure** — identical to F.c/F.d/F.e with the test path swapped, plus a cache-warmup caveat:

```bash
mkdir hf-smoke && cd hf-smoke
cp <repo>/src/nbfoundry/templates/environment.yml .
pyve init --backend micromamba
pyve run pip install nbfoundry==<latest-published>
pyve test tests/integration/test_e2e_huggingface.py -m hardware
```

The first run downloads `sshleifer/tiny-gpt2` (~5MB) into `~/.cache/huggingface/hub`. Subsequent runs read from cache. If you are behind a corporate proxy or running in an environment without internet access, set `HF_HUB_OFFLINE=1` only *after* the cache has been warmed at least once.

### Story F.f.1: v0.34.1 Fix silent SIGBUS in metal_smoke.py (framework co-residence) [Planned]

Bug fix surfaced by the F.b deferred-to-developer verify (story F.b, final task). Running `scripts/metal_smoke.py` against the refreshed Phase F env on Apple Silicon exited silently (`exit=138`, SIGBUS) partway through the Keras section, with no traceback, no `FAIL`, and no summary. (Sub-numbered under F.f because the conceptual parent — F.b's `metal_smoke.py` harness — is no longer the latest top-level ID, so a `F.b.1` sub-number is disallowed by the phase-letter rules; F.g–F.j are locked by cross-references, so renumbering to insert before them is also disallowed. F.f.1 is the placement that preserves performed-order without touching a locked ID.)

**Root cause (debug Steps 1–2).** Two independent defects:

- **B1 — native crash.** PyTorch's MPS backend and TensorFlow-Metal cannot coexist in one process. Narrowing (four isolated-subprocess permutations) showed `torch → keras` and `torch → tf → keras` crash with SIGBUS, while `keras`-only and `tf → keras` pass. Once `torch.mps` claims the system Metal device, the later TF-Metal Grappler optimization that Keras's TF backend triggers on `fit()` faults on misaligned memory. This is **not** a version-pin problem — it reproduces with a clean stack and cannot be fixed by editing `environment.yml`.
- **B2 — silent failure.** `metal_smoke.py` ran all frameworks in one process and wrapped each probe in `try/except Exception`, which cannot catch native (signal) termination. The SIGBUS killed the process before the summary printed, so the only failure mode that actually occurs was invisible.

**Fix (debug Steps 3–4).** Restructure `metal_smoke.py` as a driver/worker split: each framework probe runs in its own subprocess (`--probe <name>`), the driver (which imports no framework itself) collects each child's exit code and reports `PASS` / `FAIL (exit N)` / `CRASH (signal N, exit 128+N)`. Process isolation makes B1 impossible (no two Metal clients share a process) and B2 loud (a native crash surfaces as a negative child returncode). Verified on developer M3 Max hardware: all four probes `PASS`, `exit=0`.

- [x] Reproduce: confirm `metal_smoke.py` exits 138 (SIGBUS) during the Keras section on the refreshed env (developer M3 Max)
- [x] Narrow root cause via `scripts/keras_metal_narrow.py` — isolate that `torch`-preceding-`keras` is the trigger, not TensorFlow and not the env anomalies
- [x] Rewrite `scripts/metal_smoke.py` as a subprocess-isolated driver/worker (`drive()` + `_run_probe()` + `--probe`); driver process imports no ML framework
- [x] Fix the `ml-datarefinery` import probe: distribution name is `ml-datarefinery`, import name is `datarefinery` (sklearn-style); old probe used the wrong name and was masked by the SIGBUS
- [x] Add hardware-independent regression test `tests/unit/test_metal_smoke.py` — asserts per-framework subprocess isolation and that a native crash is reported, not swallowed (the B2 invariant); 4 tests pass
- [x] `ruff` clean; `mypy` introduces no new errors (pre-existing framework `import-not-found` only)
- [x] Verify on developer Apple Silicon: `pyve run python scripts/metal_smoke.py` reports all probes `PASS` and `exit=0`
- [x] Bump version to v0.34.1
- [x] Update CHANGELOG.md
- [x] **Housekeeping — env hygiene (separate from the SIGBUS, not its cause):** the resolved env carries a duplicate `tensorflow 2.16.2` (conda-forge) alongside the requested `tensorflow-macos 2.16.2`, and a standalone `keras 3.14.1` rather than TF's bundled Keras — both pulled transitively (likely via `transformers`/`datasets`/`peft`). `tf → keras` passes with these present, so they are not the crash cause, but they violate the F.b "no standalone keras / Apple TF only" intent. **Upgraded to a real bug + tracked in F.f.2** (Constrain template transitives) after F.e's `test_keras_is_the_tf_bundled_namespace` guard fired on it during the 2026-05-29 verify pass on M3 Max. F.f.2 is blocked on the pyve named-testenvs feature bundle.
- [ ] **Follow-up (deferred to `plan_phase`):** the subprocess-isolation pattern proven here is the basis for a platform-detecting diagnostic CLI plus an `docs/specs/apple-metal-micromamba-pip.md` spec capturing the Metal/micromamba/pip gotchas (torch+TF co-residence, transitive contamination, dist-vs-import names). Recommend at the gate, not started in this cycle.
- [ ] **Throwaway diagnostics:** `scripts/keras_metal_fit_repro.py` and `scripts/keras_metal_narrow.py` are debug-cycle reproduction scratch; the regression is now covered by `tests/unit/test_metal_smoke.py`. Recommend deletion (developer's call) once the fix is committed.
- [ ] **Prevention scan — same pattern elsewhere:** the per-framework hardware smokes (`tests/integration/test_e2e_{pytorch,keras,huggingface,tensorflow}.py`) each import their own framework, but a no-path-filter `pyve test -m hardware` collects them all into a single pytest process, re-creating torch + keras co-residence and the same SIGBUS risk. The documented per-file run procedure (one `pyve test <file> -m hardware` invocation each) is isolated and safe; the footgun is the un-filtered run. Options for a follow-up: enforce per-file invocation (process isolation via `pytest-forked`/subprocess), or guard with a session-scoped check. Not fixed in this cycle — captured here.
- [x] **pyve testenv trap — documented + fixed in pyve:** the prevention-scan discussion found that `pyve test` routes to a stack-less venv testenv even when the bundled `environment.yml` main env has both pytest and the stack, so hardware smokes **silently skip**. Captured in `docs/specs/phase-f-pyve-micromamba-testenv-trap.md`; pyve shipped `pyve test --env main` + a silent-skip advisory in response.
- [x] **pyve named-testenvs — context brief for pyve planning:** authored `docs/specs/phase-f-pyve-named-testenvs.md`, a use-case/requirements brief (light-CI-vs-heavy-smoke envs, conda/runtime parity, native-dep backends, payload-fidelity, polyglot) to drive a pyve planning phase for general **named / multiple test environments**. Implementation is pyve's, in the pyve repo — tracked here only as the debug-cycle paper trail.
- [ ] **e2e smoke run-procedure docstrings (deferred):** the F.c–F.f `test_e2e_*.py` docstrings (and the F.f run-procedure block) still say "run from inside the repo: `pyve test …`", which silently skips per the testenv trap. Correct form is the main-env runner (`pyve test --env main <repo>/… -m hardware`, or `pyve run python -m pytest …` on older pyve), one file at a time. Held pending the pyve named-testenvs direction to avoid churn; update once that lands.

**Run procedure** — the F.b verify, now expected green:

```bash
mkdir env-refresh-test && cd env-refresh-test
cp <repo>/src/nbfoundry/templates/environment.yml .
pyve init --backend micromamba
pyve run python <repo>/scripts/metal_smoke.py   # all probes PASS, exit 0
```

### Story F.f.2: v0.34.2 Constrain template transitives (standalone keras / duplicate tensorflow) [Planned]

> **Blocked on:** the pyve **named test environments** feature bundle — see
> [`phase-f-pyve-named-testenvs.md`](phase-f-pyve-named-testenvs.md). The fix
> itself is a constraint on `src/nbfoundry/templates/environment.yml`, but the
> *verify cycle* (build a micromamba env from the modified template, run F.e's
> hygiene guard + the F.c/F.d/F.f smokes against it, iterate on the constraint)
> is the manual separate-directory dance today and dramatically smoother once
> named testenvs let the stack-bearing env live in-repo. Do not work this story
> before pyve ships that bundle.

Restore the F.b "no standalone keras / Apple TF only" contract that's currently violated by the resolved env. F.f.1's prevention scan flagged this as housekeeping; F.e's `test_keras_is_the_tf_bundled_namespace` guard then caught it as a hard test failure on the developer-hardware verify pass (2026-05-29 on M3 Max): `a standalone keras distribution is installed (3.14.1)`. The same resolution also carries a duplicate `tensorflow 2.16.2` from conda-forge alongside the requested `tensorflow-macos 2.16.2`. Neither is the SIGBUS cause (that was torch+TF-Metal co-residence, fixed in F.f.1), but both violate the manifest's stated intent and trip the regression guard F.b authored against exactly this drift.

**Symptom & evidence:**
- F.e verify on M3 Max 2026-05-29: 1 failed, 1 passed. Training test (`test_keras_3_mps_loss_decreases`) passes. Guard test (`test_keras_is_the_tf_bundled_namespace`) fails on standalone `keras 3.14.1`.
- `pip list` in the resolved env: `tensorflow 2.16.2` (conda-forge) **and** `tensorflow-macos 2.16.2` (pip), plus `keras 3.14.1` standalone — none of which the template explicitly requests.

**Root-cause hypothesis (to confirm in the cycle, not prescribe here):** conda-forge's `transformers` / `datasets` / `peft` recipes pull `tensorflow` and `keras` as optional/runtime deps; the conda solver materializes them even though the template's `pip:` block separately installs Apple's `tensorflow-macos` distribution. Likely fix axes — moving HF deps to the `pip:` block, channel/build constraints, explicit excludes, or `nodefaults` — to be chosen during root-cause analysis.

**Acceptance criteria:**
- F.e's `test_keras_is_the_tf_bundled_namespace` guard passes on developer Apple Silicon (no standalone `keras` distribution installed).
- Resolved env contains exactly one `tensorflow*` distribution, matching the manifest's stated Apple-Silicon choice (`tensorflow-macos`).
- F.e training test (`test_keras_3_mps_loss_decreases`), F.c, F.d, F.f smokes remain green — no regression in the broader stack.
- A hygiene assertion (no standalone `keras`, no duplicate `tensorflow`) is added to the in-repo test suite, runnable via the new pyve named-testenv infrastructure once shipped.

**Tasks** *(all `[ ]` until unblocked)*:

- [ ] Root-cause which conda-forge package(s) pull standalone `keras` and `tensorflow` as transitives in the current template resolution
- [ ] Choose and apply the manifest constraint (move HF to `pip:` / channel constraint / exclude pin / `nodefaults` — picked during investigation)
- [ ] Add an in-repo hygiene assertion test (uses the named-testenv infra to build the env from the modified template and assert: no standalone `keras` distribution; exactly one `tensorflow*` distribution matching the manifest's intent)
- [ ] Verify F.e on developer Apple Silicon: `pyve test --env main <repo>/tests/integration/test_e2e_keras.py -m hardware` — both tests pass
- [ ] Verify F.c / F.d / F.f smokes remain green on the same env (no regression)
- [ ] Run `pyve run python <repo>/scripts/metal_smoke.py` — all probes still `PASS`, `exit=0`
- [ ] Bump version (patch on whatever the line-current version is at ship time; titled v0.34.2 here as the nominal post-F.f.1 patch, but may be revised if F.g/F.h/F.i/F.j ship first)
- [ ] Update `CHANGELOG.md`
- [ ] Flip F.e's `[ ]` verify task to `[x]` with the dated empirical confirmation

**Related:**
- `phase-f-pyve-named-testenvs.md` — the blocker.
- `phase-f-pyve-micromamba-testenv-trap.md` — adjacent pyve issue (now resolved).
- Story F.b — origin contract ("no standalone keras / Apple TF only").
- Story F.e — guard test that surfaced the regression.
- Story F.f.1 — where this was first captured as `[ ]` housekeeping, upgraded here to a real blocker after F.e's guard fired.

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
