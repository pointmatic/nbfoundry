# pyve-micromamba-testenv-trap.md — The `pyve test` / micromamba-main-env dependency trap

**Status:** **Resolved in pyve** (2026-05-29). pyve added a `--env main` flag
and a silent-skip advisory — see [Resolution](#resolution-fixed-in-pyve).
Retained as the rationale record and for the nbfoundry-side run procedure.
**Audience:** pyve maintainers (now historical) + nbfoundry developers (run procedure)
**Scope:** behavior of `pyve test` vs. `pyve run` when the *main* environment is a
micromamba env that bundles both the test runner (`pytest`) and a heavy
dependency stack.

---

## Resolution (fixed in pyve)

pyve now supports running tests in the main environment directly, implementing
the recommended pair from [Options for fixing in pyve](#options-for-fixing-in-pyve-for-maintainer-consideration)
below (options 2 + 1). See the pyve docs:
<https://pointmatic.github.io/pyve/testing/#choosing-which-environment-runs-your-tests>.

- **`pyve test --env main`** — routes pytest to the **main** env instead of the
  testenv. `--env` defaults to `testenv` (the prior behavior); `main` is the
  opt-in for bundled-stack envs.

  ```bash
  pyve test --env main tests/integration/test_e2e_tensorflow.py -m hardware
  ```

- **Silent-skip advisory** — when the main env has `pytest` importable and you
  run the default `pyve test`, pyve prints a one-line advisory before
  executing, so a stack-less testenv no longer skips silently. Suppress it
  (when keeping pytest in the main env deliberately) with
  `PYVE_NO_TESTENV_ADVISORY=1`.

**Canonical nbfoundry form going forward** (replaces the
`pyve run python -m pytest` workaround below):

```bash
# from the smoke env dir (built from environment.yml)
pyve test --env main <repo>/tests/integration/test_e2e_<tool>.py -m hardware
```

The one-file-at-a-time rule still applies (see [workaround](#nbfoundry-side-workaround-in-effect-now)).

---

## TL;DR

`pyve test` always routes pytest to the dedicated **dev/test runner env**
(`.pyve/testenv/venv`, a plain `python -m venv`), never the **main env**
(`.pyve/envs/<name>`). That is correct for a *repo* checkout, where the main
venv intentionally has no pytest and the stack-under-test is light. It is
silently **wrong** for a **smoke environment built from a bundled
`environment.yml`** that puts *both* `pytest` *and* the full ML stack
(`tensorflow`, `torch`, `keras`, …) in the main env: `pyve test` runs in the
stack-less testenv, every `pytest.importorskip("tensorflow")` **skips**, and
the hardware smoke silently no-ops while *looking* green.

The failure mode is a **SKIP, not an error** — so it is easily mistaken for a
clean run.

**Fix (pyve, 2026-05-29):** `pyve test --env main` routes pytest to the main
env; the default `pyve test` now also prints an advisory when the main env has
pytest. See [Resolution](#resolution-fixed-in-pyve).

```bash
pyve test --env main <path>/test_e2e_*.py -m hardware
```

**Pre-fix workaround (still works on older pyve):** run the runner in the main
env explicitly — `pyve run` resolves to the main micromamba env, which for an
`environment.yml`-built env has both the ML stack and pytest:

```bash
pyve run python -m pytest <path>/test_e2e_*.py -m hardware
```

---

## Background — pyve's two-environment model

pyve deliberately isolates two environments (see the pyve `testenv`
subcommand reference and nbfoundry's `project-essentials.md`):

| Environment | Path (micromamba backend) | Contents | Selected by |
|---|---|---|---|
| **Main** | `.pyve/envs/<name>` | Runtime package + its dependencies | `pyve run …` |
| **Testenv** | `.pyve/testenv/venv` | `pytest` + dev tools (`ruff`, `mypy`, …), a plain venv | `pyve test …`, `pyve testenv run …` |

For a normal **repo checkout** this split is exactly right:

- The main venv holds only the package under development and its light deps.
- `pytest` is *intentionally absent* from the main venv (keeps the runtime env
  clean); it lives in the testenv.
- Hence `project-essentials.md` instructs: *"Tests: `pyve test` — not
  `pyve run pytest`. Pytest is not installed in the main `.venv/`."* This is
  correct guidance **for the repo**.

## The trap — a smoke env built from a bundled `environment.yml`

nbfoundry's `src/nbfoundry/templates/environment.yml` is a single shared file
that bundles, into the **main** env:

- the full ML stack: `pytorch`, `tensorflow-macos` + `tensorflow-metal`,
  bundled Keras, `transformers`, `datasets`, `peft`, `optuna`, …
- **and** the dev tooling: `ruff`, `mypy`, **`pytest`**, `pytest-cov`.

So a developer who builds a smoke env per the F.c–F.j run procedure —

```bash
mkdir tf-smoke && cd tf-smoke
cp <repo>/src/nbfoundry/templates/environment.yml .
pyve init --backend micromamba          # main env now has stack + pytest
```

— ends up with a **main env that already contains pytest and the entire ML
stack**. The testenv, by contrast, does not exist yet; when `pyve test` is
first run it is **auto-created as an empty plain venv** and only `pytest` is
dropped into it. It has **none** of the ML stack.

The convention therefore **reverses** relative to the repo:

| Context | ML stack lives in | pytest lives in | Correct runner |
|---|---|---|---|
| Repo checkout | (light deps only) | testenv | `pyve test` ✅ |
| `environment.yml` smoke env | **main env** | **main env** (and a stack-less testenv) | `pyve run python -m pytest` ✅ |

`pyve test` hard-routes to the testenv in *both* contexts. In the smoke-env
context that is the stack-less env, so the tests skip.

## Evidence (observed 2026-05-29)

Running the documented procedure from the smoke env directory:

```text
$ pyve test ../nbfoundry/tests/integration/test_e2e_tensorflow.py -m hardware
  ▸ Creating dev/test runner environment in '.pyve/testenv/venv'...
  $ python -m venv .pyve/testenv/venv
  ✔ Created dev/test runner environment
pytest is not installed in the dev/test runner environment. Install now? [y/N]: y
  ▸ Installing pytest into dev/test runner environment...
  …
  ✔ pytest installed
======================== test session starts ========================
collected 1 item
../nbfoundry/tests/integration/test_e2e_tensorflow.py s          [100%]
SKIPPED [1] …:41: could not import 'tensorflow': No module named 'tensorflow'
======================== 1 skipped in 0.01s ========================
```

Key tells:

1. pyve **created a fresh testenv** (`python -m venv`) and installed *only*
   pytest into it — confirming the runner env is independent of the
   micromamba main env that holds the stack.
2. The result is `s` (**skip**), not a failure — the smoke silently no-ops.
3. `could not import 'tensorflow'` even though the **main** env runs
   TensorFlow fine (the same env runs `scripts/metal_smoke.py`'s TF probe on
   `/GPU:0` without issue).

Adding a `<repo>/` path prefix to the `pyve test` command (an earlier
hypothesis) does **not** change the outcome — the path was never the problem;
the environment selection is.

The correct invocation, in the same directory, runs the tests against the
main env and the TF smoke executes for real:

```bash
pyve run python -m pytest ../nbfoundry/tests/integration/test_e2e_tensorflow.py -m hardware
```

## Impact

- **Silent false-confidence.** A developer following the F.c–F.j docstrings
  verbatim sees "skipped," which is the *normal* state for hardware-gated
  tests on non-hardware CI, and may conclude the smoke "ran." It did not.
- **The skip masks real regressions.** The whole point of the hardware smokes
  (and the per-release verify) is to exercise the published stack on Apple
  Silicon. A silent skip defeats that.
- **The misleading guidance is self-consistent with the repo convention**, so
  it is hard to spot: `pyve test` *is* the blessed form — just not in a
  bundled-env context.

## Why this reads as a pyve bug (not just a docs bug)

The docstrings can be fixed (and will be, via the workaround), but the
underlying sharp edge is in pyve:

1. `pyve test` routes to the testenv **unconditionally**, even when the main
   env already contains `pytest` *and* the dependencies the tests need.
2. When it auto-creates a stack-less testenv, it gives **no signal** that the
   resulting env is missing dependencies the tests will need — the user is
   prompted only about installing pytest.
3. The resulting mass-skip is **not surfaced** as anything unusual; pytest's
   own "1 skipped" is the only hint, and skips are expected for hardware
   gating, so it blends in.

## Options for fixing in pyve (for maintainer consideration)

> **Adopted:** pyve shipped options **2** (`pyve test --env main`) and **1**
> (the silent-skip advisory) on 2026-05-29. The list below is retained as the
> rationale that informed that choice.

Listed roughly cheapest → most invasive; not mutually exclusive.

1. **Skip-visibility warning (cheap, high value).** After `pyve test`, if a
   meaningful fraction of collected tests skipped due to `ModuleNotFoundError`
   / failed `importorskip`, print a prominent hint: *"N tests skipped due to
   missing imports in the testenv; if these deps live in your main env, run
   `pyve run python -m pytest …` instead."* Addresses the silent-skip masking
   directly without changing routing.

2. **Explicit env selection flag.** `pyve test --env main` (or a distinct
   `pyve run-tests`) routes pytest to the main env. Low-magic, opt-in, makes
   the bundled-env case a documented one-liner instead of a `pyve run python
   -m pytest` incantation.

3. **Main-env pytest detection.** When `pyve test` is invoked and the main env
   already has `pytest` importable, prompt/offer to use the main env rather
   than silently spinning up a stack-less testenv. Risk: changes long-standing
   default behavior; needs a clear opt-in.

4. **Testenv dependency seeding.** When the project's `environment.yml` (or
   the main env) bundles a heavy stack the tests import, allow the testenv to
   inherit from / layer on top of the main env instead of starting empty.
   Heaviest option; risks duplicating large native packages (torch, TF) and
   re-creating the cross-framework co-residence issues the smokes care about.

5. **Docs-only.** Document the bundled-env reversal in pyve's `testenv`
   reference. Necessary regardless, but insufficient alone — the silent skip
   is the trap, and docs do not surface it at failure time.

**Recommendation for discussion:** (1) is nearly free and directly attacks the
silent-skip masking; (2) gives a clean supported path for bundled envs. The
pair covers the trap without the risk of (3)/(4).

## nbfoundry-side run procedure

On current pyve, the F.c–F.j hardware smokes (and the `metal_smoke.py` verify)
are run from the smoke-env directory against the main env via `--env main`:

```bash
# from the smoke env dir (e.g. tf-smoke/ or nbfoundry-env-refresh-test/)
pyve test --env main <repo>/tests/integration/test_e2e_<tool>.py -m hardware
```

On older pyve without `--env`, use the equivalent main-env runner instead:

```bash
pyve run python -m pytest <repo>/tests/integration/test_e2e_<tool>.py -m hardware
```

Run **one file at a time** — never an unfiltered `-m hardware` collection —
because the per-framework smokes otherwise share a single process and
re-create the PyTorch-MPS / TensorFlow-Metal co-residence SIGBUS documented in
story F.f.1 (`docs/specs/stories.md`).

## Related

- `phase-f-pyve-named-testenvs.md` — forward-looking context brief for a pyve
  planning phase: the general "named / multiple test environments" capability
  (per-env backend + manifest, light-default, anti-drift) that this trap
  motivated. `--env main` is the shipped point fix; that doc is the general one.
- `docs/specs/stories.md` — story **F.f.1** (silent SIGBUS in
  `scripts/metal_smoke.py`); this trap surfaced during that debug cycle's
  prevention scan.
- `docs/specs/project-essentials.md` — "Pyve Essentials / Workflow rules"
  (the repo-context `pyve test` guidance that this trap inverts for bundled
  envs).
- Deferred follow-up: the planned `apple-metal-micromamba-pip.md` spec + the
  platform-detecting diagnostic CLI should bake the main-env runner form into
  a single command so developers never type the raw incantation.
