# features.md -- learningfoundry (Python 3.12 + SvelteKit)

This document defines **what** the `learningfoundry` project does -- requirements, inputs, outputs, behavior -- without specifying **how** it is implemented. This is the source of truth for scope.

For a high-level concept (why), see [`concept.md`](concept.md). For implementation details (how), see [`tech-spec.md`](tech-spec.md). For a breakdown of the implementation plan (step-by-step tasks), see [`stories.md`](stories.md). For project-specific must-know facts that future LLMs need to avoid blunders, see [`project-essentials.md`](project-essentials.md). For the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), see [`docs/project-guide/go.md`](../project-guide/go.md) — re-read it whenever the mode changes or after context compaction.

---

## Project Goal

learningfoundry is a PyPI package that turns a versioned YAML curriculum definition into a deployable, self-contained SvelteKit learning application. An author defines curriculum structure — modules, lessons, content blocks (markdown text, YouTube videos, assessments, model-training exercises) — in a single YAML file. learningfoundry reads that definition, assembles content from referenced markdown files and library integrations (quizazz for assessments, nbfoundry for training exercises), and produces a static SvelteKit app with in-browser SQLite progress tracking. The goal is to eliminate the manual assembly cost of building a structured, multi-format learning curriculum so that an educator can go from a topic outline to a working learner-facing application using a single tool.

### Core Requirements

1. **YAML curriculum parser** — Read and validate a versioned (`semver`) YAML curriculum definition file that describes the full curriculum structure: modules, lessons, and content blocks.
2. **Pipeline orchestrator** — Process the parsed YAML by resolving content references (markdown files, video URLs) and invoking library integrations (quizazz, nbfoundry) to assemble all learning artifacts.
3. **SvelteKit frontend generation** — Produce a static SvelteKit application that presents all content types in a unified learner experience with module/lesson navigation and in-browser progress tracking.
4. **In-browser SQLite** — The generated app uses sql.js/WASM to persist learner progress (module completion, assessment scores, exercise status) entirely client-side with no server dependency.
5. **quizazz integration** — Consume assessment content produced by quizazz for pre- and post-module assessments, rendered inline in the SvelteKit frontend.
6. **nbfoundry integration** — Consume scaffolded model-training exercises produced by nbfoundry, rendered inline in the SvelteKit frontend. Exercise authoring details (code insertion points, data prep) are handled by nbfoundry, which integrates with modelfoundry.
7. **Static deployment** — The final artifact is a static site deployable to any CDN or runnable locally via a dev server.

### Operational Requirements

1. **Fail-fast error handling** — The CLI exits immediately on the first error with a clear, actionable message (file path, line number where applicable, what went wrong, how to fix it). No partial recovery or silent fallback.
2. **Structured logging** — Use a configurable logging library (e.g., `structlog` or `logging` with structured formatters). Log levels (DEBUG, INFO, WARNING, ERROR) are configurable via the global config file. Output defaults to stdout; file output is configurable.
3. **Global configuration** — A user-level config file at `~/.config/learningfoundry/config.yml` stores defaults for logging level, log output destination, and other pipeline parameters. CLI flags override config-file values; config-file values override built-in defaults.
4. **YAML versioning** — Every curriculum YAML file includes a top-level `version` field (semver string, e.g., `"1.0.0"`). The parser selects the correct schema/parser based on the major version, enabling backward-compatible evolution of the format.

### Quality Requirements

1. **Cross-platform** — The Python pipeline (data preparation, model training/optimization/evaluation via nbfoundry + modelfoundry; YAML parsing; content assembly) must run on macOS, Linux, and Windows. The generated SvelteKit artifacts have no cross-platform concerns.
2. **Python 3.12 pinned** — The project requires Python 3.12 exactly, due to GPU acceleration library compatibility constraints.
3. **Minimal dependencies** — Prefer standard-library solutions where practical. Third-party dependencies must be justified and pinned.
4. **Readable, maintainable code** — Clear module boundaries, docstrings on public APIs, consistent code style enforced by linter/formatter.

### Usability Requirements

1. **CLI interface** — learningfoundry is invoked via CLI subcommands:
   - `learningfoundry build` — Run the full pipeline: parse YAML, resolve content, invoke integrations, produce the SvelteKit app.
   - `learningfoundry validate` — Check the curriculum YAML for schema errors, missing file references, and version compatibility without running the full build.
   - `learningfoundry preview` — Build and launch a local dev server for the generated SvelteKit app.
