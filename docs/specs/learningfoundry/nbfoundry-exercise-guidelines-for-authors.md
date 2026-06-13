# nbfoundry-exercise-guidelines-for-authors.md — Authoring Exercises for LearningFoundry

**Status:** Authoring guidelines, drafted 2026-06-01. Practical companion to [`applied-exercise-requirements.md`](applied-exercise-requirements.md) (LF-side requirements) and [`../learningfoundry-embedded-learning-exercise-vs-native-applied-exercise.md`](../learningfoundry-embedded-learning-exercise-vs-native-applied-exercise.md) (architectural decision).
**Audience:** Curriculum authors writing nbfoundry exercises that ship in LearningFoundry curricula.

---

## Orientation: Two Surfaces, Two Authoring Modes

You're writing exercises for one of two surfaces. **Pick the right surface before you start writing.**

| Surface | Where it runs | Framework menu | Hardware | Typical use |
|---|---|---|---|---|
| **Embedded learning exercise** | In LF browser, via Pyodide (WASM) | NumPy, scikit-learn, **Keras-3-NumPy-backend**, scipy, matplotlib, small custom Python | CPU only; no GPU/Metal/CUDA possible | Concept demonstration, interactive exploration, small models, visualization |
| **Native applied exercise** | Learner's own machine, via the trio (nbfoundry + DataRefinery + ModelFoundry) | Anything (PyTorch, TF, Keras, transformers, ...) — declared in the per-series env recipe | Whatever the learner has (CPU / Apple Metal / CUDA) | Practitioner-style training, real data, real hardware, the trio in actual use |

**You almost always pair them.** A learning exercise teaches the concept in-browser; an applied series reinforces it on the learner's hardware. See [`applied-exercise-requirements.md`](applied-exercise-requirements.md) FR-AE-1 for the schema.

The remainder of this document covers:

