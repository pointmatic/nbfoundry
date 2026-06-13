# learningfoundry-embedded-learning-exercise-vs-native-applied-exercise.md — Architectural Decision Record

**Status:** Decision record, 2026-06-01. Captures the architectural decision to split LearningFoundry exercises into two execution surfaces — **embedded learning** (in-browser, Pyodide) and **native applied** (on the learner's own hardware, via the NbFoundry + DataRefinery + ModelFoundry trio) — and the constraint analysis that forced it.
**Audience:** Architects and maintainers of LearningFoundry, NbFoundry, DataRefinery, and ModelFoundry. This decision binds all four.
**Sister documents:**
- LF-side requirements: [`learningfoundry/applied-exercise-requirements.md`](learningfoundry/applied-exercise-requirements.md)
- Author-side guidelines: [`learningfoundry/nbfoundry-exercise-guidelines-for-authors.md`](learningfoundry/nbfoundry-exercise-guidelines-for-authors.md)

---

## Decision

LearningFoundry exercises split into two execution surfaces:

1. **Embedded learning exercise** — runs in the browser via Pyodide. Pyodide-compatible framework set only (NumPy, scikit-learn, Keras-3-NumPy-backend, scipy, matplotlib, small custom code). CPU-bound, small data, designed for conceptual density and immediate-feedback interactivity.
2. **Native applied exercise** — runs on the learner's own hardware. Uses the **trio**: nbfoundry + DataRefinery + ModelFoundry. Full framework choice (PyTorch+MPS, TensorFlow+Metal, CUDA, etc.) driven by the learner's hardware. Plural by design — typically 3–4 rounds per concept, the first round always a fully-scaffolded **Hello ML World**. Optional by default — curriculum completion does not require hardware.

A **bundler** emits a small JSON payload from each applied round. The learner uploads it into LF's browser app, where it is parsed in Pyodide and stored in the in-browser SQLite. **No backend, no kernel-as-a-service, no Metal-in-container.**

---

## Context — The Constraint Stack

The decision is forced by three constraints, no two of which can be satisfied while the third holds.

| # | Constraint | Source | Hard? |
|---|---|---|---|
| 1 | LF v1 runtime is fully static — no backend, browser-only | `features.md` Non-goals 3 ("No server-side persistence or APIs"), Non-goals 9 (nbfoundry integration out of scope v1); `tech-spec.md` uses `@sveltejs/adapter-static`; Acceptance Criteria 4 | **Hard** — v1 design choice; relaxing it is a major architectural shift |
| 2 | Deep learning training requires hardware acceleration (GPU / MPS / CUDA) | D802 Deep Learning Essentials is the reference curriculum | Soft — small CPU models are pedagogically valid; the constraint is about *scale*, not *concept* |
| 3 | In-browser Python = Pyodide (only path; WASM sandbox) | Physical layer — no other path exists | **Hard** — cannot relax |

**The collision:** Pyodide does not include PyTorch, TensorFlow, or Keras-with-TF/PyTorch-backend, and **cannot ever** — Pyodide is WASM, and there is no Metal/CUDA/MPS driver inside a browser sandbox. The DL stack the curriculum requires cannot run in the LF runtime, period.

You can pick any two of {static LF, browser-only, real DL training} but not all three. The decision below resolves the collision by *narrowing* what "in-LF" execution means (conceptual / small / CPU / Pyodide-compatible) and *externalizing* the heavy hardware-bound work to a distinct surface (the learner's own machine).

---

## Options Considered

Each rejected for a real reason — none on vague distaste.

### Option 1 — Pyodide-only, ship DL frameworks in-browser

**Rejected.** Physical impossibility for real DL training. Pyodide's standard package set has NumPy, scikit-learn, scipy, pandas, matplotlib — but no production PyTorch or TensorFlow. Experimental `pyodide-torch` builds exist but are CPU-only and slow; no Metal/CUDA path exists in any browser. Even if torch-CPU shipped first-class, the curriculum's training tasks would be intolerably slow.

**What survived:** the Pyodide framework set as the embedded-learning surface (small models, conceptual demos, sklearn pipelines, Keras-NumPy-backend). This is exactly what the embedded-learning surface IS in the chosen architecture — but extending it to cover real DL training is impossible.

### Option 2 — Backend-served Marimo kernel

**Rejected.** Breaks the v1 static-site design (`features.md` Non-goals 3: "No server-side persistence or APIs"). Introduces hosting cost, auth, multi-tenancy, scaling, billing. Wrong fit for a self-hosted, learner-owned curriculum-engine product. If pursued in a future LF v2, this becomes a legitimate path — but it should be a deliberate architectural shift, not v1's default.

### Option 3 — Cloud-redirect (Colab / Kaggle / Lightning AI / etc.)

**Rejected as primary.** Fragments the experience across external services with their own accounts, terms, and lifecycle. Loses integrated progress tracking unless re-wired. Acceptable as a fallback recommendation in the applied-exercise authoring guidelines for hardware-less learners, but not as the architecture.

### Option 4 — Containerized client/server compute (Docker/Podman + Pyodide client + pluggable compute server)

**Rejected.** Three concrete reasons:

- **Apple Metal does not work inside Docker/Podman on macOS.** Docker Desktop runs a Linux VM; Metal is a macOS-userspace API the Linux guest has no view into. A Metal-backed compute server must run as a native macOS process, not in a container. The "one homogeneous container model" breaks at the most important target hardware. The deployment story is forced hybrid (native on Mac, container on Linux+CUDA), which collapses the design's main simplification claim.
- **Custom wire-protocol cost.** Routing arbitrary Python from a browser to a kernel reinvents Jupyter's kernel protocol. Reusing Jupyter's protocol incurs a heavy dependency surface; inventing custom incurs years of edge-case work (security, multiplexing, state, lifecycle).
- **Per-cell network latency** dominates fast-feedback interactivity — the very property that browser-embedded execution is meant to provide. Mitigations exist but stack complexity quickly.

### Option 5 (chosen) — Embedded learning + native applied with bundler feedback

**Chosen.** Embedded learning runs in-browser (Pyodide; CPU; conceptual exercises). Native applied runs on the learner's own hardware via the trio (full DL stack as available). Bundler closes the feedback loop without any backend infrastructure. Constraints are honored rather than fought.

---

## The Synthesis (Why This Works)

The chosen split is more than constraint compromise — it actively aligns with pedagogical principles that improve the curriculum.

### Pedagogy alignment

1. **Conceptual density favors small CPU examples.** Manipulating a 3×3 conv kernel on one image teaches more per minute than waiting for ResNet to train. Pyodide's framework set (NumPy + Keras-NumPy-backend + sklearn + matplotlib) is *exactly* what's needed for high-density conceptual exercises. The constraint that forced this is also pedagogically preferable.

2. **Repeated retrieval beats one big practice event** (Ericsson; Karpicke & Roediger). Three to four applied rounds per concept — with progressive scaffolding — drives procedural mastery in a way one capstone never can. The "many rounds" structure is enabled by making applied exercises lightweight per-round, not climactic — exactly what the bundler-feedback design produces.

3. **Hello ML World validates the toolchain first.** The first round of every applied series is a fully-scaffolded run-as-is notebook. Learners experience the full feedback loop (env → train → bundle → upload → progress) before being asked to write any code. Toolchain failures get isolated immediately; later rounds assume a working baseline. This is nbfoundry's own "Hello World First — Spike Early, Spike Often" philosophy applied symmetrically to learners.

4. **Worked → faded → independent across rounds** (Sweller; Renkl). The progressive-scaffolding pattern already exists in LF as markdown container directives at the lesson scale (`features.md` FR-2 / Story J.d.1). The applied series promotes the same pattern from *within a lesson* to *across a notebook sequence*. Same mental model for authors; two scales.

5. **Cross-surface API continuity.** Keras 3's NumPy backend works in Pyodide; the same `keras.Sequential(...)` / `model.fit(...)` code runs on TF or PyTorch backend on the learner's GPU at the applied tier with a one-line backend swap. *"The API you learned in the browser is the API you scale on your hardware"* is a pedagogical win the surface split makes possible.

### Architectural compounding

- **The static-site constraint is preserved.** LF v1's "no backend" promise stays intact: bundles are files the learner drops into the browser; parsing happens in Pyodide; storage is the existing in-browser SQLite.
- **The trio gets its real value proposition.** nbfoundry, DataRefinery, and ModelFoundry are positioned not as "tools for capstone submission" but as **the practitioner stack the learner is being onboarded onto, gradually, by use.** Stronger product claim; more honest pitch.
- **Per-series env recipes solve nbfoundry's env-hygiene problem cleanly.** The contamination problem documented in F.f.1/F.f.2 (standalone Keras + duplicate TF transitively pulled by conda-forge HuggingFace recipes) only existed because the shipped template was one bundled env with everything. Per-applied-series env recipes are each focused — a Keras series doesn't ship HF, so no transitive Keras pull. Same root cause, solved naturally.
- **The named-testenvs primitive serves both sides.** pyve v2.8's `[tool.pyve.testenvs]` (the named-test-environments feature nbfoundry asked pyve to deliver) is the env primitive for both nbfoundry's own dev tests AND the per-series applied env recipes on the learner side. One primitive, two consumer surfaces. Architectural compounding.

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Authors mistakenly ship "real DL training" as an embedded learning exercise | Authoring guidelines explicitly enumerate the Pyodide-compatible framework set and forbid `import torch` etc. in learning exercises. nbfoundry compile-time lint flags out-of-band imports. |
| Authors put a single Hello-ML-World as the entire applied surface ("capstone-style"), defeating retrieval practice | Guidelines mandate 3-round minimum (4 recommended). nbfoundry scaffolder defaults to a 4-round series. |
| Per-series env recipes accumulate to multi-GB total for hardware-equipped learners | Series share base envs where reasonable; lazy provisioning per pyve's `lazy = true` flag means uninstalled series cost nothing on disk until first use. |
| Learners without hardware feel they're missing core content | Applied series are optional by default. Curriculum-level metric: target ≥80% of curriculum completable without hardware. Authoring guidelines specify when "applied required" is legitimate (rare). |
| Bundle parsing in Pyodide is fragile (malformed bundle, version skew, schema drift) | Bundle schema is versioned (`bundle_format`); LF validates and surfaces actionable errors. Strict-validated; permissive bundle generation is the bug, not the receiver. |
| Co-residence SIGBUS (F.f.1) re-emerges in applied exercises that mix frameworks in one notebook | Each applied exercise is single-framework by guideline. Multi-framework exercises must split into separate applied rounds with separate env recipes. nbfoundry compile-time lint flags multi-framework notebooks. |
| Curriculum drift: real DL exercises authored before this decision land as LF-embedded and fail in Pyodide | Audit pass on any existing exercise authoring; migrate DL-heavy exercises to the applied surface. |
| Apple Metal-on-laptop is the most-tested applied path, but Linux+CUDA and Windows+CUDA are pedagogically important too | Per-series env recipes include cross-platform swap notes (already a convention in nbfoundry's `templates/environment.yml`). CI validates a CPU-only fallback path for every series. |

---

## Implications

### For LearningFoundry

- Schema: `type: exercise` accepts paired `learning:` + `applied:` sections (see [`learningfoundry/applied-exercise-requirements.md`](learningfoundry/applied-exercise-requirements.md) FR-AE-1).
- Bundler upload UI on the exercise page (file picker, Pyodide-parsed, in-browser SQLite write).
- Progress dimension for applied series, distinct from lesson-completion glyph.
- Documentation: "embedded learning runs in your browser on CPU; applied exercises run on your hardware" framing in learner-facing onboarding.
- Honest scope copy: in-LF execution is CPU-only and bound to small-data conceptual exercises.

### For nbfoundry

- Two compile targets: **embedded** (Pyodide-compatible framework set; restricted) and **native** (full framework choice, per series).
- Scaffolder produces Hello ML World as round 1 of any applied series, automatically.
- Bundler is a first-class nbfoundry concern (the program emits the bundle; ModelFoundry may provide evaluator-metric primitives).
- The nbfoundry package itself does not need to *run* any ML framework — only emit notebooks that use them. Dev env stays light; framework presence is a *payload* concern, not a *tool* concern.
- F.f.2 (env-hygiene fix) narrows substantially: the contamination problem largely dissolves under per-series env recipes; the remaining concern is dev-side test isolation, addressed by the in-flight named-testenvs experiment.
- The shipped `templates/environment.yml` ceases to be one-env-for-everything; it splits into **per-applied-series env recipes** declared by the curriculum.

### For DataRefinery

- Used by applied exercises for data preparation; not used in embedded learning exercises (Pyodide-incompatible until further notice).
- May ship a lightweight Pyodide-compatible sub-API for in-LF demos of data-prep concepts (separate decision; not required for this architecture to land).
- Bundle integration: contribute recipe-hash / provenance metadata to applied bundles for reproducibility (optional but valuable).

### For ModelFoundry

- Provides training and evaluation scaffolds for applied exercises (Hello ML World uses ModelFoundry verbatim; later rounds may replace pieces).
- Optionally provides evaluator-metric primitives the bundler can call (the "auto-graded" bundle path).
- Not used in embedded learning exercises (same Pyodide-incompatibility reason).

### For Pyve

- v2.8's `[tool.pyve.testenvs]` is the env primitive curriculum authors use to declare per-series env recipes in their curriculum project. **No new pyve work required** for this architecture — the feature shipped 2026-05-30 is sufficient.

---

## Status of Related Work

- **pyve v2.8** ships named test environments — the env primitive the per-series recipes need on the dev side. Validated 2026-05-30 against nbfoundry's F.c–F.f hardware smokes (F.f Keras still blocked on env-hygiene fix — story F.f.2, [`stories.md`](stories.md)).
- **nbfoundry F.f.1** (silent SIGBUS in `metal_smoke.py`) is fixed and verified end-to-end. The same subprocess-isolation pattern informs the "one framework per applied notebook" guideline.
- **nbfoundry F.f.2** (constrain template transitives) is `[Planned]`, blocked on the named-testenvs feature bundle that pyve has now shipped. The architectural decision recorded here **narrows F.f.2's scope**: the SHIPPED template ceases to be one-env-for-everything; it splits into per-series recipes per the applied-exercise design. F.f.2's work simplifies from "untangle the conda solver's optional-dep behavior" to "verify each per-series recipe is clean" — much smaller and more contained.

---

## References

### LearningFoundry specs
- [`learningfoundry/concept.md`](learningfoundry/concept.md)
- [`learningfoundry/features.md`](learningfoundry/features.md)
- [`learningfoundry/tech-spec.md`](learningfoundry/tech-spec.md)
- [`learningfoundry/README.md`](learningfoundry/README.md)

### nbfoundry specs
- [`stories.md`](stories.md) — F.f.1 (co-residence SIGBUS) and F.f.2 (env-hygiene fix, in-flight)
- [`phase-f-pyve-named-testenvs.md`](phase-f-pyve-named-testenvs.md) — the use-case brief that informed pyve v2.8's named-testenv design
- [`phase-f-pyve-micromamba-testenv-trap.md`](phase-f-pyve-micromamba-testenv-trap.md) — the resolved trap doc

### Pyve
- [`pyve/features.md`](pyve/features.md) — FR-11a (Named Test Environments)
- [Pyve testing docs](https://pointmatic.github.io/pyve/testing/) — `--env <name>` runtime contract

### Pyodide
- [Pyodide packages list](https://pyodide.org/en/stable/usage/packages-in-pyodide.html) — defines the embedded-learning framework menu

### Pedagogical principles
- Ericsson, K. A. — *Deliberate practice and procedural automation* (the foundation for skill-building through repetition).
- Karpicke, J. D. & Roediger, H. L. — *Retrieval practice and long-term retention* ("the testing effect"; the basis for many-round structure).
- Sweller, J.; Renkl, A. — *Worked examples and cognitive load* (the basis for progressive scaffolding tiers).