2. **Target users** — Educators, graduate students, technical teams, and developer advocates who are comfortable with YAML, markdown, and the command line. No web-based authoring UI.
3. **Content authoring** — Authors write curriculum content in markdown files and reference them from the YAML definition. LLM-generated content is produced via ad hoc scripts or browser-based LLM chat and pasted into markdown files — learningfoundry does not invoke LLMs directly (LLM orchestration is delegated to lmentry for future integration).

### Non-goals

1. **Admin/authoring UI** — No web-based curriculum builder; authoring is YAML + markdown + CLI.
2. **User accounts or authentication** — Single-user, local-first; no login system.
3. **Server-side persistence or APIs** — The generated app is fully static; no backend at runtime.
4. **AI video generation** — Videos are YouTube embeds only.
5. **Spaced repetition or adaptive sequencing** — Beyond future pre/post-assessment gating, no adaptive learning algorithms.
6. **Content locking/gating (v1)** — Post-assessment `pass_threshold` gates progression on subsequent items in the module flow (Phase J / Story J.v); the sequential-module rule consumes the same gate so the next module stays locked until the previous module's post-assessment is passed. `role: pre` is non-gating by convention (soft-gate). Cross-module assessment dependencies (e.g. M3 post gates M5 pre) and pre-assessment hard-gating remain out of scope.
7. **Multi-curriculum dashboard** — No cross-curriculum analytics or management surface.
8. **Mobile native wrappers** — Web-only delivery.
9. **nbfoundry integration (v1)** — Marimo notebook generation is out of scope; placeholder slots in the frontend anticipate future integration.
10. **d3foundry integration (v1)** — D3.js visualization generation is out of scope; placeholder slots in the frontend anticipate future integration.
11. **Progress export/import** — Progress is ephemeral and local to the browser; no export or sync mechanism in v1.
12. **Direct LLM invocation** — learningfoundry does not call LLM APIs. Content generation is done externally; LLM orchestration will be handled by lmentry in a future version.

---

## Inputs

### Curriculum YAML file

The primary input is a single YAML file defining the curriculum structure. The file must include a semver `version` field. Structure:

```yaml
version: "1.0.0"

curriculum:
  title: "D802 Deep Learning Essentials"
  description: "A hands-on curriculum covering deep learning fundamentals."

  modules:
    - id: mod-01
      title: "Introduction to Neural Networks"
      description: "..."

      assessments:
        - role: pre
          position: before_lessons
          source: quizazz
          ref: assessments/mod-01-pre.yml
        - role: post
          position: after_lessons
          source: quizazz
          ref: assessments/mod-01-post.yml
          pass_threshold: 0.8

      lessons:
        - id: lesson-01
          title: "What is a Neural Network?"
          content_blocks:
            - type: text
              ref: content/mod-01/lesson-01.md

            - type: video
              url: "https://www.youtube.com/watch?v=..."

            - type: assessment
              source: quizazz
              ref: assessments/mod-01-lesson-01-assessment.yml

            - type: exercise
              source: nbfoundry
              ref: exercises/mod-01-exercise-01.yml
```

**Content block types (v1):**
- **text** — References a markdown file (`ref`). The most common content type.
- **video** — `url` (YouTube watch or youtu.be). Optional `provider` (default `youtube`). Optional `extensions` — a JSON object for player-specific data (e.g. chapters, transcript refs); the frontend interprets keys per provider so new players do not require a unified schema.
- **assessment** — References a quizazz assessment definition file (`ref`).
- **exercise** — References an nbfoundry exercise definition file (`ref`).

### Markdown content files

Markdown files referenced by `text` content blocks. Standard markdown; no custom extensions in v1.

**Lesson title vs. markdown H1 — authoring convention.** The generated lesson page renders the curriculum-yml `lesson.title` as the page's outer `<h1>` (in the layout) and then renders the markdown body — including any leading `# Heading` — inside the lesson content. Identical strings in the two places produce a duplicative-looking page. Authors are expected to keep the YAML `title:` short and navigation-shaped (e.g. `"Lesson 3"`, `"Lesson 3: Cultural Diffusion"`) and use the markdown `# H1` for a complementary descriptive long-form title — or omit the markdown heading entirely. See README → "Lesson titles and markdown headings" for the full convention with examples.

