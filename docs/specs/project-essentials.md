<!--
This file captures must-know facts future LLMs need to avoid blunders when
working on this project. It is injected verbatim under a `## Project
Essentials` section in every rendered `go.md`, so entries here use `###` for
subsections (not `##`). No top-level `#` title — the wrapper provides it.

Pyve-specific rules live in the bundled `pyve-essentials.md` sibling
artifact and render automatically — do NOT duplicate them here.
-->

### File header conventions

Every new source file must begin with a copyright notice and license
identifier. Use the comment syntax for the file type:

| File type | Comment syntax |
|-----------|---------------|
| Python, YAML, shell, Makefile | `#` |
| JavaScript, TypeScript, Go, Java, C/C++ | `//` or `/* */` |
| HTML, Svelte, XML | `<!-- -->` |
| CSS, SCSS | `/* */` |

**This project's header:**

- **Copyright**: `Copyright (c) 2026 Pointmatic`
- **SPDX identifier**: `SPDX-License-Identifier: Apache-2.0`

Python example:
```python
# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
```

TypeScript example:
```typescript
// Copyright (c) 2026 Pointmatic
// SPDX-License-Identifier: Apache-2.0
```

HTML example:
```html
<!-- Copyright (c) 2026 Pointmatic -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
```

**Compiler exception (FR-8 step 3):** the `nbfoundry` compiler does **not**
inject headers into author-authored notebooks it processes. If an author
has stripped the header from their own notebook, that's their choice —
preserve it as-is rather than re-injecting. This applies only to
hand-authored notebook source consumed by `nbfoundry compile` /
`compile_exercise`; it does **not** apply to files **you** create as part
of this project's source tree, which always carry the header.

### No standalone `keras` package — Keras 3 ships bundled with TF 2.16+

Do **not** add `keras` (or `keras>=3.x`) as a standalone line in
`templates/environment.yml`, `requirements-dev.txt`, or any other dependency
manifest in this project. Keras 3 is bundled inside TensorFlow 2.16+ and is
exposed as both `tf.keras` and the bare `keras` namespace (re-exported by
TF). Adding a separate `keras` pin pulls a parallel Keras 3 minor version
that conflicts with TF's bundled copy, producing silent API-surface drift
that is hard to diagnose.

In code, use `from tensorflow import keras` — or `import keras`, since TF
re-exports the namespace. Both resolve to the TF-bundled module when no
standalone install is present, which is the contract this project relies
on. The `tests/integration/test_e2e_keras.py` smoke (story F.e) explicitly
asserts that `keras` is not separately installed; it will fail loudly if a
standalone pin is reintroduced.

### End-to-end smoke tests install nbfoundry from PyPI, not the editable repo

The hardware-gated end-to-end smokes under `tests/integration/test_e2e_*.py`
(Phase F stories F.c–F.j) install `nbfoundry==<published-version>` from
PyPI into their test environment — **not** via `pip install -e .` from the
working tree. This is deliberate: editable installs silently mask packaging
bugs (missing package data, broken `[project.scripts]` entry points, wheel
layout problems, omitted templates) that real users hit on `pip install
nbfoundry`. The smokes' purpose is to validate the *published* surface, so
they must install the same way users do.

This is the opposite of the convention for everything else in `tests/` —
unit tests, CLI smoke tests, and `test_cli_*.py` integration tests run
against the testenv editable install (`pyve test`) because they exercise
the source tree directly. Only the `test_e2e_*.py` smokes install from
PyPI.

When adding a new test: if it exercises the library or CLI surface against
the local source, use the editable install path (the testenv default). If
it should also catch *packaging* regressions — missing files in the wheel,
broken entry points, install-time failures — install from PyPI like the
existing `test_e2e_*.py` smokes do.

### Exclusively venv/pip — no conda or micromamba anywhere

This project uses **Pyve + `venv`** exclusively. No environment in the repo —
the `root` utility env, the default `testenv`, the `smoke-torch` /
`smoke-tensorflow` hardware-smoke envs, **and** the learner-facing bundled
stack — uses conda or micromamba. The entire Metal ML stack is pip-installable
on Apple Silicon: `torch`'s macOS arm64 wheel is MPS-enabled (PyTorch's own
recommended Mac install), Apple ships `tensorflow-macos` + `tensorflow-metal`
on PyPI, and the HuggingFace stack (`transformers`/`datasets`/`peft`/
`sentencepiece`/`protobuf`/`tiktoken`) plus `optuna` are all pip wheels. conda
bought nothing for the Apple-Silicon-first target, so it was dropped (stories
F.f.3 dev side, F.f.4 learner side).

