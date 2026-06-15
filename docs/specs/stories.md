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

**Reframed 2026-06-13 around Pyve v3.0.6 named environments.** The per-framework smoke envs declared in `pyve.toml` and specified in `docs/specs/env-dependencies.md` (`smoke-torch` and `smoke-tensorflow` — lazy `venv`, pip requirements) replace the original single-bundled-env smoke model. This dissolves both Phase F debug-cycle bugs at the env layer (F.f.1 torch/TF co-residence SIGBUS; F.f.2 standalone-keras hygiene) and unblocks the phase. See the plan doc's "Named-Environment Reframe" section; the migration is story F.f.3.

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

**Run procedure (one-time per release, on developer Apple Silicon)** — migrated to the named-env model (F.f.3):

```bash
pyve test --env smoke-tensorflow tests/integration/test_e2e_tensorflow.py -m hardware
```

`smoke-tensorflow` (declared in `pyve.toml`; deps in `tests/integration/env/tensorflow.txt`) is a lazy-provisioned venv that pip-installs `tensorflow-macos` + `tensorflow-metal` on first targeted use — no micromamba, no `environment.yml`, no PyPI install of nbfoundry (this framework smoke `importorskip`s only TensorFlow). The `@pytest.mark.hardware` marker is gated out by default via `addopts = "-ra -m 'not hardware'"` in `pyproject.toml`, so routine `pyve test` runs skip it; the developer opts in with `-m hardware`. Run one smoke file per process.

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

**Run procedure** — migrated to the named-env model (F.f.3):

```bash
pyve test --env smoke-torch tests/integration/test_e2e_pytorch.py -m hardware
```

`smoke-torch` (declared in `pyve.toml`; deps in `tests/integration/env/torch.txt`) is the lazy-provisioned torch-family venv (torch + HuggingFace + Optuna; no TensorFlow — the F.f.1 boundary). One smoke file per process.

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

**Run procedure** — migrated to the named-env model (F.f.3):

```bash
pyve test --env smoke-tensorflow tests/integration/test_e2e_keras.py -m hardware
```

Keras runs in `smoke-tensorflow` (Keras 3 is the TF-bundled namespace). With HuggingFace absent from this env, `test_keras_is_the_tf_bundled_namespace` passes by construction — no standalone `keras` transitive can reach it. One smoke file per process.

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

**Run procedure** — migrated to the named-env model (F.f.3), plus a cache-warmup caveat:

```bash
pyve test --env smoke-torch tests/integration/test_e2e_huggingface.py -m hardware
```

HuggingFace rides the torch backend, so it runs in `smoke-torch` alongside PyTorch and Optuna (deps in `tests/integration/env/torch.txt`). One smoke file per process. The first run downloads `sshleifer/tiny-gpt2` (~5MB) into `~/.cache/huggingface/hub`. Subsequent runs read from cache. If you are behind a corporate proxy or running in an environment without internet access, set `HF_HUB_OFFLINE=1` only *after* the cache has been warmed at least once.