**Co-located image assets.** Authors may reference images directly from a lesson's markdown using either the markdown form (`![alt](path)`, `![alt](path "title")`) or the HTML form (`<img src="path">`). Relative paths are resolved against the markdown file's own directory, so authors organise images alongside the markdown that uses them. Absolute URLs (`http://`, `https://`, protocol-relative `//`, root-absolute `/`, and `data:` URIs) pass through unchanged so authors can mix CDN-hosted and co-located images freely. Image refs inside fenced code blocks (``` ``` `` or `~~~`) are left as literal text — code samples that *show* image syntax are not silently rewritten.

### Global config file

`~/.config/learningfoundry/config.yml` — Optional. Stores user-level defaults:

```yaml
logging:
  level: INFO          # DEBUG | INFO | WARNING | ERROR
  output: stdout       # stdout | <file path>
```

Additional parameters will be added as the project evolves.

### CLI arguments

CLI flags for subcommands (`build`, `validate`, `preview`). Flags override config-file values.

---

## Outputs

### Static SvelteKit application

The primary output is a build-ready SvelteKit project directory containing:

- All curriculum content compiled into SvelteKit pages/components
- Module and lesson navigation
- Embedded assessment, video, and exercise components
- In-browser SQLite (sql.js/WASM) for progress tracking
- Placeholder slots for future nbfoundry and d3foundry content
- A `static/content/<hash12>/<basename>` directory holding every co-located image asset referenced by any lesson's markdown. The 12-character prefix is the SHA-256 hash of the source file's bytes, so identical images dedupe automatically and the URL is stable across rebuilds.

The application is deployable to any static hosting provider (CDN) or runnable locally.

### Console output

- **build** — Progress log of pipeline stages (parsing, content resolution, integration invocation, SvelteKit generation). Errors halt the pipeline immediately with actionable messages.
- **validate** — Schema validation results: OK or a list of errors with file paths and descriptions.
- **preview** — Dev server URL and log output.

---

## Functional Requirements

### FR-1: YAML Curriculum Parsing

Parse and validate the curriculum YAML file against the schema for the declared `version`.

**Behavior:**
1. Read the YAML file specified as a CLI argument.
2. Extract the `version` field and select the corresponding schema/parser.
3. Validate the full document against the schema: required fields, valid content block types, file reference existence, URL format.
4. Return a structured in-memory representation of the curriculum for downstream pipeline stages.

**Locking configuration fields (parsed in v1 schema):**
- `curriculum.locking` (optional `LockingConfig`): `sequential: bool` (default false — module N+1 requires module N complete), `lesson_sequential: bool` (default false — lesson N+1 requires lesson N complete within a module).
- `module.locked` (optional `bool | None`): per-module override. `None`/absent inherits from curriculum/global locking config. Explicit `true`/`false` trumps inheritance.
- `lesson.unlock_module_on_complete` (optional `bool`, default false): when this lesson completes, unlocks sibling lessons and the next module.
- `assessment` block `pass_threshold` (optional `float`, 0.0–1.0, default 0.0): minimum `score / maxScore` ratio required for the assessment to count as "passed" for block-completion purposes.

**Edge Cases:**
- Missing `version` field → Error: "Curriculum YAML must include a top-level `version` field (semver)."
- Unsupported major version → Error: "Unsupported curriculum version `X.0.0`. Supported versions: 1.x."
- Referenced file does not exist → Error: "File not found: `content/mod-01/lesson-01.md` (referenced by mod-01 / lesson-01 / content_blocks[0])."
- Duplicate module or lesson IDs → Error with location of both duplicates.

### FR-2: Content Resolution

Resolve all content references in the parsed curriculum to their actual content.

**Behavior:**
1. For each `text` block, read the referenced markdown file, then scan the markdown for image references and rewrite them (see "Image asset resolution" below).
2. For each `video` block, validate the YouTube URL format.
3. For each `assessment` block, delegate to quizazz to parse the referenced assessment file and return renderable content.
4. For each `exercise` block, delegate to nbfoundry to parse the referenced exercise file and return renderable content.
5. Attach resolved content to the in-memory curriculum structure.

**Image asset resolution (sub-requirement of `text` block resolution):**
1. Walk the markdown source for `![alt](path)`, `![alt](path "title")`, and HTML `<img src="path">` references; skip references inside fenced code blocks.
2. Pass through any reference whose URL is absolute (`http://`, `https://`, `//`, leading `/`) or a `data:` URI — these stay unchanged in the rewritten markdown and produce no asset records.
3. Resolve every other reference relative to the markdown file's own directory.
4. Hash each unique source file's bytes (SHA-256, first 12 hex chars) and record an `(source_path, dest_relative)` pair where `dest_relative = "content/<hash12>/<basename>"`. The hashing is what produces global dedup: two lessons referencing the same image content produce one asset record.
5. Rewrite every relative reference's URL to `/content/<hash12>/<basename>` so it resolves at every nested SvelteKit route.
6. Aggregate all asset records onto the in-memory `ResolvedCurriculum` for the generator to copy into `static/content/...`.

