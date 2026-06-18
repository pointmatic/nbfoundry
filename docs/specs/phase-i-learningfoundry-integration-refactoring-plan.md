# Phase I — LearningFoundry Integration Refactoring (Option C) — Plan

**Status:** Draft for approval, 2026-06-18. Pre-1.0 feature phase (`plan_phase`).
**Trigger:** LearningFoundry revised the consumer contract — [`learningfoundry/consumer-dependency-spec.md`](learningfoundry/consumer-dependency-spec.md) — replacing the static-display API (Option B) with a notebook-emit API (Option C).
**Scope boundary:** This phase changes **NbFoundry's Python API only** (the BR-* build-time contract). The `learningfoundry launch <id>` CLI, the `exercises-manifest.json` sidecar, marimo process lifecycle, and the SvelteKit banner are **LearningFoundry's** repo (the contract's RR-* / Package-Distribution sections are explicitly *not part of NbFoundry's contract*).

---

## Gap Analysis — what exists vs. what Option C needs

### What the shipped package does today (Option B, archived through v0.45.0)

`compile_exercise(yaml_path, base_dir) -> dict` reads an exercise YAML and returns a **static-display dict**: `{type, source, ref, status, title, instructions, sections[], expected_outputs[], assets[], hints[], submission, environment}`. It renders markdown→HTML, inlines `code_file` into `sections[].code`, validates the BR-4 `submission` schema, enumerates BR-5 image assets (path-only), and enforces path-escape / no-network / no-exec. Implemented across `compiler.py`, `validator.py`, `schema.py`, `assets.py`, `markdown.py`, `paths.py`, with a heavy unit/integration suite and a golden `valid_graded.json`.

### What Option C requires

`compile_exercise(yaml_path, base_dir) -> dict` returns a **banner + generated notebook**:

```python
{
    "type": "exercise",
    "source": "nbfoundry",
    "ref": "<original ref path>",
    "title": "...",
    "description": "<HTML>",        # banner body, markdown → HTML
    "hints": ["<HTML or text>"],    # optional, banner
    "environment": {"python_version": ..., "dependencies": [...], "setup_instructions": ...},
    "notebook_source": "import marimo\napp = marimo.App()\n@app.cell\ndef _():\n    ...",
}
```

- **`notebook_source`** is the headline new capability: a complete, self-contained `marimo.App()` module **as a string**, runnable by `marimo edit|run` with no further codegen. All third-party imports (`torch`, …) appear **as source text in cells**; `compile_exercise` must not import them.
- **Dropped from the output:** `status`, `instructions`, `sections`, `expected_outputs`, `assets`, `submission`.
- **Unchanged:** the `compile_exercise` / `validate_exercise` / `ExerciseError` signatures (BR-1/BR-2/BR-3 names), no-network / no-exec / no-file-write guarantees, deterministic output.

### The hardest constraint is already satisfied

Option C's central rule — *the codegen path MUST NOT import `torch`/`modelfoundry` at build time* — is already guaranteed by NbFoundry's architecture: the compiler core is ML-free (FR-7) and the modelfoundry boundary is isolated in `_modelfoundry.py` (AC-10). Imports become **text** in generated cells; nothing new is needed to honor the constraint.

---

## Feature Requirements (Option C contract, as NbFoundry requirements)

- **FR-I1 — Notebook-emit compile.** `compile_exercise` returns the Option-C dict above, with `notebook_source` a valid, self-contained marimo module string.
- **FR-I2 — Banner metadata.** `title`, `description` (markdown→HTML), optional `hints`, and `environment` (passed through; `marimo` guaranteed present in `dependencies`).
- **FR-I3 — Deterministic codegen.** Same input → byte-identical `notebook_source` and dict (OR-5 extended to the generated module).
- **FR-I4 — Build-time purity.** No import of `torch`/`modelfoundry`/any ML framework; no file writes; no process spawn; no network (carried over).
- **FR-I5 — Validation.** `validate_exercise` validates the new definition shape (collects all errors); `ExerciseError` unchanged (BR-3).
- **FR-I6 — Retire the static path.** `submission` (BR-4) and image-asset enumeration (BR-5) are removed from the contract and the implementation; `expected_outputs`/`instructions`/`sections`/`assets`/`status` no longer emitted.

### Input YAML (NbFoundry-owned)

Keep a `sections`-style author definition — each section carries `title`, `description` (markdown), and `code` **or** `code_file`. Generation maps each section to a marimo **markdown cell** (the rendered description) followed by a **code cell** (the section's code). Top-level `title` / `description` / `hints` / `environment` feed the banner and the notebook header. **Dropped from input:** `expected_outputs`, `submission`, and the `editable` flag (editability is the curriculum author's `ExerciseBlock` choice on LF's side, not NbFoundry's — per contract). Insertion points remain expressible as ordinary `# YOUR CODE HERE` comments in section code (pass-through text).

