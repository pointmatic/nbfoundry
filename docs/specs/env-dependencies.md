<!-- Vendored from Pyve env-dependencies-template.md at spec_version "3.0". Closed vocabulary is Pyve-owned; project-guide refreshes via a dedicated story when Pyve bumps. See docs/specs/project-essentials.md → "Pyve env-spec vendored-template contract" for the protocol. -->

# env-dependencies.md -- nbfoundry (Python 3.12.13)

This document formally enumerates the **named environments** the `nbfoundry` repo needs:

1. The **root development environment** required to develop the repo (the environment a contributor or LLM must stand up before doing anything else).
2. One or more **named test environments** (the first defaults to `testenv`) required to *efficiently, effectively, and completely* test the codebase.

A secondary purpose is to surface **environment requirements Pyve does not yet materialize** (advisory backends) and **mechanisms missing from the closed vocabulary entirely** (Pyve change-requests), so the Pyve-owned backend vocabulary can grow over time. See [§3 Backend Catalog](#3-backend-catalog) and [§8 Backend Gaps & Pyve Change-Requests](#8-backend-gaps--pyve-change-requests).

> **Related docs**
> - `concept.md` — why the project exists (problem and solution space).
> - `features.md` — what the project does (scope, requirements, behavior).
> - `tech-spec.md` — how the project is built (architecture, dependencies, testing strategy).
> - `docs/project-guide/go.md` — workflow steps tailored to the current mode (cycle steps, approval gates, conventions).
> - Pyve backends reference: <https://pointmatic.github.io/pyve/backends/>

### Background — why this env topology exists

The four-test-env topology recorded below did not arise in isolation. It is the dev-side
crystallization of an architectural conversation spread across three sibling specs in
`docs/specs/`:

1. **`phase-f-pyve-micromamba-testenv-trap.md`** — the original *testenv trap* incident
   surfaced during the F.f.1 prevention scan: `pyve test` silently routing to a stack-less
   testenv when the bundled `environment.yml` main env held both pytest and the ML stack, so
   hardware smokes returned a green-looking "skipped" instead of running. Resolved upstream
   in pyve via the shipped `pyve test --env main` flag and the silent-skip advisory.
2. **`phase-f-pyve-named-testenvs.md`** — the use-case brief that distilled the *named test
   environments* requirement (out of the trap and out of an earlier nbfoundry attempt to
   smoke-test from a separate ad-hoc directory tree): a project routinely has more than one
   test category — light/CI vs. heavy/hardware, different backends, different manifests —
   and forcing them through one env produces either bloat or a missing capability. Pyve
   shipped this as `[tool.pyve.testenvs]` blocks in `pyproject.toml` at v2.8 and as the
   first-class `pyve.toml` `[env.<name>]` schema at v3.0.
3. **`learningfoundry-embedded-learning-exercise-vs-native-applied-exercise.md`** — the
   architectural decision record that splits LearningFoundry curriculum exercises into
   *embedded learning* (in-browser, Pyodide-bound) and *native applied* (the learner's own
   hardware, via the nbfoundry + DataRefinery + ModelFoundry trio) surfaces. The applied
   side adopts **per-applied-series env recipes** as its dependency primitive.

The same pyve named-test-env primitive serves both surfaces — the dev side (the four envs
enumerated in this document) and the learner side (per-applied-series env recipes declared
by individual curricula). The four envs below also bake in two empirical findings from the
debug cycle captured in `stories.md` stories **F.f.1** and **F.f.2**: (a) PyTorch-MPS and
TensorFlow-Metal cannot coexist in a single process on Apple Silicon (SIGBUS during the
Metal plugin's Grappler optimization step), and (b) bundling HuggingFace's conda-forge
transitives alongside TensorFlow pulls a parallel standalone `keras 3.x` distribution that
fights TF's bundled copy. Both problems dissolve at the env layer under the per-framework
focused-manifest topology recorded here. The detailed reasoning lives in
[§4.1](#41-inventory-table) below.

---

## 1. Document Metadata

| Field | Value |
|-------|-------|
| **Repo name** | `nbfoundry` |
| **Primary language(s)** | Python 3.12.13 |
| **Pyve version** | 3.0.6 |
| **Doc status** | Approved |
| **Last updated** | 2026-06-13 |
| **Author / maintainer** | Michael Smith (Pointmatic) |

---

## 2. Conventions & Terminology

- **Environment** — a named, isolated dependency space materialized by a backend. Every
  environment has exactly one **purpose** (surface), one **backend**, and a structured
  attribute set (`app_type`, `frameworks`, `languages`, `packaging`). Environments are
  enumerated machine-readably in [§4.0](#40-environment-surface-enumeration).
- **Purpose (surface)** — the single role an environment serves. Exactly one of:

  | `purpose` | Meaning |
  |-----------|---------|
  | `run` | The deployable/executable artifact's **runtime** — "the thing that ships or executes in production." Its dependency closure is the app's runtime deps, not dev/test tooling. This is the surface `pyve package` / `pyve deploy` (future) operate on. *Disambiguator:* if you would ship or execute it in production, it is `run`; if it only supports development, it is `utility`. |
  | `test` | Hosts **test runners and test-only dependencies**; the env where a class of tests executes. `pyve test --env <name>` gates on `purpose == test`. *Disambiguator:* pytest / vitest / bats and their fixtures live here, never in `run`. |
  | `utility` | Hosts **development / orchestration tooling that is neither the app nor its tests** — formatters, linters, codegen, the `project-guide` host, LLM CLIs. The `root` env defaults to `utility`. *Disambiguator:* it makes development easier but never ships and is not a test surface. *Intended lifecycle (not yet wired):* survives `pyve purge` — it is your tooling, not the project's materialized output. |
  | `temp` | A **declared, reproducible, disposable** workspace that is part of a defined workflow (e.g. the `mktemp -d` sandbox a test harness spins up per run). Concretely: contents are **volatile**, the env is **safe to delete at any time**, and pyve may **prune** it. *The line is declared-vs-ad-hoc:* a reproducible part of a defined workflow → model it as `temp` and enumerate it; a one-off "hello world" poke → do **not** model it at all. *Intended lifecycle (not yet wired):* auto-prune. Today `temp` carries no special runtime behavior — it is a recognized value awaiting its lifecycle. |

  One environment = one purpose. If a single backing directory genuinely serves two
  purposes, declare two environments. (Lists are intentionally **not** supported — forcing
  a single choice keeps each environment's intent unambiguous. Revisit only if real
  friction cases emerge.)
- **Root development environment** — the environment activated at the repo root (pyve's
  primary environment, e.g. `.venv/` for the `venv` backend). Its purpose is typically
  `utility` — it hosts tooling, not necessarily the app or the tests.
- **Named test environment** — a `purpose: test` environment. The first/default is named
  `testenv`. Additional environments use distinct names (e.g. `testenv-integration`,
  `testenv-min`, or — as in this repo — `smoke-pytorch`, `smoke-tensorflow`,
  `smoke-huggingface`). Each maps to exactly one backend.
- **Backend** — the environment-management mechanism pyve uses to materialize an
  environment. Values are a **closed, Pyve-owned set** of specific mechanism names, never
  generic categories, and fall into three S6 categories: *project-virtualized* (`venv`,
  `micromamba`, `pnpm`, `npm`, `yarn`, `uv`, `poetry`, `conda`, `bun`, `deno` — per-project
  state + PATH activation), *cache-backed* (`cargo`, `go`, `bundler`, `swiftpm`, `xcode`,
  `android_sdk`, `gradle`, `maven`, `sbt`, `dotnet`, `conan`, `cmake` — shared cache +
  lockfile + a CLI build tool; an un-installable toolchain such as Xcode is recorded via the
  advisory `require_min_version` field, not by demoting the backend), and *check-only*
  (`homebrew`, `apt`, `docker`, `podman` — presence-verified, no pyve build). Closely-related
  mechanisms with leaky behavioral differences are kept as **separate flavored values** (e.g.
  `docker` vs `podman`, `npm` vs `pnpm` vs `yarn`) so each flavor's quirks are codified once
  instead of patched per repo. The special value **`none`** means there is no formal
  configuration mechanism — the environment is the bare OS, the implicit default for any
  surface pyve does not materialize. See [§3](#3-backend-catalog).
- **Structured attributes** — fixed-vocabulary descriptors recorded per environment. Each is
  a **closed set** (Pyve-owned, versioned); a value outside it is a spec violation. Values are
  either *implemented* (pyve acts on them today) or *advisory* (recorded + surfaced, never
  materialized):

  | Attribute | Closed vocabulary (use `none` when not applicable) |
  |-----------|----------------------------------------------------|
  | `app_type` | `api`, `cli`, `service`, `library`, `desktop`, `mobile`, `embedded`, `script`, `web`, `none` |
  | `packaging` | `container`, `static`, `server`, `serverless`, `package`, `binary`, `mobile_app`, `lock_bundle`, `none` |
  | `frameworks` (kind: app) | `sveltekit`, `flask`, `fastapi`, `django`, `react`, `vue`, `jupyter`, `marimo`, `spring`, `j2ee`, `kotlin_multiplatform`, `rails`, `sinatra`, `swiftui`, `uikit`, `none` |
  | `frameworks` (kind: test) | `pytest`, `vitest`, `jest`, `mocha`, `playwright`, `cypress`, `bats`, `rspec`, `minitest`, `xctest`, `junit` |
  | `frameworks` (kind: lint) | `ruff`, `mypy`, `black`, `isort`, `flake8`, `pylint`, `eslint`, `prettier`, `shellcheck`, `shfmt`, `ktlint`, `detekt`, `scalafmt`, `scalafix`, `google_java_format`, `rustfmt`, `clippy`, `gofmt`, `golangci_lint`, `rubocop`, `swiftlint`, `swiftformat`, `clang_format`, `clang_tidy` |
  | `languages` | `python`, `javascript`, `typescript`, `bash`, `c`, `cpp`, `c_sharp`, `java`, `kotlin`, `scala`, `go`, `swift`, `objective_c`, `rust`, `ruby` |

  Each framework's `kind` (app/test/lint) is *intrinsic* — looked up, not an authoring choice;
  one env's `frameworks` list may mix kinds. Two **advisory** fields may also appear per
  environment: **`require_min_version`** (`{ <tool>: "<ver>" }` — un-installable-toolchain
  pins, e.g. `{ xcode = "15.0" }`) and **`manual_steps`** (a string list of human-only seams
  pyve cannot drive, e.g. iOS signing). Both are surfaced in `pyve check` / `status`, never
  materialized.
- **Value class — *implemented* vs *advisory*.** Every value in every closed vocabulary is
  exactly one of two classes. **Implemented** = pyve has a real integration that acts on it
  today (materializes a backend, runs a verb, detects a framework). **Advisory** = recognized
  in the vocabulary but pyve takes no materializing action — it is *recorded* in `pyve.toml`
  and *surfaced* in `pyve check` / `pyve status`, never built, never an error. "Advisory" is
  the single home for every not-yet-implemented value (the runtime trichotomy's "known +
  no-op" class); an **unknown** value — outside the closed set — is a spec violation that
  hard-errors. Distance from Python/Node is irrelevant to the class; only whether pyve acts
  on it.
- **Framework `kind` (app / test / lint)** — every framework carries one *intrinsic* kind,
  looked up in Pyve's registry (never an authoring choice), governing which verb consumes it:
  - **app** — defines the application's serve/build shape; supplies the `serve` / `package`
    command (e.g. `flask` → `flask run`, `sveltekit` → the adapter build). A framework that
    supplies no command (a plain library) is **not** an app framework — it belongs in a
    dependency manifest, not here.
  - **test** — supplies the `test` command for a class of tests (e.g. `pytest`, `vitest`,
    `bats`).
  - **lint** — supplies a read-only code-quality command (linter, format-check, or
    type-check) for `pyve lint`, plus its fixable subset for `pyve lint --fix` (e.g. `ruff`,
    `mypy`, `eslint`, `shellcheck`).

  `none` = no framework activation (framework-less envs are first-class).
- **`packaging` — the artifact kind a materialize step produces** for an env (the *form*, not
  the destination):

  | `packaging` | Meaning |
  |-------------|---------|
  | `container` | An OCI image (Docker/Podman) — the deployable is a container. |
  | `static` | A static asset bundle (HTML/JS/CSS/Wasm) served by any web server / CDN — e.g. a SvelteKit static build, a Kotlin/JS or Compose-Web bundle. |
  | `server` | A long-running server process/artifact (a runnable app that listens), not containerized. |
  | `serverless` | A function/handler package for a serverless platform (zip / layer / bundle). |
  | `package` | A language package for a registry — a Python wheel, an npm tarball, a Ruby gem, a JVM jar. |
  | `binary` | A compiled standalone executable (a Rust/Go binary, a native CLI). |
  | `mobile_app` | A mobile app bundle — an iOS `.app`/`.ipa`, an Android `.apk`/`.aab`. (Absorbs the former `ios_app`/`android_app` framework entries.) |
  | `lock_bundle` | The deployable *is* the pinned lock set (the materialized dependency closure), not a built artifact. |
  | `none` | The env produces no materialized artifact (e.g. a `utility` tooling env). |

  Two things pyve deliberately does **not** model: **`build_target`** (the platform/runtime
  you build *for* — `linux/amd64`, a Rust target triple, a SvelteKit adapter) and
  **`deploy_target`** (the *destination* you ship to — GHCR, Vercel, PyPI). Pyve materializes
  the form; external CD ships it.
- **`app_type` — advisory descriptor of what the env's code *is*** (never materialized;
  surfaced in `check` / `status`):

  | `app_type` | Meaning |
  |------------|---------|
  | `api` | An HTTP/RPC API service consumed by other programs. |
  | `cli` | A command-line tool. |
  | `service` | A long-running non-web backend (worker, daemon, queue consumer). |
  | `library` | An importable package with no app of its own. |
  | `desktop` | A desktop GUI application. |
  | `mobile` | A mobile application. |
  | `embedded` | Firmware / a hardware-deployed artifact. |
  | `script` | A standalone script or automation. |
  | `web` | A browser-delivered web app/site. |
  | `none` | Not applicable (e.g. a tooling env). |
- **Dependency source class** — where a dependency comes from and how it is installed.
  This document recognizes the following classes (a single environment may mix several):

  | Class | Examples | Manifest / install mechanism |
  |-------|----------|------------------------------|
  | `pip` (PyPI) | `pytest`, `ruff`, `mypy` | `requirements.txt` / `requirements-dev.txt` |
  | `conda` (conda-forge) | `numpy`, `pytorch`, `transformers` | `environment.yml` → `conda-lock.yml` |
  | `system` (OS / Homebrew / apt) | `git`, `micromamba` (bootstrap), `bash` | `brew install` / `apt-get install` |
  | `vendored` (git-clone / submodule) | — (none for nbfoundry today) | `git clone` into a known path |
  | `runtime` (language interpreter) | `python=3.12.13` | conda channel pin (env-pinned, not asdf in this repo) |

- **Canonical backend** — a backend pyve materializes today (the *implemented* class).
  **Currently `venv` (default) and `micromamba` (Python plugin), plus `pnpm` / `npm` / `yarn`
  (Node plugin).** Every other value in the closed vocabulary is *advisory*: pyve records and
  surfaces it but does not yet materialize it. Advisory backends are **not** "proposed by the
  author" — the vocabulary is Pyve-owned and closed (see [§8](#8-backend-gaps--pyve-change-requests)).

### nbfoundry-specific terms

- **Hardware smoke** — a test marked `@pytest.mark.hardware` that exercises real ML
  acceleration on Apple Silicon (Metal/MPS). Excluded from default `pyve test` runs by
  `pyproject.toml`'s `addopts = "-ra -m 'not hardware'"`; opted in per-file with
  `pyve test --env <smoke-env> <file> -m hardware`. The hardware smokes live under
  `tests/integration/test_e2e_*.py` (Phase F stories F.c–F.j) and own the three `smoke-*`
  environments enumerated in §4.
- **Bundled-payload manifest** — `src/nbfoundry/templates/environment.yml`, the conda
  manifest *shipped to learners* as the runtime stack for scaffolded projects. Distinct from
  the dev-side smoke manifests under `tests/integration/env/` which target *focused, per-
  framework dev-side testing*. The applied-exercise architecture
  (`docs/specs/learningfoundry-embedded-learning-exercise-vs-native-applied-exercise.md`) calls
  for the bundled-payload manifest to split into per-applied-series recipes; that work is
  tracked separately in `stories.md` and does not change this document's env topology.

---

## 3. Backend Catalog

| Backend | Status | Env location | Dependency manifest | Lock artifact | Init command |
|---------|--------|--------------|---------------------|---------------|--------------|
| `venv` | **canonical (default)** | `.pyve/envs/<name>/venv/` | `requirements.txt` (root) / `requirements-dev.txt` (testenv) | `requirements*.txt` w/ `--hash` (pip-tools) — not yet enforced for nbfoundry v0.x | `pyve init` |
| `micromamba` | **canonical** | `.pyve/envs/<name>/conda/` | `environment.yml` (per-env, declared via `manifest` in `pyve.toml`) | `conda-lock.yml` (`pyve lock --env <name>`) — not yet generated for the smoke envs | `pyve init --backend micromamba` (root) or auto-provisioned on first `pyve test --env <name>` for lazy testenvs |

**Default-backend assumption:** any environment may benefit from the `venv` backend, since
Python is a general-purpose workhorse for scripting/automation even in non-Python repos.
Choose a non-`venv` backend only with a stated reason (recorded per environment in §5).

**On `none`:** an environment whose dependencies have no formal configuration mechanism
(installed ad-hoc on the host, or materialized at runtime) uses backend `none` — the bare
OS. Use a specific name (`homebrew`, `apt`, ...) instead whenever a real mechanism exists,
even if pyve does not yet materialize it — it is an *advisory* value in the closed vocabulary
(record it in §4 with its advisory status; see §8 only if the mechanism is missing entirely).

**On container flavors:** `docker` and `podman` are **distinct backends that share a single
OCI `Dockerfile`** manifest — they diverge in *runtime behavior* (socket path, mount/SELinux
flags, rootless/userns, compose provider, BuildKit vs Buildah), not in the manifest. Pick
the flavor that matches the target host; pin the image by digest (`@sha256:...`) for
reproducibility. A container backend is also an *isolation level* and may nest another
backend (e.g. a `Dockerfile` that runs `pip install` or `apt-get`).

**Backend tiers (for orientation):** backends fall into rough tiers — *language-env*
(`venv`, `micromamba`, `npm`, `pnpm`, `yarn`: a project-local dependency dir + a runtime +
a lockfile), *host-package* (`homebrew`, `apt`: OS-level tools), and *isolation*
(`docker`, `podman`: an OS boundary that may nest the others). Node flavors `npm`/`pnpm`/
`yarn` share a `package.json` declaration but diverge in **both** lockfile
(`package-lock.json` / `pnpm-lock.yaml` / `yarn.lock`) and `node_modules` layout (hoisted vs
pnpm's symlinked store vs Yarn PnP), which is why they are separate flavors.

**Backends nbfoundry uses:** `venv` (root + default testenv) and `micromamba` (three smoke
testenvs). No advisory backends, no container flavors, no non-canonical mechanisms.

---

## 4. Environment Inventory

### 4.0 Environment Surface Enumeration

```yaml
spec_version: "3.0"
project: nbfoundry
description: Marimo-based notebook framework for ML/DS — standalone tools + embeddable learningfoundry exercises from one source.
envs:
  root:
    purpose: utility
    backend: venv
    default: false                       # `default` flag is meaningful for `purpose: test` envs only
    path: "."
    languages: [python]
    frameworks: [none]                   # nbfoundry is a Python library + thin CLI; no app/test/lint framework binds to root
    packaging: package                   # produces a Python wheel via hatchling
    app_type: library                    # primary integration is `from nbfoundry import compile_exercise`; the CLI is a thin wrapper

  testenv:
    purpose: test
    backend: venv
    default: true                        # the default `pyve test` target
    path: "."
    languages: [python]
    frameworks: [pytest, ruff, mypy]     # test runner + two lint frameworks; one env may mix framework kinds
    packaging: none
    app_type: none

  smoke-pytorch:
    purpose: test
    backend: micromamba
    default: false
    path: "."
    languages: [python]
    frameworks: [pytest]                 # ML libraries (torch, numpy) are dependencies declared in the manifest, NOT pyve frameworks
    packaging: none
    app_type: none
    # manifest: tests/integration/env/pytorch.yml  (declared in pyve.toml; file authored by the F.f.2 follow-up)
    # lazy: true

  smoke-tensorflow:
    purpose: test
    backend: micromamba
    default: false
    path: "."
    languages: [python]
    frameworks: [pytest]
    packaging: none
    app_type: none
    # manifest: tests/integration/env/tensorflow.yml
    # lazy: true
    # Notes: serves F.c TensorFlow AND F.e Keras hardware smokes (Keras 3 ships bundled with TF 2.16+).

  smoke-huggingface:
    purpose: test
    backend: micromamba
    default: false
    path: "."
    languages: [python]
    frameworks: [pytest]
    packaging: none
    app_type: none
    # manifest: tests/integration/env/huggingface.yml
    # lazy: true
    # Notes: ships torch alongside transformers/datasets/peft because HF defaults to the torch backend in nbfoundry's smokes.
```

### 4.1 Inventory Table

| # | Environment name | Purpose | Backend | Default? | App type | Frameworks | Languages |
|---|------------------|---------|---------|----------|----------|------------|-----------|
| 0 | `root` (repo root) | `utility` | `venv` | n/a | `library` | `[none]` | `[python]` |
| 1 | `testenv` | `test` | `venv` | yes | `none` | `[pytest, ruff, mypy]` | `[python]` |
| 2 | `smoke-pytorch` | `test` | `micromamba` | no | `none` | `[pytest]` | `[python]` |
| 3 | `smoke-tensorflow` | `test` | `micromamba` | no | `none` | `[pytest]` | `[python]` |
| 4 | `smoke-huggingface` | `test` | `micromamba` | no | `none` | `[pytest]` | `[python]` |

**Why this many test environments:** four envs are required because the dev-side test
surface splits along *two orthogonal axes* that cannot be collapsed without recreating the
two bugs the debug cycle in `stories.md` just fixed (story **F.f.1** SIGBUS and story
**F.f.2** env hygiene). Each axis is empirically grounded; neither is theoretical.

**Axis 1 — weight × platform.** The hardware-independent unit/integration tests
(currently 11 tests, plus `ruff check`, `ruff format --check`, `mypy --strict`, and coverage
measurement) must run in CI on any platform, every push, and complete in seconds. They need
pytest + dev tools only. The hardware smokes (`@pytest.mark.hardware`) must run manually on
Apple Silicon and need a multi-GB ML stack with native Metal libraries. One env cannot
serve both contracts — CI would download gigabytes of TensorFlow it never executes, taxing
every push and compounding across the matrix. This axis is the routine-vs-smoke split, and
it maps cleanly onto pyve's `lazy = true` mechanism: the heavy envs are *declared* but
*not materialized* until a developer explicitly targets one.

**Axis 2 — framework isolation (the F.f.1 / F.f.2 inheritance).** The hardware smokes
themselves split across three envs because two debug-cycle findings make a single bundled
ML env structurally unworkable:

- **PyTorch-MPS and TensorFlow-Metal cannot coexist in one process on Apple Silicon**
  (SIGBUS during the Metal plugin's Grappler optimization step). The full root-cause
  analysis and subprocess-isolation fix live in story **F.f.1**; the empirical narrowing
  (`scripts/keras_metal_narrow.py`) showed that `torch → keras` reliably crashes while
  `tf → keras` passes — co-residence is the trigger, not the order or the env contents.
  Putting both frameworks in a single env makes every future test that imports them
  simultaneously a regression source. Per-framework envs make co-residence **impossible by
  construction**; the subprocess-isolation logic in `scripts/metal_smoke.py` becomes
  belt-and-suspenders rather than load-bearing.
- **Bundling HuggingFace's conda-forge transitives with TensorFlow pulls a parallel
  standalone `keras 3.x` distribution** that fights TF's bundled copy (story **F.f.2**,
  empirically blocking F.e's hygiene guard test against the bundled-payload env). The
  `transformers` / `datasets` / `peft` recipes on conda-forge declare keras as an optional
  dep, and conda's solver pulls it transitively even when no top-level recipe asks for it.
  The fix is not to wrestle the conda solver — it is to keep HuggingFace **out of the env
  that owns the Keras hygiene contract**. `smoke-tensorflow` therefore ships TF + Metal
  plugin + numpy + pytest only; `smoke-huggingface` ships HF + torch (HF's default backend
  in nbfoundry's smokes) and has no Keras hygiene contract to honor.

Together the two axes give a four-env topology — one light routine env and three focused
heavy smoke envs — that solves both problems at the env layer rather than at the test-
harness layer.

**Why exactly four and not three, five, or six.** Each alternative was considered and
rejected for a specific reason:

- **Not three (bundle the ML stack into `testenv` itself).** Defeats Axis 1: CI provisioning
  a multi-GB env to skip the hardware tests is exactly the failure mode pyve's silent-skip
  advisory exists to warn against (see `phase-f-pyve-micromamba-testenv-trap.md`).
- **Not five with a separate `smoke-keras`.** Keras 3 is bundled inside TensorFlow 2.16+
  and is exposed as both `tf.keras` and the bare `keras` namespace; no standalone install
  is needed, and adding one re-creates the F.f.2 anti-pattern. `smoke-tensorflow` owns
  both story **F.c** (TF) and story **F.e** (Keras) smokes correctly.
- **Not five with a torch-free `smoke-huggingface`.** HuggingFace's smoke uses the torch
  backend (the default in nbfoundry's smokes — see `tests/integration/test_e2e_huggingface.py`);
  pulling torch out leaves nothing to run. The env preserves the one-framework-family-per-env
  invariant by hosting *HuggingFace* (which happens to ride torch internally) as a distinct
  family from raw PyTorch experimentation in `smoke-pytorch`.
- **Not six with a future `smoke-optuna` or per-template smoke env.** Future stories F.g
  (Optuna) and F.h–F.j (per-template smokes) will fold into one of the three existing smoke
  envs based on which framework family they exercise; no new env is anticipated unless a
  future smoke introduces a fourth framework family.

**Architectural compounding (dev side ↔ learner side).** The same pyve named-test-env
primitive that gives nbfoundry these four dev-side envs also serves the *learner* side of
the LearningFoundry applied-exercise architecture
(`docs/specs/learningfoundry-embedded-learning-exercise-vs-native-applied-exercise.md`):
each applied-exercise *series* in a curriculum declares a focused env recipe via the same
`[env.<name>]` shape, identical in spirit to the smoke envs declared here. **One primitive,
two consumer surfaces, one mental model for authors and contributors.** This is the
practical payoff of the conversation that produced
`phase-f-pyve-named-testenvs.md` — pyve added the capability once; nbfoundry and every
LearningFoundry curriculum reuse it twice.

---

## 5. Environment Specifications

### 5.0 Environment: `root` (purpose: `utility`)

- **Purpose (surface):** `utility` — hosts the nbfoundry package itself (editable install for
  development), the `project-guide` host, and any LLM CLIs. The root env is what `pyve run`
  resolves to.
- **Attributes:** app_type `library`; frameworks `[none]`; languages `[python]`; packaging
  `package` (the wheel hatchling builds for PyPI).
- **Backend & rationale:** `venv` — nbfoundry's runtime deps are all pure-Python or
  pip-installable wheels (`marimo`, `typer`, `pyyaml`, `markdown-it-py`, `pydantic`). No
  native conda-only packages live in the *runtime* surface; the heavy ML stack ships as the
  *bundled-payload manifest* (`src/nbfoundry/templates/environment.yml`), not as a root-env
  dependency. micromamba would be overkill and noticeably slower to provision.
- **Language runtime / pins:** Python `>=3.12.13,<3.14` (from `pyproject.toml`). No
  `.tool-versions` / `.python-version` in the repo — the version constraint lives in
  `pyproject.toml` and (for the smoke envs and the shipped payload) in
  `environment.yml` as `python=3.12.13` (exact).
- **Bootstrap (one-time):**
  ```bash
  pyve init                                # creates the root venv at .pyve/envs/root/venv/
  ```
- **Install dependencies:**
  ```bash
  pyve run pip install -e .                # editable install of nbfoundry into root
  ```
- **Managed dependencies (`pip` / `conda`):**

  | Package | Version pin | Source class | Purpose |
  |---------|-------------|--------------|---------|
  | `marimo` | unpinned (latest at install) | `pip` | Notebook substrate; parser used by `compile` |
  | `typer` | unpinned | `pip` | CLI framework |
  | `pyyaml` | unpinned | `pip` | YAML parsing for exercise definitions (`safe_load`) |
  | `markdown-it-py` | unpinned | `pip` | Markdown → HTML renderer for instructions / sections |
  | `pydantic` | `>=2` | `pip` | Schema validation for exercise YAML + BR-4 submission |

- **System / external dependencies (`system` / `vendored` / `runtime`):**

  | Dependency | Version | Source class | Install method | Why not in the managed env |
  |------------|---------|--------------|----------------|----------------------------|
  | `git` | — | `system` | OS-provided | Source control; not a Python package |
  | `micromamba` | `>=1` | `system` | Pyve bootstrap or `brew install micromamba` | Required to materialize the smoke envs (testenvs #2–4); not a runtime dep of nbfoundry itself |

- **Lock / reproducibility strategy:** `pyproject.toml` declares loose pins; the wheel
  hatchling builds is what ships to PyPI. Exact-pin lockfiles for the root env are not
  enforced for nbfoundry v0.x — the runtime surface is small and PyPI installation should
  resolve cleanly. Re-evaluate at 1.0.
- **Verification (smoke test):**
  ```bash
  pyve run python -c "import nbfoundry; print(nbfoundry.__version__)"
  pyve run nbfoundry --version
  ```
- **CI parity notes:** Not directly exercised in CI today. CI runs `pyve test` (the testenv
  surface); the root env is recreated implicitly when CI installs the package for tests.
  `.github/workflows/publish.yml` exercises the wheel-build surface on tag.

---

### 5.1 Environment: `testenv` (purpose: `test`, default)

- **Purpose (surface):** `test` — the default `pyve test` target. Owns every test category
  that does **not** need the ML stack: unit tests, integration tests (CLI / determinism /
  no-network / aggregate-tree), lint (ruff), and type-check (mypy --strict).
- **Attributes:** app_type `none`; frameworks `[pytest, ruff, mypy]` (test + two lint kinds);
  languages `[python]`; packaging `none`.
- **Backend & rationale:** `venv` — all dev tools are pip-installable; pytest-collected tests
  exercise the editable nbfoundry source. No conda-only deps in this surface.
- **Test categories covered:** unit, integration (non-hardware), lint, type-check (see §6).
- **Language runtime / pins:** Same as root (Python `>=3.12.13,<3.14`).
- **Bootstrap (one-time):**
  ```bash
  pyve testenv init                                # creates .pyve/testenvs/testenv/venv/
  ```
- **Install dependencies:**
  ```bash
  pyve testenv run pip install -e .                # CLI tests need entry-point registration; pythonpath alone is insufficient
  pyve testenv install -r requirements-dev.txt     # ruff, mypy, pytest, pytest-cov, types-PyYAML
  ```
- **Managed dependencies (`pip` / `conda`):**

  | Package | Version pin | Source class | Purpose |
  |---------|-------------|--------------|---------|
  | `ruff` | unpinned | `pip` | Lint + format (rule set: E, F, W, B, I, UP, SIM, RUF) |
  | `mypy` | unpinned | `pip` | Strict type-check over the whole package |
  | `pytest` | unpinned | `pip` | Test runner |
  | `pytest-cov` | unpinned | `pip` | Coverage measurement (target ≥85% on public modules) |
  | `types-PyYAML` | unpinned | `pip` | mypy stubs for `pyyaml` |

- **System / external dependencies:** None beyond root's (`git`).
- **Lock / reproducibility strategy:** `requirements-dev.txt` carries the dev-tool list,
  unpinned for v0.x. As with root, exact-pin lockfiles are deferred to 1.0.
- **How to run the tests this env owns:**
  ```bash
  pyve test                                        # runs all collected tests, hardware-marked tests deselected by default
  pyve testenv run ruff check .
  pyve testenv run ruff format --check .
  pyve testenv run mypy
  ```
- **Verification (smoke test):**
  ```bash
  pyve test --version
  pyve testenv run ruff --version
  pyve testenv run mypy --version
  ```
- **CI parity notes:** `testenv` is what every CI test job materializes. No test workflow
  exists in `.github/workflows/` today (only `publish.yml`); adding `ci.yml` to run
  `pyve test` + `ruff check` + `mypy` is tracked in `stories.md` under Phase H.

---

### 5.2 Environment: `smoke-pytorch` (purpose: `test`)

- **Purpose (surface):** `test` — hosts the PyTorch hardware smoke (story F.d,
  `tests/integration/test_e2e_pytorch.py`). Validates that the shipped stack trains on Apple
  Silicon's MPS device.
- **Attributes:** app_type `none`; frameworks `[pytest]` (the test runner; the ML stack is a
  set of manifest-declared dependencies, **not** pyve `frameworks` — torch, numpy,
  tensorflow, transformers are libraries, not app/test/lint frameworks per §2's closed
  vocabulary); languages `[python]`; packaging `none`.
- **Backend & rationale:** `micromamba` — `pytorch>=2.5` from conda-forge is the proven Apple
  Silicon MPS path (`tech-spec.md` "Pinned ML stack"). conda-forge resolves PyTorch with its
  native deps cleanly; pip-wheel installs of torch on macOS arm64 are workable but vary
  build-to-build. Matches the shipped payload's choice for the same package.
- **Test categories covered:** hardware-smoke — PyTorch (see §6).
- **Language runtime / pins:** `python=3.12.13` (exact, pinned in the smoke-env's
  `environment.yml`).
- **Bootstrap (one-time):** Lazy-provisioned by pyve on first `pyve test --env smoke-pytorch
  ...`. No explicit init step required. (Equivalent explicit form:)
  ```bash
  pyve testenv init smoke-pytorch
  ```
- **Install dependencies:** Driven by the manifest declared in `pyve.toml`
  (`tests/integration/env/pytorch.yml`). Pyve provisions on first targeted use.
- **Managed dependencies (`pip` / `conda`):** As of this document's draft date the manifest
  file does not yet exist; authoring it is the immediate follow-up. The intended contents:

  | Package | Version pin | Source class | Purpose |
  |---------|-------------|--------------|---------|
  | `python` | `=3.12.13` | `runtime` (conda channel pin) | Pinned interpreter (matches the shipped-payload manifest) |
  | `pytorch` | `>=2.5` | `conda` (conda-forge) | The framework under test; MPS-enabled on macOS arm64 |
  | `numpy` | unpinned | `conda` (conda-forge) | Tensor data setup for the smoke |
  | `pytest` | unpinned | `conda` (conda-forge) | Test runner |

  **Deliberately absent:** `tensorflow*`, `keras` (standalone), `transformers`, `datasets`,
  `peft`. Their absence is what guarantees no PyTorch-MPS / TensorFlow-Metal co-residence
  inside this env.
- **System / external dependencies:** `micromamba` (system; see root §5.0).
- **Lock / reproducibility strategy:** Per-env `conda-lock.yml` via `pyve lock --env
  smoke-pytorch` is the v2.8+ workflow; lockfile generation for the smoke envs is **not yet
  enforced for v0.x**. Tracked as a Phase H follow-up; the immediate priority is the manifest
  itself.
- **How to run the tests this env owns:**
  ```bash
  pyve test --env smoke-pytorch tests/integration/test_e2e_pytorch.py -m hardware
  ```
- **Verification (smoke test):**
  ```bash
  pyve testenv run --env smoke-pytorch python -c "import torch; print(torch.backends.mps.is_available())"
  ```
- **CI parity notes:** Not run in CI. Hardware smokes are manual, developer-Apple-Silicon
  only, per release. CI requires `-m 'not hardware'` (the `pyproject.toml` default `addopts`).

---

### 5.3 Environment: `smoke-tensorflow` (purpose: `test`)

- **Purpose (surface):** `test` — hosts both the TensorFlow hardware smoke (story F.c,
  `tests/integration/test_e2e_tensorflow.py`) and the Keras hardware smoke (story F.e,
  `tests/integration/test_e2e_keras.py`). Validates the Apple Silicon `tensorflow-macos` +
  `tensorflow-metal` path and the env-hygiene guard that asserts no standalone `keras`
  distribution is present (`go.md` § "No standalone `keras` package").
- **Attributes:** app_type `none`; frameworks `[pytest]`; languages `[python]`; packaging
  `none`.
- **Backend & rationale:** `micromamba` — TensorFlow's Apple Silicon distribution is
  pip-only (Apple ships `tensorflow-macos` and `tensorflow-metal` via PyPI, not conda-forge),
  but the env is conda-backed so it can pin Python exactly via `python=3.12.13` and use
  conda-forge for `numpy` + `pytest`. The pip block carries the Apple TF distribution.
  Matches the structure of the shipped-payload manifest's framework section.
- **Test categories covered:** hardware-smoke — TensorFlow, hardware-smoke — Keras (see §6).
- **Language runtime / pins:** `python=3.12.13` (exact).
- **Bootstrap (one-time):** Lazy-provisioned. Explicit form:
  ```bash
  pyve testenv init smoke-tensorflow
  ```
- **Install dependencies:** Driven by `tests/integration/env/tensorflow.yml` (declared in
  `pyve.toml`; file pending).
- **Managed dependencies (`pip` / `conda`):** Intended contents of the manifest:

  | Package | Version pin | Source class | Purpose |
  |---------|-------------|--------------|---------|
  | `python` | `=3.12.13` | `runtime` | Pinned interpreter |
  | `numpy` | unpinned | `conda` (conda-forge) | Tensor data setup |
  | `pytest` | unpinned | `conda` (conda-forge) | Test runner |
  | `tensorflow-macos` | `>=2.16` | `pip` (PyPI) | Apple Silicon TF distribution; ships Keras 3 bundled |
  | `tensorflow-metal` | `>=1.1` | `pip` (PyPI) | Metal acceleration plugin |

  **Deliberately absent:** standalone `keras` (Keras 3 is bundled inside TF 2.16+; a separate
  pin pulls a parallel minor that fights TF's bundled copy — `go.md` § "No standalone `keras`
  package"), `pytorch`, `transformers`, `datasets`, `peft`. The absence of HF deps is the
  fix to story F.f.2 — conda-forge HuggingFace pulls a parallel standalone `keras`
  transitively; with HF absent here, that contamination cannot occur, and the F.e hygiene
  guard passes by construction.
- **System / external dependencies:** `micromamba`.
- **Lock / reproducibility strategy:** Same as smoke-pytorch (per-env conda-lock deferred to
  Phase H).
- **How to run the tests this env owns:**
  ```bash
  pyve test --env smoke-tensorflow tests/integration/test_e2e_tensorflow.py -m hardware
  pyve test --env smoke-tensorflow tests/integration/test_e2e_keras.py      -m hardware
  ```
- **Verification (smoke test):**
  ```bash
  pyve testenv run --env smoke-tensorflow python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
  pyve testenv run --env smoke-tensorflow python -c "import importlib.metadata as m; \
      print('OK' if m.PackageNotFoundError else m.version('keras'))" 2>&1 | grep -q "PackageNotFoundError" && \
      echo "Keras hygiene: PASS" || echo "Keras hygiene: FAIL (standalone keras present)"
  ```
- **CI parity notes:** Not run in CI (hardware-only).

---

### 5.4 Environment: `smoke-huggingface` (purpose: `test`)

- **Purpose (surface):** `test` — hosts the HuggingFace hardware smoke (story F.f,
  `tests/integration/test_e2e_huggingface.py`). Validates `transformers` + `datasets` +
  `peft` against a small pretrained model running on PyTorch's MPS backend.
- **Attributes:** app_type `none`; frameworks `[pytest]`; languages `[python]`; packaging
  `none`.
- **Backend & rationale:** `micromamba` — the HuggingFace stack on conda-forge ships
  `transformers`, `datasets`, `peft`, `sentencepiece`, `protobuf`, `tiktoken` with their
  native deps cleanly resolved. Same pattern as the shipped payload's `# huggingface`
  section.
- **Test categories covered:** hardware-smoke — HuggingFace (see §6).
- **Language runtime / pins:** `python=3.12.13` (exact).
- **Bootstrap (one-time):** Lazy-provisioned. Explicit form:
  ```bash
  pyve testenv init smoke-huggingface
  ```
- **Install dependencies:** Driven by `tests/integration/env/huggingface.yml` (declared in
  `pyve.toml`; file pending).
- **Managed dependencies (`pip` / `conda`):** Intended contents:

  | Package | Version pin | Source class | Purpose |
  |---------|-------------|--------------|---------|
  | `python` | `=3.12.13` | `runtime` | Pinned interpreter |
  | `pytorch` | `>=2.5` | `conda` (conda-forge) | Default backend for transformers in nbfoundry's smokes |
  | `transformers` | unpinned | `conda` (conda-forge) | The library under test |
  | `datasets` | unpinned | `conda` (conda-forge) | Tiny synthetic Dataset for the smoke |
  | `peft` | unpinned | `conda` (conda-forge) | LoRA adapter for the smoke's forward-pass test |
  | `sentencepiece` | unpinned | `conda` (conda-forge) | Tokenizer dep |
  | `protobuf` | unpinned | `conda` (conda-forge) | Tokenizer dep |
  | `tiktoken` | unpinned | `conda` (conda-forge) | Tokenizer dep |
  | `numpy` | unpinned | `conda` (conda-forge) | Data setup |
  | `pytest` | unpinned | `conda` (conda-forge) | Test runner |

  **Deliberately absent:** `tensorflow*` (HuggingFace's TF backend is not exercised here; the
  smoke uses torch). The standalone-keras transitive that contaminated the bundled-payload
  env in F.f.2 may still appear in this env (because HuggingFace conda-forge recipes pull it)
  — but since no `tensorflow` is present, there is no TF-bundled Keras to conflict with, and
  the standalone keras is benign here. F.e's hygiene guard does not run against this env.
- **System / external dependencies:** `micromamba`.
- **Lock / reproducibility strategy:** Same as smoke-pytorch (per-env conda-lock deferred to
  Phase H).
- **How to run the tests this env owns:**
  ```bash
  pyve test --env smoke-huggingface tests/integration/test_e2e_huggingface.py -m hardware
  ```
- **Verification (smoke test):**
  ```bash
  pyve testenv run --env smoke-huggingface python -c "from transformers import AutoTokenizer; print('OK')"
  pyve testenv run --env smoke-huggingface python -c "import torch; print(torch.backends.mps.is_available())"
  ```
- **CI parity notes:** Not run in CI (hardware-only). First-run cost includes a small
  pretrained-model download (~5 MB cached under `~/.cache/huggingface/hub`).

---

## 6. Test Coverage Matrix

| Test category | Tooling | Owning environment | Covered? | Notes |
|---------------|---------|--------------------|----------|-------|
| Static analysis / lint | `ruff check` | `testenv` | yes | Rule set: E, F, W, B, I, UP, SIM, RUF (`pyproject.toml`) |
| Formatting | `ruff format --check` | `testenv` | yes | Same tool as lint |
| Type checking | `mypy --strict` over `src/nbfoundry/` | `testenv` | yes | `tech-spec.md` QR-4 |
| Unit tests | `pytest` (`tests/unit/`) | `testenv` | yes | 8 modules per `tech-spec.md` Package Structure; hardware-independent |
| Integration tests (non-hardware) | `pytest` (`tests/integration/test_cli_*.py`, `test_determinism.py`, `test_no_network.py`, `test_aggregate_tree.py`) | `testenv` | yes | Exercise the CLI surface against the editable install |
| Coverage measurement | `pytest-cov` | `testenv` | yes | Target ≥85% on public `nbfoundry` modules (`tech-spec.md`) |
| Hardware smoke — PyTorch | `pytest -m hardware` (`tests/integration/test_e2e_pytorch.py`) | `smoke-pytorch` | yes | Story F.d; Apple Silicon MPS |
| Hardware smoke — TensorFlow | `pytest -m hardware` (`tests/integration/test_e2e_tensorflow.py`) | `smoke-tensorflow` | yes | Story F.c; tensorflow-macos + tensorflow-metal |
| Hardware smoke — Keras | `pytest -m hardware` (`tests/integration/test_e2e_keras.py`) | `smoke-tensorflow` | yes | Story F.e; Keras 3 via the TF-bundled namespace + hygiene guard |
| Hardware smoke — HuggingFace | `pytest -m hardware` (`tests/integration/test_e2e_huggingface.py`) | `smoke-huggingface` | yes | Story F.f; transformers + datasets + peft on torch backend |
| Packaging / distribution | `hatch build` + PyPI trusted-publish | n/a (GitHub Actions) | yes | `.github/workflows/publish.yml` on `v*` tag; not a pyve env |

**Completeness statement:** every test category the nbfoundry codebase requires today is
covered by exactly one environment. The hardware-smoke category splits across three envs
along the framework-family axis, which is the minimum split required to avoid the F.f.1
co-residence SIGBUS and the F.f.2 transitive-contamination problem; no further split is
needed (Keras rides with TensorFlow because Keras 3 is TF-bundled). Future stories F.g
(Optuna) and F.h–F.j (per-template smokes) will fold into one of the three existing smoke
envs based on which framework family they exercise; no new env is anticipated for them
unless a future smoke introduces a fourth framework family.

---

## 7. Reproducibility & Bootstrapping

```bash
# Fresh-clone → fully testable, from the repo root:

# Step 1: Bootstrap the root environment (Python 3.12.13 + nbfoundry runtime deps)
pyve init                                                            # creates .pyve/envs/root/venv/
pyve run pip install -e .                                            # editable install of nbfoundry

# Step 2: Bootstrap the default testenv (dev tools + editable install for CLI tests)
pyve testenv init                                                    # creates .pyve/testenvs/testenv/venv/
pyve testenv run pip install -e .                                    # entry-point registration for CLI integration tests
pyve testenv install -r requirements-dev.txt                         # ruff, mypy, pytest, pytest-cov, types-PyYAML

# Step 3: Verify the hardware-independent surface
pyve test                                                            # runs all non-hardware tests; should pass green
pyve testenv run ruff check .                                        # lint clean
pyve testenv run mypy                                                # type-check clean

# Step 4 (Apple Silicon only, optional, lazy-provisioned on first use):
pyve test --env smoke-pytorch    tests/integration/test_e2e_pytorch.py    -m hardware
pyve test --env smoke-tensorflow tests/integration/test_e2e_tensorflow.py -m hardware
pyve test --env smoke-tensorflow tests/integration/test_e2e_keras.py      -m hardware
pyve test --env smoke-huggingface tests/integration/test_e2e_huggingface.py -m hardware
```

- **Files that must be committed for reproducibility:** `pyproject.toml`,
  `requirements-dev.txt`, `pyve.toml`, `src/nbfoundry/templates/environment.yml` (the
  bundled-payload manifest shipped to learners), `tests/integration/env/pytorch.yml`,
  `tests/integration/env/tensorflow.yml`, `tests/integration/env/huggingface.yml` (the
  per-smoke-env manifests; not yet authored — see story F.f.2 follow-up), and
  `src/nbfoundry/_version.py` (single source of truth for the version string).
- **Files that must NOT be committed:** `.pyve/envs/`, `.pyve/testenvs/`, `.venv/`, `.env`,
  any `__pycache__/` or `.pytest_cache/` directories, any `*.egg-info/` build artifact.

---

## 8. Backend Gaps & Pyve Change-Requests

| Need | In closed vocab? | Status today | Action |
|------|------------------|--------------|--------|
| (none) | — | — | None — the closed vocabulary covers all of nbfoundry's environment needs. Both `venv` and `micromamba` are canonical/implemented backends; the `frameworks` vocabulary cleanly accommodates `pytest`, `ruff`, and `mypy`; no advisory backend is required. |

The only vocabulary-adjacent observation worth recording is that the ML stack (PyTorch,
TensorFlow, Keras, transformers, datasets, peft, optuna, etc.) is **deliberately not** in
the `frameworks` vocabulary because none of those packages supplies a pyve verb (app
serve/build, test command, lint command). They are libraries, declared via per-env
`manifest` files, not pyve frameworks. This is correct vocabulary discipline rather than a
gap — surfaced here so a future reader does not mistake the design intent for an oversight.
The discipline is also load-bearing for the four-env topology: because the ML stack is not
in the frameworks vocabulary, the smoke envs are differentiated **only** by their manifest
files — which is exactly the mechanism that gives per-framework focused envs their isolation
property. A future Pyve change-request to add `pytorch` / `tensorflow` / `transformers` to
the frameworks vocabulary would break that mechanism by giving the same ML library two
declaration paths (frameworks attribute vs. manifest) and would re-open the F.f.2-class
contamination question. The closed vocabulary is doing real work here; leaving it alone is
the right call.

---

## 9. Change Log & Approval

| Date | Version | Author | Change | Status |
|------|---------|--------|--------|--------|
| 2026-06-13 | 0.1 | Michael Smith | Initial draft — five environments (`root` + `testenv` + three `smoke-*` framework smokes); both canonical backends; no advisory needs. | Draft |
| 2026-06-13 | 1.0 | Michael Smith | Approved by developer; no structural changes from 0.1. | Approved |