**Edge Cases:**
- Markdown file is empty → Warning logged; empty content block rendered in frontend.
- Invalid YouTube URL format → Error with block location.
- quizazz or nbfoundry returns an error → Error surfaced with the originating block location and the library's error message.
- Image reference points at a non-existent file → `ContentResolutionError` with the markdown file path AND the lesson location ("module `mod-01` / lesson `lesson-01` / block[0]") in the error message.
- Same image referenced from N lessons → Copied exactly once; all N markdown rewrites point at the same `/content/<hash12>/<basename>` URL.

#### Phase J: Pedagogical authoring

The remaining subsections under FR-2 — `meta` blocks, the generalized `assessments[]` array, module-flow rendering, the curriculum-wide time aggregate, and the tutorial-scaffold container directives — are the Phase J pedagogical-authoring affordances that compose into a single author-facing story. They were landed as separate stories (J.a → J.f) for blast-radius reasons but are designed to be used together. See README's "Pedagogical authoring" section for a unified worked example and the migration note for `pre_assessment` / `post_assessment` → `assessments[]`. The cross-cutting integration test that pins the composition lives at `tests/test_pedagogical_authoring_smoke.py`.

**Module assessments — generalized array (Phase J / Story J.e):**

Each module declares assessments as a list of `AssessmentDefinition` entries — one entry per assessment — replacing the legacy two-slot `pre_assessment` / `post_assessment` fields (removed outright; pre-1.0 makes the breakage acceptable).

- `id` is optional (Story J.r) — a stable per-assessment identifier within the module, used by the route layer (Story J.s) and the progress store (Story J.u). When omitted, the parser auto-generates: the first assessment with a given role takes the bare role (`pre`, `post`, `practice`), and subsequent same-role entries append a 1-based counter (`practice-2`, `practice-3`). Explicit ids are honoured verbatim; intra-module uniqueness is enforced at parse time, so duplicate explicit ids — or an explicit id colliding with an auto-gen result — fail loud.
- `role` is an open string. Conventional values: `pre`, `practice`, `post`, `checkpoint`. Used as a UI label and a tag for downstream consumers; the schema does not constrain the vocabulary.
- `position` is a discriminated union:
  - `before_lessons` — anchors the assessment at the start of the module flow.
  - `after_lessons` — anchors at the end.
  - `{ before_lesson: <lesson-id> }` — anchors immediately before the named lesson.
  - `{ after_lesson: <lesson-id> }` — anchors immediately after.
- `source` and `ref` follow the same provider-+-path convention as assessment content blocks.
- `pass_threshold` is optional (`0.0`–`1.0`); recorded but not gating in v1.
- The parser validates `before_lesson` / `after_lesson` refs against the module's `lessons` and rejects unknown ids at parse time.
- The resolver materializes assessments into canonical placement order: `before_lessons` first, then for each lesson the `before_lesson` and `after_lesson` anchors, then `after_lessons`.

**Module flow renders assessments at resolved positions (Phase J / Story J.f):**

The expanded module in the sidebar interleaves assessment rows with lesson rows according to each assessment's `position`. The resolver-emitted ordering is honoured, so authors see the same sequence in the UI that they declared in YAML once normalized:

- `before_lessons` entries → above every lesson in the module.
- `{ before_lesson: <id> }` entries → directly above the named lesson row.
- `{ after_lesson: <id> }` entries → directly below the named lesson row.
- `after_lessons` entries → below every lesson.

Each assessment row shows the role label (capitalized, e.g. `Pre Assessment` / `Practice Assessment` / `Post Assessment`) and, when `pass_threshold` is set, a secondary annotation `"X% to pass"`. Rows are clickable `<button>` controls (Story J.t) that navigate to `/{moduleId}/assessment/{id}` (Story J.s); post-assessment `pass_threshold` gates progression on subsequent items in the module flow (Story J.v), with `role: pre` exempt as a soft-gate convention. Per-role styling beyond the amber active-state palette and mid-lesson placement remain deferred.

**Pedagogical metadata (Phase J / Stories J.a, J.h):**

