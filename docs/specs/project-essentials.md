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
