# applied-exercise-requirements.md — Applied Exercises in LearningFoundry

**Status:** Requirements brief, drafted from an architectural design session 2026-06-01. Not yet implemented; supersedes the deferred `nbfoundry` integration stub in LF `features.md` FR-6.
**Audience:** LearningFoundry maintainers and curriculum authors.
**Scope:** Defines the "applied exercise" content type, its schema, runtime semantics, bundler/feedback-loop contract, and progress-tracking integration.
**Sister documents:**
- [`nbfoundry-exercise-guidelines-for-authors.md`](nbfoundry-exercise-guidelines-for-authors.md) — author's perspective on writing exercises against this surface.
- [`../learningfoundry-embedded-learning-exercise-vs-native-applied-exercise.md`](../learningfoundry-embedded-learning-exercise-vs-native-applied-exercise.md) — the cross-cutting architectural decision record (the *why* behind the embedded/native split).

---

## TL;DR

A curriculum exercise is now a *pair*: an **embedded learning exercise** that runs in-browser via Pyodide, plus an optional **applied exercise series** that runs on the learner's native hardware using the nbfoundry + DataRefinery + ModelFoundry trio. The applied series is **plural by design** — typically 3–4 rounds with progressive scaffolding (worked → faded → independent), the first round always a **Hello ML World** that validates the entire toolchain end-to-end. Each round emits a small **bundle** that the learner uploads back into LF; progress tracks per-round completion. The applied series is **optional by default** — hardware-less learners can complete the curriculum.

---

## Pedagogical Context

Three principles from learning science underpin the design and should be promoted in every authoring guideline downstream:

1. **Retrieval practice + spaced repetition + procedural automation** (Ericsson; Karpicke & Roediger). Mastery comes from *repeated retrieval at varying difficulty*, not from one large practice event. A single end-of-course capstone is structurally too few repetitions to convert a concept into procedural fluency. The plural applied series (3–4 rounds per concept) is what moves a learner from "I did that thing once" to "I have the steps memorized."

2. **Worked example → faded example → independent practice** (Sweller; Renkl). Cognitive load is highest when learners must hold the full procedure in working memory. Progressive removal of scaffolding lets the procedure become automatic before it has to be reproduced from scratch. This pattern already exists in LF as markdown container directives (`::: worked-example`, `::: faded-example`, `::: independent-practice` — `features.md` FR-2 / Story J.d.1); the applied series promotes the same pattern from *within a lesson* to *across a sequence of notebooks*.

3. **Hello-world-first.** The toolchain must be proven to work *before* the learner spends cognitive load on the concept. nbfoundry's own development philosophy ("Hello World First — Spike Early, Spike Often", per `best-practices-guide.md`) applies symmetrically here. The first round of any applied series is always a fully-scaffolded run-as-is notebook whose only job is to close the feedback loop end-to-end.

---

## Hardware Reality (Why Embedded vs Native)

LearningFoundry v1 is fully static (no backend, no kernel — `features.md` Non-goals 3, Acceptance criteria 4). Python in the browser means **Pyodide** — which does not include PyTorch, TensorFlow, or Keras with native backends, and never will, because Pyodide is WASM and **there is no Metal/CUDA/MPS driver inside a browser sandbox**. Real GPU-accelerated DL training cannot happen in-LF, regardless of how the LF runtime is architected.

The embedded/native split is therefore not a workaround for v1 limitations — it is the only architecture honest about the constraint stack. The full constraint analysis (with rejected alternatives) lives in [`../learningfoundry-embedded-learning-exercise-vs-native-applied-exercise.md`](../learningfoundry-embedded-learning-exercise-vs-native-applied-exercise.md). This document accepts the decision as input.

---

## Definitions

| Term | Definition |
|---|---|
| **Embedded learning exercise** | Runs in-browser via Pyodide. Restricted to Pyodide-compatible frameworks (NumPy, scikit-learn, Keras-3-NumPy-backend, scipy, matplotlib, small custom code). CPU-only; small data; designed for conceptual density and immediate-feedback interactivity. |
| **Applied exercise** | Runs on the learner's native hardware (CPU, Apple Metal, CUDA, etc.). A Marimo notebook produced by nbfoundry; uses the **trio** — nbfoundry (scaffolds project + notebook), DataRefinery (data prep), ModelFoundry (training/eval scaffolding). Full framework choice per the series's env recipe. |
| **Applied exercise series** | An ordered list of applied exercises that share a single learning exercise as their conceptual anchor. Typically 3–4 rounds. One env recipe, reused across all rounds in the series. |
| **Hello ML World** | Round 1 of any applied series. A fully-scaffolded notebook the learner runs as-is. Validates env provisioning, hardware detection, data load, model train, bundler emission, upload to LF, progress UI registration — *the loop*, not the ML. Mandatory; see FR-AE-2. |
| **Bundle** | The artifact emitted by the bundler at the end of each applied round. JSON+attachments per a versioned schema. Uploaded into LF via the browser; parsed in Pyodide; stored in the in-browser SQLite. |
| **Bundler** | The program that emits a bundle. Lives in nbfoundry's responsibility surface (may delegate evaluator metrics to ModelFoundry). Conventionally the applied notebook's final cell. |
| **Scaffold tier** | Per-round progressive-scaffolding level. One of: `worked` (round 1 / Hello ML World), `lightly_faded`, `more_faded`, `independent`. Authoring metadata; the SvelteKit UI may render visual hints per tier. |