### Story F.f.1: v0.34.1 Fix silent SIGBUS in metal_smoke.py (framework co-residence) [Done]

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
- [x] **Housekeeping — env hygiene (separate from the SIGBUS, not its cause):** the resolved env carries a duplicate `tensorflow 2.16.2` (conda-forge) alongside the requested `tensorflow-macos 2.16.2`, and a standalone `keras 3.14.1` rather than TF's bundled Keras — both pulled transitively (likely via `transformers`/`datasets`/`peft`). `tf → keras` passes with these present, so they are not the crash cause, but they violate the F.b "no standalone keras / Apple TF only" intent. **Upgraded to a real bug** after F.e's `test_keras_is_the_tf_bundled_namespace` guard fired on it during the 2026-05-29 verify pass on M3 Max. **Resolved structurally in the Pyve v3.0.6 named-env reframe (2026-06-13):** the per-framework smoke-env split (F.f.3) keeps HuggingFace out of `smoke-tensorflow`, so the standalone-keras transitive cannot reach the env that owns the Keras-hygiene contract and F.e's guard passes by construction. The original constrain-transitives story F.f.2 is closed as obsolete.
- [x] **Follow-up — dispositioned in the v3.0.6 named-env reframe (2026-06-13):** the Metal/micromamba/pip gotchas (torch+TF co-residence, transitive contamination, dist-vs-import names) are captured in `docs/specs/project-essentials.md` at this phase's project-essentials step; the platform-detecting diagnostic CLI built on the subprocess-isolation pattern is **deferred** as its own future feature (plan-doc Out of Scope). The `apple-metal-micromamba-pip.md` spec is subsumed by the `env-dependencies.md` env topology + the project-essentials capture.
- [x] **Throwaway diagnostics → folded into F.f.3 housekeeping:** `scripts/keras_metal_fit_repro.py` and `scripts/keras_metal_narrow.py` are debug-cycle reproduction scratch; the regression is now covered by `tests/unit/test_metal_smoke.py`. Their deletion is an F.f.3 task.
- [x] **Prevention scan — resolved-by-topology in the v3.0.6 reframe:** the footgun was that a no-path-filter `pyve test -m hardware` collected all `test_e2e_*.py` into one process, re-creating torch + TF co-residence. Under the named-env split (F.f.3) no single smoke env contains both torch and TensorFlow (`smoke-torch` = torch-family incl. HuggingFace/Optuna; `smoke-tensorflow` = TF/Keras), so even an unfiltered `pyve test --env smoke-<fw> -m hardware` run loads at most one of the two conflicting Metal clients — the others `importorskip` and skip. Co-residence is structurally impossible; no `pytest-forked`/session-guard is needed.
- [x] **pyve testenv trap — documented + fixed in pyve:** the prevention-scan discussion found that `pyve test` routes to a stack-less venv testenv even when the bundled `environment.yml` main env has both pytest and the stack, so hardware smokes **silently skip**. Captured in `docs/specs/phase-f-pyve-micromamba-testenv-trap.md`; pyve shipped `pyve test --env main` + a silent-skip advisory in response.
- [x] **pyve named-testenvs — context brief for pyve planning:** authored `docs/specs/phase-f-pyve-named-testenvs.md`, a use-case/requirements brief (light-CI-vs-heavy-smoke envs, conda/runtime parity, native-dep backends, payload-fidelity, polyglot) to drive a pyve planning phase for general **named / multiple test environments**. Implementation is pyve's, in the pyve repo — tracked here only as the debug-cycle paper trail.
- [x] **e2e smoke run-procedure docstrings → folded into F.f.3:** the F.c–F.f `test_e2e_*.py` docstrings (and the F.f run-procedure block) still describe the old single-bundled-env / `--env main` recipe. The named-env reframe supersedes that with the per-framework one-liner `pyve test --env smoke-<fw> tests/integration/test_e2e_<fw>.py -m hardware`; migrating the docstrings is an F.f.3 task.

**Run procedure** — the F.b verify, now expected green:

```bash
mkdir env-refresh-test && cd env-refresh-test
cp <repo>/src/nbfoundry/templates/environment.yml .
pyve init --backend micromamba
pyve run python <repo>/scripts/metal_smoke.py   # all probes PASS, exit 0
```

### Story F.f.2: Constrain template transitives (standalone keras / duplicate tensorflow) [Closed — obsoleted]

**Closed 2026-06-13 by the Pyve v3.0.6 named-environment reframe — superseded by F.f.3.** This story was going to constrain `src/nbfoundry/templates/environment.yml` so its resolved env wouldn't pull a standalone `keras 3.x` (fighting TF's bundled copy) or a duplicate conda-forge `tensorflow` alongside Apple's `tensorflow-macos`. F.e's `test_keras_is_the_tf_bundled_namespace` guard caught that drift on the 2026-05-29 M3 Max verify (`a standalone keras distribution is installed (3.14.1)`). It was blocked on the pyve named-testenvs feature bundle, which shipped in Pyve v3.0.6.

**Why it's obsolete (resolved by topology, not by constraining the solver):** under the per-framework smoke-env split (F.f.3), `smoke-tensorflow` ships TensorFlow only — no HuggingFace — so the conda-forge `transformers`/`datasets`/`peft` recipes that transitively pulled a standalone `keras` are simply *not present* in the env that owns the Keras-hygiene contract. F.e's guard therefore passes **by construction**, with no manifest constraint required for the dev-side smoke surface. The original constrain-transitives investigation (move HF to `pip:` / channel constraints / `nodefaults`) is no longer needed.

