# phase-f-pyve-named-testenvs.md — Use cases for named / multiple test environments in pyve

**Status:** Context brief for a **pyve** planning phase (drafted from an
nbfoundry session, 2026-05-29). **Not** a design or implementation spec — pyve
owns the design. This doc supplies the use cases, the requirements they imply,
and the open questions, so pyve can plan a proper, comprehensive, *general*
solution.
**Audience:** pyve maintainers (planning input).
**Origin:** surfaced while fixing the silent-skip "testenv trap" — see
`phase-f-pyve-micromamba-testenv-trap.md` (the motivating case study) and story
**F.f.1** in `stories.md`.

---

## The core insight

pyve today models **one main env + one test env** (the test env a plain
`python -m venv`). But a non-trivial project routinely has **more than one
test *category*, each with materially different environment needs** along one
or more axes:

- **Dependency weight** — a light lint/unit set vs. a multi-GB stack.
- **Backend** — pip/venv vs. conda/micromamba (native libs, channel-only pkgs).
- **Runtime / target platform** — cross-platform CI vs. hardware-gated
  (e.g. Apple-Silicon-only) smokes; or DOM vs. server runtimes in JS land.
- **Manifest source** — the deps come from `requirements*.txt`, a
  `pyproject` extra, or a conda `environment*.yml`.

With a single test env, you are forced to either (a) make that one env the
union of all needs — bloating routine runs with deps they never exercise — or
(b) keep it minimal and push the other categories out of band (separate
hand-built directories, `pyve run python -m pytest` incantations, etc.). Both
are what bit nbfoundry. The general fix is letting a project **declare
multiple, named test environments**, each with its own backend and manifest,
and select which one a given test run uses.

### Already shipped (build on, don't re-litigate)

pyve already added, in response to the trap:

- **`pyve test --env main`** — a two-value env selector (`testenv` default,
  `main` opt-in).
- **Silent-skip advisory** + `PYVE_NO_TESTENV_ADVISORY=1`.

The capability below is, in large part, the **generalization of `--env`** from
a fixed {`testenv`, `main`} pair into an arbitrary set of named environments —
plus per-env backend and manifest configurability.

---

## Use cases

Each use case states the scenario, what the project needs, why the current
one-test-env model fails it, and the capability it implies.

### UC1 — Heavy hardware-smoke env vs. light CI env (the nbfoundry case)

**Scenario.** nbfoundry has two test categories: (a) ~dozen hardware-*independent*
unit/lint/type checks that run in CI on any platform every push; (b)
`@pytest.mark.hardware` smokes that need a multi-GB ML stack (PyTorch+MPS,
TensorFlow-Metal, Keras, HuggingFace) and run only manually on Apple Silicon.

**Need.** A **light** test env for (a) and a **heavy** test env for (b), so CI
never downloads/installs gigabytes of a stack it deselects and never executes.

**Why current model fails.** One test env forces a choice: heavy (taxes every
CI run) or light (no in-repo home for the smoke stack → the separate-directory
workaround).

**Implies:** named test environments; lazy/opt-in provisioning (the heavy env
is only built when that category is run); per-invocation env selection.

### UC2 — Test/runtime parity when the runtime is conda (the trap's root cause)

**Scenario.** The runtime/main env is micromamba (conda-forge resolution). The
venv test env resolves a *different* dependency graph (pip wheels), so tests
can pass against a graph that differs from what actually ships/runs.

**Need.** A test env that resolves **the same way the runtime does** — same
backend, ideally same lock.

**Why current model fails.** The test env is venv-only; it cannot mirror a
conda main env. This divergence is a cousin of the duplicate-TensorFlow /
standalone-Keras hygiene problem found in F.f.1.

**Implies:** per-test-env **backend selection**, with the ability to **inherit
the main env's backend** by default.

### UC3 — Conda-managed native/system test dependencies

**Scenario.** Tests must import a package whose native deps are painful or
unavailable via pip wheels but clean via conda-forge — GDAL/GEOS/PROJ
(geospatial), CUDA toolkit, MKL/BLAS variants, HDF5, ffmpeg — or must invoke a
**non-Python** binary at test time (a database, a compiler, node).

**Need.** A conda-backed test env (and/or one that can carry non-Python tools).

**Why current model fails.** A `python -m venv` test env can only pip-install
Python wheels; it cannot provision conda-only native libs or system binaries.

**Implies:** conda/micromamba as a selectable test-env backend.

### UC4 — Validating a bundled payload manifest (fidelity, anti-drift)

**Scenario.** The artifact under test *is* a shipped manifest — nbfoundry's
`src/nbfoundry/templates/environment.yml`, the conda env every scaffolded
student project receives. The smoke's entire purpose is to prove **that exact
manifest** produces a working stack on real hardware.

**Need.** Build the test env **from that same manifest** (not a hand-maintained
parallel file that can drift). If a separate dev manifest is used, a guard that
flags divergence from the shipped one.

