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