**Deliberately NOT covered (deferred elsewhere):** the *learner-facing* bundled payload `src/nbfoundry/templates/environment.yml` still co-locates HuggingFace + TensorFlow and therefore still pulls a standalone `keras` when a learner builds it via `pyve init --backend micromamba`. That hygiene concern is real but out of scope here — it is tracked with the bundled-payload split into per-applied-series env recipes (`docs/specs/env-dependencies.md` § "Bundled-payload manifest"; the LearningFoundry applied-exercise architecture). F.f.3 does not touch the bundled payload. The original v0.34.2 version slot moves to F.f.3.

**Related:**
- Story F.f.3 — the named-env migration that supersedes this story.
- `docs/specs/env-dependencies.md` — the env topology that makes the dev-side guard pass by construction.
- Story F.b — origin contract ("no standalone keras / Apple TF only").
- Story F.e — guard test that surfaced the regression; its open verify is closed by F.f.3.
- Story F.f.1 — where this was first captured as `[ ]` housekeeping before being upgraded to its own story.

### Story F.f.3: v0.34.2 Per-framework smoke-env manifests + migrate hardware smokes [Done]

Stand up the Pyve v3.0.6 named test environments for the hardware smokes and migrate F.c–F.f onto them. This is the unit that makes the named-env reframe real: it authors the two per-framework-family smoke requirements files `pyve.toml` declares (`torch.txt`, `tensorflow.txt`), repoints the smoke run procedures from the old single-bundled-env / `--env main` dance to the named-env one-liner, and re-verifies every framework smoke green under its env on developer hardware — closing F.e's open verify by construction. See `docs/specs/env-dependencies.md` §5.2–5.3 for the intended requirements contents and the four-env rationale, and the plan doc's "Named-Environment Reframe" section.

**Why now:** the named-testenv capability F.f.2 was blocked on shipped in Pyve v3.0.6, but the requirements files `pyve.toml` references (`tests/integration/env/*.txt`) do not yet exist, so the smokes cannot run under the new model until this lands. This story also discharges F.f.1's deferred docstring + diagnostics-deletion follow-ups. (The smoke envs are `venv` + pip — every dep is a macOS arm64 wheel — so no micromamba is involved.)

- [x] Author `tests/integration/env/torch.txt` (venv, pip requirements) — the **torch-family** env covering F.d PyTorch + F.f HuggingFace (and F.g Optuna once it lands): `torch>=2.5`, `transformers`, `datasets`, `peft`, `sentencepiece`, `protobuf`, `tiktoken`, `numpy`, `pytest`; **no** `tensorflow*` / standalone `keras` — their absence guarantees no torch-MPS + TF-Metal co-residence (F.f.1) and no keras-hygiene contamination (F.f.2). Interpreter inherited from the project venv. Per `env-dependencies.md §5.2`.
- [x] Author `tests/integration/env/tensorflow.txt` (venv, pip requirements) — the **TensorFlow-family** env covering F.c TF + F.e Keras: `tensorflow-macos>=2.16`, `tensorflow-metal>=1.1`, `numpy`, `pytest`; **no** standalone `keras`, **no** torch/HF — this absence is the structural fix to the F.f.2 keras-hygiene problem. Per `env-dependencies.md §5.3`.
- [x] Framework-only requirements — confirm none install `nbfoundry`: the F.c–F.f tests `importorskip` only their framework and never `import nbfoundry`; published-surface validation stays with F.h–F.j. (Confirmed: neither `*.txt` lists `nbfoundry`; the docstrings now state each smoke does not import nbfoundry. Locked by `tests/unit/test_smoke_env_requirements.py`.)
- [x] Apache-2.0 / Pointmatic header on each new `*.txt` (pip requirements; `#` comments).
- [x] Migrate run-procedure prose in the F.c / F.d / F.f story bodies **and** the `test_e2e_{tensorflow,pytorch,keras,huggingface}.py` module docstrings: replace the `mkdir <fw>-smoke && cp environment.yml && pyve init --backend micromamba && pip install nbfoundry==… && pyve test --env main …` recipe with the named-env one-liner `pyve test --env smoke-<fw> tests/integration/test_e2e_<fw>.py -m hardware` (lazy-provisioned, in-repo, one file per process). Discharges F.f.1's deferred "e2e docstring" follow-up. (F.e's story-body block also migrated for consistency.)
- [x] Delete throwaway debug scratch `scripts/keras_metal_fit_repro.py` and `scripts/keras_metal_narrow.py` (regression now covered by `tests/unit/test_metal_smoke.py`). Discharges F.f.1's "throwaway diagnostics" follow-up.
- [x] Bump version to v0.34.2 (patch; test-env scaffolding + docs, no public-surface change — inherits the version slot vacated by the closed F.f.2).
- [x] Update `CHANGELOG.md`.
- [ ] **Verify on developer Apple Silicon** (lazy-provisioned named envs, one file per process) — **deferred to developer hardware**:
  - [ ] `pyve test --env smoke-torch tests/integration/test_e2e_pytorch.py -m hardware` → passes.
  - [ ] `pyve test --env smoke-torch tests/integration/test_e2e_huggingface.py -m hardware` → passes.
  - [ ] `pyve test --env smoke-tensorflow tests/integration/test_e2e_tensorflow.py -m hardware` → passes.
  - [ ] `pyve test --env smoke-tensorflow tests/integration/test_e2e_keras.py -m hardware` → **both** tests pass, including `test_keras_is_the_tf_bundled_namespace` (no standalone keras present, by construction). **Then flip F.e's open `[ ]` verify task to `[x]`** with the dated confirmation.

