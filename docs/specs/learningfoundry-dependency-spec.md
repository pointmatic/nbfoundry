# dependency-spec.md — nbfoundry (as consumed by learningfoundry)

This document defines what learningfoundry **requires** from nbfoundry — the contract between the two projects. nbfoundry does not yet exist as a library; this spec defines the interface that learningfoundry codes against, enabling a stub implementation for v1 and a real integration when nbfoundry is available.

---

## Role in learningfoundry

nbfoundry is the **experiential content provider**. It produces interactive, executable notebook-based exercises that learners complete within the curriculum. In the D802 Deep Learning Essentials curriculum, these exercises involve building neural networks, training models, and analyzing results — with nbfoundry handling the scaffolding (data loading, training loops, evaluation) and providing explicit insertion points where the learner writes code.

nbfoundry depends on **modelfoundry** internally for data preparation, model training, optimization, and evaluation scaffolding. learningfoundry does not interact with modelfoundry directly — it is an implementation detail of nbfoundry.

### Integration Points

| learningfoundry Stage | nbfoundry Role |
|----------------------|----------------|
| **Content resolution** (Python, build time) | Compile exercise definition → renderable exercise artifact |
| **SvelteKit frontend** (TypeScript, runtime) | Render interactive exercise in the browser |
| **Progress tracking** (runtime) | Report exercise completion event to learningfoundry's progress database |

---

## Design Decision: Rendering Approach

nbfoundry exercises need to render executable Python code in the browser. Two approaches are viable:

### Option A: Marimo WASM Embed (Recommended for future)