**Why current model fails.** No way to point a test env at an arbitrary
`environment.yml`; the venv test env is built from pip manifests only, so the
shipped conda manifest can't be the source of truth for what's tested.

**Implies:** test envs buildable from an **arbitrary, project-named manifest**
(`environment*.yml` or `requirements*.txt`); optionally a drift check when the
test manifest is meant to equal a shipped one.

### UC5 — Polyglot / full-stack: distinct *runtime* test environments

**Scenario.** Generalizing beyond Python: a SvelteKit app with an API surface
has component tests that need a **browser-like** runtime (jsdom/Playwright) and
API/server tests that want a plain **Node** runtime. (JS tooling already solves
this via Vitest "projects"/workspaces.)

**Need.** Multiple test environments distinguished by **runtime**, not just
dependency set.

**Why it matters here.** It shows the "one project, N test environments"
principle is **general** — the axis is sometimes weight/backend (UC1–4),
sometimes runtime/platform. pyve should decide *how general* it wants to be
(Python-only? a model that could extend to non-Python runtimes?), but the
underlying topology requirement is identical.

**Implies:** the named-env model should treat "what distinguishes envs" as
open (deps, backend, runtime, platform tag), not hard-wired to dependency set.

### UC6 — Matrix testing (flagged as a scope question, not a demand)

**Scenario.** Run the same suite against multiple dependency sets or
interpreters — e.g. torch 2.5 vs 2.6, or py3.11 vs py3.12 — to catch
version-specific breakage.

**Need.** Several test envs that differ only by a pinned axis, selectable
individually or as a set.

**Why mention it.** Named test envs are a natural substrate for a test matrix.
Whether pyve scopes matrix support *in* or *out* is a planning decision — but
the named-env primitive should not accidentally preclude it.

---

## Requirements distilled from the use cases

These are the *properties* a general solution should have. Mechanism/syntax is
pyve's to design.

1. **Multiple, named test environments per project.** Declarable in pyve
   config; `--env <name>` selects one (generalizing the shipped
   `--env {testenv,main}`).
2. **Per-env backend.** At least venv and micromamba; a test env should be able
   to **inherit the main env's backend** by default (UC2).
3. **Per-env manifest source.** `requirements*.txt`, a `pyproject` extra, or an
   arbitrary `environment*.yml` (UC3, UC4).
4. **Light default preserved.** The pure-Python majority keeps a single light
   venv test env with zero added ceremony. Named/heavy/conda envs are
   **opt-in** (don't tax simple projects).
5. **Lazy provisioning.** A heavy env is built/installed only when a run
   actually targets it; CI selects the light env and never materializes the
   heavy one (UC1).
6. **Fidelity / anti-drift.** Support building a test env from the *same*
   manifest as the artifact under test, ideally with a divergence check (UC4).
7. **Missing-dependency visibility.** Extend the existing silent-skip advisory:
   when a selected env lacks deps the tests import, surface it loudly rather
   than letting a mass-skip masquerade as a pass. (This is the trap's core
   lesson — it should hold for *every* named env, not just the default.)
8. **Coherent selection across CLI/CI.** One obvious way to pick the env in a
   `pyve test` invocation and in CI config; sensible default when unspecified.

---

## Explicitly out of scope (for pyve, from nbfoundry's view)

- **Co-residence process isolation.** nbfoundry's hardware smokes must run
  **one test file per process** (PyTorch-MPS and TensorFlow-Metal SIGBUS when
  co-resident — story F.f.1). That is a *pytest execution* concern
  (per-file invocation / `pytest-forked`), **orthogonal** to env topology.
  Named test envs neither cause nor fix it; pyve should not conflate the two.
- **Implementation specifics** — config schema, command names, lockfile
  handling, env storage layout. All pyve's to decide. The illustrative
  `--env <name>` above is descriptive, not prescriptive.

## Open questions for pyve's planning phase

1. How do named envs **unify with the shipped `--env main`** — is `main` just a
   reserved env name in the same namespace?
2. **Config location** — a `[tool.pyve.testenvs]`-style block in
   `pyproject.toml`, a pyve-native config, or per-manifest convention?
3. **Backend inheritance default** — does a test env default to the main env's
   backend, or to venv, with conda as explicit opt-in?
4. **Matrix scope** (UC6) — in or out for v1?
5. **Generality boundary** (UC5) — Python-only, or a topology model that could
   later host non-Python runtimes? Even if Python-only now, avoid baking in
   assumptions that preclude it.
6. **Drift guard** (UC4) — built-in feature, or left to a project-authored test?

## Related

- `phase-f-pyve-micromamba-testenv-trap.md` — the motivating case study (the
  silent-skip trap; `--env main` + advisory already shipped).
- `stories.md` story **F.f.1** — the debug cycle whose prevention scan surfaced
  all of this.
- `project-essentials.md` "Pyve Essentials" — the repo-context two-env
  conventions this capability generalizes.