---

## Functional Requirements

### FR-AE-1: Exercise Content Block — Paired Shape

LearningFoundry's `exercise` content block accepts a paired structure with `learning:` (in-LF, embedded) and `applied:` (native, optional) subsections. Either subsection alone is valid; both together is the standard pattern.

**Schema** (extending the v1 curriculum schema):

```yaml
- type: exercise
  id: ex-conv2d-intro
  title: "Convolutional Layers"

  learning:                                # in-LF, runs in Pyodide
    ref: exercises/learning/conv2d.yml     # nbfoundry exercise YAML (Pyodide-compatible)

  applied:                                 # optional; native, runs on learner hardware
    required: false                        # optional by default
    env_recipe: applied/conv2d/env.yml     # per-series env recipe (one env, reused across rounds)
    rounds:
      - ref: applied/conv2d/round-1-hello.yml
        scaffold: worked                   # Hello ML World; run-as-is
      - ref: applied/conv2d/round-2.yml
        scaffold: lightly_faded            # swap dataset
      - ref: applied/conv2d/round-3.yml
        scaffold: more_faded               # replace architecture
      - ref: applied/conv2d/round-4.yml
        scaffold: independent              # build equivalent from scratch
```

**Rules:**

- `id` is **required** and unique within the curriculum. Used by the bundler upload to map bundles back to exercises and rounds.
- `learning.ref` is optional but recommended. A curriculum may have applied-only exercises (rare); the embedded learning exercise is the conceptual anchor for the applied series and should usually exist.
- `applied.rounds` must contain at least one round when `applied:` is present.
- `applied.rounds[0]` is the Hello ML World by convention. Authoring lint should warn if its `scaffold:` value is not `worked`.
- `applied.env_recipe` is **required** when `applied:` is present. One recipe shared across the entire series; different series declare different recipes.
- `applied.required` defaults to `false`. When `true`, completion of the required rounds gates the exercise's `complete` state per the existing locking rules. When `false`, applied rounds contribute to a separate progress dimension that does not gate.

### FR-AE-2: Hello ML World Invariant

The first round of any applied series **MUST** be runnable as-is, with no learner code modification required, and **MUST** exercise the entire feedback loop end-to-end:

1. Env provisioning succeeds (the trio installs without learner intervention beyond the documented setup script).
2. Hardware detection runs (Metal / CUDA / CPU; reported in the bundle).
3. Data loads (DataRefinery scaffold).
4. A trivial model trains for one short cycle (ModelFoundry scaffold; small data; CPU-fallback safe).
5. Evaluation metrics are computed.
6. The bundler emits a bundle.
7. The bundle uploads into LF (file picker; in-browser parse).
8. The LF progress UI registers the round as complete.

**Why this is mandatory:** Hello ML World is what *earns* every subsequent round. Without proving the loop closes, every later round assumes a working toolchain that may not actually be working — and "it broke and I don't know where" is the dominant dropout mode for technical curricula. The diagnostic question for any broken later round becomes *"does Hello ML World still run?"*, which the structure builds in for free.

The Hello ML World notebook should be **boring**. A 10-line model on a small dataset, trained for one epoch on CPU-safe defaults. The point is the loop, not the ML.

### FR-AE-3: Bundler Contract

Each applied round emits a bundle on completion. The bundle is the *unit of feedback* between the learner's native environment and LF.

**Required fields:**

| Field | Type | Description |
|---|---|---|
| `version` | semver string | Bundle schema version |
| `curriculum_id` | string | Curriculum identifier (from `curriculum.yml`) |
| `exercise_id` | string | Matches `exercise.id` from the curriculum |
| `round_id` | string | Matches the round's position/identifier in the series |
| `bundle_format` | string | Schema variant — `auto-graded-v1` or `self-report-v1` (see FR-AE-4) |
| `learner_environment` | object | `{ python_version, os, hardware_tag, trio_versions }` |
| `execution` | object | `{ started_at, ended_at, duration_seconds, exit_status }` |
| `metrics` | object | Round-defined metric dict (loss, accuracy, custom) |