**Note on `scripts/metal_smoke.py`:** unchanged by this story. It remains a standalone full-stack diagnostic (the subprocess-isolated driver/worker from F.f.1) run against a bundled-payload micromamba env; it is **not** one of the named pytest smoke envs and keeps its own run procedure. *(F.f.4 then converts that bundled payload to venv and reconciles/retires this script.)*

### Story F.f.4: v0.34.3 Convert learner stack from conda environment.yml → per-stage venv/pip requirements [Done]

The last conda holdout. F.f.3 and the `plan_envs` reframe moved every `pyve.toml` env to `venv`; this story moves the **learner-facing** stack — the bundled `src/nbfoundry/templates/environment.yml` shipped into every scaffolded project — off conda/micromamba and onto per-stage venv/pip requirements, making the project **exclusively venv**. The per-stage split (vs. one combined file) gives learners the same co-residence-impossible-by-construction property the dev smoke envs got: `torch` and `tensorflow` are never installed into the same venv, so a learner cannot hit the F.f.1 SIGBUS. See `docs/specs/env-dependencies.md` and the plan doc's "Named-Environment Reframe → Conda fully eliminated (F.f.4)" subsection.

**Stack form** — three composable pip files mirroring the dev envs `testenv` / `smoke-torch` / `smoke-tensorflow`:

| File | Contents |
|---|---|
| `templates/requirements-base.txt` | agnostic core: numpy, scipy, pandas, pyarrow, matplotlib, seaborn, plotly, scikit-learn, pillow, h5py, marimo, pyyaml, click, rich, python-dotenv, ml-datarefinery |
| `templates/requirements-torch.txt` | `-r requirements-base.txt` + torch + transformers, datasets, peft, sentencepiece, protobuf, tiktoken + optuna |
| `templates/requirements-tf.txt` | `-r requirements-base.txt` + tensorflow-macos + tensorflow-metal |

Stage → file: `data_exploration` / `data_preparation` → `requirements-base.txt`; `model_experimentation` / `model_optimization` / `model_evaluation` → `requirements-torch.txt` (all three model templates are torch-based today). `requirements-tf.txt` is not bound to a shipped template — it's the TF-based-learner option, validated by `smoke-tensorflow`.