**This supersedes any reference to `templates/environment.yml`** elsewhere in
this file or the specs: F.f.4 **deletes** that conda manifest and replaces it
with per-stage pip requirements `templates/requirements-{base,torch,tf}.txt`.
The `pyve.toml` smoke envs use `requirements = [...]`
(`tests/integration/env/{torch,tensorflow}.txt`), never a conda `manifest`.

**Naming gotchas:** the pip distribution is **`torch`** (not conda's
`pytorch`) — use `torch` in any `requirements*.txt`. And `ml-datarefinery`
installs under the **distribution** name `ml-datarefinery` but **imports** as
`datarefinery` (sklearn-style); a probe using the wrong name silently no-ops.

### Env topology and the one hard isolation boundary (torch ≠ TensorFlow in a process)

Four dev environments (`pyve.toml`): **`root`** (venv, utility — editable
nbfoundry + runtime deps), **`testenv`** (venv, default, light —
`pytest`/`ruff`/`mypy`, all hardware-independent tests), and two lazy
hardware-smoke envs **`smoke-torch`** and **`smoke-tensorflow`** (venv,
`@pytest.mark.hardware`, Apple-Silicon-only, never materialized in CI).

The split into exactly those two smoke envs rests on **one hard physical
constraint**: **PyTorch-MPS and TensorFlow-Metal cannot coexist in one process
on Apple Silicon** — they SIGBUS (story F.f.1: `torch` claims the Metal device,
then TF-Metal's Grappler faults). So the **torch-family** (`torch` +
HuggingFace + `optuna`) and the **TensorFlow-family** (`tensorflow-macos`/
`tensorflow-metal` + bundled Keras) live in **separate envs and are never
co-installed**. The learner stack mirrors this exactly: `requirements-torch.txt`
and `requirements-tf.txt` never share a venv, so a learner can't hit the SIGBUS
either.

**How to apply:** never create a "both frameworks" env or requirements file;
never add `tensorflow*` to a torch env (or vice versa). HuggingFace and Optuna
are torch-family → they ride with `torch`. A new env is warranted only if a
future smoke introduces a third framework *family* (e.g. JAX); otherwise fold
new smokes into one of the two existing families.

### mypy's typed surface is ML-free — `templates/` is excluded, no heavy env

nbfoundry's actual typed surface (the compiler, CLI, schema, validators under
`src/nbfoundry/*.py`) imports **zero** ML stack by design (FR-7: the compiler
operates on notebook source as text/AST). So `mypy --strict` needs **no** ML
dependencies and runs in the light `testenv`. `[tool.mypy]` **excludes
`src/nbfoundry/templates/`** (mirroring the existing `[tool.ruff]
extend-exclude`): the template notebooks import `numpy`/`pandas`/`sklearn`/
`torch` only as *example* code and are intentionally full of unannotated marimo
cells — they are not part of nbfoundry's typed API, and their correctness is
covered by the F.h–F.j template smokes, not by strict typing.

**How to apply:** if `mypy` reports `import-not-found` for ML packages, the
cause is a template leaking into the check — **fix it by tightening the
`templates/` exclude, never by adding the ML stack to `testenv` or standing up
a separate "mypy" env.** The real package modules are already strict-clean;
only the excluded templates aren't.

### The framework smokes don't import nbfoundry — PyPI-install applies only to the template smokes

The hardware **framework** smokes
`tests/integration/test_e2e_{pytorch,tensorflow,keras,huggingface,optuna}.py`
(stories F.c–F.g) `pytest.importorskip` **only their framework** and never
`import nbfoundry` — they validate the *shipped ML stack on Metal*, not
nbfoundry's code. Their envs (`smoke-torch` / `smoke-tensorflow`) are therefore
**framework-only**: nbfoundry is not installed into them.

This refines the "*End-to-end smoke tests install nbfoundry from PyPI*" note
above: the **published-surface / PyPI-install** convention applies specifically
to the **template** smokes F.h–F.j (`test_e2e_template_*.py`), which actually
invoke `nbfoundry init` and thus exercise the packaged wheel + entry points.
The framework smokes F.c–F.g neither need nor install the published nbfoundry.
