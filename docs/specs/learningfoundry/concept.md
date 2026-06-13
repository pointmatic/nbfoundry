# concept.md — learningfoundry

This document defines why the `{{project_name}}` project exists. 
- **Problem space**: problem statement, why, pain points, target users, value criteria
- **Solution space**: solution statement, goals, scope, constraints
- **Value mapping**: Pain point to solution mapping

For requirements and behavior (what), see [`features.md`](features.md). For implementation details (how), see [`tech-spec.md`](tech-spec.md). For a breakdown of the implementation plan (step-by-step tasks), see [`stories.md`](stories.md). For project-specific must-know facts (workflow rules, hidden coupling, tool-wrapper conventions that the LLM would otherwise random-walk on), see [`project-essentials.md`](project-essentials.md). For the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), see [`docs/project-guide/go.md`](../project-guide/go.md) — re-read it whenever the mode changes or after context compaction.

## Problem Space

### Problem Statement

Building a structured, multi-format learning curriculum — especially one that teaches hands-on technical skills like deep learning — requires assembling dozens of disparate tools and manually wiring them together: LLM providers for content generation, quiz platforms for assessments, notebook environments for experiential exercises, visualization libraries for data exploration, and a frontend for delivery. Each tool has its own data format, its own deployment model, and its own assumptions about how learning content is structured. The result is a fragile, bespoke pipeline that is expensive to build the first time and nearly impossible to reuse for a second curriculum.

This problem is acute for individual educators, graduate students, and small teams who lack the resources to build custom learning management systems but need more control and ownership than SaaS platforms provide — particularly when the curriculum involves executable code, model training, and interactive data exploration.

### Why the Problem Persists

- **Tool fragmentation**: Content generation (LLMs), assessment (quiz platforms), experiential learning (notebooks), and visualization (D3/charting) each live in separate ecosystems with no shared data model or orchestration layer.
- **SaaS lock-in**: The most capable learning platforms (Coursera, Canvas, Moodle) are hosted services that impose rigid content formats, lock content behind accounts, and cannot embed arbitrary executable code or client-side model training.
- **No reusable curriculum engine**: Every new curriculum starts from scratch — there is no package you can `pip install` that provides a configurable pipeline from topic definition to deployable learning artifact.
- **High integration cost**: Wiring an LLM to generate didactic text, then feeding that into a quiz generator, then embedding both alongside a Marimo notebook and a D3 visualization into a cohesive frontend is a custom engineering project every time.
- **Expertise mismatch**: Subject-matter experts (the people who know what to teach) are rarely also frontend engineers, DevOps specialists, and LLM prompt engineers simultaneously.

### Pain Points

- **Manual assembly**: Every curriculum requires hand-wiring content generation, assessment, notebooks, and visualization into a one-off pipeline with no reusable structure.
- **No unified delivery surface**: Learners must jump between separate apps (quiz tool, notebook server, video player, static site) with no shared progress tracking or navigation.
- **Content format lock-in**: Learning content authored in one platform's format cannot easily be version-controlled, diffed, or repurposed for a different delivery channel.
- **Assessment disconnect**: Assessment tools operate independently from the curriculum structure, with no built-in mechanism for pre/post-module gating or adaptive sequencing.
- **Experiential learning gap**: Embedding executable, interactive coding exercises (notebooks, model training) into a curriculum requires custom infrastructure that most educators cannot build.
- **Visualization isolation**: Data visualizations live in separate tools or notebooks rather than being integrated into the learning flow where the learner encounters the relevant concept.
- **Progress opacity**: There is no unified way to track a learner's progress across text, video, assessments, and hands-on exercises within a single curriculum.
- **Repetitive infrastructure**: Each new curriculum repeats the same infrastructure work (frontend scaffolding, database setup, deployment pipeline) with no economies of scale.

### Target Users