- [x] Author `templates/requirements-base.txt`, `requirements-torch.txt`, `requirements-tf.txt` (pip; `-r` base includes; Apache-2.0 `#` headers). Carry cross-platform swap guidance as pip comments: torch CUDA via `--index-url`/`--extra-index-url` (cpu/cu126/cu128); `tensorflow-macos`+`tensorflow-metal` → `tensorflow` (or `tensorflow[and-cuda]`) for non-Mac. (Stack follows the F.f.4 table; dev tooling — `ruff`/`mypy`/`pytest` — is **not** carried in the learner stack per the table, a content change from the old conda env; flag at gate if learner dev-tooling is wanted back.)
- [x] **Delete** `src/nbfoundry/templates/environment.yml` (the conda bundled payload).
- [x] Update the scaffolder (`cli.py` `cmd_init`): `nbfoundry init <name> --template <stage>` emits the **stage-appropriate** requirements file (base for `data_*`, torch+base for `model_*`) instead of the shared `environment.yml`. `_emit_shared_env` → `_emit_stage_requirements`.
- [x] Update `standalone.py` so `nbfoundry compile` emits the stage-appropriate requirements file into the standalone artifact (`_ensure_requirements`: preserve any adjacent `requirements*.txt`, fall back to `requirements-base.txt`).
- [x] Reconcile `scripts/metal_smoke.py` with per-stage venv. **Decided: (b) retire** — the named smoke envs (`smoke-torch`/`smoke-tensorflow`, F.f.3) already validate each framework on Metal via pytest, so a venv-based full-stack diagnostic would just duplicate them. Deleted `scripts/metal_smoke.py` **and** its regression `tests/unit/test_metal_smoke.py` (the subprocess-isolation invariant it guarded is now structurally guaranteed: no env holds both frameworks). `scripts/` is now empty and removed.
- [x] Drop `conda-lock` from the stack (pip-tools `pip-compile --generate-hashes` is the venv lock path; lockfile generation itself remains a Phase H follow-up). (conda-lock lived only in the deleted `environment.yml`; also struck from the tech-spec stack table.)
- [x] **Reverse the micromamba constraint in the foundational docs** (the constraint change that authorizes the whole reframe):
  - `concept.md` Constraints (+ vision/pain-point mentions) — Pyve + micromamba → Pyve + **venv**; the Metal stack is pip-installable on Apple Silicon.
  - `features.md` — CR-10, QR-1, AC-5, PE-3, env-manifest output, config `spec_path`: micromamba/`environment.yml` → venv/pip requirements.
  - `tech-spec.md` — env-management row, system-deps, "Pinned ML stack" section, package-structure tree, atomic-write step, config example, distribution row: conda `environment.yml` → per-stage pip requirements; micromamba → venv.
  - `README.md` — Installation + Apple Silicon quickstart + cross-platform: `pyve init --backend micromamba` + `environment.yml` + `metal_smoke.py` → `nbfoundry init` + `pyve init` (venv) + `pip install -r requirements-<stage>.txt`.
- [x] Bump version to v0.34.3 (patch; continues the reframe arc — a shipped-template format change, no API change).
- [x] Update `CHANGELOG.md`.
- [ ] Verify on developer Apple Silicon: `nbfoundry init demo --template model_experimentation` emits `requirements-torch.txt`; `pyve init` + `pip install -r requirements-torch.txt` builds a working torch/MPS venv; a `data_*` scaffold emits `requirements-base.txt` and builds with no ML framework present. **No conda/micromamba anywhere in the flow.** — **deferred to developer hardware** (the emission half is covered by `tests/integration/test_cli_init_requirements.py`; the venv-build-on-MPS half is the hardware verify).

**Out of scope (unchanged):** the learner-side *per-applied-series* env recipes (LearningFoundry applied-exercise architecture) remain a separate future track — this story changes only the *format* (conda → per-stage venv) of the existing bundled payload, not the per-series decomposition. The latent same-process torch+tf footgun is now structurally removed for learners (the two are never co-installed).

### Story F.g: v0.35.0 Optuna hyperparameter search happy path [Done]

End-to-end smoke running a small `optuna` study against a tiny PyTorch model. Runs in the **`smoke-torch`** named env (Optuna rides the torch family), per `env-dependencies.md §6` ("F.g folds into `smoke-torch`").