`CurriculumDef`, `Module`, and `Lesson` each accept an optional `meta` block carrying author-declared pedagogical context. The pipeline does not interpret these fields beyond schema validation — they are passed through verbatim into `curriculum.json` for downstream rendering and tooling. `LessonMeta` and `ModuleMeta` landed in Story J.a; `CurriculumMeta` followed in Story J.h alongside the schema-extensions mechanism described below.

- `lesson.meta` (`LessonMeta`): `role` (e.g. `opener`, `concept`, `tutorial`, `practice`, `hands_on`, `bonus`), `hook` (a `{tagline, image_prompt?}` object), `introduces` / `reinforces` (lists of learning-item IDs the lesson covers), `duration_minutes`.
- `module.meta` (`ModuleMeta`): `theme`, `big_problem`, `objectives`, `experiential_summary`, `target_audience`.
- `curriculum.meta` (`CurriculumMeta`, Phase J / Story J.h): `target_audience`, `objectives`, `prerequisites`. Curriculum-wide pedagogical context — passed through to `curriculum.json` for downstream rendering / tooling. Rendering is deferred to a later phase, matching the J.a precedent for `ModuleMeta`.
- All three meta blocks (and the nested `Hook`) use Pydantic `extra="allow"`, so authors can attach genre-specific fields without schema churn.
- Frontend rendering of `meta` lands in subsequent Phase J stories (J.b–J.c). Story J.a is schema + JSON pass-through only.

**Project-specific `meta` schema extensions (Phase J / Story J.h):**

`extra="allow"` on the three meta models is permissive by design — authors should be able to attach project-specific fields without forcing a learningfoundry schema change. The trade-off is that an LLM-driven authoring workflow can silently introduce *phantom* fields (typos like `prequisites` instead of `prerequisites`) that pass validation, end up in `curriculum.json`, and break downstream consumers in subtle ways.

The schema-extensions mechanism is an opt-in tightening:

- A project drops `learningfoundry-schema-extensions.yml` next to its `curriculum.yml`. When present, learningfoundry synthesizes strict subclasses of `CurriculumMeta` / `ModuleMeta` / `LessonMeta` with the project-declared fields appended and `extra` flipped from `allow` to `forbid` (default; opt-out per model via `extra: allow`).
- File-path resolution order: `--schema-extensions PATH` CLI flag > `[tool.learningfoundry] schema_extensions` in `pyproject.toml` next to the curriculum > auto-discovery of `learningfoundry-schema-extensions.yml` next to the curriculum > none (base `extra="allow"` preserved).
- Supported field types: `str`, `int`, `bool`, `list[str]`, `enum` (with `values:` list), `object` (single nested object — `fields:` recurses, no `default:`, use `required: false`), `list[object]` (list of nested objects — `fields:` declares the element shape; only `default: []` allowed). Per-field `required: bool` (default `true`) and `default:` (optional — presence makes the field optional regardless of `required`). See the README "Strict project-specific extensions" subsection for the worked `object` / `list[object]` example.
- Worked example:

```yaml
version: "1"
curriculum_meta:
  fields:
    pedagogical_approach: { type: str, required: false }
module_meta:
  fields:
    curriculum_thread: { type: str, required: false }
lesson_meta:
  fields:
    covers:        { type: list[str], default: [] }
    difficulty:    { type: enum, values: [intro, intermediate, advanced] }
    prerequisites: { type: list[str], default: [] }
```

- Error contract: an unknown field on a `meta` block raises Pydantic `ValidationError` naming the field (so `prequisites: [...]` against the example above fails with `prequisites` in the message); a malformed extension file raises `SchemaExtensionError` citing the file path; the extensions file itself is strict-validated (typos like `defalt:` instead of `default:` fail at load time).
- When the file is absent, today's `extra="allow"` behaviour is preserved bit-for-bit — backward compatible with every existing curriculum.

### FR-3: SvelteKit Application Generation

Generate a complete, build-ready SvelteKit project from the resolved curriculum.

**Behavior:**
1. Scaffold the SvelteKit project structure (or populate a bundled template).
2. Generate a page/component for each module and lesson, embedding resolved content blocks in order.
3. Include navigation components: module list, lesson list within a module, prev/next lesson navigation.
4. Include a progress dashboard component showing per-module completion status and assessment scores.
5. Embed the sql.js/WASM runtime and initialize the progress database schema on first load.
6. Include placeholder component slots for future nbfoundry (notebook) and d3foundry (visualization) content types.