---

## Technical Changes (module-level)

| Module | Change |
|---|---|
| `schema.py` | New input model (`ExerciseDefinition` + `SectionModel`); new output `TypedDict` (`CompiledExercise` = banner + `notebook_source`). **Delete** `SubmissionModel`/`SubmissionFieldModel`/`ExpectedRule`/`RawExpectedOutputModel` and the `CompiledSubmission*`/`CompiledExpected*` shapes. |
| `codegen.py` *(new)* | Definition → `notebook_source`: emit `import marimo` + `mo`, one `mo.md(...)` cell per section description, one code cell per section, byte-stable ordering. Imports emitted as text only. |
| `compiler.py` | Rewrite `compile_exercise` orchestration: read → validate → render banner markdown → `codegen.generate()` → assemble Option-C dict. Drop asset/submission/expected-output handling. |
| `validator.py` | Validate the new definition shape; drop BR-4/BR-5 checks. |
| `assets.py` | **Delete** (BR-5 removed). |
| `markdown.py` | Keep (banner `description`/`hints`, section descriptions). |
| `paths.py` | Keep (path-escape for `code_file`). |
| `errors.py`, `_modelfoundry.py`, `config.py`, `logging_setup.py` | Unchanged. |
| `cli.py` | `compile-exercise` emits the new dict (`--out` writes JSON incl. `notebook_source`); `validate` unchanged in shape. `init` / `compile` (standalone) surfaces untouched. |
| `notebooks.py` / `standalone.py` | Untouched as features; reuse their marimo-module know-how in `codegen.py`. |
| tests | Remove the static-path suites + `valid_graded.json` golden; add codegen unit/integration + a marimo-loads-the-generated-module smoke; extend the no-ML-import AST scan to the codegen path. |
| `concept.md` / `features.md` / `tech-spec.md` / `README.md` | Reconcile Option B → Option C (CR-3/CR-6, FR-3/FR-5, data models, AC-2/AC-3, package structure). |

---

## Out of Scope (deferred) — please confirm each

1. **Scaffold-template injection.** NbFoundry generating data-load/train/eval scaffold cells itself (the "NbFoundry handles scaffolding" framing). v1 assembles **author-supplied** cells only. Grouped into a single Future entry alongside the modelfoundry/DataRefinery integration work (they share the "emit framework scaffold as text" mechanism).
2. **Graded submission.** BR-4 `submission` schema + scoring — parked in `## Future` as a marimo-cell-output concern, not a returned field (per contract).
3. **Image-asset staging (BR-5).** The notebook renders its own outputs at run time; no separate asset list.
4. **LearningFoundry-side work.** `learningfoundry launch`, `exercises-manifest.json`, process lifecycle, the SvelteKit banner — LF's repo.
5. **Marimo WASM (Option A).** Still deferred; the banner/launch contract is forward-compatible with a future `marimo_wasm_bundle` field.

---

## Proposed Story Breakdown (Phase I)

Versioning: **phase-bundled** — the contract is only Option-C-compliant once I.d flips `compile_exercise`, so intermediate stories (spike, schema, generator) land unversioned and the phase ships a single **v0.46.0** at the end (minor: pre-1.0, output-shape change). Adjustable to per-story minors if preferred.

- **I.a — Codegen spike** *(throwaway)*. Prove a self-contained `marimo.App()` string runs under `marimo run`/`edit`, deterministically, with zero ML imports at generation time. Deliverable: the documented cell-emission pattern + marimo-version target. De-risks I.c.
- **I.b — Option C schema.** New input definition model + banner/`notebook_source` output `TypedDict`; delete the submission/expected-output/asset models.
- **I.c — Marimo notebook generator (`codegen.py`).** Definition → `notebook_source`; byte-stable; imports-as-text.
- **I.d — Rewire `compile_exercise`/`validate_exercise` → Option C; retire the static path** (delete `assets.py`, BR-4/BR-5 handling; update `compile-exercise` CLI).
- **I.e — Test-suite rebuild for Option C** (codegen unit/integration; extend the no-ML-import AST scan; marimo-loads-generated-module smoke; remove static-path suites + golden).
- **I.f — Spec + docs reconciliation** to Option C; **bump to v0.46.0**; CHANGELOG.

---

## Acceptance (phase-level)

`from nbfoundry import compile_exercise` returns the Option-C dict for a well-formed definition; `notebook_source` loads and runs under marimo (smoke); `compile_exercise` imports no ML framework at build time (AST-scan + sandbox); `validate_exercise` collects all errors; the static-display fields are gone; nbfoundry's own specs describe Option C; suite + coverage + mypy + ruff green.

---

## Story I.a — Spike Findings (cell-emission pattern, feeds I.b/I.c)