[Marimo](https://marimo.io) supports [WASM-based browser execution](https://docs.marimo.io/guides/wasm/) — a full Python runtime (via Pyodide) running in the browser with reactive notebook semantics. This would allow learners to write and execute Python code directly within the learningfoundry SvelteKit app with no server.

**Pros:** True in-browser code execution, reactive cells, rich output (plots, tables), no server infrastructure.
**Cons:** Large WASM payload (~40MB Pyodide), cold start latency, limited library support in Pyodide (PyTorch not available in WASM), complexity of embedding.

### Option B: Static Exercise Display (v1)

For v1, nbfoundry produces a **static exercise artifact** — structured content (instructions, code scaffolding, expected outputs) that learningfoundry renders as read-only content blocks. The learner reads the exercise, works in a separate local environment (JupyterLab, Marimo desktop, VS Code), and marks the exercise as complete in the app.

**Pros:** Simple, no WASM complexity, works with any Python library (including PyTorch/GPU).
**Cons:** Breaks the unified experience — learner must context-switch to a separate environment.

### Decision

**v1: Option B (static exercise display).** The exercises are blackbox content — nbfoundry returns structured data, learningfoundry renders it, no data handoff or code execution in the browser. The exercise content is curated by the author, not auto-generated.

**Future: Option A (Marimo WASM embed)** for exercises that don't require GPU-dependent libraries. The interface is designed to accommodate both approaches — the `ExerciseProvider` protocol returns a dict that can represent either static content or a Marimo WASM bundle.

---

## Build-Time Requirements (Python API)

### BR-1: Exercise Compilation API

nbfoundry must expose a Python API that learningfoundry can call during content resolution to compile a single exercise definition file into a renderable artifact.

**Required interface:**

```python
def compile_exercise(yaml_path: Path, base_dir: Path) -> dict:
    """
    Compile an exercise definition file into a renderable exercise artifact.

    Args:
        yaml_path: Path to the exercise definition YAML file (relative to base_dir).
        base_dir: Root directory for resolving relative paths within the YAML.

    Returns:
        A dict representing the compiled exercise, suitable for JSON serialization
        and consumption by the exercise frontend component. Structure:

        {
            "type": "exercise",
            "source": "nbfoundry",
            "ref": "<original ref path>",
            "status": "ready",           # "ready" | "stub"
            "title": "Build a CNN Classifier",
            "instructions": "<HTML string>",    # Rendered from markdown
            "sections": [
                {
                    "title": "Data Loading",
                    "description": "<HTML>",
                    "code": "import torch\\n...",     # Pre-filled code
                    "editable": false                  # Scaffold (read-only)
                },
                {
                    "title": "Define Your Model",
                    "description": "<HTML>",
                    "code": "# YOUR CODE HERE\\n...", # Insertion point
                    "editable": true                   # Learner writes here
                },
                {
                    "title": "Training Loop",
                    "description": "<HTML>",
                    "code": "for epoch in range(...)...",
                    "editable": false
                },
                {
                    "title": "Evaluate Results",
                    "description": "<HTML>",
                    "code": "",
                    "editable": true
                }
            ],
            "expected_outputs": [
                {
                    "description": "Training loss curve",
                    "type": "image",               # "image" | "text" | "table"
                    "path": "expected_loss_curve.png",   # relative to base_dir; staged by learningfoundry
                    "alt": "Training loss decreasing across 20 epochs"   # required for type=image, accessibility
                },
                {
                    "description": "Test accuracy threshold",
                    "type": "text",
                    "content": "Expected: accuracy >= 0.65"
                }
            ],
            "assets": [                              # See BR-5. Enumerates every relative path the dict references.
                "expected_loss_curve.png"
            ],
            "hints": [
                "Start with nn.Conv2d for the first layer.",
                "Remember to flatten before the fully connected layer."
            ],
            "submission": {                          # Optional. None for manual-completion exercises.
                "pass_threshold": 0.65,              # Optional float in [0.0, 1.0]; default 0.0 (= manual / self-attest)
                "fields": [
                    {
                        "name": "test_accuracy",
                        "type": "number",            # "number" | "text"
                        "label": "Test set accuracy",
                        "placeholder": "0.65",
                        "expected": {
                            "type": "range",         # "range" | "equals" | "contains_all"
                            "min": 0.65,
                            "max": 1.0,
                            "weight": 1
                        }
                    },
                    {
                        "name": "model_summary",
                        "type": "text",
                        "label": "Paste your model architecture",
                        "expected": {
                            "type": "contains_all",
                            "values": ["Conv2d", "Linear", "ReLU"],
                            "weight": 1
                        }
                    }
                ]
            },
            "environment": {
                "python_version": "3.12",
                "dependencies": ["torch", "torchvision", "matplotlib"],
                "setup_instructions": "Run `pip install -r requirements.txt` in your local environment."
            }
        }

    Raises:
        nbfoundry.ExerciseError: If the exercise definition is invalid.
            Must include file path and human-readable description.
    """
```

**Behavior:**
1. Read the exercise YAML at `base_dir / yaml_path`.
2. Validate required fields (title, instructions, at least one section).
3. Render markdown fields to HTML.
4. Resolve any referenced code files or data files.
5. **Asset references:** for every `expected_outputs[]` entry of `type: image` (and any future binary type), validate that the referenced file exists at `base_dir / <path>` and emit the relative `path` in the compiled dict. **Do not** read the asset bytes, do not base64-encode them, do not embed them in the dict. Asset staging is learningfoundry's responsibility (see "Asset Handling" below).
6. Return the compiled exercise dict.

**Constraints:**
- Synchronous function, importable from the `nbfoundry` package.
- No side effects beyond reading referenced files (no file writes, no asset copying — learningfoundry owns the build output).
- The returned dict must be JSON-serializable. Asset references travel as relative `path` strings; binary bytes never enter the dict.
- Image entries in `expected_outputs[]` MUST include an `alt` field for accessibility (WCAG 1.1.1). The validator (BR-2) rejects image outputs without `alt`.

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

nbfoundry errors must be catchable as `nbfoundry.ExerciseError` (or similar), carrying:
- **file_path**: The exercise file that failed.
- **message**: Human-readable description.
- **detail**: Optional structured detail (section index, field name).

### BR-4: Submission Schema and Evaluation Contract

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

Image (and other binary) assets referenced by an exercise travel as **relative file paths**, not as inline bytes. This matches how SvelteKit, Vite, and the broader web platform handle media — HTTP-cacheable, lazy-loadable, image-pipeline-friendly, diff-readable.

**Division of responsibilities:**

| Concern | Owner | Mechanism |
|---------|-------|-----------|
| Author writes asset path in YAML | Curriculum author | `expected_outputs[].reference: references/expected_loss_curve.png` (path relative to the exercise YAML's directory) |
| Validate asset files exist at compile time | nbfoundry | BR-1 step 5 — `(base_dir / <path>).exists()` check; raise `ExerciseError` if missing |
| Emit `path` field in compiled dict | nbfoundry | Forward the relative path verbatim — no URL construction, no bytes, no encoding |
| Stage asset files into the build output | learningfoundry pipeline | Copy `base_dir/<path>` → `output_dir/static/exercises/<exerciseRef>/<path>` |
| Construct runtime URL for `<img src>` | `ExerciseBlock` (runtime) | `` `/exercises/${exerciseRef}/${output.path}` `` |

**Why nbfoundry doesn't construct URLs:** the `exerciseRef` is a curriculum-level concern (set by learningfoundry's curriculum YAML, not by the exercise author), and the `static/exercises/` URL convention is a learningfoundry build-output choice. Pushing URL construction into nbfoundry would couple the library to a host-specific path layout. Relative paths in the dict + runtime URL composition is the loose-coupling design — the same as how QuizBlock manifests carry `quizRef` separately from the rendering host's URL scheme.

**Asset enumeration for the pipeline:** so learningfoundry doesn't have to traverse the dict hunting for paths, the compiled exercise SHOULD include a top-level `assets: list[str]` field enumerating every relative path the dict references. The pipeline iterates this list to do the copy step. Empty list when there are no binary assets.

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

**Inline-by-value remains forbidden** — even for tiny images. Premature optimization that costs the points listed in the "why URLs not base64" rationale (HTTP cache loss, JSON bloat, diff noise, no image-pipeline tooling). If a future build optimization wants to inline very-small assets, that's a SvelteKit / Vite layer concern (`assetInlineLimit`) operating on URL-referenced files, not a contract change in nbfoundry's output dict.

---

## Exercise Definition Format (YAML Input)

The curriculum author writes exercise definitions in YAML. This is the input format that nbfoundry consumes:

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

### RR-1: Exercise Display Component

learningfoundry's SvelteKit template includes an `ExerciseBlock` component that renders the compiled exercise artifact.

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
12. Fire the `complete` event with the full payload (including `score`, `maxScore`, `passed`, `submittedValues`). The event fires on **every** submit, not only on the first pass — the recording layer is responsible for "best score wins" semantics if it cares (mirrors the QuizBlock convention; see learningfoundry's [`saveQuizScore` upsert](../../src/learningfoundry/sveltekit_template/src/lib/db/progress.ts) for the prior-art pattern).
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
    → learningfoundry calls nbfoundry.compile_exercise(ref, base_dir)
        → nbfoundry internally uses modelfoundry for scaffolding (opaque to learningfoundry)
        → nbfoundry validates that every path in `assets[]` exists at base_dir/<path>
    → receives exercise dict (with relative `path`s in expected_outputs[type=image] and a top-level `assets: list[str]`)
    → learningfoundry pipeline copies each `assets[]` entry from base_dir/<path>
        to output_dir/static/exercises/<exerciseRef>/<path> (BR-5 asset staging)
    → serializes the dict to JSON in the generated SvelteKit project; assets are served by the SvelteKit static adapter

Runtime (SvelteKit):
  LessonView renders ExerciseBlock component with exercise data + exerciseRef
    → v1 manual-completion path (no `submission` block):
        static display of instructions, code, expected outputs
        → learner works locally, then clicks "Mark as Complete"
        → fires `complete` event with {exerciseRef, status: "completed"}
        → learningfoundry writes status to exercise_status table
    → v1 graded-submission path (with `submission` block):
        static display + typed input fields per `submission.fields`
        → learner works locally, pastes results into the form, clicks Submit
        → component grades client-side via BR-4 comparison rules
        → fires `complete` event with {exerciseRef, status, score, maxScore, passed, submittedValues}
        → learningfoundry writes status (+ score/max_score for analytics if desired)
    → Future (Marimo WASM):
        graded path swaps form-fields for cell-output subscription;
        same scoring formula, same `complete` payload, same exercise_status write
    → progress dashboard reads exercise_status for module-level display
```

---

## Package Distribution

| Concern | Value |
|---------|-------|
| **Python package** | `nbfoundry` on PyPI (not yet published) |
| **learningfoundry dependency** | Optional: `pip install learningfoundry[nbfoundry]` (future) |
| **v1 stub** | `NbfoundryStub` class in `learningfoundry.integrations.nbfoundry_stub` returns placeholder exercise dicts |

---

## v1 Stub Behavior

Until nbfoundry is published, learningfoundry ships a `NbfoundryStub` that implements the `ExerciseProvider` protocol:

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
- When nbfoundry is published, learningfoundry adds it as an optional dependency and replaces the stub with a real `NbfoundryProvider` that delegates to `nbfoundry.compile_exercise`.
- The SvelteKit `ExerciseBlock` component handles both stub and real exercise dicts.

---

## Testing Contract

| Test | Owner | What is tested |
|------|-------|----------------|
| `compile_exercise` returns valid artifact for well-formed YAML | nbfoundry | Unit test in nbfoundry repo (future) |
| `compile_exercise` raises `ExerciseError` for malformed YAML | nbfoundry | Unit test in nbfoundry repo (future) |
| learningfoundry's `NbfoundryStub` returns correct placeholder structure | learningfoundry | Unit test |
| learningfoundry's `ExerciseProvider` protocol matches nbfoundry's API | learningfoundry | Type check (mypy) |
| `ExerciseBlock` renders stub content with placeholder message | learningfoundry | Component test |
| `ExerciseBlock` renders real exercise with sections and hints | learningfoundry | Component test (future, with fixture data) |
| `ExerciseBlock` fires `complete` event on "Mark as Complete" click (manual path) | learningfoundry | Component test |
| `ExerciseBlock` renders typed input fields when `submission` is present | learningfoundry | Component test |
| `ExerciseBlock` Submit button is disabled until every field has a parseable value | learningfoundry | Component test |
| `ExerciseBlock` grades a passing submission and fires `complete` with `passed: true`, correct `score`/`maxScore` | learningfoundry | Component test |
| `ExerciseBlock` grades a failing submission and fires `complete` with `passed: false`, allows resubmit | learningfoundry | Component test |
| `range`, `equals`, `contains_all` comparison rules each pass and fail correctly with edge values | learningfoundry | Unit test on the comparison helper |
| Scoring formula: `score = sum of weights of passing rules`, `maxScore = sum of all weights`, `passed = score / maxScore >= pass_threshold` | learningfoundry | Unit test on the comparison helper |
| `compile_exercise` validator rejects malformed `submission` blocks (BR-4 validator requirements) | nbfoundry | Unit test in nbfoundry repo (future); stub-side: validator is a no-op |
| `compile_exercise` rejects an exercise that references a missing asset file (BR-1 step 5) | nbfoundry | Unit test in nbfoundry repo (future) |
| `compile_exercise` validator rejects `expected_outputs[type=image]` missing the `alt` field (BR-1 constraint) | nbfoundry | Unit test in nbfoundry repo (future) |
| Compiled dict's `assets[]` enumerates every relative path the dict references (no orphans, no duplicates) | nbfoundry | Unit test in nbfoundry repo (future); stub returns `[]` |
| learningfoundry pipeline copies every `assets[]` entry from `base_dir/<path>` to `output_dir/static/exercises/<exerciseRef>/<path>` (BR-5 staging) | learningfoundry | Pipeline test |
| `ExerciseBlock` renders image expected-outputs as `<img>` with `src` composed from `exerciseRef + path` and `alt` from the dict | learningfoundry | Component test |
| `ExerciseBlock` renders image `<img>` with `loading="lazy"` so off-screen exercise media doesn't block other content | learningfoundry | Component test |