- [x] Add `optuna` to `tests/integration/env/torch.txt` (extends the `smoke-torch` pip requirements authored in F.f.3; Optuna is pure-Python and rides torch — no co-residence concern)
- [x] `tests/integration/test_e2e_optuna.py` marked `@pytest.mark.slow` and `@pytest.mark.hardware`
- [x] Test procedure: define a small objective (2 hyperparameters — `lr`, `hidden`) wrapping a tiny PyTorch model on MPS; run a 5-trial Optuna study; assert all 5 trials complete, `study.best_trial` is populated, and `best_value` matches the minimum recorded objective (trial history accessible)
- [x] Budget: under 60s on M-series silicon (5 tiny trials)
- [x] Apache-2.0 / Pointmatic header
- [x] Document the named-env run procedure in the story body and the test-module docstring
- [x] Bump version to v0.35.0
- [x] Update CHANGELOG.md
- [ ] Verify: `pyve test --env smoke-torch tests/integration/test_e2e_optuna.py -m hardware` passes on developer Apple Silicon — **deferred to developer hardware**

**Run procedure** — named-env model, on developer Apple Silicon:

```bash
pyve test --env smoke-torch tests/integration/test_e2e_optuna.py -m hardware
```

Optuna rides the torch family, so it runs in `smoke-torch` (deps in `tests/integration/env/torch.txt`, which now includes `optuna`) alongside PyTorch and HuggingFace. One smoke file per process. The test is deselected by the default `-m 'not hardware'`; opt in with `-m hardware`.

### Story F.h: v0.36.0 data_exploration template happy path [Planned]

End-to-end smoke against the scaffolded `data_exploration` template, exercising the framework-agnostic load → describe → visualize flow on synthetic data.

> **Env/marker (named-env reframe — finalize when this body is implemented):** this template is framework-agnostic (pandas / scikit-learn / matplotlib / marimo + `nbfoundry`, no torch/TF/Metal), so it does **not** fit either per-framework-family `smoke-*` env and likely needs no Metal hardware. **Current lean:** drop `@pytest.mark.hardware` and run it in the default **`testenv`** (which already CLI-tests the editable `nbfoundry`), adding the template's light deps there — rather than spawning a third smoke env. Unlike F.c–F.f, this smoke **does** invoke `nbfoundry init`, so it is also where published-surface validation lives if run against the PyPI install. **Payload-fidelity option (after F.f.4):** build the stage's shipped `templates/requirements-base.txt` in a dedicated lazy env and run the smoke against *exactly what ships* — higher fidelity than adding ad-hoc deps to `testenv`. Decision surfaced at this story's gate.

- [ ] Decide the env + marker per the note above (lean: `testenv`, no `@pytest.mark.hardware`); record the choice in the body before implementing
- [ ] `tests/integration/test_e2e_template_data_exploration.py` (marker per the decision above)
- [ ] Test procedure: `nbfoundry init demo --template data_exploration` in a temp dir; create synthetic input data the template expects; run the scaffolded notebook end-to-end (via `marimo edit --headless` or equivalent); assert each cell completes and the expected describe/visualize outputs are produced
- [ ] Budget: under 60s on M-series silicon
- [ ] Apache-2.0 / Pointmatic header
- [ ] Document the run procedure (named-env form) in the story body
- [ ] Bump version to v0.36.0
- [ ] Update CHANGELOG.md
- [ ] Verify on developer hardware (exact invocation per the env decision; e.g. `pyve test --env testenv tests/integration/test_e2e_template_data_exploration.py`) — **deferred to developer hardware**

### Story F.i: v0.37.0 data_preparation template happy path [Planned]

End-to-end smoke against the scaffolded `data_preparation` template, exercising the cleaning → feature engineering → split scaffolding.

> **Env/marker:** same framework-agnostic situation as F.h — see F.h's env/marker note (lean: default `testenv`, drop `@pytest.mark.hardware`). Decide and record at this story's gate.

