# consumer-dependency-spec.md — NbFoundry (as consumed by LearningFoundry)

This document defines what LearningFoundry **requires** from NbFoundry — the contract between the two projects. NbFoundry is published on PyPI; this spec sustains the interface that LearningFoundry supports for its curriculum exercises as NbFoundry (Marimo-based) notebooks.

---

## Role in LearningFoundry

NbFoundry is the **experiential content provider**. It produces interactive, executable notebook-based exercises that learners complete within the curriculum. In the "Deep Learning Essentials" curriculum, these exercises involve building neural networks, training models, and analyzing results — with NbFoundry handling the scaffolding (data loading, training loops, evaluation) and providing explicit insertion points where the learner writes code.

NbFoundry depends on **ModelFoundry** internally for data preparation, model training, optimization, and evaluation scaffolding. LearningFoundry does not interact with ModelFoundry directly — it is an implementation detail of NbFoundry.

### Integration Points

| LearningFoundry Stage | NbFoundry Role |
|----------------------|----------------|
| **Content resolution** (Python, build time) | Compile exercise definition → renderable exercise artifact |
| **SvelteKit frontend** (TypeScript, runtime) | Render interactive exercise in the browser |
| **Progress tracking** (runtime) | Report exercise completion event to LearningFoundry's progress database |

---

## Design Decision: Rendering Approach

NbFoundry exercises are runnable Python (model-building/training). Three approaches were considered:

### Option A: Marimo WASM Embed (future, blocked for GPU/PyTorch)