**Optional fields:**

- `artifacts` — small attached files (model summary text, generated plots as inline base64). **Bounded in size** (suggested cap: 256 KB per artifact, 1 MB per bundle). Full model weights are NOT bundled.
- `learner_reflection` — free-text field for self-report bundles.
- `notebook_excerpt` — fragment of the executed notebook for instructor review.

**Excluded fields (must not be bundled):**

- PII (learner identity beyond an opaque local UUID, file paths beyond home-anonymized).
- Secrets, API keys, environment variables.
- Raw datasets.
- Full model weights (reference only).

**Bundle delivery:** the learner triggers bundle generation as the final cell of the round's notebook. The bundle is written to a known path (e.g., `./.bundle/<exercise_id>-<round_id>.json`). The learner then drags-and-drops or file-picks the bundle into LF's browser app.

**LF receives** by parsing in Pyodide and writing to the in-browser SQLite. No upload to any backend — preserves the v1 static-site/no-backend constraint.

### FR-AE-4: Two Bundle Evaluation Modes

Two legitimate evaluation paths, declared per round (or defaulted per series):

- **Auto-graded** (`bundle_format: auto-graded-v1`) — the bundle includes evaluator-computed metrics; LF compares to a threshold declared in the round's metadata and marks pass/fail. Works for "achieved ≥80% accuracy" or "loss < 0.5." Round metadata includes the threshold.
- **Self-report** (`bundle_format: self-report-v1`) — the bundle includes execution metrics + learner reflection; LF accepts as evidence of completion without auto-comparing. Works for open-ended exploration ("explore three different architectures and write what you learned").

Both modes use the same bundle envelope and same upload UI; only the evaluation rubric differs. Authors mix freely across rounds within a series.

### FR-AE-5: Per-Series Env Recipe

The applied series has a single, focused environment recipe (the `applied.env_recipe` field). The recipe is either a conda `environment.yml` (micromamba backend, for hardware-accelerated stacks) or a `requirements.txt` (venv backend, for lighter stacks).

**Discipline (required of authors, enforced in authoring lint):**

- The recipe declares **only** what the series needs. A Keras-focused series ships an env with TensorFlow-macos + Keras + NumPy + pytest, not the full HuggingFace stack.
- Avoiding kitchen-sink env recipes prevents the transitive-contamination problems documented in nbfoundry's F.f.1/F.f.2 (a conda-forge `transformers` recipe pulls a parallel standalone `keras` distribution that fights TF-bundled Keras — see [`../stories.md`](../stories.md) for the incident record).
- Single-framework per series is strongly recommended. Multi-framework series risk the PyTorch-MPS / TensorFlow-Metal SIGBUS documented in nbfoundry F.f.1.

**Setup ergonomics:** the learner runs a setup script on the first applied round (`./setup.sh` or `nbfoundry init --from-applied <id>`) that provisions the env. Subsequent rounds in the same series reuse the env — first-round friction is acceptable; second-round friction is not. The named-test-environments primitive in pyve v2.8 (`[tool.pyve.testenvs]`) is the substrate the curriculum can use to declare per-series envs in a single project's `pyproject.toml`.

### FR-AE-6: Progress UI Requirements

The applied series is a new progress dimension distinct from lesson completion.

- Per-exercise progress widget displays both: the existing lesson glyph (four-state lesson lifecycle from FR-P15) AND applied-series progress (e.g., `●●●○` for 3 of 4 rounds bundled).
- Each round shows its scaffold tier as metadata (`worked` / `lightly_faded` / `more_faded` / `independent`) so the learner sees the progression structure.
- Optional applied rounds (the default) do not gate exercise / lesson / module completion.
- Required applied rounds (`applied.required: true`) participate in the existing locking-config rules.
- Curriculum dashboard surfaces aggregate applied progress alongside lesson completion: *"12 of 20 applied rounds completed across the curriculum."*

### FR-AE-7: Bundle Upload UI

LF's curriculum app accepts bundles via a file picker on any exercise page that has a non-empty `applied:` section. The picker:

- Accepts `.json` files matching the bundle schema.
- Parses the bundle in Pyodide.
- Validates against the declared `bundle_format`.
- Writes round completion + metrics to the in-browser SQLite.
- Provides clear feedback: ✓ for accepted bundles, descriptive errors for malformed bundles or bundles whose `exercise_id` / `round_id` does not match the current page.