**Edge Cases:**
- Curriculum with zero modules → Error: "Curriculum must contain at least one module."
- Module with zero lessons → Error: "Module `mod-01` must contain at least one lesson."
- Very large curriculum (50+ modules) → No hard limit; build may be slow but must complete correctly.

**Pedagogical metadata surfaces (Phase J / Story J.b):**

The schema-level `meta` blocks added by Story J.a (`lesson.meta`, `module.meta`) surface in the generated app at two leverage points; both render only when their backing field is present.

- **Sidebar role chip.** When `lesson.meta.role` is set, the sidebar lesson row renders a small uppercase chip (e.g. `OPENER`, `PRACTICE`) at the right edge of the row, distinct in styling from the progress glyph and locked-row indicators.
- **Lesson tagline.** When `lesson.meta.hook.tagline` is set, the lesson body renders the tagline as a quiet italic line directly above the lesson title — a teaser that reads as a superscript to `<h1>{lesson.title}</h1>`.

`hook.image_prompt` and module-level `meta.theme` rendering on the module index are deferred to later Phase J stories.

**Curriculum-wide time estimate (Phase J / Story J.c):**

Generation sums `lesson.meta.duration_minutes` across every lesson and emits the result as `curriculum.total_duration_minutes` (top level of `curriculum.json`). Lessons without `meta` or without `duration_minutes` are skipped; when no lesson contributes, the field is `null` and the index page renders nothing. When non-null, the index renders the estimate above the dashboard as `≈ Xh Ym` (or `≈ Xm` under an hour). Per-module aggregation, learner-elapsed-time, and adaptive estimates are out of scope.

**Tutorial scaffold directives (Phase J / Story J.d.1):**

Lesson markdown supports three named container directives that surface the worked-example → faded-example → independent-practice progression as visually distinct cards. Each directive opens with `::: <name>` on its own line and closes with `:::` on its own line; the body is itself markdown.

- `::: worked-example` — filled gray card. The author shows a fully worked solution.
- `::: faded-example` — outlined dim card. The author poses a similar problem with reduced scaffolding.
- `::: independent-practice` — amber-highlighted challenge prompt. The learner solves on their own.

Unknown directive names pass through untouched at render time; the Python-side lint that flags malformed or misspelled directive blocks at build time lands in Story J.d.2. Interactivity (progressive reveal, hint toggles, checkmark affordances) is out of scope — static styling only.

### FR-4: In-Browser Progress Tracking

Track learner progress entirely client-side using sql.js/WASM (SQLite in the browser).

**Lesson lifecycle (Story I.p / FR-P15):**
The `lesson_progress.status` column moves through four states plus the orthogonal `optional`:

- `not_started` — never opened.
- `opened` — `LessonView` mounted; `markLessonOpened` ran. No content engagement yet.
- `in_progress` — at least one content block fired its completion event.
- `complete` — every content block has fired completion; `markLessonComplete` ran.

`opened` and `in_progress` share the sidebar `…` icon — the lifecycle distinction is data-only, intended for analytics / future hooks. `LessonView` emits three callback-prop events (`onlessonopen`, `onlessonengage`, `onlessoncomplete`) that fire at most once per mount session and are suppressed when the corresponding state transition is a no-op (e.g. revisiting a `complete` lesson fires `onlessonopen` only). No internal subscribers exist today.

**Behavior:**
1. On first app load, create the SQLite database and initialize the schema (`lesson_progress`, `assessment_scores`, `module_assessment_scores`, `exercise_status`).
2. Mark a lesson as completed when every content block in the lesson has fired its completion event. Per-block completion contracts:
   - **Text block** — fires when a sentinel `<div data-textblock-end>` placed at the *end* of the rendered markdown is continuously visible in the viewport for 1 s. Observing the end-of-block sentinel (rather than any portion of the wrapper) is what makes a tall lesson require actual reading-time scroll: simply landing on the page is no longer sufficient.
   - **Video block** — fires on the YouTube IFrame Player API `ENDED` state, with a 3-second viewport-fallback when the IFrame API is unavailable.
   - **Assessment block** — fires when `score / maxScore >= passThreshold` (default `0.0`); failed attempts retry internally without firing.