[Marimo](https://marimo.io) supports [WASM-based browser execution](https://docs.marimo.io/guides/wasm/) — a full Python runtime (via Pyodide) in the browser. **Cons:** ~40MB Pyodide payload, cold-start latency, and **PyTorch is not available under Pyodide** — which rules it out for the model-training exercises that motivate this integration. Revisit for non-GPU exercises.

### Option B: Static Exercise Display — **SUPERSEDED**

NbFoundry compiled the exercise to a static dict (`sections`/`expected_outputs`) that LearningFoundry rendered as read-only blocks. **This failed in practice:** a model-building exercise rendered as static text is just the notebook's *source code* in a `<pre>` block — no executed cells, no plots, no metrics. The pedagogical value only exists when the notebook **runs**.

### Option C: Locally-hosted live marimo + banner/launch (v1)

NbFoundry's `compile_exercise` builds a runnable **marimo `.py`** and returns it (as source) alongside banner metadata. LearningFoundry stages the notebook and an `exercises-manifest.json` sidecar. The learner runs `learningfoundry launch <id>` — a CLI that owns marimo's lifecycle (port check, pidfile, spawn `marimo edit|run … --headless`) — and the SvelteKit app renders a **banner** (title/description + a 4-state button) that opens the live marimo page in a new tab and records completion.

**Why this shape:** the generated SvelteKit app is **static** — a browser page cannot spawn or kill an OS process. So the lifecycle lives in a CLI the *learner* runs, not the page. PyTorch never enters the LearningFoundry build or the browser; it is a **learner-runtime** dependency only, present when marimo actually executes the notebook locally.

### Decision

**v1: Option C.** `compile_exercise` emits notebook source + metadata (no static render); the learner runs the notebook via `learningfoundry launch`; the app is a banner that links to it. **Future: Option A** (Marimo WASM) for non-GPU exercises — the banner/launch contract is forward-compatible (a future `marimo_wasm_bundle` field would let the banner embed instead of link).

> **Contract history.** The Option-B static-display API (`compile_exercise → {sections, expected_outputs, submission, …}`) was the prior version of this contract; it is replaced by the notebook-emit API in BR-1. LearningFoundry tracks its own migration internally (its `stories.md`); NbFoundry only needs the current BR-* contract below.

---

## Build-Time Requirements (Python API)

### BR-1: Exercise Compilation API

NbFoundry must expose a Python API that LearningFoundry can call during content resolution to compile a single exercise definition file into a renderable artifact.

**Required interface (Option C):**

```python
def compile_exercise(yaml_path: Path, base_dir: Path) -> dict:
    """
    Compile an exercise definition file into (a) a runnable marimo notebook
    and (b) banner metadata. LearningFoundry stages the notebook source and
    renders the metadata as a banner that links to the locally-run notebook.

    Args:
        yaml_path: Path to the exercise definition YAML file (relative to base_dir).
        base_dir: Root directory for resolving relative paths within the YAML.

    Returns:
        A JSON-serializable dict. Structure:

        {
            "type": "exercise",
            "source": "nbfoundry",
            "ref": "<original ref path>",
            "title": "Build a CNN Classifier",
            "description": "<HTML string>",      # banner body (rendered from markdown)
            "hints": [                            # optional, shown on the banner
                "Start with nn.Conv2d for the first layer."
            ],
            "environment": {                      # what the learner needs to run it locally
                "python_version": "3.12",
                "dependencies": ["marimo", "torch", "torchvision", "matplotlib"],
                "setup_instructions": "pip install -r requirements.txt"
            },
            "notebook_source": "import marimo\\napp = marimo.App()\\n@app.cell\\ndef _():\\n    ..."
                                                  # the full marimo notebook as a STRING — a
                                                  # self-contained `marimo.App()` module (see
                                                  # "notebook_source requirements" below).
        }

    Raises:
        nbfoundry.ExerciseError: If the exercise definition is invalid.
            Must include file path and human-readable description.
    """
```

**`notebook_source` requirements:**
- A complete, self-contained **marimo notebook module** — the same text marimo writes to a `.py` file: a top-level `app = marimo.App()` with `@app.cell` functions, runnable by `marimo edit <file>` and `marimo run <file>` with no further codegen.
- All third-party imports (`torch`, `torchvision`, …) appear **as source text in cells**. `compile_exercise` itself must not import them (see Constraints).
- Self-contained relative to the learner's working directory: any data/asset paths it reads are resolvable from where the learner runs `learningfoundry launch` (the curriculum repo root).
- Target a marimo version compatible with the learner runtime; surface that version (and other run deps) in `environment.dependencies`.

**Not returned (owned elsewhere):**
- **`mode`** (`edit` | `run`) is **not** NbFoundry's to set — the same notebook serves either way, and the choice is a pedagogical one the *curriculum author* makes on LearningFoundry's `ExerciseBlock`. Do not emit it.
- **`id`**, the staging path, and the `exercises-manifest.json` sidecar are LearningFoundry's — it keys the notebook by an `id` NbFoundry doesn't know.

**Behavior:**
1. Read the exercise YAML at `base_dir / yaml_path`.
2. Validate required fields (title, description).
3. Render markdown banner fields (`description`, `hints`) to HTML.
4. **Generate the marimo notebook as source** and return it in `notebook_source`. This is *code generation* — emit `import torch …` as text; do **not** execute it.
5. Return the dict. LearningFoundry does all I/O (writes the notebook to a runnable path keyed by the exercise `id`, and writes the `exercises-manifest.json` sidecar).

**Constraints:**
- Synchronous function, importable from the `nbfoundry` package.
- **The codegen path MUST NOT import `torch` / `modelfoundry` (or any GPU/ML framework).** `compile_exercise` runs in LearningFoundry's *build* process; importing a multi-hundred-MB framework there is the failure this contract revision exists to avoid. Torch is a **learner-runtime** dependency only — named in `environment.dependencies`, imported when marimo runs the notebook on the learner's machine, never at build time.
- No side effects: no file writes, no process spawning (`compile_exercise` returns source as a string; LearningFoundry does all I/O).
- The returned dict must be JSON-serializable. `notebook_source` is a plain string.
- **Removed from the contract** (do not emit): `sections`, `expected_outputs`, `submission`, `instructions`, and the inline image-asset list — the prior static-display fields. The notebook now carries the cells, scaffolding, and rendered outputs. Graded submission is parked in `## Future` as a marimo-cell-output concern, not a returned field.

> **Removed from the contract (Option C).** **BR-4** (submission schema) and **BR-5** (inline image-asset handling) describe the retired static-display path — NbFoundry does **not** implement them under Option C; the notebook carries its own cells, rendered outputs, and any grading. The **RR-** "Runtime Requirements" sections spec LearningFoundry's *own* SvelteKit frontend (the banner that links to the locally-run notebook) and are **not part of NbFoundry's contract** at all. Graded submission is parked in `## Future`. The sections below are retained for design rationale only.

### BR-2: Exercise Validation API

```python
def validate_exercise(yaml_path: Path, base_dir: Path) -> list[str]:
    """
    Validate an exercise definition file without compiling.

    Returns:
        An empty list if valid, or a list of human-readable error strings.
    """
```

### BR-3: Error Contract

NbFoundry errors must be catchable as `nbfoundry.ExerciseError` (or similar), carrying:
- **file_path**: The exercise file that failed.
- **message**: Human-readable description.
- **detail**: Optional structured detail (section index, field name).

### BR-4: Submission Schema and Evaluation Contract

> ⛔ **Removed from the Option-C contract — do not implement.** Retained for design rationale (the future graded-submission path). Under Option C grading happens in the notebook's own cells; `compile_exercise` does not emit `submission`.

`compile_exercise` may emit an optional `submission` block describing how the learner's outcome is captured and graded. This is the contract that lets `ExerciseBlock` produce a `score / maxScore` payload analogous to QuizBlock, with a configurable `pass_threshold` for completion.

**Forward-compat by design.** The `submission` schema is the *author's contract for what counts as success*, independent of *how* the values get captured. In v1 (Option B static display), the frontend renders typed input fields and the learner pastes their results from a local run. In the future Marimo WASM mode (Option A), the same `submission` schema is satisfied by cell outputs from the executing notebook — same comparison rules, same scoring formula, same `complete` event payload. **Existing exercises authored against v1's paste-in flow do not require YAML rewrites when WASM lands.**

**Field shape:**

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `pass_threshold` | float | No (default `0.0`) | Range `[0.0, 1.0]`. `0.0` means "no threshold gate" (the exercise is treated as manual / self-attest, but still records the captured score). `1.0` means "every field must pass." |
| `fields` | list of field objects | Yes (when `submission` is present) | At least one field. |

**Field object shape:**

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `name` | string | Yes | Stable identifier; used as the form field name and in any future telemetry. |
| `type` | `"number"` \| `"text"` | Yes | v1 input types. Future additions: `"json"`, `"image"` (file upload, hash-compared). |
| `label` | string | Yes | Human-readable prompt rendered next to the input. |
| `placeholder` | string | No | Optional placeholder text for the input. |
| `expected` | comparison-rule object | Yes | Rule by which the captured value is graded. See below. |

**Comparison rules (`expected.type`):**

| Rule | Applies to | Required keys | Match condition |
|------|-----------|---------------|-----------------|
| `range` | `number` | `min` and/or `max`, `weight` | `min <= value <= max`. Either bound may be omitted (treated as `-∞` / `+∞`). |
| `equals` | `number`, `text` | `value`, `weight` | Strict equality (numeric: `==`; text: case-sensitive string compare). |
| `contains_all` | `text` | `values` (list of strings), `weight` | Every entry in `values` is a substring of the captured text. Case-sensitive. |

`weight` is a positive integer (default `1` if omitted). It contributes both to the numerator (when the rule passes) and the denominator (always) of the final score.

**Scoring formula (locked):**

```
score    = sum(rule.weight  for rule in submission.fields if rule passed)
maxScore = sum(rule.weight  for rule in submission.fields)
passed   = (maxScore > 0) AND (score / maxScore >= pass_threshold)
```

This is the same shape QuizBlock uses (see [features.md FR-4 quiz block](../features.md#fr-4-in-browser-progress-tracking) — "fires when `score / maxScore >= passThreshold`"). Reusing the formula keeps the recording schema in [`learningfoundry`'s `quiz_scores` table-shape mental model](../project-essentials.md#domain-conventions) consistent: `score` (points earned), `max_score` (total), with completion gated on a threshold.

**When `submission` is absent (or `None`):** the exercise renders today's manual-completion UI ("Mark as Complete" button). No scoring; the `complete` event carries `status: "completed"` only. This is the default and lets authors opt into evaluation incrementally.

**Validator requirements (BR-2 extension):**
- Reject `pass_threshold` outside `[0.0, 1.0]`.
- Reject empty `fields` lists when `submission` is present.
- Reject mismatched rule/type combinations (e.g., `contains_all` on a `number` field, `range` on a `text` field).
- Reject duplicate field `name` values within one exercise.
- Reject `weight <= 0` and non-integer weights.

### BR-5: Asset Handling

> ⛔ **Removed from the Option-C contract — do not implement.** This covered the inline image-asset list of the static-display path. Under Option C the marimo notebook renders its own outputs (plots, tables) at run time, so there is no separate asset list to emit or stage. Retained for rationale.

Image (and other binary) assets referenced by an exercise travel as **relative file paths**, not as inline bytes. This matches how SvelteKit, Vite, and the broader web platform handle media — HTTP-cacheable, lazy-loadable, image-pipeline-friendly, diff-readable.

**Division of responsibilities:**

| Concern | Owner | Mechanism |
|---------|-------|-----------|
| Author writes asset path in YAML | Curriculum author | `expected_outputs[].reference: references/expected_loss_curve.png` (path relative to the exercise YAML's directory) |
| Validate asset files exist at compile time | NbFoundry | BR-1 step 5 — `(base_dir / <path>).exists()` check; raise `ExerciseError` if missing |
| Emit `path` field in compiled dict | NbFoundry | Forward the relative path verbatim — no URL construction, no bytes, no encoding |
| Stage asset files into the build output | LearningFoundry pipeline | Copy `base_dir/<path>` → `output_dir/static/exercises/<exerciseRef>/<path>` |
| Construct runtime URL for `<img src>` | `ExerciseBlock` (runtime) | `` `/exercises/${exerciseRef}/${output.path}` `` |

**Why NbFoundry doesn't construct URLs:** the `exerciseRef` is a curriculum-level concern (set by LearningFoundry's curriculum YAML, not by the exercise author), and the `static/exercises/` URL convention is a LearningFoundry build-output choice. Pushing URL construction into NbFoundry would couple the library to a host-specific path layout. Relative paths in the dict + runtime URL composition is the loose-coupling design — the same as how QuizBlock manifests carry `quizRef` separately from the rendering host's URL scheme.

**Asset enumeration for the pipeline:** so LearningFoundry doesn't have to traverse the dict hunting for paths, the compiled exercise SHOULD include a top-level `assets: list[str]` field enumerating every relative path the dict references. The pipeline iterates this list to do the copy step. Empty list when there are no binary assets.

```python
{
    "type": "exercise",
    # ...
    "assets": [
        "expected_loss_curve.png",
        "references/sample_input.npy"
    ],
    # ...
}
```

**Inline-by-value remains forbidden** — even for tiny images. Premature optimization that costs the points listed in the "why URLs not base64" rationale (HTTP cache loss, JSON bloat, diff noise, no image-pipeline tooling). If a future build optimization wants to inline very-small assets, that's a SvelteKit / Vite layer concern (`assetInlineLimit`) operating on URL-referenced files, not a contract change in NbFoundry's output dict.

---

## Exercise Definition Format (YAML Input)

The curriculum author writes exercise definitions in YAML. This is the input format that NbFoundry consumes. NbFoundry owns this format's exact schema; the example below is illustrative.

> Under Option C, the definition's content compiles into the marimo **notebook** rather than static `sections`/`expected_outputs`. The **`submission:` block is deferred** (see `## Future`) — omit it; graded submission will be a marimo-cell-output concern, not a returned field.

```yaml
title: "Build a CNN Classifier"
description: |
  In this exercise, you'll build a convolutional neural network to classify
  CIFAR-10 images. The data loading and training loop are provided — your
  job is to define the model architecture and evaluation logic.

sections:
  - title: "Data Loading"
    description: "Pre-built data pipeline. Review but do not modify."
    code_file: scaffolds/data_loading.py
    editable: false

  - title: "Define Your Model"
    description: |
      Build a CNN with at least two convolutional layers. Use `nn.Conv2d`,
      `nn.ReLU`, `nn.MaxPool2d`, and `nn.Linear`.
    code: |
      import torch.nn as nn

      class SimpleCNN(nn.Module):
          def __init__(self):
              super().__init__()
              # YOUR CODE HERE: define layers

          def forward(self, x):
              # YOUR CODE HERE: define forward pass
              pass
    editable: true

  - title: "Training Loop"
    description: "Standard training loop. Review to understand the process."
    code_file: scaffolds/training_loop.py
    editable: false

  - title: "Evaluate Results"
    description: "Compute accuracy on the test set and plot the loss curve."
    code: |
      # YOUR CODE HERE: compute test accuracy
      # YOUR CODE HERE: plot training loss curve
    editable: true

expected_outputs:
  - description: "Training loss should decrease over epochs"
    type: image
    reference: references/expected_loss_curve.png

  - description: "Test accuracy should exceed 65%"
    type: text
    content: "Expected: accuracy >= 0.65"

hints:
  - "Start with nn.Conv2d(3, 16, kernel_size=3, padding=1) for the first layer."
  - "Use nn.MaxPool2d(2) to reduce spatial dimensions."
  - "Remember to flatten the tensor before the fully connected layer."

# Optional. Omit this block to keep today's "Mark as Complete" behavior.
# When present, ExerciseBlock renders typed input fields, grades the
# learner's submission against `expected` rules, and fires `complete`
# with score/maxScore/passed. The same schema is satisfied by Marimo
# WASM cell outputs in the future Option A path — no YAML rewrite.
submission:
  pass_threshold: 0.65
  fields:
    - name: test_accuracy
      type: number
      label: "Test set accuracy"
      placeholder: "0.65"
      expected:
        type: range
        min: 0.65
        max: 1.0
        weight: 1
    - name: model_summary
      type: text
      label: "Paste your model architecture (output of `print(model)`)"
      expected:
        type: contains_all
        values: ["Conv2d", "Linear", "ReLU"]
        weight: 1

environment:
  python_version: "3.12"
  dependencies:
    - torch
    - torchvision
    - matplotlib
```

---

## Runtime Requirements (SvelteKit Component)

> ℹ️ **Not part of NbFoundry's contract.** The RR-* sections spec LearningFoundry's *own* SvelteKit frontend, included here for end-to-end context. NbFoundry implements only the BR-* (Python API) above. Under Option C, `ExerciseBlock` is a **banner** linking to the locally-run marimo notebook; the static-render details below are historical (the prior Option-B display).

### RR-1: Exercise Display Component

LearningFoundry's SvelteKit template includes an `ExerciseBlock` component that renders the compiled exercise artifact.

**For v1 (static display):**

```svelte
<ExerciseBlock
  exercise={exerciseData}
  exerciseRef={refPath}
  on:complete={handleExerciseComplete}
/>
```

**Props:**
- `exercise` — The compiled exercise dict.
- `exerciseRef` — Unique string identifying this exercise instance (ref path from curriculum YAML).

**Events:**
- `complete` — Fired when the learner finishes the exercise, either by manual mark-complete (no `submission` block) or by submitting graded values (with `submission` block).

```typescript
interface ExerciseCompleteEvent {
  exerciseRef: string;
  status: "completed";

  // The fields below are present when the exercise's compiled dict includes
  // a `submission` block. Absent for manual-completion exercises.
  score?: number;        // sum of weights of rules that passed
  maxScore?: number;     // sum of all rule weights
  passed?: boolean;      // (maxScore > 0) AND (score / maxScore >= passThreshold)
  submittedValues?: Record<string, string | number>;   // raw inputs by field name; for telemetry / replay
}
```

**v1 Rendering Behavior — manual completion (no `submission` block):**
1. Display exercise title and instructions.
2. Render each section with its title, description, and code block (syntax-highlighted).
3. Visually distinguish editable sections (insertion points) from scaffold sections (read-only).
4. Display expected outputs:
    - `type: image` → `<img src="/exercises/${exerciseRef}/${output.path}" alt="${output.alt}" loading="lazy" />` — URL is composed at runtime from the prop `exerciseRef` and the dict's relative `path`. Lazy loading ensures off-screen exercise media doesn't block other lessons. Asset files are staged into `output_dir/static/exercises/<exerciseRef>/` by the build pipeline (BR-5).
    - `type: text` → render the `content` string inline.
    - `type: table` → render `content` as a markdown table (or as a fetched CSV/JSON when `path` is set; deferred — text-content tables only in v1).
5. Provide collapsible hints.
6. Display environment/setup instructions so the learner knows how to run the exercise locally.
7. Provide a "Mark as Complete" button that fires the `complete` event with `status: "completed"` only.

**v1 Rendering Behavior — graded submission (with `submission` block):**

All of the manual-completion rendering above, *plus*:

8. Render each `submission.fields` entry as a typed input control (HTML `<input type="number">` / `<input type="text">` / `<textarea>` for multi-line) with the field's `label` and `placeholder`.
9. Replace the "Mark as Complete" button with a "Submit" button. Submit is enabled when every field has a non-empty value (numeric fields must parse as `Number.isFinite`).
10. On submit, evaluate every field's value against its `expected` rule using the BR-4 comparison logic; compute `score`, `maxScore`, and `passed`.
11. Render an inline result panel:
    - **Pass** (`passed === true`): a green "Submission accepted" banner with `score / maxScore` shown, a list of which fields passed, and a Resubmit affordance for learners who want to improve.
    - **Fail** (`passed === false`): an amber "Submission below threshold" banner with the same per-field breakdown, the gap to threshold, and a Retry affordance that re-enables the inputs without clearing them.
12. Fire the `complete` event with the full payload (including `score`, `maxScore`, `passed`, `submittedValues`). The event fires on **every** submit, not only on the first pass — the recording layer is responsible for "best score wins" semantics if it cares (mirrors the QuizBlock convention; see LearningFoundry's [`saveQuizScore` upsert](../../src/learningfoundry/sveltekit_template/src/lib/db/progress.ts) for the prior-art pattern).
13. Comparison logic runs entirely in the browser. **The component does not POST submission values anywhere.** This preserves the v1 no-server constraint.

**Future (Marimo WASM) Rendering Behavior:**

When `compile_exercise` returns a `marimo_wasm_bundle` field (Option A future path):
- Render an embedded Marimo WASM notebook instead of static code blocks (manual-completion case) or instead of typed input fields (graded-submission case).
- The learner writes and executes code in-browser.
- For graded exercises: the host subscribes to designated Marimo cell outputs identified by the same `submission.fields[].name` values. Each cell emits a value that satisfies the same `expected` rule it would have satisfied via paste-in. The grading logic, scoring formula, and `complete` event payload stay identical — only the input source changes.
- For manual exercises (no `submission`): completion is detected when the learner clicks a "Mark as Complete" button or, optionally, when authored evaluation cells produce expected outputs (deferred design decision for the WASM phase).

### RR-2: No Data Handoff (v1)

In v1, there is no data transfer between the SvelteKit app and the learner's local Python environment. The exercise is purely informational — it shows what to build and what to expect, but execution happens externally. The `ExerciseBlock` component does not execute code.

---

## Data Flow Summary

```
Build time (Python):
  curriculum.yml
    → content resolution encounters `type: exercise, source: nbfoundry, ref: ...`
    → LearningFoundry calls nbfoundry.compile_exercise(ref, base_dir)
        → NbFoundry internally uses ModelFoundry for scaffolding (opaque to LearningFoundry)
        → NbFoundry validates that every path in `assets[]` exists at base_dir/<path>
    → receives exercise dict (with relative `path`s in expected_outputs[type=image] and a top-level `assets: list[str]`)
    → LearningFoundry pipeline copies each `assets[]` entry from base_dir/<path>
        to output_dir/static/exercises/<exerciseRef>/<path> (BR-5 asset staging)
    → serializes the dict to JSON in the generated SvelteKit project; assets are served by the SvelteKit static adapter

Runtime (SvelteKit):
  LessonView renders ExerciseBlock component with exercise data + exerciseRef
    → v1 manual-completion path (no `submission` block):
        static display of instructions, code, expected outputs
        → learner works locally, then clicks "Mark as Complete"
        → fires `complete` event with {exerciseRef, status: "completed"}
        → LearningFoundry writes status to exercise_status table
    → v1 graded-submission path (with `submission` block):
        static display + typed input fields per `submission.fields`
        → learner works locally, pastes results into the form, clicks Submit
        → component grades client-side via BR-4 comparison rules
        → fires `complete` event with {exerciseRef, status, score, maxScore, passed, submittedValues}
        → LearningFoundry writes status (+ score/max_score for analytics if desired)
    → Future (Marimo WASM):
        graded path swaps form-fields for cell-output subscription;
        same scoring formula, same `complete` payload, same exercise_status write
    → progress dashboard reads exercise_status for module-level display
```

---

## Package Distribution

| Concern | Value |
|---------|-------|
| **Python package** | `nbfoundry` on PyPI |
| **LearningFoundry dependency** | Optional extra: `pip install learningfoundry[nbfoundry]` (`nbfoundry>=0.1`); the provider lazy-imports it and raises an install hint when absent |
| **Real provider** | `NbfoundryProvider` in `learningfoundry.integrations.nbfoundry` delegates to `nbfoundry.compile_exercise` — the default for `status: ready` blocks |
| **Stub** | `stub_exercise()` factory + `NbfoundryStub` test-double in `learningfoundry.integrations.nbfoundry_stub`; the resolver emits the placeholder directly for `status: stub` blocks (no provider call, no nbfoundry import). `NbfoundryStub` is retained only as a test double / "no-notebooks" injectable |

---

## Stub Behavior

LearningFoundry supports a `stub` status for an exercise block. NbFoundry publishes a stub class that can be inserted into the curriculum structure, and that is useful for curriculum development and testing. Here is the `NbfoundryStub` class that implements the `ExerciseProvider` protocol:

```python
class NbfoundryStub:
    def compile_exercise(self, ref_path: Path, base_dir: Path) -> dict:
        return {
            "type": "exercise",
            "source": "nbfoundry",
            "ref": str(ref_path),
            "status": "stub",
            "title": f"Exercise: {ref_path.stem}",
            "instructions": f"<p>Exercise placeholder for <code>{ref_path}</code>. "
                            "nbfoundry integration pending.</p>",
            "sections": [],
            "expected_outputs": [],
            "assets": [],          # No binary assets to stage for stub exercises
            "hints": [],
            "submission": None,    # Stub exercises stay manual-completion-only
            "environment": None,
        }
```

The `ExerciseBlock` component detects `status: "stub"` and renders a placeholder card with the message. Because the stub returns `submission: None`, the placeholder card always uses the manual-completion UI regardless of whether the eventual real exercise is graded.

---

## Versioning and Compatibility

- The exercise dict schema is the versioning boundary. The `status` field distinguishes stub content from real content.
- NbFoundry is published; LearningFoundry consumes it through the optional `[nbfoundry]` extra and the real `NbfoundryProvider`. The `status` switch is resolver-owned: `ready` (the default) compiles via `NbfoundryProvider`; `stub` emits the placeholder directly. `NbfoundryStub` is no longer the routing target — it survives as a test double only.
- The SvelteKit `ExerciseBlock` component handles both stub and real exercise dicts.

---

## Testing Contract

| Test | Owner | What is tested |
|------|-------|----------------|
| `compile_exercise` returns valid artifact for well-formed YAML | NbFoundry | Unit test in NbFoundry repo (future) |
| `compile_exercise` raises `ExerciseError` for malformed YAML | NbFoundry | Unit test in NbFoundry repo (future) |
| LearningFoundry's `stub_exercise()` / `NbfoundryStub` return correct placeholder structure | LearningFoundry | Unit test |
| `NbfoundryProvider.compile_exercise` delegates to `nbfoundry.compile_exercise` and returns its dict unchanged | LearningFoundry | Unit test (mocked) |
| `NbfoundryProvider` wraps nbfoundry errors in `IntegrationError` citing `ref_path`; missing package raises `ImportError` with `learningfoundry[nbfoundry]` hint | LearningFoundry | Unit test (mocked) |
| Resolver routes `status: stub` to `stub_exercise()` (no provider call, no nbfoundry import) and `status: ready`/default to the provider, failing loud on a bad ref | LearningFoundry | Unit test |
| LearningFoundry's `ExerciseProvider` protocol matches NbFoundry's API | LearningFoundry | Type check (mypy) + runtime `isinstance` (protocols are `@runtime_checkable`) |
| `ExerciseBlock` renders stub content with placeholder message | LearningFoundry | Component test |
| `ExerciseBlock` renders real exercise with sections and hints | LearningFoundry | Component test (future, with fixture data) |
| `ExerciseBlock` fires `complete` event on "Mark as Complete" click (manual path) | LearningFoundry | Component test |
| `ExerciseBlock` renders typed input fields when `submission` is present | LearningFoundry | Component test |
| `ExerciseBlock` Submit button is disabled until every field has a parseable value | LearningFoundry | Component test |
| `ExerciseBlock` grades a passing submission and fires `complete` with `passed: true`, correct `score`/`maxScore` | LearningFoundry | Component test |
| `ExerciseBlock` grades a failing submission and fires `complete` with `passed: false`, allows resubmit | LearningFoundry | Component test |
| `range`, `equals`, `contains_all` comparison rules each pass and fail correctly with edge values | LearningFoundry | Unit test on the comparison helper |
| Scoring formula: `score = sum of weights of passing rules`, `maxScore = sum of all weights`, `passed = score / maxScore >= pass_threshold` | LearningFoundry | Unit test on the comparison helper |
| `compile_exercise` validator rejects malformed `submission` blocks (BR-4 validator requirements) | NbFoundry | Unit test in NbFoundry repo (future); stub-side: validator is a no-op |
| `compile_exercise` rejects an exercise that references a missing asset file (BR-1 step 5) | NbFoundry | Unit test in NbFoundry repo (future) |
| `compile_exercise` validator rejects `expected_outputs[type=image]` missing the `alt` field (BR-1 constraint) | NbFoundry | Unit test in NbFoundry repo (future) |
| Compiled dict's `assets[]` enumerates every relative path the dict references (no orphans, no duplicates) | NbFoundry | Unit test in NbFoundry repo (future); stub returns `[]` |
| LearningFoundry pipeline copies every `assets[]` entry from `base_dir/<path>` to `output_dir/static/exercises/<exerciseRef>/<path>` (BR-5 staging) | LearningFoundry | Pipeline test |
| `ExerciseBlock` renders image expected-outputs as `<img>` with `src` composed from `exerciseRef + path` and `alt` from the dict | LearningFoundry | Component test |
| `ExerciseBlock` renders image `<img>` with `loading="lazy"` so off-screen exercise media doesn't block other content | LearningFoundry | Component test |