- [Authoring an embedded learning exercise](#authoring-an-embedded-learning-exercise)
- [Authoring an applied series](#authoring-an-applied-series)
- [Cross-cutting pitfalls](#cross-cutting-pitfalls)
- [Practical workflow](#practical-workflow)

---

## Authoring an Embedded Learning Exercise

### Framework menu — what you may import

| Framework | Use it for | Notes |
|---|---|---|
| NumPy | Tensor math, manual autograd demos, small models from scratch | Always available |
| scikit-learn | Classical ML pipelines (regression, classification, clustering) | Trains in seconds at toy scale |
| **Keras 3 (NumPy backend)** | ML-API teaching with cross-surface continuity | **Recommended** for any ML concept that has a "real" version on the applied side. The same `keras.Sequential(...)` code runs at scale on the learner's hardware via a one-line backend swap. |
| scipy | Optimization, statistics, linear algebra | Useful for "why does this algorithm work" exercises |
| matplotlib | Visualization | Inline in Marimo |
| pandas | Tabular data manipulation | Available; use sparingly — keep data small |
| Pure Python | Micrograd-style autograd, hand-rolled implementations | High pedagogical value for "show me how it actually works" |

### Framework menu — what you may NOT import

- `torch`, `tensorflow`, `tensorflow-macos`, `tensorflow-metal` — do not run in Pyodide.
- Standalone `keras` with TF, PyTorch, or JAX backend — those backends require their respective ML frameworks, which Pyodide cannot host.
- `transformers`, `datasets`, `peft`, the full HuggingFace stack — too heavy for WASM; native deps fail to build.
- Anything that requires a GPU, Metal, CUDA, or MPS — physical-layer mismatch (no hardware access from the browser sandbox).
- Anything that loads multi-GB datasets — browser memory, Pyodide cold-start cost.

**If your exercise needs any of the above, it belongs in the applied surface, not embedded.** This is not a workaround; it's the design.

### Design principles for embedded learning exercises

1. **Pedagogical density over realism.** Manipulating a 3×3 conv kernel on one image teaches more in 30 seconds than waiting 10 minutes for a CIFAR run. Lean into "see this work" rather than "achieve a benchmark."
2. **Immediate feedback.** Marimo's reactive cells + tiny CPU operations = sub-second feedback per change. Exploit this. Interactive sliders, real-time updates, "what happens if I change this?" are killer features here.
3. **Small data.** A 10×10 image, a 5-token sentence, a 4-dimensional embedding. Just enough to illustrate. Model parameters in the hundreds at most.
4. **Keras-NumPy-backend for ML APIs.** When teaching Keras's API (Sequential, layers, fit, evaluate), use the NumPy backend in the learning exercise. **The same code** will run with PyTorch or TF backend in the applied surface — `keras.config.set_backend("torch")` is a one-liner. Continuity across surfaces is pedagogically valuable.
5. **Self-contained.** No network calls, no external dataset downloads, no API keys. The exercise must run from a clean Pyodide load.

### Common patterns

- **Interactive concept demos** — slider → recompute → updated visualization. Conv kernels, activation functions, attention weights, loss surfaces.
- **Micrograd-style autograd** — build a 100-line autograd engine in pure Python. Teach backprop by *implementing* it, not by importing it.
- **sklearn pipelines** — train a real model in 2 seconds, see the decision boundary, vary a hyperparameter, train again.
- **Visualization of internals** — PCA of embeddings, t-SNE of features, attention heatmaps, loss-curve plotting.
- **Numerical exercises** — "Compute the gradient by hand, then by autograd, confirm they match."

### Anti-patterns

- Trying to import torch / tf / keras-with-TF-backend (will fail at Pyodide load).
- Loading datasets larger than a few MB (slow; consumes learner's browser memory).
- Designing an exercise that needs "real" training time (>10 seconds of compute) — the in-browser experience is wrong for that.
- Splitting a concept across N learning exercises when it could be one with interactive sliders.

---

## Authoring an Applied Series

An applied series is **3–4 rounds minimum**. Fewer rounds defeats the retrieval-practice principle (see the pedagogy section of the architectural decision doc). More is fine if the topic warrants it.

### The Hello ML World — round 1, always

Round 1 is **fully scaffolded, run-as-is, no learner code modification required**. Its job is to validate the entire feedback loop end-to-end:

1. Learner provisions the env (`./setup.sh` or `nbfoundry init --from-applied <id>`).
2. Learner opens the notebook (`marimo edit round-1-hello.py`).
3. Learner runs every cell with no edits.
4. Notebook trains a trivial model, computes metrics, emits a bundle.
5. Learner drags-and-drops the bundle into LF's browser app.
6. LF shows round 1 complete; `●○○○` progression visible.

**This is non-negotiable.** Without Hello ML World, the learner has no way to distinguish "I broke the toolchain" from "I broke my code" when round 2 fails. The diagnostic flow for any later round is: *"Does Hello ML World still run?"* — keep this question always answerable.

The Hello ML World notebook should be **boring**. A 10-line model on a small dataset, trained for one epoch on CPU-safe defaults. **The point is the loop, not the ML.**

### Progressive scaffolding across rounds

Rounds 2 through N implement the worked → faded → independent progression. This pattern is the same one used by LF's markdown directives at the lesson scale (`::: worked-example`, `::: faded-example`, `::: independent-practice`); the applied series promotes it to the notebook scale.

| Round | Scaffold tier | What the learner does |
|---|---|---|
| 1 | `worked` | **Hello ML World.** Run as-is. Validate the loop. |
| 2 | `lightly_faded` | One axis varied (different dataset, different hyperparam). Minimal learner code. |
| 3 | `more_faded` | One major component replaced (architecture, training loop, evaluator). Substantial learner code. |
| 4 | `independent` | Build the equivalent from scratch with starter scaffolding only. Most learner code. |

### Round-design principle — vary one axis per round

Identical rounds are pedagogically boring and defeat the purpose of repetition. Each round should vary **one** axis from the previous:

- Round 2: same model + new dataset (learner manages data ingestion).
- Round 3: same dataset + new architecture (learner designs the model).
- Round 4: new task, learner integrates everything.

This keeps the *procedure* (env, training loop, evaluation, bundling) consistent while the *substance* changes — exactly the structure that drives procedural automation. 3–4 rounds of "do the same thing again with slightly different hyperparams" is not retrieval practice; it's tedium.

### Per-series env recipe

Each applied series ships **ONE** env recipe — used by all rounds in the series. The recipe lives at `applied/<exercise-id>/env.yml` (micromamba) or `applied/<exercise-id>/requirements.txt` (venv) and is declared in the curriculum YAML as `applied.env_recipe`.

**Discipline:**

- Declare ONLY what the series needs. A Keras series needs `tensorflow-macos` + `tensorflow-metal` + `numpy` + the bundler/scaffolder deps. It does **NOT** need `transformers` / `datasets` / `peft`.
- **Avoid bundled-everything stacks.** Bundling pulls transitive dependencies — the F.f.2 problem in nbfoundry's own [`../stories.md`](../stories.md): conda-forge `transformers` pulls a parallel `keras` distribution that fights TF-bundled Keras, etc. Per-series focus prevents this entirely.
- **One env per series.** The learner provisions once, reuses across rounds 1–N. First-round friction is acceptable; subsequent-round friction is not. The trio's repeat-use surface should be near-zero friction (`nbfoundry next` or equivalent).

**Single-framework per series is strongly recommended.** If your series uses both PyTorch and TensorFlow in the same notebook, you re-create the F.f.1 SIGBUS (PyTorch-MPS + TensorFlow-Metal co-residence on Apple Silicon). If you genuinely need two frameworks for the topic, **split into two separate applied exercises** with separate env recipes — each runs in its own learner-side process.

### The trio in an applied series

| Tool | Role in the applied exercise |
|---|---|
| **nbfoundry** | Scaffolds the project on first use (`nbfoundry init --from-applied <id>` provisions the env via the declared recipe + emits the Hello ML World notebook). Subsequent rounds (`nbfoundry next` or `nbfoundry round <n>`) emit the next round's notebook into the same project. |
| **DataRefinery** | Prepares the round's data. Recipe-driven, reproducible. Shipped with the round's starter notebook; later rounds may swap recipes. |
| **ModelFoundry** | Provides training-loop and evaluator scaffolds. Hello ML World uses ModelFoundry scaffolds verbatim; later rounds may replace pieces. |
| **Bundler** (in nbfoundry) | The notebook's final cell. Captures execution metrics + (optional) artifacts + (optional) learner reflection into a `<exercise>-<round>.json` bundle written to a known path. Learner drops it into LF. |

### Bundle contents

What to put in the bundle (round-author's decision; declare in the round YAML):

- **Always:** round metadata (`exercise_id`, `round_id`, `bundle_format`, schema version), learner-environment fingerprint (Python, OS, hardware tag, trio versions), execution stats (start/end/duration), declared metrics.
- **Sometimes:** small artifacts (model summary text, inline base64 plots — keep small; **no full model weights**), learner reflection text.
- **Never:** PII, secrets, raw datasets, full model weights.

**Pick an evaluation mode per round:**

- **Auto-graded** (`bundle_format: auto-graded-v1`) for well-defined tasks (e.g., "classification accuracy ≥ 80% on holdout"). Declare the threshold in the round metadata.
- **Self-report** (`bundle_format: self-report-v1`) for open-ended exploration (e.g., "explore three architectures and write what you learned"). Bundle captures evidence; LF accepts without auto-comparing.

Same bundle envelope, different evaluator. Mix freely across rounds within a series — Hello ML World is typically auto-graded (trivial metric), later rounds may be auto-graded or self-report based on what's appropriate.

### Cross-surface API continuity (canonical pairing pattern)

A well-designed exercise pair looks like:

- **Learning exercise** (embedded, in-LF): Keras-NumPy-backend, 8-sample synthetic data, 2-layer MLP, interactive slider for learning rate, visualize loss curve. The learner manipulates and observes.
- **Applied series** (native): Same `keras.Sequential(...)` code, swapped to TensorFlow or PyTorch backend, real dataset, real hardware. Round 1: run-as-is. Round 2: swap to a CNN. Round 3: swap to a different dataset. Round 4: build a similar pipeline for a related task.

The continuity between surfaces is the pedagogical payoff. The learner's mental model carries from browser to hardware unchanged; only the backend changes.

---

## Cross-Cutting Pitfalls

### Pitfall 1 — Trying to ship a "real DL" exercise as embedded

**Symptom:** the embedded exercise imports `torch` or `tensorflow`. Fails at Pyodide load.

**Why it happens:** authors want the embedded exercise to "feel real." But real DL needs hardware Pyodide cannot access.

**Fix:** Use Keras-NumPy-backend for the API-level demo; move the hardware-accelerated version to the applied surface. **The pair is the design pattern.**

### Pitfall 2 — Skipping Hello ML World

**Symptom:** "round 1" of an applied series asks the learner to write substantial code.

**Why it happens:** authors think round 1 should be "real work" or feel impatient about the scaffolding cost.

**Fix:** Round 1 is always run-as-is. Its job is toolchain validation, not concept work. Concept work starts in round 2. Without Hello ML World, you lose the ability to disambiguate "broken toolchain" from "broken code" the first time anything goes wrong.

### Pitfall 3 — Too few rounds

**Symptom:** an applied series has 1 or 2 rounds.

**Why it happens:** authors carry the old "capstone" mental model — one big project per topic.

**Fix:** 3 rounds minimum, 4 recommended. The retrieval-practice principle requires repetition with variation. One big round teaches no more than one small round; many small rounds compound.

### Pitfall 4 — Identical rounds

**Symptom:** rounds 2, 3, 4 are all "do the same thing again with slightly different hyperparams."

**Why it happens:** authors confuse "repetition" with "no variation."

**Fix:** Vary **one substantive axis per round** (data, architecture, evaluator). Repetition is the *procedure* (env, train, bundle); the *substance* changes.

### Pitfall 5 — Marking applied-required when it should be optional

**Symptom:** `applied.required: true` on most exercises in the curriculum.

**Why it happens:** authors think the curriculum "needs" the applied work to be meaningful.

**Fix:** Default to `false`. Hardware-less learners must be able to complete the curriculum. **Aim for ≥80% of the curriculum completable without hardware.** Mark exercises required only when the topic genuinely cannot land without hands-on hardware work — and even then, weigh against losing the hardware-less audience.

### Pitfall 6 — Multi-framework single notebook

**Symptom:** an applied notebook imports both `torch` (using MPS) and `tensorflow` (using Metal) in one kernel.

**Why it happens:** authors want to "compare" frameworks side-by-side in one exercise.

**Fix:** Split into two notebooks with separate env recipes. The PyTorch-MPS + TensorFlow-Metal co-residence is exactly the SIGBUS nbfoundry's `metal_smoke.py` hit in F.f.1 — same root cause, just relocated into student code. The only safe in-process pattern is "one framework per kernel." Comparing frameworks across notebooks works fine; sharing a kernel does not.

### Pitfall 7 — Kitchen-sink env recipes

**Symptom:** every applied series ships the same "everything stack" env recipe (the old `templates/environment.yml`-style).

**Why it happens:** authors avoid thinking about what each series actually needs and reach for the maximum.

**Fix:** Per-series, focused. A Keras series ships Keras + TF + numpy; not the full HF stack. Reduces install time, disk usage, and the transitive-contamination problems documented in F.f.2.

### Pitfall 8 — Hello ML World that is not actually trivial

**Symptom:** "Hello ML World" is a 200-line notebook that does substantial work.

**Why it happens:** authors confuse "minimal" with "complete."

**Fix:** Hello ML World should be 30–80 lines including comments. One model, one dataset (synthetic OK), one training step, one metric, one bundle. The point is *proving the loop closes*. Anything more belongs in round 2.

---

## Practical Workflow

```bash
# Author workflow (in your curriculum repo)

# 1. Scaffold a new exercise pair (learning + 4-round applied series)
nbfoundry scaffold exercise ex-conv2d \
  --learning \
  --applied --rounds 4

# Generates (proposed):
#   exercises/learning/ex-conv2d.yml          (Pyodide-compatible learning exercise)
#   applied/ex-conv2d/env.yml                 (per-series env recipe; edit to your needs)
#   applied/ex-conv2d/round-1-hello.yml       (Hello ML World; scaffold: worked)
#   applied/ex-conv2d/round-2.yml             (scaffold: lightly_faded)
#   applied/ex-conv2d/round-3.yml             (scaffold: more_faded)
#   applied/ex-conv2d/round-4.yml             (scaffold: independent)

# 2. Iterate on the learning exercise
nbfoundry preview-learning ex-conv2d         # opens in-browser preview using Pyodide

# 3. Test the applied series end-to-end (you, as author, are the first Hello-ML-World learner)
nbfoundry init --from-applied ex-conv2d      # provisions the env recipe locally
marimo edit applied/ex-conv2d/round-1-hello.py
# ... run it, verify it bundles, drop the bundle into LF preview

# 4. Add to your curriculum
# In curriculum.yml:
#   - type: exercise
#     id: ex-conv2d-intro
#     learning: { ref: exercises/learning/ex-conv2d.yml }
#     applied:
#       required: false
#       env_recipe: applied/ex-conv2d/env.yml
#       rounds:
#         - { ref: applied/ex-conv2d/round-1-hello.yml, scaffold: worked }
#         - { ref: applied/ex-conv2d/round-2.yml,       scaffold: lightly_faded }
#         - { ref: applied/ex-conv2d/round-3.yml,       scaffold: more_faded }
#         - { ref: applied/ex-conv2d/round-4.yml,       scaffold: independent }

# 5. Validate and preview the curriculum
learningfoundry validate curriculum.yml
learningfoundry preview curriculum.yml
```

### Pre-ship testing checklist

- [ ] Embedded learning exercise loads in Pyodide without import errors.
- [ ] Embedded learning exercise's longest computation completes under ~5 seconds.
- [ ] Applied env recipe provisions cleanly on at least one hardware target (Mac Metal, Linux CUDA, or pure CPU).
- [ ] Hello ML World runs end-to-end with no learner edits and emits a bundle.
- [ ] Bundle uploads into LF (preview server) and registers progress.
- [ ] Each subsequent round runs against the **same env** (no re-provisioning).
- [ ] **No round imports more than one ML framework.**
- [ ] Env recipe declares **only what the series needs** — no kitchen-sink transitives.
- [ ] If using Keras: cross-backend test confirms the learning exercise (NumPy backend) and applied exercise (TF or PyTorch backend) accept the same `keras.Sequential(...)` model code with only a `keras.config.set_backend(...)` swap.
- [ ] Each round varies a substantive axis from the previous — no copy-paste rounds with hyperparam tweaks.
- [ ] `applied.required` is `false` unless the topic genuinely cannot land without hardware.

---

## Related Documents

- [`applied-exercise-requirements.md`](applied-exercise-requirements.md) — LF-side requirements for the applied-exercise feature (schema, bundler contract, progress UI, persistence).
- [`../learningfoundry-embedded-learning-exercise-vs-native-applied-exercise.md`](../learningfoundry-embedded-learning-exercise-vs-native-applied-exercise.md) — architectural decision record explaining the embedded/native split, options considered, why this design.
- nbfoundry repo: [`../stories.md`](../stories.md) — story F.f.1 (single-framework-per-notebook origin incident) and F.f.2 (per-series env recipes, in-flight).
- LearningFoundry: [`README.md`](README.md) "Pedagogical authoring" section — broader authoring conventions, the `meta` schema, and worked examples.
- nbfoundry: [`../phase-f-pyve-named-testenvs.md`](../phase-f-pyve-named-testenvs.md) — the use-case brief that informed pyve v2.8's named-test-environments feature (the substrate for per-series env recipes).
