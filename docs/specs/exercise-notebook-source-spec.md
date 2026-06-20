# exercise-notebook-source-spec.md — NbFoundry (upstream feature request)

**Status:** proposed — filed by a consumer.
**Affects:** `nbfoundry` ≥ 0.46.0 (Option-C `compile_exercise` → `notebook_source`).
**Audience:** nbfoundry maintainers. This is a consumer-authored upstream spec (same pattern as
the sql.js bug spec. The consumer project ships an interim workaround (below); this
document tracks the clean fix.

## Determination

For now, we will continue to use the YAML-based approach rather than ingesting complete Marimo notebooks as the source for exercises.

---

## Problem

nbfoundry's `compile-exercise` builds `notebook_source` by emitting **exactly one markdown cell +
one code cell per YAML `section`** (`codegen.generate` → `_markdown_cell` + `_code_cell`). Each
section's `code` (or the verbatim contents of its `code_file`) is indented into a **single**
`@app.cell def _(): …` body.

That model assumes a section's code is a **plain cell-body snippet**. But the natural ML/DS
authoring artifact — and the thing nbfoundry's own README advertises as the shared source for
"two surfaces" — is a **complete Marimo notebook** (`import marimo` / `app = marimo.App()` /
many `@app.cell` functions / `if __name__ == "__main__": app.run()`).

When a section points `code_file` at such a notebook, nbfoundry inlines the **entire app verbatim
into one cell**, producing a Marimo notebook with a *nested* `marimo.App()` (and nested
`@app.cell`s and `app.run()`) inside a single cell. The result:

- `marimo run` may still render (the outer app drives the inner one by luck), but
- `marimo edit` shows the whole notebook as **one giant un-editable cell** — there is no
  cell-by-cell structure, which defeats an editable exercise.

### Reproduction (nbfoundry 0.46.0)

1. Author a complete multi-cell Marimo notebook `nb.py` (`app = marimo.App()`, N `@app.cell`s).
2. Author `ex.yml` with one section: `code_file: nb.py`.
3. `nbfoundry compile-exercise ex.yml --base-dir .` → inspect `notebook_source`:
   - `notebook_source.count("marimo.App()") == 2` (outer wrapper + the inlined inner app)
   - the inner app's `@app.cell` lines are indented inside one outer cell body
   - a nested `app.run()` appears inside the cell.

The consumer hit this on `exercises/m03-mlp-sklearn.yml` (`code_file:
notebooks/m03-mlp-baseline.py`).

## Why it matters

It breaks the headline promise — "one notebook source → standalone **and** embeddable exercise."
A hand-authored multi-cell notebook (the standalone surface, `nbfoundry compile`) cannot be the
source for the exercise surface (`compile-exercise`) without being flattened into one cell. The
only workaround is to **duplicate** every cell body into per-section YAML snippets, which then
drift from the standalone notebook.

## Proposed fix (pick one)

1. **Notebook-as-source field (recommended).** Add an optional top-level `notebook:` to the
   exercise definition pointing at a Marimo `.py`. When present, `notebook_source` is that
   notebook's cells **verbatim**, with the exercise `title`/`description`/`hints` prepended as a
   banner markdown cell. `sections` becomes optional (instructional overlay only). One source,
   two surfaces, no duplication.
2. **Marimo-aware `code_file`.** When a section's `code_file` parses as a Marimo notebook, splice
   its `@app.cell` functions into `notebook_source` as **separate** top-level cells (strip the
   inner `import marimo` / `app = marimo.App()` / `app.run()` scaffolding) rather than inlining
   the file as one cell.
3. **Notebook-tree passthrough.** Generalize FR-6 (notebook trees) so a tree's entry-point
   notebook's cells flow through as separate cells.

Option 1 is the smallest, most explicit contract change and keeps `sections` semantics intact for
authors who genuinely want snippet-per-section exercises.

## Interim consumer workaround

Until upstream lands, authors `exercises/m03-mlp-sklearn.yml` as **per-cell sections** —
each section's `code` is a plain cell body (no Marimo scaffolding), mirroring the cells of the
standalone `notebooks/m03-mlp-baseline.py`. This compiles to a clean, editable, reactive
multi-cell notebook (verified via `marimo export html`). The cost is the documented duplication
between the YAML sections and the standalone notebook; this spec's fix removes that cost.

## Acceptance (upstream)

- A complete multi-cell Marimo notebook can be the single source for both `compile` and
  `compile-exercise`.
- The resulting `notebook_source` has exactly one `marimo.App()`, one `app.run()`, and N
  top-level `@app.cell`s (no nesting).
- `marimo edit <staged notebook>` shows the original cells, individually editable.