3. Store assessment scores with timestamps. Two write paths exist (Story J.u):
   - **Content-block assessments** (lesson content blocks of `type: assessment`) persist via `progressRepo.saveAssessmentScore(score)` into `assessment_scores`, keyed on the global `assessmentRef`.
   - **Module-level assessments** (the J.e generalized `assessments[]` array) persist via `progressRepo.markAssessmentComplete(moduleId, assessmentId, score)` into `module_assessment_scores`, keyed on `(moduleId, assessmentId)` so two modules referencing the same quizazz YAML don't collide.
   - `passed: boolean` is **not** stored — read sites compute it via `computeAssessmentPassed(score, pass_threshold)`. This keeps the active YAML threshold authoritative if an author retunes it.
4. Store exercise completion status.
5. Surface progress in the navigation UI: per-module completion percentage, assessment score indicators.
6. Provide a course-level reset button in the sidebar (Story I.l): disabled when no learner activity exists; on confirmed click, truncate `lesson_progress`, `assessment_scores`, `module_assessment_scores`, and `exercise_status` and route to `/`.

**Locking and sequential access:**
The locking configuration (parsed from YAML and global config) controls which modules/lessons the learner can access:
- Config hierarchy (most local wins): per-module `locked` bool → curriculum `locking.sequential` → global config `locking.sequential`.
- When `sequential` is true, module N+1 is locked until module N is complete (unless overridden by `locked: false`).
- When `lesson_sequential` is true, lesson N+1 within a module is locked until lesson N is complete.
- `unlock_module_on_complete`: completing this lesson unlocks its siblings and the next module regardless of sequential state.
- The frontend enforces locking by making locked modules/lessons non-interactive (Story I.j).

**Recording-paused state (Story I.bb):**
When the sql.js WASM asset (`/sql-wasm.wasm`) cannot be fetched at runtime — asset-pipeline regression, deploy misconfiguration, browser cache poisoning, network partition — `Database.getDb()` rejects with the typed `WasmAssetMissingError`. The frontend MUST:
- Surface a persistent, non-blocking banner above the main content area: "Progress recording is paused. Your activity in this session will not be saved. Try refreshing to retry." with a refresh CTA that reloads the page.
- Continue rendering the dashboard, sidebar, and lesson views as if no progress had been recorded yet (empty `not_started` state). A missing-WASM read MUST NOT render an error page.
- Best-effort write attempts (lesson opens, assessment scores, exercise status) MUST resolve quietly so UI flows complete without unhandled rejections; the banner is the user-facing signal.
- The banner clears once a refresh successfully fetches the WASM asset (`dbInit` transitions to `ready`).

**Edge Cases:**
- Browser storage cleared → Database is recreated; progress resets. This is expected behavior (ephemeral).
- Multiple browser tabs → No cross-tab sync in v1; last-write-wins on the same IndexedDB backing store.
- WASM asset missing → recording-paused banner; reads return empty, writes are no-ops (Story I.bb).

### FR-5: quizazz Integration

Consume assessment content produced by quizazz and render it in the SvelteKit frontend. For the author-facing how-to (install, embedding shapes, worked example, gotchas), see README's [Embedding a quizazz assessment](../../README.md#embedding-a-quizazz-assessment) walkthrough.

**Behavior:**
1. During content resolution, invoke quizazz to parse assessment YAML files referenced by `assessment` content blocks and entries in the module's `assessments` array (Story J.e — replaces the legacy two-slot `pre_assessment`/`post_assessment` fields).
2. quizazz returns a content-only artifact (questions, answer choices, correct answers, explanations).
3. The SvelteKit frontend renders assessments inline with immediate scoring and explanation display.
4. Assessment scores are written to the in-browser SQLite database.

**Edge Cases:**
- quizazz assessment file is malformed → Error surfaced with file path and quizazz's error message.
- Assessment has zero questions → Warning; empty assessment section rendered.

### FR-6: nbfoundry Integration

Consume scaffolded model-training exercises produced by nbfoundry and render them in the SvelteKit frontend.

**Behavior:**
1. During content resolution, invoke nbfoundry to parse exercise YAML files referenced by `exercise` content blocks.
2. nbfoundry returns renderable exercise content (instructions, code scaffolding with insertion points, expected outputs). Exercise authoring details (data prep, training steps, evaluation) are fully delegated to nbfoundry.
3. The SvelteKit frontend renders exercises inline with instructions and code display.
4. Exercise completion status is written to the in-browser SQLite database.

**Edge Cases:**
- nbfoundry exercise file is malformed → Error surfaced with file path and nbfoundry's error message.
- Exercise references a dataset not available locally → Error from nbfoundry surfaced to the user.