- [ ] Decide the env + marker per F.h's note (lean: `testenv`, no `@pytest.mark.hardware`); record the choice in the body before implementing
- [ ] `tests/integration/test_e2e_template_data_preparation.py` (marker per the decision above)
- [ ] Test procedure: `nbfoundry init demo --template data_preparation` in a temp dir; create synthetic input data; run the scaffolded notebook end-to-end; assert clean splits are produced with the expected shapes and class balance
- [ ] Budget: under 60s on M-series silicon
- [ ] Apache-2.0 / Pointmatic header
- [ ] Document the run procedure (named-env form) in the story body
- [ ] Bump version to v0.37.0
- [ ] Update CHANGELOG.md
- [ ] Verify on developer hardware (exact invocation per the env decision) — **deferred to developer hardware**

### Story F.j: v0.38.0 model_evaluation template happy path [Planned]

End-to-end smoke against the scaffolded `model_evaluation` template, exercising the held-out evaluation → confusion matrix → calibration scaffolding.

> **Env/marker:** same framework-agnostic situation as F.h — see F.h's env/marker note (lean: default `testenv`, drop `@pytest.mark.hardware`). Decide and record at this story's gate. As the last Phase F story, this is the natural place to confirm the phase-level acceptance check below passes end-to-end.

- [ ] Decide the env + marker per F.h's note (lean: `testenv`, no `@pytest.mark.hardware`); record the choice in the body before implementing
- [ ] `tests/integration/test_e2e_template_model_evaluation.py` (marker per the decision above)
- [ ] Test procedure: `nbfoundry init demo --template model_evaluation` in a temp dir; provide a pre-trained tiny model + holdout split (synthetic); run the scaffolded notebook end-to-end; assert confusion matrix is rendered and calibration plot is produced
- [ ] Budget: under 60s on M-series silicon
- [ ] Apache-2.0 / Pointmatic header
- [ ] Document the run procedure (named-env form) in the story body
- [ ] Bump version to v0.38.0
- [ ] Update CHANGELOG.md
- [ ] Verify on developer hardware (exact invocation per the env decision) — **deferred to developer hardware**

Phase-level acceptance check (covers AC-4 / AC-5 / CR-10 against the refreshed stack), in two parts after the named-env reframe:

- **Dev-side framework smokes (F.c–F.g):** from a fresh clone on Apple Silicon, `pyve init` + `pyve test` pass the light surface, then each hardware smoke runs green via its lazy-provisioned named env — `pyve test --env smoke-torch …` (PyTorch, HuggingFace, Optuna) and `--env smoke-tensorflow …` (TF + Keras) — with no SIGBUS and F.e's keras-hygiene guard passing by construction.
- **Learner-facing template path (F.h–F.j):** a clean Apple Silicon machine can `pyve init --backend micromamba` against the bundled `templates/environment.yml`, `pip install nbfoundry==v0.38.0` from PyPI, `nbfoundry init demo --template <each>` for all five templates, and run each scaffolded notebook to completion with the relevant tool exercised.

Each story above carries its own minimal pass/fail check; the phase-level acceptance is the integral of those.

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

QR-4 / TR-5 — strict typing across nbfoundry's **typed surface** (the ML-free compiler/CLI/schema). The author notebook **templates** are excluded — they import the ML stack only as example code and are full of intentional unannotated marimo cells; their correctness is covered by the F.h–F.j template smokes, not by strict typing. nbfoundry's real surface is ML-free (FR-7), so this runs in the light `testenv` with **no** ML deps — see `env-dependencies.md §5.1` "mypy scope".

- [ ] Configure `[tool.mypy]` in `pyproject.toml` with `strict = true`, `mypy_path = "src"`, `packages = ["nbfoundry"]`, **and `exclude` covering `src/nbfoundry/templates/`** (mirrors the existing `[tool.ruff] extend-exclude`; final regex tuned at implementation). This keeps the typed surface ML-free and the typecheck env light.
- [ ] Resolve every strict-mode error in `src/nbfoundry/` **excluding `templates/`** (the 13 real package modules already type-clean today; the only pre-existing errors are in the excluded templates). Do **not** add the ML stack to `testenv` to silence template `import-not-found` — exclude the templates.
- [ ] Add `types-PyYAML` (already in `requirements-dev.txt`); add any further `types-*` stubs the strict pass surfaces
- [ ] Bump version to v0.42.0
- [ ] Update CHANGELOG.md
- [ ] Verify: `pyve testenv run mypy` reports zero errors (templates excluded; no heavy deps required)

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