- **Educators and course authors** building structured, multi-module curricula (e.g., graduate-level deep learning courses) who need pre/post-assessment gating, experiential notebooks, and a polished delivery frontend — without building a custom LMS.
- **Graduate students and self-directed learners** who want to create or consume richly structured learning material that goes beyond passive video and text, incorporating executable code and interactive exercises.
- **Technical teams and developer advocates** producing educational content around ML, data science, or programming topics who want a repeatable pipeline from content definition to deployable learning app.

### Value Criteria

- **Time to deployable curriculum**: How quickly can an author go from a topic outline to a working, learner-facing application?
- **Reusability**: Can the same engine and templates be used to produce a second curriculum on a different topic without re-engineering the pipeline?
- **Learner engagement signal**: Do pre/post-assessment scores, notebook completion, and progress tracking provide meaningful signal on learner comprehension?
- **Content ownership**: Is all content version-controlled, portable, and free of platform lock-in?
- **Integration cohesion**: Does the learner experience feel like one application, not a patchwork of embedded tools?

---

## Solution Space

### One-Liner

This project turns a YAML curriculum definition into a deployable SvelteKit learning application — with LLM-generated content, interactive assessments, executable notebooks, and data visualizations — in a single pipeline.

### Solution Statement

learningfoundry is a PyPI package that acts as a curriculum engine and pipeline orchestrator. An author defines a curriculum's structure — modules, content templates, assessment gates, notebook exercises, and visualizations — in a YAML format. learningfoundry reads that definition and orchestrates a suite of owned, pluggable libraries to produce the learning artifacts: **lmentry** for LLM-powered content generation, **quizazz** for assessment content, **nbfoundry** for Marimo notebook generation which relies on **modelfoundry** for data preparation and model training scaffolding, and **d3foundry** for D3.js visualizations. The final output is a self-contained SvelteKit application with an in-browser SQLite database for progress tracking, deployable to a CDN or runnable locally. Each curriculum lives in its own application repository and consumes learningfoundry as a dependency, keeping the engine reusable across projects.

For v1, the focus is on delivering a working end-to-end pipeline for a single reference curriculum (Deep Learning Essentials) using the hello-world-first philosophy: mock and hack beneath the abstracted dependency interfaces, ship a functional learning artifact, and iterate. The library integrations will be minimal viable implementations — sufficient to prove the pipeline and produce a usable curriculum — with the expectation that each library matures independently over time.

### Goals

- **Rapid curriculum delivery**: An author with a topic outline and YAML templates can produce a deployable learning app without building custom infrastructure.
- **Unified learner experience**: Text, video (YouTube embeds), assessments, notebooks, and visualizations are presented in a single SvelteKit application with shared navigation and progress tracking via in-browser SQLite.
- **Reusable engine**: The same learningfoundry package and pipeline templates can produce curricula on different topics — the deep learning curriculum is the first instance, not a one-off.
- **Content ownership**: All curriculum content lives in YAML and markdown under version control. The compiled SvelteKit app is a static artifact with no external service dependency at runtime.
- **Pluggable library architecture**: Each capability (LLM access, assessments, model training, notebooks, visualizations) is encapsulated in an independent library with a clear interface, allowing any component to be replaced or upgraded without rewriting the engine.
- **Velocity-first v1**: Deliver a working end-to-end artifact before optimizing any single component. Mock, stub, and hack beneath the abstraction boundaries to prove the pipeline, then iterate.

### Scope

**In scope (v1):**

- YAML-based curriculum definition format (pipeline templates and content templates)
- Pipeline orchestrator that reads YAML and invokes library integrations
- lmentry integration for LLM-powered content generation (didactic text, explanations)
- quizazz integration for pre/post-module assessment content (content-only artifact mode consumed by the unified frontend)
- nbfoundry integration for model training exercises (interacting with modelfoundry for data prep, training, optimization, and evaluation steps with student code insertion points in the notebook)
- YouTube video embedding via URL references in YAML
- SvelteKit frontend shell — unified learner experience with module navigation, progress tracking (SQLite/IndexedDB), and embedded content types
- In-browser SQLite database for learner progress (module completion, assessment scores, exercise status)
- Deep Learning Essentials as the reference curriculum implementation
- Static deployment target (CDN or local)

