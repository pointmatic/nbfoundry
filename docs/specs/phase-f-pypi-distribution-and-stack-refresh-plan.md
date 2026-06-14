# phase-f-pypi-distribution-and-stack-refresh-plan.md — Phase F Plan

**Status:** Reframed 2026-06-13 for Pyve v3.0.6 named environments (see "Named-Environment Reframe" below); the original single-bundled-env smoke approach is superseded.
**Phase:** F — PyPI Distribution and Stack Refresh
**Predecessor:** Phase E (Pinned ML Stack and Five-Stage Templates), shipped through v0.28.0
**Successor:** Phase G (Testing, Quality, and Documentation)
**Version range:** v0.29.0 – v0.38.0 (stories F.a–F.j, plus follow-ups F.f.1–F.f.3)

Phase F establishes nbfoundry as a real installable package, refreshes the template ML stack from the narrow Apple-only PyTorch+TF+Keras pinning to a broader cross-project stack derived from the proven sentiment-poc environment, and demonstrates per-tool and per-template happy paths on developer Apple Silicon hardware. Phase G is then free to focus on edges, quality, and documentation against a known-working stack.

---

## Named-Environment Reframe (Pyve v3.0.6)

**Added 2026-06-13.** Phase F's smoke stories (F.c–F.j) were originally designed against a *single bundled* `src/nbfoundry/templates/environment.yml` that co-located the entire ML stack (PyTorch + TensorFlow-Metal + bundled Keras + HuggingFace + Optuna + dev tools) in one micromamba env, then smoke-tested by hand-building a side directory and running `pyve test --env main` / `pyve run python -m pytest`. That model produced **both** of the phase's debug-cycle bugs (F.f.1 SIGBUS, F.f.2 keras hygiene). Pyve **v3.0.6** shipped the *named test environments* capability (`pyve.toml` `[env.<name>]`, per-env backend + manifest, `lazy = true`) — the exact capability **F.f.2 was blocked on** — so the phase is reframed around it. The `plan_envs` session that motivated this reframe landed `pyve.toml` and the authoritative env spec `docs/specs/env-dependencies.md`.

**New topology** (authoritative spec: `docs/specs/env-dependencies.md`; declared in `pyve.toml`):

| Env | Backend | Purpose | Manifest |
|---|---|---|---|
| `root` | venv | utility (nbfoundry + runtime deps) | `pyproject.toml` |
| `testenv` (default) | venv | light CI: pytest, ruff, mypy | `requirements-dev.txt` |
| `smoke-torch` | venv, lazy | torch-family: PyTorch (F.d) + HuggingFace (F.f) + Optuna (F.g) | `tests/integration/env/torch.txt` |
| `smoke-tensorflow` | venv, lazy | TensorFlow (F.c) + Keras (F.e) smokes | `tests/integration/env/tensorflow.txt` |

**Both phase bugs dissolve at the env layer:**

