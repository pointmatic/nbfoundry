# learningfoundry

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org)
[![CI](https://github.com/pointmatic/learningfoundry/actions/workflows/ci.yml/badge.svg)](https://github.com/pointmatic/learningfoundry/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/pointmatic/learningfoundry/branch/main/graph/badge.svg)](https://codecov.io/gh/pointmatic/learningfoundry)

A curriculum engine that turns a YAML curriculum definition into a deployable SvelteKit learning application — with interactive assessments, executable notebooks, and data visualizations — in a single pipeline.

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Curriculum YAML Format](#curriculum-yaml-format)
- [Video blocks](#video-blocks)
- [Lesson titles and markdown headings](#lesson-titles-and-markdown-headings)
- [Images and assets](#images-and-assets)
- [Pedagogical authoring](#pedagogical-authoring)
- [Content locking](#content-locking)
- [Configuration File](#configuration-file)
- [Development Setup](#development-setup)
- [Maintenance](#maintenance)

---

## Overview

`learningfoundry` takes a single `curriculum.yml` file and generates a fully self-contained [SvelteKit](https://kit.svelte.dev/) learning application. The generated app supports:

- **Text** — Markdown content rendered in the browser
- **Video** — YouTube embeds
- **Assessment** — Interactive assessments via [quizazz](https://github.com/pointmatic/quizazz) (optional)
- **Exercise** — Executable notebooks via nbfoundry (stub provided)
- **Visualization** — D3-based charts via d3foundry (stub provided)

Learner progress is persisted locally in SQLite (via sql.js) — no backend required.

---

## Installation

```bash
pip install learningfoundry
```

**With optional quizazz support:**

```bash
pip install "learningfoundry[quizazz]"
```

**Requirements:**

- Python 3.12+
- [pnpm](https://pnpm.io) (for `preview` command and generated app development)
- Node.js 18+ (for the generated SvelteKit app)

---

## Quick Start

1. **Create a curriculum file** (see [Curriculum YAML Format](#curriculum-yaml-format)):

   ```bash
   cat > curriculum.yml << 'EOF'
   version: "1.0.0"
   curriculum:
     title: "My Course"
     description: "A short description."
     modules:
       - id: mod-01
         title: "Module One"
         lessons:
           - id: lesson-01
             title: "Getting Started"
             content_blocks:
               - type: text
                 ref: content/lesson-01.md
               - type: video
                 url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
   EOF
   ```

2. **Validate** the curriculum:

   ```bash
   learningfoundry validate
   # OK — curriculum is valid.
   ```

3. **Build and preview** locally:

   ```bash
   learningfoundry preview
   # Preview server started at http://localhost:5173
   ```

   `learningfoundry preview` is the canonical "see your work" command — it builds the SvelteKit project, installs Node dependencies on first run (and again whenever they change), and starts a Vite dev server. On subsequent runs it skips the install step automatically.

   `learningfoundry build` alone is also available if you want to generate the SvelteKit project without serving it (e.g. to inspect output, deploy a static export via `cd dist && pnpm build`, or wire into your own toolchain).

---

## CLI Reference

### `learningfoundry build`

Parse → resolve → generate a SvelteKit project.

```
Usage: learningfoundry build [OPTIONS]

Options:
  -c, --config PATH       Path to the curriculum YAML file.  [default: curriculum.yml]
  --log-level LEVEL       Logging verbosity.  [default: INFO]
                          Choices: DEBUG, INFO, WARNING, ERROR
  -o, --output PATH       Output directory for the generated SvelteKit project.
                          [default: dist]
  --base-dir PATH         Base directory for content refs.
                          (default: curriculum file's parent directory)
  --help                  Show this message and exit.
```

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Curriculum validation error |
| 2 | Content resolution error (missing file, bad URL, etc.) |
| 3 | SvelteKit generation error |
| 4 | Configuration file error |

---

### `learningfoundry validate`

Validate a curriculum YAML without generating any output.

```
Usage: learningfoundry validate [OPTIONS]

Options:
  -c, --config PATH       Path to the curriculum YAML file.  [default: curriculum.yml]
  --log-level LEVEL       Logging verbosity.  [default: INFO]
  --base-dir PATH         Base directory for resolving content refs.
  --help                  Show this message and exit.
```

Prints `OK — curriculum is valid.` on success, or a list of errors and exits with code 1.

---

### `learningfoundry preview`

Build then launch a local Vite dev server.

```
Usage: learningfoundry preview [OPTIONS]

Options:
  -c, --config PATH       Path to the curriculum YAML file.  [default: curriculum.yml]
  --log-level LEVEL       Logging verbosity.  [default: INFO]
  -o, --output PATH       Output directory for the generated SvelteKit project.
                          [default: dist]
  --base-dir PATH         Base directory for content refs.
  --port INTEGER          Port for the local dev server.  [default: 5173]
  --help                  Show this message and exit.
```

Runs `learningfoundry build`, then `pnpm install` (skipped when every declared dependency is already present in `node_modules/`), then `pnpm run dev` in the generated project directory. Requires `pnpm` on `PATH`.

This serves the SvelteKit project from source via Vite's dev server; it does **not** serve the static `pnpm build` output in `dist/build/`. For static deploys, use `cd dist && pnpm build` and host the resulting `dist/build/` directory on any static host.

---

## Curriculum YAML Format

```yaml
version: "1.0.0"

curriculum:
  title: "Course Title"           # required
  description: "Course overview." # optional

  modules:
    - id: mod-01                  # required, kebab-case
      title: "Module One"         # required
      description: "..."          # optional

      # Optional assessments (requires quizazz-builder).
      # Each assessment carries an open-string `role` and a `position`
      # (`before_lessons`, `after_lessons`, or `{ before_lesson: <id> }`
      # / `{ after_lesson: <id> }`). The order in `assessments` after
      # build is the canonical placement order.
      assessments:
        - role: pre
          position: before_lessons
          source: quizazz
          ref: assessments/mod-01-pre.yml

        - role: practice
          position: { before_lesson: lesson-04 }
          source: quizazz
          ref: assessments/mod-01-practice.yml
          pass_threshold: 0.7

        - role: post
          position: after_lessons
          source: quizazz
          ref: assessments/mod-01-post.yml
          pass_threshold: 0.8

      lessons:
        - id: lesson-01           # required, kebab-case; unique within module
          title: "Lesson One"     # required

          content_blocks:

            # Text block — Markdown file
            - type: text
              ref: content/mod-01/lesson-01.md

            # Video block — `provider` selects the player (default: youtube)
            - type: video
              url: "https://www.youtube.com/watch?v=XXXXXXXXXXX"
              # provider: youtube          # optional today; only youtube is implemented
              # extensions: {}            # optional; player-specific payload (see "Video blocks")

            # Assessment block — requires learningfoundry[quizazz];
            # see "Embedding a quizazz assessment" below for the full author flow
            - type: assessment
              source: quizazz
              ref: assessments/mod-01-assessment.yml

            # Exercise block — requires nbfoundry (stub included)
            - type: exercise
              source: nbfoundry
              ref: exercises/mod-01-exercise.yml

            # Visualization block — requires d3foundry (stub included)
            - type: visualization
              source: d3foundry
              ref: visualizations/mod-01-vis.yml
```

**Rules:**

- Module and lesson `id` values must be unique within their scope, and match the pattern `[a-z0-9][a-z0-9-]*`.
- Every curriculum must have at least one module; every module at least one lesson.
- All `ref` paths are resolved relative to `--base-dir` (default: directory containing the curriculum YAML).
- Only YouTube URLs are accepted for `video` blocks when `provider` is `youtube` (the default): `youtube.com/watch?v=` or `youtu.be/`.

---

## Video blocks

Each `video` content block carries:

- **`url`** — Watch URL for the provider (validated for YouTube when `provider: youtube`).
- **`provider`** — Which player to use. Omitted in YAML means `youtube`. New providers (e.g. Vimeo) will add new literal values here together with resolver + frontend support.
- **`extensions`** — Optional mapping of player-specific data. There is **no** cross-player generic schema: keys and shapes are defined per provider. Examples you might add later for YouTube: `chapters` (timestamp + title list), `transcript_ref` (path to WebVTT or plain text), `autoplay`. The build passes `extensions` through to `curriculum.json` unchanged; the Svelte app can grow per-provider components that read `content.extensions`.

Older generated apps only had `url` in each video block’s `content`; the template still treats missing `provider` as `youtube`.

---

## Lesson titles and markdown headings

Each lesson page renders **two** title strings, from two different sources:

1. The **lesson title** from `curriculum.yml` (the `title:` on a lesson). Used by the sidebar, the breadcrumb, the browser tab, and the page's outer `<h1>`.
2. The **leading heading** in the lesson's markdown file (the `# Heading` at the top, if any). Rendered inside the lesson body.

If both strings are identical, the page renders the same title twice and looks broken. The fix is purely an authoring convention — there is no rendering bug to chase.

### Convention

- Keep the YAML `title:` **short and navigation-shaped**. Either a number (`"3"`), a label (`"Lesson 3"`), or label-plus-abbreviation (`"Lesson 3: Cultural Diffusion"`).
- Make the markdown `# Heading` the **descriptive long-form title** that *complements* the YAML title — never echoes it. Imagine reading them together as `"<yaml title>: <markdown H1>"`; that sentence should flow naturally and contain no repeated words.
- If the lesson genuinely has nothing extra to add in a heading, **omit the markdown `# Heading` entirely** and start the lesson with body prose. The page already has the YAML title rendered as its `<h1>`.

### Examples

**Good — complementary, reads as one sentence:**

```yaml
# curriculum.yml
- id: lesson-03
  title: "Lesson 3"
```

```markdown
<!-- content/mod-01/lesson-03.md -->
# The Diffusion of Cultural Artifacts

Most cultural products fail. A reasonable estimate places the fraction…
```

Renders as:

> **Lesson 3**
> # The Diffusion of Cultural Artifacts
> Most cultural products fail. …

**Good — slightly more YAML detail, still no echo:**

```yaml
- id: lesson-03
  title: "Lesson 3: Cultural Diffusion"
```

```markdown
# Why Most Pop Releases Disappear
```

**Bad — duplicative; both titles render the same string:**

```yaml
- id: lesson-03
  title: "The Diffusion of Cultural Artifacts"
```

```markdown
# The Diffusion of Cultural Artifacts
```

**Also fine — no markdown heading at all:**

```yaml
- id: lesson-03
  title: "Lesson 3: Cultural Diffusion"
```

```markdown
Most cultural products fail. A reasonable estimate places the fraction…
```

---

## Images and assets

Lesson markdown can embed images directly. Place the image file alongside the markdown that uses it and reference it with a relative path:

```
content/
└── mod-01/
    ├── lesson-01.md
    ├── diagram.png
    └── figures/
        └── architecture.svg
```

```markdown
# Lesson One

![Architecture diagram](figures/architecture.svg "Hover title")

Here is a smaller inline diagram:

<img src="diagram.png" alt="Diagram" />
```

**How it works:**

- Relative URLs (`diagram.png`, `figures/architecture.svg`) are resolved against the markdown file's own directory. `learningfoundry build` copies each unique image into `dist/static/content/<sha256[:12]>/<basename>` and rewrites the markdown URL to the absolute path `/content/<sha256[:12]>/<basename>` so it resolves at every nested route in the generated app.
- Both the markdown form (`![alt](path)`, `![alt](path "title")`) and the HTML form (`<img src="path">`) are recognised.
- Absolute URLs (`https://`, `http://`, protocol-relative `//...`, root-absolute `/...`) and `data:` URIs pass through unchanged — useful for CDN-hosted assets you don't want copied into the build.
- Image references inside fenced code blocks (` ``` ` or `~~~`) are left as literal text, so code samples that *demonstrate* image syntax aren't silently rewritten.
- The same image referenced from N lessons is copied exactly once (deduped by content hash).
- A missing image fails the build with the lesson location and the expected on-disk path in the error message.

For production deployment to a CDN, just run `cd dist && pnpm build` — the `static/content/` tree gets bundled into the static export under `build/content/`, so deploying `build/` to any static host (Cloudflare Pages, Netlify, S3+CloudFront, …) serves the images at the same URLs the markdown references.

---

## Pedagogical authoring

Phase J adds first-class authoring affordances for the worked-example → faded-example → independent-practice progression and for declaring pedagogical context the build pipeline can act on. Three building blocks compose into one story:

1. **`meta` blocks** declare the *intent* of a module or lesson — its theme, role, opening hook, learning items, and time estimate.
2. **Container directives** in lesson markdown style worked / faded / independent-practice cards inline.
3. **`assessments[]`** on each module places assessments at named positions (before all lessons, before/after a specific lesson, after all lessons) — replacing the legacy `pre_assessment` / `post_assessment` pair (see migration note below).

The subsections below cover each in detail — the [`meta` reference](#meta-reference) and [custom `meta` fields](#custom-meta-fields), the [tutorial scaffold directives](#tutorial-scaffold-directives), [embedding a quizazz assessment](#embedding-a-quizazz-assessment) (full author flow for the assessment content-block type), the module-level [`Assessments`](#assessments) model, and the [migration path](#migrating-from-pre_assessment--post_assessment-pre-v0680) from the legacy `pre_assessment` / `post_assessment` pair.

A small worked example bringing the three together:

```yaml
modules:
  - id: mod-01
    title: "Why convolutions exist"

    meta:
      theme: "Why convolutions exist"
      objectives:
        - "Explain why FC nets fail on images"
        - "Describe weight sharing"
      target_audience: "Intermediate Python; high-school math"

    assessments:
      - role: pre
        position: before_lessons
        source: quizazz
        ref: assessments/mod-01-pre.yml
      - role: practice
        position: { before_lesson: lesson-02 }
        source: quizazz
        ref: assessments/mod-01-practice.yml
        pass_threshold: 0.7
      - role: post
        position: after_lessons
        source: quizazz
        ref: assessments/mod-01-post.yml
        pass_threshold: 0.8

    lessons:
      - id: lesson-01
        title: "What is a convolution?"
        meta:
          role: opener
          hook:
            tagline: "What if your first layer of vision was just a flashlight on the world?"
          introduces: [receptive_field, simple_cells]
          duration_minutes: 15
        content_blocks:
          - type: text
            ref: content/mod-01/lesson-01.md
```

And the lesson markdown can sprinkle in the three directives:

```markdown
# What is a convolution?

::: worked-example
Compute the output shape for a 32×32 input, 3×3 kernel, stride 1, padding 0.

We apply $(W - K + 2P) / S + 1 = 30$. Output: **30×30**.
:::

::: faded-example
For a 64×64 input, 5×5 kernel, stride 1, padding 2 — what's the output shape?
:::

::: independent-practice
Given a 28×28 input, design a `Conv2d` that outputs 14×14. State your kernel, stride, and padding.
:::
```

### `meta` reference

**Lesson `meta`** carries:
- `role` — open string, conventional values `opener`, `concept`, `story`, `math`, `tutorial`, `practice`, `hands_on`, `bonus`. Renders as a small chip in the sidebar.
- `hook` — `{ tagline, image_prompt? }`. The tagline renders as a quiet italic line above the lesson title.
- `introduces` / `reinforces` — lists of learning-item ids (open vocabulary; useful for downstream tooling).
- `duration_minutes` — integer; aggregated across the curriculum into `total_duration_minutes` and surfaced on the index page as `≈ Xh Ym`.

**Module `meta`** carries:
- `theme`, `big_problem`, `objectives`, `experiential_summary`, `target_audience`. Rendering of these is deferred; today they pass through to `curriculum.json` for downstream tooling.

**Curriculum `meta`** (Story J.h) carries:
- `target_audience`, `objectives`, `prerequisites`. Curriculum-wide pedagogical context — passed through to `curriculum.json` for downstream tooling, no rendering in v1.

### Custom `meta` fields

All three meta models — `CurriculumMeta`, `ModuleMeta`, `LessonMeta` (and the `hook` sub-block) — accept undeclared fields. Authors can attach genre-specific data alongside the declared ones at any layer without a schema change:

```yaml
version: "1.0.0"
curriculum:
  title: "Convolutional Neural Networks"
  meta:
    # Declared fields — type-checked:
    target_audience: "Working software engineers new to ML"
    objectives: ["Explain backprop", "Build a conv net"]

    # Author-defined extras — accepted as-is:
    pedagogical_approach: "spiral"
    estimated_total_minutes: 480

  modules:
    - id: mod-01
      title: "Why convolutions exist"
      meta:
        # Declared + extras compose the same way at module level:
        theme: "Why convolutions exist"
        objectives: ["Explain weight sharing"]
        curriculum_thread: "vision"          # author-defined extra

      lessons:
        - id: lesson-01
          title: "What is a convolution?"
          meta:
            # Declared fields — type-checked:
            role: opener
            introduces: [receptive_field]
            duration_minutes: 15

            # Author-defined extras — accepted as-is:
            covers: ["pe:hubel-wiesel", "hi:receptive-field-discovery"]
            difficulty: intermediate
            prerequisites: [lesson-00]
            author_notes: "Revisit after the kernel-size deep-dive lands."
          content_blocks:
            - type: text
              ref: content/mod-01/lesson-01.md
```

The escape hatch is scoped to `meta` (and `hook`) only. `CurriculumDef`, `Module`, `Lesson`, and the top-level `curriculum:` mapping itself reject unknown fields — so a misplaced `difficulty:` at the *lesson* level (sibling of `meta`, not nested inside it) still fails the build. Same for a stray `pedagogical_approach:` at the *curriculum* level outside the `meta:` block. The strictness that catches typos like a mis-nested `sequential: true` is preserved everywhere outside the `meta` blocks at all three layers.

Declared fields keep their normal type checks; only undeclared keys ride through unvalidated. Extras pass through unchanged into the generated `curriculum.json`, so downstream tooling (custom Svelte components, analytics dashboards, external reports) can read them without any further pipeline wiring.

### Strict project-specific extensions

The permissive `extra="allow"` posture above is too loose for LLM-driven authoring — an LLM that writes `prequisites` instead of `prerequisites` will pass validation, lose the data in `curriculum.json`, and break downstream consumers silently. The schema-extensions mechanism is an opt-in tightening: a project drops `learningfoundry-schema-extensions.yml` next to its `curriculum.yml`, declares the additional fields it cares about, and learningfoundry flips the `meta` blocks from "allow anything" to "reject anything not on the list."

Minimal example — `learningfoundry-schema-extensions.yml`:

```yaml
version: "1"
lesson_meta:
  fields:
    covers:        { type: "list[str]", default: [] }
    difficulty:    { type: enum, values: [intro, intermediate, advanced] }
    prerequisites: { type: "list[str]", default: [] }
```

> **YAML gotcha — `list[T]` inside a flow mapping must be quoted.** PyYAML parses `{ type: list[str] }` (unquoted) as the scalar `list` followed by a flow sequence `[str]` and fails with `expected ',' or '}', but got '['`. Two safe forms: quote the scalar — `{ type: "list[str]" }` — or use block style on its own line (`type: list[str]` with no surrounding braces). `learningfoundry validate` recognises this failure signature and appends a hint to the error message, so a build hitting it surfaces the fix without the author needing to recognise the PyYAML quirk first.

With this file in place:

```yaml
# curriculum.yml lesson — typo `prequisites` instead of `prerequisites`
meta:
  difficulty: intermediate
  prequisites: [lesson-00]   # ❌ now a build error
```

`learningfoundry validate` exits non-zero with a message naming the offending field (the Pydantic `ValidationError` puts `prequisites` directly in the output). Without the extensions file, the same typo silently passes — the original `extra="allow"` posture is preserved.

**Supported field types:** `str`, `int`, `bool`, `list[str]`, `enum` (with `values:` list), `object` (single nested object), `list[object]` (list of nested objects). Each scalar field accepts `required: bool` (default `true`) and `default:` (presence makes the field optional). Per-model `extra: allow` overrides the default `extra: forbid` if you want one meta layer tight and another loose during a staged rollout.

**Nested objects** — declare a structured dict by giving it `type: object` and its own inner `fields:` block. Authors recurse to arbitrary depth: an `object` field inside an `object` field works without further ceremony. `extra: forbid` is the default at every nesting level (a typo three layers deep still fails the build); per-object `extra: allow` opts that one layer back into the permissive posture.

```yaml
version: "1"
curriculum_meta:
  fields:
    citations:
      type: list[object]
      default: []                        # the only valid default — non-empty lists are rejected at load time
      fields:
        key:      { type: str }
        apa:      { type: str }
        doi:      { type: str, required: false }
        verified: { type: bool }
        role:     { type: str, required: false }
        note:     { type: str, required: false }
lesson_meta:
  fields:
    provenance:
      type: object
      required: false                    # whole object is optional; `default:` is not supported on `object` — use `required: false`
      fields:
        author:  { type: str }
        license: { type: str }
```

With those declarations, a lesson that writes `provanance:` (instead of `provenance:`) at the lesson level — or `verfied:` (instead of `verified:`) inside a citation entry — fails the build with the field path in the error (e.g. `citations.0.verfied`). Mistyped *nested* fields are caught with the same strictness as mistyped top-level ones.

For `object`, only `required: false` makes the whole object optional; declaring `default:` on an `object` is rejected at load time (object literal defaults are a footgun — they share mutable state across instances and silently desynchronize from inner schema changes). For `list[object]`, only `default: []` is meaningful; any non-empty list default is rejected at load time.

**File-path resolution order** (highest precedence first):

1. `--schema-extensions PATH` CLI flag on `build`, `validate`, `preview`.
2. `[tool.learningfoundry] schema_extensions = "..."` in `pyproject.toml` next to the curriculum.
3. Auto-discovery: `learningfoundry-schema-extensions.yml` next to the curriculum.
4. None — base `extra="allow"` behaviour, no enforcement.

The extensions file is itself strict-validated, so a typo there (e.g. `defalt:` instead of `default:`) fails at load time naming the field, not silently degrading the contract the file is supposed to tighten. The mechanism applies to all three meta layers (`curriculum_meta`, `module_meta`, `lesson_meta`) independently — declaring one does not require declaring the others.

### Tutorial scaffold directives

Three named container directives:

- `::: worked-example` — filled gray card. Use it for fully worked solutions.
- `::: faded-example` — outlined dim card. Use it for similar problems with reduced scaffolding.
- `::: independent-practice` — amber-highlighted challenge prompt. Use it for problems the learner solves on their own.

Inner markdown (headings, lists, math, emphasis) renders normally inside each directive. Unknown directive names pass through untouched at render time. Static styling only — no progressive-reveal interactivity in v1. An unbalanced known-name block (open with no `:::` close on its own line) fails the build with the lesson location, so the failure mode is loud rather than rendered as silent prose.

### Embedding a quizazz assessment

[quizazz](https://github.com/pointmatic/quizazz) is the default assessment provider — interactive question/answer blocks with scoring, review, and progress persistence. This subsection walks the full author flow once; cross-links point at the canonical sources for the parts owned by quizazz (assessment-YAML schema, vendor component behavior).

**What you need.** `pip install learningfoundry[quizazz]` installs the Python builder side (the [`quizazz` PyPI package](https://pypi.org/project/quizazz/)) so `learningfoundry build` can compile assessment YAML at build time. The SvelteKit template already declares [`@pointmatic/quizazz`](https://www.npmjs.com/package/@pointmatic/quizazz) as a runtime dependency, so the vendor component is wired into the generated app automatically — no separate `npm` / `pnpm install` step for the author.

**Where the assessment content lives.** One `*.yml` file per assessment, conventionally under an `assessments/` directory inside your curriculum source tree. **The assessment-YAML schema is owned by quizazz** — for the authoritative format (question types, answer counts, weighted scoring rules, review options), see [quizazz README](docs/specs/quizazz/README.md) and [quizazz features.md](docs/specs/quizazz/features.md). Do not consult learningfoundry's docs for the schema; this README only covers how learningfoundry **references** quizazz YAML files.

**Two ways to embed.** Pick based on the pedagogical role:

1. **Inline in a lesson** — add a `type: assessment` entry to a lesson's `content_blocks`. Use this for in-lesson knowledge checks that interrupt the reading flow at a specific point.
2. **At module level** — add an entry to the module's `assessments[]` array with a `position`. Use this for module-level pre / practice / post placements that bracket multiple lessons. See the [Assessments](#assessments) subsection below for the full positional vocabulary.

Both shapes select quizazz via `source: quizazz`; both accept an optional `pass_threshold`. The schema of the *referenced YAML files* is identical regardless of which embedding shape points at them — quizazz doesn't know or care which one called.

**Worked example.** A `curriculum.yml` snippet using both shapes against the same provider:

```yaml
modules:
  - id: mod-01

    # Module-level: opens the module with a pre-assessment, closes with a graded post
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
      - id: lesson-02
        content_blocks:
          - type: text
            ref: content/mod-01/lesson-02.md
          # Content-block-level: a quick check inside lesson 2
          - type: assessment
            source: quizazz
            ref: assessments/lesson-02-check.yml
            pass_threshold: 0.6
```

The referenced file (`assessments/lesson-02-check.yml`) is a standalone quizazz YAML file — its schema is described in [quizazz README](docs/specs/quizazz/README.md). A minimal one looks like:

```yaml
# See quizazz docs for the full schema (question types, answer counts, scoring rules).
quizName: "Lesson 2 — knowledge check"
questions:
  - question: "Which kernel produces a vertical-edge detector?"
    correct: "[[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]"
    ridiculous: "[[1, 1, 1], [1, 1, 1], [1, 1, 1]]"
    # ...remaining answer slots per quizazz's schema
```

**What the learner sees.** At build time, learningfoundry's `QuizazzProvider` invokes quizazz's `compile_assessment` API on each referenced YAML, embeds the compiled manifest into the generated SvelteKit app's `curriculum.json`, and the frontend mounts the vendor `<QuizBlock>` component to render the assessment. Each completed assessment fires a score event; learningfoundry persists scores to the in-browser SQLite. quizazz manages its own per-assessment IndexedDB database for per-question detail — the two storage layers are separate by design (see [quizazz consumer-dependency-spec.md](docs/specs/quizazz/consumer-dependency-spec.md) RR-1, RR-1a, RR-1b for the full contract).

**Module-level assessment routes (Story J.s, J.t).** A module-level `assessments[]` entry becomes a dedicated route at `/{moduleId}/assessment/{id}` — the `id` is the explicit `id:` if you supplied one, otherwise the role-based auto-gen (`pre`, `post`, `practice`, `practice-2`, …; see [Assessments](#assessments)). The sidebar renders each module-level row as a clickable `<button>` that navigates to its route, lights up an amber palette while the assessment is the active spot in the curriculum, and renders a grey `aria-disabled` style when locked by an upstream gate (see [Content locking](#content-locking)). Content-block-level assessments (`type: assessment` inside a lesson's `content_blocks`) stay inline within the lesson page — no separate route. The two persistence paths live in separate tables: content-block scores in `assessment_scores` keyed on global `assessmentRef`; module-level scores in `module_assessment_scores` keyed on `(moduleId, assessmentId)` so two modules referencing the same YAML don't collide.

**Pass-threshold gating.** Optional `pass_threshold: 0.0–1.0` on either embedding shape. Content-block-level: the assessment block fires its completion event upward only when `score / maxScore` clears the threshold, which gates lesson-completion progression in the sidebar. Module-level: the gate is broader — items after the assessment in the module flow lock until a recorded passed score, and the next sequential module stays locked until the previous module's post-assessment is passed (Story J.v). `role: pre` is the soft-gate exception — see [Content locking](#content-locking) and the `pass_threshold` bullet under [Assessments](#assessments).

**Common gotchas:**

- **Refs resolve relative to `--base-dir`.** The `ref:` path is *not* relative to the lesson markdown or to `curriculum.yml`; it resolves under whatever directory `learningfoundry build --base-dir <path>` was given. The default `--base-dir` is the directory containing `curriculum.yml`.
- **`learningfoundry[quizazz]` is an optional extra.** Plain `pip install learningfoundry` does not pull in quizazz; running `learningfoundry build` on a curriculum that references `source: quizazz` will fail with an `ImportError`. Install the extra explicitly.
- **`<QuizBlock>` is a vendor component name** — preserved at the vendor boundary. A future "consistency rename" pass that tried to rename it to `<AssessmentBlock>` (learningfoundry's wrapper component) would break the integration silently. See the "Vendor terminology stops at the vendor boundary" note in [project-essentials.md](docs/specs/project-essentials.md).

### Assessments

Each module declares an `assessments[]` array; each entry carries:

- `id` — **optional** (Story J.r, v0.75.0+). A stable per-assessment identifier within the module, used by the route layer and the progress store. **When omitted, learningfoundry auto-generates it from `role`:** the first assessment with a given role takes the bare role (`pre`, `post`, `practice`), and subsequent same-role entries append a 1-based counter (`practice-2`, `practice-3`). Explicit ids are honoured verbatim — typical reasons to set one are to opt into a more descriptive URL segment (`diagnostic` instead of `pre`) or to lock the id against author-order shuffles. Intra-module uniqueness is enforced at build time, so duplicate explicit ids — or an explicit id that happens to collide with an auto-gen result — fail loudly with the module id and offending id.
- `role` — open string. Conventional values: `pre`, `practice`, `post`, `checkpoint`. Surfaces as a capitalized label in the sidebar (`Pre Assessment`, `Practice Assessment`, …).
- `position` — discriminated union:
  - `before_lessons` — anchors at the start of the module flow.
  - `after_lessons` — anchors at the end.
  - `{ before_lesson: <lesson-id> }` — anchors immediately before the named lesson.
  - `{ after_lesson: <lesson-id> }` — anchors immediately after.
- `source`, `ref` — provider + path, same shape as `assessment` content blocks.
- `pass_threshold` — optional `0.0`–`1.0`. Surfaces as a `"X% to pass"` annotation on the assessment row when set. **Gating semantics (Story J.v, v0.79.0+):**
  - On any assessment with `role` other than `pre`, a `pass_threshold` makes that assessment a gate — items appearing after it in the module flow (lessons and later assessments) stay locked until a recorded score meets the threshold. A module's sequential next-module unlock consumes the same gate, so an unpassed `after_lessons` post-assessment keeps the next module locked even when every lesson is complete.
  - On `role: pre`, `pass_threshold` is **non-gating** by convention — pre-assessments are diagnostic, and locking a learner out of lesson 1 behind a test they haven't earned the right to skip yet defeats the purpose. Scores are still recorded; they just don't block progression. Authors who want hard pre-gating use `role: practice` with `position: { before_lesson: <lesson-id> }`.
  - Assessments without `pass_threshold` are informational — they record scores but never gate.

Lesson-anchored refs (`before_lesson` / `after_lesson`) are validated against the module's `lessons` at build time — typing a wrong lesson id fails the build with the module id, role, and unknown lesson id.

**Worked example — `id` auto-gen vs. explicit:**

```yaml
assessments:
  - role: pre               # auto-gen id = "pre"
    position: before_lessons
    source: quizazz
    ref: assessments/mod-01-diag.yml
  - role: practice          # auto-gen id = "practice"
    position: { before_lesson: lesson-02 }
    source: quizazz
    ref: assessments/mod-01-warmup.yml
  - role: practice          # auto-gen id = "practice-2"
    position: { after_lesson: lesson-03 }
    source: quizazz
    ref: assessments/mod-01-checkpoint.yml
  - id: final               # explicit id overrides auto-gen
    role: post
    position: after_lessons
    pass_threshold: 0.8
    source: quizazz
    ref: assessments/mod-01-final.yml
```

### Migrating from `pre_assessment` / `post_assessment` (pre-v0.68.0)

`Module.pre_assessment` and `Module.post_assessment` were removed in v0.68.0 (Story J.e). To migrate an external curriculum that pre-dates the cutover, replace each block with a single `assessments[]` entry using the `before_lessons` or `after_lessons` position:

```yaml
# BEFORE (v0.67.x and earlier)
pre_assessment:
  source: quizazz
  ref: assessments/mod-01-pre.yml
post_assessment:
  source: quizazz
  ref: assessments/mod-01-post.yml

# AFTER (v0.68.0+)
assessments:
  - role: pre
    position: before_lessons
    source: quizazz
    ref: assessments/mod-01-pre.yml
  - role: post
    position: after_lessons
    source: quizazz
    ref: assessments/mod-01-post.yml
```

Strict-mode Pydantic rejects an unmigrated `pre_assessment` / `post_assessment` field with a `ValidationError` naming the offending field, so the build fails loudly until the migration is complete. There is no compatibility shim or deprecation warning — pre-1.0 makes the clean break acceptable.

---

## Content locking

Control access to modules and lessons with three orthogonal mechanisms:

1. **Per-module `locked`** — explicit `true`/`false` override; trumps everything.
2. **Sequential locking** (`locking.sequential` + `locking.lesson_sequential`) — when on, modules / lessons must be completed in order. Hierarchy: curriculum-level config beats global config (see Configuration File below).
3. **Assessment-threshold gating (Story J.v)** — a module-level assessment with `pass_threshold` set (and `role` other than `pre`) gates every item appearing after it in the module flow. The sequential rule consumes the same gate, so an unpassed `after_lessons` post-assessment keeps the next module locked even when every lesson is complete. `role: pre` is non-gating by convention — pre-assessments are diagnostic, not gates; authors who want hard pre-gating use `role: practice` with `position: { before_lesson: <id> }`.

```yaml
curriculum:
  locking:
    sequential: true            # modules must be completed in order
    lesson_sequential: false    # lessons within a module are free-order

  modules:
    - id: mod-01
      locked: false             # always accessible regardless of sequential
      lessons:
        - id: lesson-01
          unlock_module_on_complete: true   # completing this unlocks siblings + next module
          content_blocks:
            # See "Embedding a quizazz assessment" above for the full author flow
            - type: assessment
              source: quizazz
              ref: assessments/assessment.yml
              pass_threshold: 0.7           # 70% required to count as passed

      # Module-level post-assessment with a threshold — gates the next module
      # (Story J.v). An unpassed score here keeps `mod-02` locked even after
      # every lesson in `mod-01` is complete.
      assessments:
        - role: post
          position: after_lessons
          source: quizazz
          ref: assessments/mod-01-post.yml
          pass_threshold: 0.7

    - id: mod-02
      lessons: [...]
```

`unlock_module_on_complete` is useful for "gateway" lessons — a single content-block assessment that, once passed, opens the rest of the module and the next one. It composes with assessment-threshold gating: an `after_lessons` post-assessment with `pass_threshold` still has to pass before the next module unlocks, even if the gateway lesson short-circuited the in-module lesson requirements.

---

## Configuration File

An optional config file can set defaults for logging and locking. The CLI always takes precedence.

**Default location:** `~/.config/learningfoundry/config.yml`

```yaml
logging:
  level: INFO      # DEBUG | INFO | WARNING | ERROR
  output: stdout   # stdout | stderr

locking:
  sequential: false          # default for all curricula on this machine
  lesson_sequential: false
```

Pass a custom config location with `-c / --config`.

---

## Development Setup

### Prerequisites

- Python 3.12+
- [pyve](https://github.com/pointmatic/pyve) (virtual env manager used in this project)
- pnpm 9+ and Node.js 18+

### Setup

```bash
git clone https://github.com/pointmatic/learningfoundry.git
cd learningfoundry

# Create the Python environment and install the package in editable mode
pyve init
pip install -e .

# Create the test runner environment and install dev dependencies
pyve testenv --init
pyve testenv --install -r requirements-dev.txt
```

### Running Tests

```bash
# Fast unit + integration tests (~2 min)
pyve test

# End-to-end SvelteKit smoke tests (requires pnpm, ~15 s extra)
pyve test tests/test_smoke_sveltekit.py -v
```

### Linting and Type Checking

```bash
pyve testenv run ruff check .
pyve testenv run mypy src/
```

### Project Structure

```
learningfoundry/
├── src/learningfoundry/
│   ├── cli.py              # Click CLI entry point
│   ├── config.py           # Configuration loading
│   ├── exceptions.py       # Exception hierarchy
│   ├── generator.py        # SvelteKit project generator
│   ├── integrations/       # Assessment / exercise / visualization providers
│   ├── logging_config.py   # Logging setup
│   ├── parser.py           # YAML parser + version dispatch
│   ├── pipeline.py         # run_build / run_validate / run_preview
│   ├── resolver.py         # Content reference resolver
│   └── schema_v1.py        # Pydantic v1 curriculum schema
├── sveltekit_template/     # SvelteKit app template (copied on build)
├── tests/                  # pytest test suite
├── requirements-dev.txt    # Dev dependencies
└── pyproject.toml          # Build config, ruff, mypy, pytest settings
```

---

## Maintenance

Dependency updates are tracked by [GitHub Dependabot](https://docs.github.com/en/code-security/dependabot) via [.github/dependabot.yml](.github/dependabot.yml):

- **Weekly grouped PRs** for patch and minor updates across three ecosystems — `pip` (Python: `pyproject.toml`, `requirements-dev.txt`), `npm` (SvelteKit template at `src/learningfoundry/sveltekit_template/`), and `github-actions` (`.github/workflows/`). Patch+minor updates are bundled per ecosystem into a single PR to keep noise manageable; major updates land as individual PRs for deliberate review.
- **Security advisories file PRs immediately**, independent of the weekly schedule — the security signal is what we actually want from this wiring.
- `@types/node` major bumps are explicitly ignored: we pin to the active LTS major; odd-numbered "Current" releases are not appropriate auto-bump targets.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