**Out of scope (v1):**

- nbfoundry (Marimo notebook generation) — not yet implemented; notebook content will be manually authored or stubbed
- d3foundry (D3.js visualization generation) — not yet implemented; visualizations will be manually authored or stubbed
- Admin/authoring UI — curriculum authoring is done via YAML files and CLI; no web-based builder
- User accounts or authentication — single-user, local-first
- Server-side persistence or APIs
- AI video generation — videos are YouTube embeds only
- Spaced repetition or adaptive sequencing beyond pre/post-assessment gating
- Multi-curriculum dashboard or cross-curriculum analytics
- Mobile native wrappers

### Constraints

- **PyPI package**: learningfoundry is distributed as a Python package; curriculum implementations consume it as a dependency in their own repositories.
- **YAML-driven**: All curriculum structure and content templates are defined in an ad hoc YAML format — no proprietary binary formats.
- **Owned libraries**: All five integration libraries (lmentry, quizazz, nbfoundry, modelfoundry, d3foundry) are first-party and controlled by the same author. API contracts can evolve without third-party coordination.
- **Stack**: Python 3.12 (via Pyve/micromamba) for the backend pipeline; SvelteKit for the frontend delivery app.
- **Static delivery**: The final learning artifact is a static SvelteKit app — no server required at runtime. SQLite runs in-browser via sql.js/WASM.
- **Velocity mode**: v1 follows the best-practices-guide philosophy — direct commits, hello-world-first spikes, mock beneath abstractions, ship end-to-end before polishing components.

---

## Pain Point → Solution Mapping

**Manual assembly**:
  - The YAML curriculum definition format replaces ad hoc wiring with a declarative structure that the pipeline orchestrator reads and executes automatically.
  - Each library integration (lmentry, quizazz, nbfoundry, d3foundry) is invoked by the orchestrator — the author defines *what* content to produce, not *how* to wire tools together. (Note: modelfoundry is a dependency of nbfoundry and is not invoked directly.)

**No unified delivery surface**:
  - The SvelteKit frontend shell presents all content types — didactic text, YouTube videos, assessments, notebooks, and visualizations — in a single application with shared navigation.
  - In-browser SQLite tracks progress across all content types in one database, eliminating the need for learners to context-switch between separate apps.

**Content format lock-in**:
  - All curriculum content is defined in YAML and markdown files under version control — diffable, reviewable in PRs, and portable.
  - The compiled SvelteKit app is a static artifact; source content is never locked inside a proprietary platform format.

**Assessment disconnect**:
  - quizazz produces assessment content in a content-only artifact mode that learningfoundry consumes directly into the unified frontend.
  - The YAML curriculum definition supports pre/post-module assessment gates — assessment scores stored in the in-browser SQLite database drive module skip/retry logic within the learning flow.

**Experiential learning gap**:
  - nbfoundry provides scaffolded model training exercises with explicit student code insertion points — learners write key neural network code without managing the full data/training/evaluation pipeline. It will generate Marimo notebooks embedded in the same frontend; for v1, notebook exercises are manually authored and integrated into the SvelteKit shell.

**Visualization isolation**:
  - d3foundry (future) will generate D3.js visualizations that render inline within the module where the relevant concept is taught.
  - For v1, manually authored visualizations are embedded directly in the SvelteKit frontend alongside didactic and experiential content.

**Progress opacity**:
  - The in-browser SQLite database records a unified progress model: module completion, assessment scores (pre/post), and exercise status — all queryable from the SvelteKit frontend.
  - The navigation UI surfaces per-module mastery indicators so the learner always knows where they stand.

**Repetitive infrastructure**:
  - learningfoundry is a reusable PyPI package — the frontend shell, database schema, progress tracking, and pipeline orchestration are shared infrastructure consumed by any curriculum repository.
  - A second curriculum on a different topic reuses the same engine and templates; only the YAML content definitions change.

---