### FR-7: CLI Interface

Provide a command-line interface with subcommands for building, validating, and previewing curricula.

**Behavior:**
1. `learningfoundry build <curriculum.yml>` — Run the full pipeline (FR-1 through FR-3). Output the SvelteKit project to a configurable output directory (default: `./build/`).
2. `learningfoundry validate <curriculum.yml>` — Run FR-1 (parsing and validation) only. Report errors or "Curriculum is valid."
3. `learningfoundry preview <curriculum.yml>` — Run `build`, then start a local dev server serving the generated app. Print the local URL.
4. All subcommands accept `--log-level` and `--config` flags. CLI flags override config-file values; config-file values override built-in defaults.

**Edge Cases:**
- No curriculum file argument → Error: "Usage: learningfoundry <build|validate|preview> <curriculum.yml>"
- Output directory already exists on `build` → Overwrite with a warning logged.
- Port conflict on `preview` → Error with suggestion to use `--port` flag.

### FR-8: Global Configuration

Load and merge configuration from the global config file and CLI flags.

**Behavior:**
1. On startup, check for `~/.config/learningfoundry/config.yml`.
2. If present, parse and apply settings (logging level, logging output, other future parameters).
3. CLI flags override any config-file value.
4. If the config file is absent, use built-in defaults (INFO logging to stdout).

**Edge Cases:**
- Config file is malformed YAML → Error: "Invalid config file at `~/.config/learningfoundry/config.yml`: <parse error>."
- Unknown config keys → Warning logged; unknown keys ignored (forward-compatible).

---

## Configuration

**Precedence (highest to lowest):**
1. CLI flags (e.g., `--log-level DEBUG`)
2. Global config file (`~/.config/learningfoundry/config.yml`)
3. Built-in defaults

**Global config schema (v1):**

```yaml
# ~/.config/learningfoundry/config.yml
logging:
  level: INFO          # DEBUG | INFO | WARNING | ERROR
  output: stdout       # stdout | <file path>
```

Additional parameters will be added as the project evolves. Unknown keys are ignored with a warning.

**Curriculum YAML schema:** See [Inputs — Curriculum YAML file](#curriculum-yaml-file).

---

## Testing Requirements

Pragmatic test coverage focused on high-value paths:

1. **YAML parsing** — Unit tests for valid curricula, missing fields, invalid versions, duplicate IDs, missing file references.
2. **Content resolution** — Unit tests for markdown loading, URL validation, and error propagation from quizazz/nbfoundry (using mocks/stubs).
3. **CLI** — Integration tests for `build`, `validate`, and `preview` subcommands using a small fixture curriculum.
4. **Config merging** — Unit tests for precedence: CLI > config file > defaults; malformed config handling.
5. **SvelteKit output** — Smoke tests verifying the generated project structure contains expected files and compiles without errors.

Tests are expanded incrementally as the project matures.

---

## Security and Compliance Notes

- **No direct LLM API calls** — learningfoundry does not handle API keys or make external network requests. LLM orchestration and key management are delegated to lmentry (future integration).
- **No user authentication** — No passwords, tokens, or PII storage.
- **Static output** — The generated app makes no server-side requests at runtime. All data stays in the learner's browser.
- **Dependency auditing** — Third-party dependencies should be reviewed for known vulnerabilities before inclusion.
- **Apache 2.0 license** — All source and generated artifacts are distributed under Apache 2.0.

---

## Performance Expectations

No specific performance targets for v1. The pipeline should complete in a reasonable time for a typical curriculum (10–20 modules). Performance optimization is deferred until real workloads identify bottlenecks.

---

## Acceptance Criteria

1. An author can write a curriculum YAML file and markdown content files, run `learningfoundry build`, and receive a static SvelteKit application that renders all modules and lessons with text, video, assessment, and exercise content.
2. `learningfoundry validate` catches and reports schema errors, missing files, and version mismatches with clear, actionable messages.
3. `learningfoundry preview` builds the app and serves it locally for review.
4. The generated app tracks lesson completion and assessment scores in an in-browser SQLite database and displays progress in the navigation UI.
5. The D802 Deep Learning Essentials reference curriculum builds and runs successfully as the first end-to-end proof of the pipeline.
6. The pipeline runs on macOS, Linux, and Windows with Python 3.12.
7. Pre/post assessment data is stored in the progress database, anticipating future gating support without enforcing it in v1.
8. Placeholder slots exist in the frontend for future nbfoundry and d3foundry content types.