- **F.f.1 SIGBUS** (torch-MPS + TF-Metal co-residence) → impossible by construction; each framework family owns its env. The subprocess isolation in `scripts/metal_smoke.py` stays as belt-and-suspenders, no longer load-bearing.
- **F.f.2 keras hygiene** (HuggingFace conda transitives pull a standalone `keras` that fights TF's bundled copy) → `smoke-tensorflow` ships TensorFlow only, so F.e's `test_keras_is_the_tf_bundled_namespace` guard passes *by construction*. The constrain-transitives approach is abandoned.

**Story-level changes:**

- **F.f.1** — flipped to `[Done]` (shipped v0.34.1); open follow-ups dispositioned (docstring fix + diagnostics deletion → F.f.3; prevention-scan → resolved-by-topology; apple-metal diagnostic CLI → deferred, see Out of Scope).
- **F.f.2** — closed as a tombstone, obsoleted by the env split (no code change; the learner-facing bundled-payload hygiene is deferred — see Out of Scope).
- **F.f.3 (new, v0.34.2)** — the migration unit: author the two `tests/integration/env/*.txt` pip requirements (`torch.txt`, `tensorflow.txt`), migrate the F.c–F.f run-procedure prose to the named-env form, and re-verify F.c/F.d/F.e/F.f green under their named envs on developer hardware (closing F.e's open verify).
- **F.c / F.d / F.f** — run-procedure prose only (named-env one-liner); smoke code unchanged.
- **F.g–F.j** — retargeted to the named envs (F.g Optuna → `smoke-torch`; the framework-agnostic F.h–F.j template-smoke env + `@pytest.mark.hardware` marker is finalized when those bodies are implemented — current lean: run in the default `testenv`, no Metal needed).

**Smoke manifests are framework-only.** The F.c–F.f smoke tests `importorskip` only their framework — they never `import nbfoundry` — so the manifests carry framework + numpy + pytest, *not* nbfoundry. PyPI-published-surface validation rides with the F.h–F.j template smokes, which actually invoke `nbfoundry init`.

**New / changed files (beyond the original plan):**

- `tests/integration/env/{torch,tensorflow}.txt` — **new**, the two per-framework-family smoke **venv/pip** requirements (F.f.3; `torch.txt` = torch + HF + optuna). No conda; every dep is a macOS arm64 wheel.
- `pyve.toml`, `docs/specs/env-dependencies.md` — landed by the motivating `plan_envs` session.
- The F.c–F.f `tests/integration/test_e2e_*.py` docstrings — run-procedure prose updated (F.f.3).
- `scripts/keras_metal_{fit_repro,narrow}.py` — **deleted** (F.f.3 housekeeping; regression covered by `tests/unit/test_metal_smoke.py`).

**Acceptance check (revised).** From a fresh clone on Apple Silicon: `pyve init` + `pyve test` (light surface green), then lazily provision and run each hardware smoke via `pyve test --env smoke-<fw> tests/integration/test_e2e_<fw>.py -m hardware` — all green, no SIGBUS, F.e hygiene guard passing. The bundled-payload `pyve init --backend micromamba` learner path remains valid but is no longer the dev-side smoke mechanism.

**Out of Scope (added by this reframe):**

- **Learner-facing bundled `templates/environment.yml` hygiene / per-applied-series split** — the bundled payload still co-locates HF+TF; its split into per-applied-series env recipes is tracked separately per `env-dependencies.md` § "Bundled-payload manifest" and the LearningFoundry applied-exercise architecture. F.f.3 does not touch the bundled payload.
- **`apple-metal-micromamba-pip.md` spec + platform-detecting diagnostic CLI** — F.f.1's deferred follow-up; the core Metal/micromamba/pip gotchas are captured in `project-essentials.md` (this phase's Step 8), but the CLI is its own future feature.
- **Per-env hashed `requirements.txt` lock (pip-tools) for the smoke envs** and **CI wiring of the smoke envs** — Phase H.

---

## Gap Analysis

| Area | What exists (post-E.f) | What's missing for "demonstrated happy path" |
|---|---|---|
| Distribution | Package builds locally via `pyve run pip install -e .`; no PyPI presence | `pip install nbfoundry` from PyPI as a real install path — required for clean-machine end-to-end demos |
| Template env stack | `templates/environment.yml` pinning PyTorch + Apple-only `tensorflow-macos` + standalone `keras` (Metal-only, narrow) | Cross-platform stack derived from the proven sentiment-poc env files; HuggingFace tooling (transformers, datasets, peft); optimization tooling (optuna); standard utilities (pyarrow, plotly, seaborn, pillow, h5py, click, rich, python-dotenv); `ml-datarefinery` (now on PyPI — see Out of Scope) |
| Per-template env files | Five identical copies in each lifecycle template directory | A single sectioned `environment.yml` consumed by all templates — common section + per-stage sections |
| End-to-end execution | Each template scaffolds and compiles; runtime execution deferred to developer hardware (E.a, E.d, E.e verify steps) | Real per-tool smoke runs on developer hardware exercising TF, PyTorch, Keras, HF transformers/datasets/peft, optuna, sklearn, and each lifecycle template |
| Dev tooling in template | Absent from template env (lives in nbfoundry's pyve testenv) | ruff / mypy / pytest in template env so a scaffolded student project is dev-tool-complete out of the box |

---

## Feature Requirements

What Phase F adds (functional):

1. **Published distribution.** Tag-driven build + trusted publish to PyPI under `nbfoundry`. Already wired as story F.a; pre-conditions for every later smoke story in this phase.
2. **Refreshed pinned ML stack.** Single Apple-Silicon-default `templates/environment.yml` covering:
   - **Core scientific stack** — `numpy`, `scipy`, `pandas`, `pyarrow`, `matplotlib`, `seaborn`, `plotly`
   - **Classical ML** — `scikit-learn`
   - **Frameworks** — `pytorch`, `tensorflow-macos` + `tensorflow-metal` (the proven Apple Silicon path)
   - **HuggingFace stack** — `transformers`, `datasets`, `peft`, `sentencepiece`, `protobuf`, `tiktoken`
   - **Hyperparameter optimization** — `optuna`
   - **Utilities** — `pyyaml`, `click`, `rich`, `python-dotenv`
   - **Image/array I/O** — `pillow`, `h5py`
   - **Dev tooling** — `ruff`, `mypy`, `pytest` + plugins
   - **Lockfile generation** — `conda-lock`
   - **Notebook substrate** — `marimo`
   - **Data prep** — `ml-datarefinery` (env inclusion only; full integration deferred to a future phase per Out of Scope)

   **Drops:** `jupyterlab`, `ipykernel`, `ipywidgets` (marimo replaces them); standalone `keras>=3.5` (Keras 3 ships with TF 2.16+ via the bundled `keras` namespace, so an independent install starts version-fighting).

   **Cross-platform users** swap `tensorflow-macos` + `tensorflow-metal` → `tensorflow` (with `[and-cuda]` extra for Linux GPU) per the documented comment block.
3. **Sectioned env.yml.** One file with explicit comment-delimited sections: a shared core, plus per-lifecycle-stage groupings (`# data_exploration`, `# data_preparation`, `# model_experimentation`, `# model_optimization`, `# model_evaluation`). Per-template `environment.yml` copies are removed — every lifecycle template references the single shared file.
4. **Cross-platform swap-points.** Comment guidance covering: PyTorch index URL between cpu/cu126/cu128; `tensorflow-macos` + `tensorflow-metal` → `tensorflow` (or `tensorflow[and-cuda]`) for non-Mac users. Mac users hit the proven path with no edits; everyone else has explicit one-line swaps.
5. **Per-tool happy-path smokes.** Sequenced executable demonstrations on developer Apple Silicon hardware, ordered TensorFlow → PyTorch → Keras → HuggingFace stack → Optuna, plus per-template smokes for the three non-framework-specific stages (data_exploration, data_preparation, model_evaluation). model_experimentation and model_optimization are already framework-specific and covered by the per-framework smokes.

---

## Technical Changes

### New / modified files

- `templates/environment.yml` — rewritten as the sectioned cross-platform stack (F.b).
- `templates/{data_exploration,data_preparation,model_experimentation,model_optimization,model_evaluation}/environment.yml` — **deleted**; templates pick up the shared file via packaging (F.b).
- `src/nbfoundry/templates/__init__.py` (or wherever template assets are registered) — confirm scaffolding copies the shared env.yml into the scaffolded project (F.b).
- `scripts/metal_smoke.py` — extended to import every new package and assert basic functionality (no training step required for the import-smoke layer; framework training stays in per-tool stories) (F.b).
- `.github/workflows/publish.yml` — new; tag-triggered build + PyPI trusted publish (F.a, already drafted).
- `tests/integration/test_e2e_<tool>.py` — one per per-tool/per-template smoke story (F.c–F.j). Marked `@pytest.mark.slow` and `@pytest.mark.hardware` so they're opt-in in CI but run locally.
- `docs/specs/tech-spec.md` — dependency table, env-management section, and "Pinned ML stack" section refreshed to match the new env.yml (F.b).
- `README.md` — quickstart updated; PyPI install path documented (F.a quickstart edit, expanded across F.b).
- `CHANGELOG.md` — entries per story.

### Story breakdown

> **Post-reframe note (2026-06-13):** the table below is the original 10-story plan. Since then F.f.1 (SIGBUS fix, shipped v0.34.1) and F.f.3 (named-env migration, v0.34.2) were added, and F.f.2 was closed as obsolete. See "Named-Environment Reframe" above and `stories.md` for the current sequence; the F.c–F.j *titles/themes* below still hold, but their smoke-env mechanism is the per-framework named envs, not the single bundled env.

| ID | Version | Title | Theme |
|---|---|---|---|
| F.a | v0.29.0 | PyPI publish workflow | Tag-triggered build + trusted publish; documented release procedure |
| F.b | v0.30.0 | Pinned ML stack refresh + sectioned env.yml | Cross-project stack; sectioned single-file env; cross-platform swap-points; per-template env files deleted; `ml-datarefinery` included |
| F.c | v0.31.0 | TensorFlow happy path | E2E smoke importing TF/MPS and training a tiny model |
| F.d | v0.32.0 | PyTorch happy path | E2E smoke importing PyTorch/MPS and training a tiny model |
| F.e | v0.33.0 | Keras 3 happy path | E2E smoke using bundled `tf.keras` (no standalone keras install) |
| F.f | v0.34.0 | HuggingFace stack happy path | E2E smoke covering `transformers` + `datasets` + `peft` (small pretrained, tiny dataset) |
| F.g | v0.35.0 | Optuna hyperparameter search happy path | E2E smoke running a small `optuna` study against one of the framework models |
| F.h | v0.36.0 | data_exploration template happy path | E2E smoke against scaffolded `data_exploration` template (framework-agnostic) |
| F.i | v0.37.0 | data_preparation template happy path | E2E smoke against scaffolded `data_preparation` template (framework-agnostic) |
| F.j | v0.38.0 | model_evaluation template happy path | E2E smoke against scaffolded `model_evaluation` template (framework-agnostic) |

`model_experimentation` and `model_optimization` templates are exercised transitively by F.c–F.g (the per-framework smokes use those stages); no dedicated template-smoke stories are needed for them.

### Renumbering impact on downstream phases

Already reflected in the developer-edited `stories.md`:

- **Phase G** (Testing, Quality, and Documentation) — stories G.a–G.f, versions assigned v0.39.0–v0.43.0 (G.f is the doc-polish story, ships under v0.43.0 without its own bump).
- **Phase H** (CI/CD, renamed from "CI/CD and Non-production Release" per the v1.0.0-deferred decision) — stories H.a–H.b, versions v0.44.0–v0.45.0.
- **`?.?` Production release** (v1.0.0) — moved to `## Future` as a deferred story; not scheduled, not blocking. May surface as a Phase I when project posture changes.

### Sequencing constraints

- **F.a before F.h–F.j.** *(Revised by the named-env reframe.)* The PyPI install path (`pip install nbfoundry==<published-version>`) is exercised by the **template** smokes F.h–F.j, which invoke `nbfoundry init`. The framework smokes F.c–F.g `importorskip` only their framework and never `import nbfoundry`, so they no longer depend on F.a's publish.
- **F.f.3 before F.c–F.j re-verify.** The per-framework `tests/integration/env/*.txt` pip requirements are authored in F.f.3; no hardware smoke can run under the named-env model until they exist. They are informed by F.b's stack-version choices but are focused venv requirements, not copies of the conda bundled env.
- **F.c–F.g (per-tool) before F.h–F.j (per-template).** Framework correctness is established before being layered into stage-specific demos.

### Acceptance check at end of phase

A clean Apple Silicon machine can:
1. `pyve init --backend micromamba` against the new `environment.yml`
2. `pip install nbfoundry==v0.38.0` from PyPI
3. `nbfoundry init demo --template <each>` for each of the five templates
4. Run each scaffolded notebook to completion with the relevant tool exercised

Each story carries its own minimal pass/fail check; the phase-level acceptance check is the integral of the per-story checks.

---

## Out of Scope (Deferred)

Confirmed with developer at plan time; each item is genuinely deferrable, not a hidden requirement.

- **Per-platform lockfiles** (`conda-lock.yml` for cpu / gpu / metal). Deferred — revisit when full CI on Linux/CUDA is in place. `conda-lock` is included in the env so users can generate their own locally.
- **One-shot installer / `nbfoundry env install`.** Deferred — once the env stabilizes, an installer wrapping `pyve init --backend micromamba` is a candidate enhancement.
- **CUDA / Linux execution validation.** Tech-spec QR-3 keeps Linux/CUDA "best-effort" through v1; the env has documented CUDA swap-points but no smokes target CUDA hardware in this phase.
- **Edge cases, error paths, validator coverage, mypy --strict, ≥85% coverage.** All Phase G work.
- **CI lint/test workflow, coverage badge.** Phase H work.
- **v1.0.0 production release.** Deferred indefinitely to `## Future` in stories.md — single-developer / single-user project posture does not warrant the production-release ceremony at this time.
- **DataRefinery adapter and template integration in nbfoundry.** Phase F only adds `ml-datarefinery` to the refreshed `templates/environment.yml` so it is installable alongside nbfoundry. The actual integration work — `src/nbfoundry/_datarefinery.py` adapter, `[datarefinery]` optional extra in `pyproject.toml`, lifecycle template wiring to load/inspect/materialize DataRefinery `Instance` objects, per-template smoke updates that exercise an Instance — is deferred to a future **Phase I: DataRefinery Integration**. Rationale: Phase F's theme is distribution + stack refresh + proving existing templates work end-to-end; adding a new integration boundary muddies that theme. The env-yml slot has zero marginal cost in Phase F and means future-you isn't forced to do a stack revision to add the integration later.
  - **Design direction (decided at plan time): Coexist, not Subsume.** `_modelfoundry.py` stays as the (still-future) modeling-primitive adapter (training loops, optimizers, eval); `_datarefinery.py` will own data prep. Templates use both adapters — `_modelfoundry` for the modeling stages, `_datarefinery` for the data stages. This is the cleanest semantic split and preserves modelfoundry's contract space until that package actually exists.
  - **Caveat per developer direction:** DataRefinery bugs or small improvements that surface during nbfoundry's Phase G testing work may be addressed as additional stories in Phase G (G.g, G.h, …) at the developer's discretion. Phase G is the quality phase; quality issues that span the nbfoundry / DataRefinery boundary are in scope there. This is distinct from the deferred integration work, which remains a Phase I item.

---

## Risks

- **Solver time / size of merged stack.** TF + PyTorch + Keras + HF tooling in a single env is large. Mitigation: pinned majors; let conda-forge solve the shared section; keep marimo and dev tools in their stable channels.
- **TF on Mac is `tensorflow-macos` + `tensorflow-metal`, not plain `tensorflow`.** Field-tested wisdom: plain conda-forge `tensorflow` on Apple Silicon is a fight; the Apple-distributed pair "just works." The `environment.yml` defaults to the proven Mac path; non-Mac users follow a comment-block swap to plain `tensorflow` (or `tensorflow[and-cuda]`). Validated cross-platform later under Phase H CI when Linux runners come online.
- **Keras 3 standalone install conflicts with TF-bundled Keras 3.** Keras 3 ships inside TF 2.16+ as both `tf.keras` and the bare `keras` namespace; pinning `keras>=3.5` separately in the same env can pull a different Keras 3 minor and lead to subtle import / API-surface drift. Mitigation: no standalone `keras` line; the Keras-3 happy-path story (F.e) exercises whatever TF 2.16+ provides, which is what users will actually consume.
- **Smoke runtime on developer hardware.** Per-tool smokes should each finish in well under a minute on M-series silicon (small models, tiny datasets); each story carries an explicit budget.
- **`ml-datarefinery` env inclusion vs. integration gap.** Including the package in the env without wiring an adapter or updating templates means a curious user `import datarefinery` in a scaffolded notebook will work but will not be guided by any nbfoundry-provided example code. Mitigation: the deferred Phase I plan explicitly addresses this; in the meantime, a single-line note in the data_preparation template docstring (added in F.i if the story author judges it useful) can cross-link to DataRefinery's own quickstart.
- **First PyPI publish coincides with Phase F kickoff.** F.a is the first story; if the trusted-publisher setup or environment binding hits an unexpected snag, every subsequent story is blocked. Mitigation: F.a's verify step includes a successful end-to-end tag → publish → install round-trip against TestPyPI first if needed; release-procedure docs land alongside the workflow.