Throwaway spike at `scripts/spike_codegen.py` (deleted at story close). Three machine-checkable deliverables green; the `marimo run` / `marimo edit` round-trip is deferred to developer hardware. Cross-process determinism confirmed: SHA-256 `c96b2e9…d98d3` reproduces across three separate process invocations of the spike with the bundled sample.

### Target marimo-module shape

The production generator (`src/nbfoundry/codegen.py`, Story I.c) emits modules conforming to the shape below — chosen to match the existing template convention in `src/nbfoundry/templates/data_exploration/notebook.py`:

```python
import marimo

__generated_with = '<version>'
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    mo.md('# <title>\n\n<description>')
    return (mo,)


@app.cell
def _(mo):
    mo.md('## <section.title>\n\n<section.description>')
    return


@app.cell
def _():
    <author code, 4-space indented>
    return


if __name__ == "__main__":
    app.run()
```

Decisions baked in:

- **Header cell exports `(mo,)`** via marimo's reactive arg-injection so every downstream markdown cell can take `def _(mo):` and reuse the same import. Matches the existing template convention; no second `import marimo as mo` in subsequent markdown cells.
- **Markdown content emitted via `repr()`** (single-line `'...\n...'` literals, not triple-quoted blocks). Reason: `repr()` is byte-stable across runs and trivially handles embedded quotes, backslashes, and newlines without escape-rule edge cases. Readability is a marimo-edit concern; the `mo.md(...)` output renders identically either way.
- **Code cells receive no reactive args** in the spike (`def _():` with no parameters). The author's code is treated as opaque text and emitted indented under the function body. **Reactive arg-injection between author-supplied code cells is the one open design question** that the spike intentionally did not solve — see "Open question for I.c" below.
- **Empty / whitespace-only code bodies become `pass`** so the generated function stays syntactically valid.
- **Module-level prelude / footer are constant** across all generated notebooks (no per-exercise variation), maximizing determinism.

### Marimo version target

- **Installed at spike time:** `marimo 0.23.9`.
- **Existing `templates/data_exploration/notebook.py` carries:** `__generated_with = "0.23.5"`.
- **Pin for the Option-C generator:** surface the *currently installed* marimo version in `environment.dependencies` (so the learner runs against the same minor as the toolchain that generated their notebook) and use the same string for `__generated_with`. **Do not hard-code** the version in `codegen.py` — read it via `importlib.metadata.version("marimo")` at generation time. This keeps the spec drift-free as marimo updates land in `templates/requirements-base.txt`.
- The `templates/requirements-base.txt` `marimo` line is currently unpinned. Story I.c may want to tighten that to `marimo>=0.23,<0.24` (or whatever range I.c validates against), but pinning is out of scope for I.a.

### Determinism strategy (must hold for I.c)

- All `mo.md(...)` payloads built from input fields only; no environment-derived values (no timestamps, no host info, no random IDs).
- Cell order = sections in input order, with each section emitting exactly two cells (markdown then code) in that order.
- No `dict` iteration over user data — every traversal is over ordered `tuple`s / `list`s in the input dataclasses.
- `repr()` for string literals avoids triple-quote escape-rule branching that could vary by content.

### Build-time purity (FR-7 / AC-10 carried forward)

- The spike's AST scan against its own source confirmed zero imports from the forbidden set (`torch`, `tensorflow`, `keras`, `transformers`, `datasets`, `peft`, `sentencepiece`, `tiktoken`, `optuna`, `modelfoundry`, `datarefinery`).
- Framework imports appear *only* as source text inside emitted cells (verified by reading the generated module and confirming the `import torch` line lives inside an `@app.cell` body).
- Story I.e extends this AST scan to cover `src/nbfoundry/codegen.py` and the rewired compile path; the spike's narrow list is a starting point — I.e's list is authoritative.

### Open question for I.c (intentionally not solved here)

**Reactive dataflow between multiple author-supplied code cells.** Marimo's reactivity requires each cell to declare its inputs via the cell function's parameters (`def _(df, mo):`) and its outputs via the `return` tuple. The spike emits each code cell as `def _():` returning nothing, which works for a single self-contained code cell but breaks the moment Section 2 references a name defined in Section 1.

I.c needs to choose between:

1. **Treat each section's code as a self-contained cell** (author's responsibility to repeat imports / re-derive state). Simple; matches the spike. Loses marimo's reactivity benefit.
2. **AST-scan each section's code** to detect free names (inputs) and top-level assignments (outputs), then synthesize the `def _(...)` signature and `return` tuple. Preserves reactivity. Complex; pulls Python AST handling into `codegen.py`.
3. **Hybrid** — emit `def _():` by default, but allow a section to declare its inputs/outputs explicitly in the YAML definition (e.g., `inputs: [df, mo]`, `outputs: [summary]`). Pushes the choice to the curriculum author.

I.c should make this call up front; the spike does not. Recommendation: start with (1) for the first I.c landing, revisit (2)/(3) once a real curriculum exercise hits the limitation.