Bundles for an already-completed round may be re-uploaded (overwrites previous metrics — useful for "I improved my score and want to update"). Re-upload semantics are an [open question](#open-questions) for v1 of this feature.

### FR-AE-8: Cross-Surface API Continuity (Recommended Pattern)

When designing an exercise pair, prefer frameworks whose API survives across both surfaces:

- **Keras 3 with NumPy backend** in the embedded learning exercise (works in Pyodide).
- **Keras 3 with TensorFlow or PyTorch backend** in the applied exercises (runs on native hardware).

The learner's mental model of "the Keras API" stays constant; only the backend changes via `keras.config.set_backend(...)`. The code they wrote in the browser is the code they scale on their hardware. This is pedagogically valuable — most teach-then-scale pipelines force the learner to rewrite at the boundary; this one does not.

Recommendation, not a requirement. Single-surface exercises are valid where the topic only makes sense on one side.

---

## Persistence Schema (extending tech-spec.md `SQLite Progress Schema`)

```sql
CREATE TABLE IF NOT EXISTS applied_round_progress (
  exercise_id     TEXT NOT NULL,
  round_id        TEXT NOT NULL,
  bundle_format   TEXT NOT NULL,                       -- auto-graded-v1 | self-report-v1
  passed          INTEGER NOT NULL DEFAULT 0,          -- 1 only if auto-graded threshold met or self-report accepted
  metrics_json    TEXT NOT NULL,                       -- the bundle's metrics object, serialized
  learner_env_json TEXT NOT NULL,                      -- bundle.learner_environment
  uploaded_at     TEXT NOT NULL,                       -- ISO 8601
  PRIMARY KEY (exercise_id, round_id)
);
```

The `(exercise_id, round_id)` key allows re-upload to overwrite. Storage is per-learner per-device (the existing in-browser SQLite model — no cross-device sync in v1, per `features.md` Non-goals).

---

## Out of Scope (v1 of this feature)

- **Cloud-hosted bundle upload.** In-browser file picker only; no backend submission endpoint.
- **Cross-learner leaderboards** or comparative metrics across learners.
- **Auto-grading of arbitrary code.** Only declared-metric threshold comparisons.
- **Hot-reload of the bundle from a running Marimo notebook.** Manual file picker only.
- **Streaming progress updates** during long applied training runs (the bundle is a single artifact at the end).
- **Synchronization of progress across devices.**
- **Server-side persistence of bundles** for instructor review (separable future feature; could be added without disrupting this design).

---

## Open Questions

1. **Bundle re-upload semantics.** Overwrite previous metrics (current draft), or store all attempts (best-effort retain history)? Storage is cheap; UI complexity matters.
2. **Required applied rounds and cross-module locking.** Do `applied.required: true` rounds participate in cross-module sequential locking, or only intra-exercise gating?
3. **Self-report bundle minimum content.** What is the smallest acceptable self-report bundle? Risk: trivially-clickable "I ran it" bundles that defeat the loop. Possible mitigation: require minimum learner_reflection length, require at least one captured metric.
4. **Hardware-requirement chip in the UI.** Should LF render a "hardware required" chip on exercises with `applied.required: true`, so hardware-less learners can scan ahead and plan?
5. **Bundle file naming convention.** Is `<exercise_id>-<round_id>.json` enough, or do we need a learner-side namespace prefix to avoid collisions across multiple curricula on the same machine?
6. **Per-series env-recipe sharing across exercises.** Two exercises that need the same env recipe — do they each declare it separately, or can a top-level `[tool.pyve.testenvs]`-style block be referenced by `env_recipe: "@named:keras-stack"`? Optimization for later; flagged so the schema doesn't preclude it.

---

## Related Documents

- [`../learningfoundry-embedded-learning-exercise-vs-native-applied-exercise.md`](../learningfoundry-embedded-learning-exercise-vs-native-applied-exercise.md) — cross-cutting architectural decision record. Documents the constraint analysis, rejected alternatives, and product-wide implications.
- [`nbfoundry-exercise-guidelines-for-authors.md`](nbfoundry-exercise-guidelines-for-authors.md) — the author's-perspective companion. Practical authoring advice, anti-patterns, testing checklist.
- [`features.md`](features.md) — current LF feature surface. FR-6 (nbfoundry integration) is the stub this feature replaces in a future LF version.
- [`tech-spec.md`](tech-spec.md) — current LF tech spec. The `ContentBlock` union, `ResolvedCurriculum`, and SQLite schema are the extension points for this feature.
- nbfoundry repo: [`../stories.md`](../stories.md) — stories F.f.1 (co-residence SIGBUS) and F.f.2 (env-hygiene fix) are the source incidents that informed the per-series env discipline.
- pyve v2.8 named test environments: [`../pyve/features.md`](../pyve/features.md) FR-11a. The `[tool.pyve.testenvs]` primitive is the substrate for per-series env recipes.
