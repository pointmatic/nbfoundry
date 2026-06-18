# tech-spec.md -- learningfoundry (Python 3.12 + SvelteKit)

This document defines **how** the `learningfoundry` project is built -- architecture, module layout, dependencies, data models, API signatures, and cross-cutting concerns.

For requirements and behavior, see [`features.md`](features.md). For the implementation plan, see [`stories.md`](stories.md). For project-specific must-know facts (workflow rules, architecture quirks, hidden coupling), see [`project-essentials.md`](project-essentials.md) — `plan_tech_spec` populates it after this document is approved. For the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), see [`docs/project-guide/go.md`](../project-guide/go.md) — re-read it whenever the mode changes or after context compaction.

---

## Runtime & Tooling

| Concern | Tool | Version / Notes |
|---------|------|-----------------|
| **Language** | Python | 3.12.13 |
| **Environment manager** | pyve | venv backend; `.pyve/config` at project root |
| **Package manifest** | `pyproject.toml` | PEP 517/518, build backend: `hatchling` |
| **Package installer** | pip | Within venv managed by pyve |
| **Linter / formatter** | Ruff | Replaces flake8 + isort + black |
| **Type checker** | mypy | Strict mode (`--strict`) |
| **Test runner** | pytest | Standard |
| **Frontend framework** | SvelteKit | Latest stable; `@sveltejs/adapter-static` for static output |
| **Frontend language** | TypeScript | Strict mode |
| **Frontend styling** | Tailwind CSS 4.x | Utility-first |
| **Node runtime** | Node.js | Latest stable LTS |
| **Node package manager** | pnpm | Fast, workspace-aware |
| **Client-side DB** | sql.js (WASM) | SQLite compiled to WASM, persisted to IndexedDB |
| **Build tool (frontend)** | Vite | Via SvelteKit |

---

## Dependencies

### Python Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pyyaml` | `>=6.0` | Curriculum YAML parsing |
| `pydantic` | `>=2.0` | Schema validation and data models for curriculum structure |
| `click` | `>=8.1` | CLI framework |

### Python Development Dependencies

| Package | Purpose |
|---------|---------|
| `pytest` | Test runner |
| `ruff` | Linting and formatting |
| `mypy` | Static type checking |

### Python Optional / Integration Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `quizazz` | `>=0.1` | Assessment YAML → JSON manifest compilation (first-party) |

nbfoundry is not yet published. learningfoundry defines an `ExerciseProvider` protocol; a stub implementation ships for v1. The real nbfoundry integration will be added when nbfoundry is available as a package.

### SvelteKit App Runtime Dependencies (`package.json`)

| Package | Purpose |
|---------|---------|
| `svelte` | UI framework |
| `@sveltejs/kit` | App framework |
| `@sveltejs/adapter-static` | Static site generation |
| `sql.js` | SQLite WASM for client-side progress database |
| `lucide-svelte` | Icon library |

### SvelteKit App Dev Dependencies (`package.json`)

| Package | Purpose |
|---------|---------|
| `typescript` | Type checking |
| `tailwindcss` | Utility CSS framework |
| `@tailwindcss/vite` | Tailwind Vite plugin |
| `vitest` | Unit/integration testing |
| `eslint` | Linting |
| `prettier` | Code formatting |
| `prettier-plugin-svelte` | Svelte formatting support |

### System Dependencies

| Dependency | Required | Notes |
|------------|----------|-------|
| Node.js LTS | Yes | For SvelteKit build and preview |
| pnpm | Yes | Node package manager |
| pyve | Yes | Python environment management |

---

## Package Structure

```
learningfoundry/
├── pyproject.toml                          # Package metadata, dependencies, hatchling build
├── LICENSE                                 # Apache-2.0
├── README.md
├── .tool-versions                          # asdf/mise version pins (python 3.12.13)
├── .pyve/
│   └── config                              # pyve configuration (venv backend)
│
├── src/
│   └── learningfoundry/                    # Installable Python package
│       ├── __init__.py                     # Package version, public API exports
│       ├── py.typed                        # PEP 561 marker
│       ├── cli.py                          # Click CLI entry point (build, validate, preview)
│       ├── config.py                       # Settings model + config loading + precedence merging
│       ├── parser.py                       # YAML curriculum parser + version dispatch
│       ├── schema_v1.py                    # Pydantic models for curriculum YAML v1 schema
│       ├── resolver.py                     # Content resolution: markdown, video URLs, integrations
│       ├── asset_resolver.py               # Markdown image asset detection, hashing, and URL rewriting
│       ├── pipeline.py                     # Pipeline orchestrator: parse → resolve → generate
│       ├── generator.py                    # SvelteKit project generation from resolved curriculum
│       ├── integrations/
│       │   ├── __init__.py
│       │   ├── protocols.py                # AssessmentProvider, ExerciseProvider, and VisualizationProvider protocols
│       │   ├── quizazz.py                  # quizazz integration (delegates to quizazz.compile_assessment)
│       │   ├── nbfoundry_stub.py           # Stub ExerciseProvider for v1
│       │   └── d3foundry_stub.py           # Stub VisualizationProvider for v1
│       ├── exceptions.py                   # Project-specific exception hierarchy
│       └── logging_config.py              # Logging setup (stdlib logging, structured formatters)
│
├── sveltekit_template/                     # Bundled SvelteKit project template
│   ├── package.json                        # pnpm dependencies
│   ├── svelte.config.js                    # SvelteKit config with adapter-static
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── static/
│   │   └── sql-wasm.wasm                   # sql.js WASM binary
│   └── src/
│       ├── app.html                        # SvelteKit shell
│       ├── app.css                         # Tailwind imports + global styles
│       ├── lib/
│       │   ├── types/
│       │   │   └── index.ts                # TypeScript type definitions (curriculum, progress)
│       │   ├── db/
│       │   │   ├── index.ts                # Barrel export
│       │   │   ├── database.ts             # sql.js init, IndexedDB persistence, schema
│       │   │   └── progress.ts             # Progress CRUD: lesson completion, assessment scores, exercise status
│       │   ├── stores/
│       │   │   └── curriculum.ts           # Svelte stores for curriculum state and navigation
│       │   ├── components/
│       │   │   ├── ModuleList.svelte       # Module navigation sidebar
│       │   │   ├── LessonList.svelte       # Lesson list within a module
│       │   │   ├── LessonView.svelte       # Lesson content renderer (dispatches content blocks)
│       │   │   ├── ContentBlock.svelte     # Content block dispatcher (text, video, assessment, exercise, visualization)
│       │   │   ├── TextBlock.svelte        # Rendered markdown content (end-of-block sentinel drives `textcomplete`)
│       │   │   ├── VideoBlock.svelte       # YouTube embed
│       │   │   ├── AssessmentBlock.svelte  # Inline assessment (consumes quizazz manifest JSON)
│       │   │   ├── ExerciseBlock.svelte    # Model-training exercise (consumes nbfoundry output)
│       │   │   ├── VisualizationBlock.svelte # Data visualization (consumes d3foundry output)
│       │   │   ├── PlaceholderBlock.svelte # Placeholder for future interactive content
│       │   │   ├── ProgressDashboard.svelte # Per-module completion, assessment scores overview
│       │   │   ├── Navigation.svelte       # Prev/next lesson navigation
│       │   │   └── ProgressBar.svelte      # Visual progress indicator
│       │   └── utils/
│       │       └── markdown.ts             # Markdown-to-HTML rendering utility
│       └── routes/
│           ├── +layout.svelte              # App shell with sidebar navigation
│           ├── +page.svelte                # Landing / progress dashboard
│           └── [module]/
│               ├── [lesson]/
│               │   └── +page.svelte        # Lesson page rendering content blocks
│               └── assessment/
│                   └── [id]/
│                       └── +page.svelte    # Module-level assessment page (Story J.s)
│
├── tests/
│   ├── conftest.py                         # Shared fixtures (sample YAML, temp dirs)
│   ├── test_parser.py                      # YAML parsing: valid, missing version, bad version, dupes
│   ├── test_schema_v1.py                   # Pydantic model validation for v1 schema
│   ├── test_resolver.py                    # Content resolution: markdown, URLs, integration mocks
│   ├── test_pipeline.py                    # End-to-end pipeline orchestration
│   ├── test_generator.py                   # SvelteKit output structure verification
│   ├── test_config.py                      # Config precedence: CLI > file > defaults
│   ├── test_cli.py                         # CLI integration tests (build, validate, preview)
│   └── test_integrations/
│       ├── test_quizazz.py                 # quizazz integration (mocked builder calls)
│       ├── test_nbfoundry_stub.py          # Stub exercise provider behavior
│       └── test_d3foundry_stub.py          # Stub visualization provider behavior
│
└── docs/
    ├── project-guide/                      # project-guide configuration and templates
    └── specs/
        ├── concept.md
        ├── features.md
        ├── tech-spec.md                    # This document
        ├── stories.md
        └── project-essentials.md
```

---

## Filename Conventions

| File Type | Convention | Examples |
|-----------|------------|----------|
| **Documentation** (Markdown) | Hyphens | `tech-spec.md`, `getting-started.md` |
| **Workflow files** | Hyphens | `deploy-docs.yml`, `run-tests.yml` |
| **Python modules** | Underscores (PEP 8) | `schema_v1.py`, `logging_config.py` |
| **Python packages** | Underscores (PEP 8) | `learningfoundry/`, `integrations/` |
| **TypeScript / Svelte** | PascalCase (components), camelCase (modules) | `LessonView.svelte`, `database.ts` |
| **Configuration files** | Hyphens or dots | `pyproject.toml`, `.gitignore`, `svelte.config.js` |

---

## Key Component Design

### `cli.py` — Click CLI Entry Point

```python
import click

@click.group()
@click.option("--config", type=click.Path(exists=True), default=None,
              help="Path to config file (default: ~/.config/learningfoundry/config.yml)")
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
              default=None, help="Override log level")
def cli(config: str | None, log_level: str | None) -> None:
    """learningfoundry — turn a YAML curriculum into a SvelteKit learning app."""
    ...

@cli.command()
@click.argument("curriculum", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default="./build/",
              help="Output directory for the generated SvelteKit project")
def build(curriculum: str, output: str) -> None:
    """Run the full pipeline: parse → resolve → generate SvelteKit app."""
    ...

@cli.command()
@click.argument("curriculum", type=click.Path(exists=True))
def validate(curriculum: str) -> None:
    """Validate curriculum YAML without building."""
    ...

@cli.command()
@click.argument("curriculum", type=click.Path(exists=True))
@click.option("--port", type=int, default=5173, help="Dev server port")
@click.option("--output", "-o", type=click.Path(), default="./build/",
              help="Output directory for the generated SvelteKit project")
def preview(curriculum: str, port: int, output: str) -> None:
    """Build and launch a local dev server."""
    ...
```

### `config.py` — Settings Model

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class LoggingConfig:
    level: str = "INFO"           # DEBUG | INFO | WARNING | ERROR
    output: str = "stdout"        # stdout | <file path>

@dataclass
class AppConfig:
    logging: LoggingConfig = field(default_factory=LoggingConfig)

def load_config(
    config_path: Path | None = None,
    cli_overrides: dict[str, str] | None = None,
) -> AppConfig:
    """
    Load configuration with precedence:
      1. CLI flags (cli_overrides)
      2. Config file (config_path or ~/.config/learningfoundry/config.yml)
      3. Built-in defaults (dataclass defaults)

    Raises ConfigError on malformed YAML.
    Logs warnings for unknown keys (forward-compatible).
    """
    ...
```

### `parser.py` — YAML Curriculum Parser

```python
from pathlib import Path
from learningfoundry.schema_v1 import CurriculumV1

def parse_curriculum(yaml_path: Path) -> CurriculumV1:
    """
    Parse and validate a curriculum YAML file.

    1. Load raw YAML via PyYAML.
    2. Extract top-level `version` field.
    3. Dispatch to the correct schema/parser based on major version.
    4. Validate via Pydantic model.
    5. Return typed, validated curriculum object.

    Raises:
        CurriculumVersionError: Missing or unsupported version.
        CurriculumValidationError: Schema validation failure (with field path detail).
    """
    ...

def _dispatch_parser(major_version: int):
    """Select parser/schema for the given major version.
    Currently supports: 1 → schema_v1.CurriculumV1.
    Raises CurriculumVersionError for unsupported versions."""
    ...
```

### `schema_v1.py` — Pydantic Models (Curriculum YAML v1)

```python
from pydantic import BaseModel, field_validator, model_validator
from pathlib import Path

class BeforeLesson(BaseModel):
    before_lesson: str              # Lesson id this assessment sits immediately before

class AfterLesson(BaseModel):
    after_lesson: str               # Lesson id this assessment sits immediately after

# Discriminated union — Pydantic resolves variants by shape (Story J.e).
AssessmentPosition = (
    Literal["before_lessons", "after_lessons"] | BeforeLesson | AfterLesson
)

class AssessmentDefinition(BaseModel):
    """A single assessment bound to a module at a declared position.
    Replaces legacy `pre_assessment` / `post_assessment` fields (Story J.e)."""
    id: str | None = None           # Story J.r — auto-gen from role if omitted:
                                    #   1st of role R → "R"; Nth (N>1) → "R-N"
                                    #   (e.g. pre, post, practice, practice-2)
    role: str                       # Open string: pre|practice|post|checkpoint|...
    position: AssessmentPosition
    source: str                     # "quizazz"
    ref: str                        # Path to assessment YAML file
    pass_threshold: float | None = None  # 0.0–1.0; recorded but not enforced in v1

class TextBlock(BaseModel):
    type: str = "text"
    ref: str                        # Path to markdown file

class VideoBlock(BaseModel):
    type: str = "video"
    url: str
    provider: str = "youtube"              # Literal["youtube"] today; extend per player
    extensions: dict = {}                  # Player-specific (chapters, transcripts, …)

    @model_validator(mode="after")
    def validate_url_for_provider(self):
        """YouTube URL validation when provider is youtube."""
        ...

class AssessmentBlock(BaseModel):
    type: str = "assessment"
    source: str                     # "quizazz"
    ref: str                        # Path to quizazz assessment YAML
    pass_threshold: float = 0.0     # 0.0–1.0; minimum score ratio for completion

class ExerciseBlock(BaseModel):
    type: str = "exercise"
    source: str                     # "nbfoundry"
    ref: str                        # Path to nbfoundry exercise YAML

class VisualizationBlock(BaseModel):
    type: str = "visualization"
    source: str                     # "d3foundry"
    ref: str                        # Path to d3foundry visualization YAML

ContentBlock = TextBlock | VideoBlock | AssessmentBlock | ExerciseBlock | VisualizationBlock

class Hook(BaseModel):
    """Opening hook for a lesson. ``extra='allow'`` (Phase J / J.a)."""
    tagline: str
    image_prompt: str | None = None

class LessonMeta(BaseModel):
    """Pedagogical metadata on a lesson. ``extra='allow'``."""
    role: str | None = None             # opener|concept|story|math|tutorial|practice|hands_on|bonus
    hook: Hook | None = None
    introduces: list[str] = []
    reinforces: list[str] = []
    duration_minutes: int | None = None

class ModuleMeta(BaseModel):
    """Pedagogical metadata on a module. ``extra='allow'``."""
    theme: str | None = None
    big_problem: str | None = None
    objectives: list[str] = []
    experiential_summary: str | None = None
    target_audience: str | None = None

class CurriculumMeta(BaseModel):
    """Pedagogical metadata on a curriculum as a whole. ``extra='allow'``
    (Phase J / J.h)."""
    target_audience: str | None = None
    objectives: list[str] = []
    prerequisites: list[str] = []

class Lesson(BaseModel):
    id: str
    title: str
    unlock_module_on_complete: bool = False  # Unlock siblings + next module on complete
    meta: LessonMeta | None = None      # Phase J pedagogical metadata; passed through verbatim
    content_blocks: list[ContentBlock]

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """IDs must be non-empty, lowercase, alphanumeric + hyphens."""
        ...

class Module(BaseModel):
    id: str
    title: str
    description: str = ""
    locked: bool | None = None      # None = inherit from locking config
    meta: ModuleMeta | None = None  # Phase J pedagogical metadata; passed through verbatim
    assessments: list[AssessmentDefinition] = []  # Phase J / J.e — replaces pre/post fields
    lessons: list[Lesson]

    @model_validator(mode="after")
    def check_has_lessons(self) -> "Module":
        """Module must contain at least one lesson."""
        ...

    @model_validator(mode="after")
    def autogen_assessment_ids(self) -> "Module":
        """Story J.r — fill in `id` for assessments that omit it
        (role-based, 1-based counter per role), then assert intra-module
        uniqueness of the final id set."""
        ...

    @model_validator(mode="after")
    def validate_assessment_lesson_refs(self) -> "Module":
        """Every BeforeLesson / AfterLesson ref must name a lesson that
        exists in self.lessons (Story J.e)."""
        ...

class LockingConfig(BaseModel):
    sequential: bool = False        # Module N+1 requires module N complete
    lesson_sequential: bool = False # Lesson N+1 requires lesson N complete

class CurriculumDef(BaseModel):
    title: str
    description: str = ""
    locking: LockingConfig = LockingConfig()
    meta: CurriculumMeta | None = None  # Phase J / J.h pedagogical metadata; passed through verbatim
    modules: list[Module]

    @model_validator(mode="after")
    def check_has_modules(self) -> "CurriculumDef":
        """Curriculum must contain at least one module."""
        ...

    @model_validator(mode="after")
    def check_unique_ids(self) -> "CurriculumDef":
        """All module IDs and lesson IDs must be unique."""
        ...

class CurriculumV1(BaseModel):
    version: str                    # Semver string, e.g. "1.0.0"
    curriculum: CurriculumDef
```

### `resolver.py` — Content Resolution

```python
from pathlib import Path
from learningfoundry.schema_v1 import CurriculumV1
from learningfoundry.integrations.protocols import AssessmentProvider, ExerciseProvider, VisualizationProvider

@dataclass
class ResolvedCurriculum:
    """Curriculum with all content references resolved to actual content."""
    version: str
    title: str
    description: str
    modules: list[ResolvedModule]
    assets: list[Asset] = field(default_factory=list)  # See asset_resolver.py

@dataclass
class ResolvedAssessment:
    """One resolved assessment, ready for emission (Story J.e). Order in
    `ResolvedModule.assessments` is canonical iteration order materialized
    by the resolver."""
    id: str                          # Story J.r — always populated after parse (auto-gen if omitted in YAML)
    role: str
    position: str | dict             # "before_lessons"|"after_lessons" | {"before_lesson": ...} | {"after_lesson": ...}
    source: str
    ref: str
    pass_threshold: float | None
    content: dict                    # Resolved quizazz manifest

@dataclass
class ResolvedModule:
    id: str
    title: str
    description: str
    assessments: list[ResolvedAssessment]   # Phase J / J.e — replaces pre/post
    lessons: list[ResolvedLesson]

@dataclass
class ResolvedLesson:
    id: str
    title: str
    content_blocks: list[ResolvedContentBlock]

@dataclass
class ResolvedContentBlock:
    block_type: str                  # "text" | "video" | "assessment" | "exercise" | "visualization"
    content: str | dict              # HTML string, URL, or integration output dict

def resolve_curriculum(
    curriculum: CurriculumV1,
    base_dir: Path,
    assessment_provider: AssessmentProvider,
    exercise_provider: ExerciseProvider,
    visualization_provider: VisualizationProvider,
) -> ResolvedCurriculum:
    """
    Resolve all content references in the parsed curriculum.

    - text blocks: read markdown file from base_dir / ref, lint
      tutorial-scaffold directives (see `directives.py`), then call
      asset_resolver.resolve_markdown_assets() to detect image references,
      hash them, and rewrite the markdown to absolute /content/<hash>/
      URLs. Image asset records aggregate onto ResolvedCurriculum.assets
      (deduped globally by content hash).
    - video blocks: validate YouTube URL, pass through
    - assessment blocks: delegate to assessment_provider
    - exercise blocks: delegate to exercise_provider
    - visualization blocks: delegate to visualization_provider

    Raises ContentResolutionError on missing files (markdown or referenced
    images), invalid URLs, or integration errors. Error messages always
    include the block location (module / lesson / block index).
    """
    ...
```

### `schema_extensions.py` — Project-Specific Meta Schema Extensions (Phase J / Story J.h)

The three `meta` Pydantic models (`CurriculumMeta`, `ModuleMeta`, `LessonMeta`) ride on `extra="allow"` so authors can attach custom fields without forcing a learningfoundry schema change. That permissive posture silently swallows phantom fields — LLM-driven authoring routinely invents `prequisites` or `cover` typos that pass validation, end up missing from `curriculum.json`, and break downstream consumers in subtle ways. `schema_extensions.py` is the opt-in tightening: when a project drops `learningfoundry-schema-extensions.yml` next to its `curriculum.yml`, learningfoundry synthesizes strict subclasses of the three meta models with the project's declared fields appended and `extra` flipped from `allow` to `forbid`.

**File contract (`SchemaExtensions` model):**

```yaml
version: "1"
curriculum_meta:
  extra: forbid                                  # default when section present
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

Seven supported `FieldDef` variants (`str`, `int`, `bool`, `list[str]`, `enum`, `object`, `list[object]`) form a Pydantic discriminated union on `type:`. Each scalar field accepts `required: bool` (default `true`) and `default:` (presence makes the field optional — a default implies the field is not required). Enum `values:` must be non-empty; enum `default:` (when given) must be one of the declared values.

`ObjectFieldDef` and `ListObjectFieldDef` (Story J.q) declare structured nested data via a recursive `fields: dict[str, FieldDef]` map that reuses the full grammar — including further nested `object` / `list[object]`. Both variants carry a per-object `extra: Literal["allow", "forbid"] = "forbid"` knob that mirrors the top-level `extra` switch at every nesting level. `ObjectFieldDef` declares no `default:` field (the `_StrictExtModel` base rejects `default:` written alongside `type: object` at load time — mutable object literals as defaults are a footgun); use `required: false` instead. `ListObjectFieldDef` accepts `default: list[Any] | None = None` but a `model_validator(mode="after")` rejects any value other than `[]` at load time. Because `ObjectFieldDef.fields` and `ListObjectFieldDef.fields` are forward references into the same `FieldDef` union that lists them, the module ends the variant declarations with explicit `ObjectFieldDef.model_rebuild()` / `ListObjectFieldDef.model_rebuild()` calls so the forward refs resolve at import time rather than failing in user code with a confusing Pydantic error.

`_build_object_model(name, fields_def, extra_mode)` is the recursive builder for nested object types: it walks the declared `fields:` map, recursing into nested `object` / `list[object]` via `_object_field_entry` and falling through to the existing scalar `_field_for` for every other variant. Synthesized model names follow a deterministic two-form scheme so Pydantic's `loc` paths stay readable: `<parent>__<field>` for a single nested `object`, and `<parent>__<field>__Item` for the element type of a `list[object]` (e.g. `CurriculumMeta__citations__Item`, `LessonMeta__provenance`). `_object_field_entry` is invoked from both `_extend_one` (the top-level extension dispatcher) and `_build_object_model` itself, so the same name scheme applies at every nesting depth.

The file itself is parsed through `SchemaExtensions` which inherits `extra="forbid"` — typos in the *extensions* file (e.g. `defalt:` instead of `default:`, `lesso_meta:` instead of `lesson_meta:`) fail at load time, so the file cannot silently degrade the validation contract it is supposed to tighten.

**`create_model` integration:**

`build_extended_meta_models(extensions)` returns `(curriculum_meta_cls, module_meta_cls, lesson_meta_cls)` — each either the base class (when no section is declared) or a synthesized subclass. Pydantic v2's `create_model` cannot accept both `__base__` and `__config__`, so each extended subclass is built in two steps: a `type()` invocation creates an intermediate subclass with the new `ConfigDict(extra=...)`, then `create_model(__base__=intermediate, **fields)` layers the declared fields on top. Enum fields use `Literal[tuple(values)]` rather than a synthesized `Enum` class — Pydantic's Literal error message names the field and lists allowed values, satisfying the story's error contract without extra wiring.

`build_extended_curriculum_v1(extensions)` chains the extension through the nested hierarchy: `Lesson → Module → CurriculumDef → CurriculumV1`. Each layer is rebuilt via `create_model` only when the meta type at that layer (or the list-of-extended-children at the layer above) actually changes — when no extensions are declared, the function returns `CurriculumV1` unchanged.

**Parser swap-in:**

`parse_curriculum(yaml_path, model_cls=...)` accepts an optional override of the dispatched Pydantic class. The version-dispatch check still runs (for its error-reporting side effect, so an unsupported `version:` still fails loudly even when the caller pre-built the model), but the override takes precedence for actual validation.

**File-path resolution order** (highest precedence first, implemented in `pipeline.resolve_schema_extensions_path`):

1. `--schema-extensions PATH` CLI flag on `build`, `validate`, `preview` (threaded into `run_build` / `run_validate` / `run_preview` as `schema_extensions_path`).
2. `[tool.learningfoundry] schema_extensions = "<relative-path>"` in a `pyproject.toml` next to the curriculum (read via `tomllib`).
3. Auto-discovery: `learningfoundry-schema-extensions.yml` next to the curriculum.
4. None — no extensions loaded; base `extra="allow"` behaviour preserved.

A malformed `pyproject.toml` is swallowed and resolution falls through to auto-discovery — a broken project metadata file should not prevent curriculum builds.

### `directives.py` — Tutorial-Scaffold Directive Lint (Phase J / Story J.d.2)

Story J.d.1 added a `marked` extension in `sveltekit_template/src/lib/utils/markdown-directives.ts` that recognises three named container directives in lesson markdown — `::: worked-example`, `::: faded-example`, `::: independent-practice` — and wraps each in a styled card at *render* time. The plugin's regex requires a matching `:::` close on its own line; an unclosed known directive silently fails to match and the whole block plus trailing prose renders oddly.

`directives.py` (Story J.d.2) closes the gap with a Python-side lint pass invoked from `resolver._resolve_text` after the markdown source is read but before image-asset resolution:

```python
KNOWN_DIRECTIVES: tuple[str, ...] = (
    "worked-example", "faded-example", "independent-practice",
)

def lint_directives(markdown: str, location: str) -> None:
    """Raise ContentResolutionError on unbalanced known-directive blocks.

    - Only the three known directive names are tracked. Unknown names
      (`::: tip`) pass through untouched — same render-time semantics.
    - Lines inside fenced code blocks (``` or ~~~) are skipped so prose
      that demonstrates the directive syntax is not mistaken for an
      actual directive.
    - A bare `:::` close with nothing on the known-directive stack is
      passed through silently (likely belongs to an unknown-name block).
    - An open without a matching close raises with the lesson location
      and the 1-based opening line number.
    """
    ...
```

The TS-side `KNOWN_DIRECTIVES` list and the Python-side constant are coupled by convention — adding a new directive name to one without the other produces either silent render-time failure (TS missing) or build-time false positives (Python missing).

### `asset_resolver.py` — Markdown Image Asset Resolution

Pure module that scans a lesson's markdown for image references and rewrites
them to absolute SvelteKit-compatible URLs. Designed to be called once per
text block by `resolver.py`; emits `Asset` records that the generator
consumes to copy files into the output `static/` directory.

```python
from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen=True)
class Asset:
    """A single asset that the generator must copy into the project."""
    source: Path           # Absolute path to the source file on disk
    dest_relative: str     # "content/<sha256[:12]>/<basename>" (forward-slash, URL-safe)

    @property
    def url_path(self) -> str:
        """The leading-slash URL the rewritten markdown references."""
        return "/" + self.dest_relative

def resolve_markdown_assets(
    markdown: str,
    markdown_path: Path,
) -> tuple[str, list[Asset]]:
    """
    Find every image reference in `markdown` and resolve it.

    Match forms:
      - Markdown:  `![alt](url)`, `![alt](url "title")`
      - HTML:      `<img src="url">` or `<img src='url'>`

    Passthrough rules (no resolution, no Asset record):
      - http://, https://, // (protocol-relative)
      - leading / (already a SvelteKit static URL)
      - data:, mailto:, tel: URIs
      - References inside fenced code blocks (``` or ~~~)

    On-disk resolution:
      - Relative paths resolve against `markdown_path.parent`.
      - Query (`?cache=1`) and fragment (`#anchor`) are stripped before lookup.
      - Missing file → ContentResolutionError with the markdown path in
        the message; resolver.py wraps with the lesson location prefix.
      - SHA-256 of file bytes; first 12 hex chars become the dest dir.
      - Multiple references to the same source file → one Asset record,
        all references rewritten to the same URL.

    Returns (rewritten_markdown, deduped_assets_in_first-seen_order).
    """
    ...
```

### `integrations/protocols.py` — Provider Protocols

```python
from typing import Protocol
from pathlib import Path

class AssessmentProvider(Protocol):
    def compile_assessment(self, ref_path: Path, base_dir: Path) -> dict:
        """
        Compile an assessment YAML file into a renderable manifest dict.
        Returns the quizazz manifest structure (questions, nav tree).
        Raises IntegrationError on parse/validation failure.
        """
        ...

class ExerciseProvider(Protocol):
    def compile_exercise(self, ref_path: Path, base_dir: Path) -> dict:
        """
        Compile an exercise YAML file into a renderable exercise dict.
        Returns exercise content (instructions, code scaffolding, expected outputs).
        Raises IntegrationError on parse/validation failure.
        """
        ...

class VisualizationProvider(Protocol):
    def compile_visualization(self, ref_path: Path, base_dir: Path) -> dict:
        """
        Compile a visualization definition into a renderable artifact dict.
        Returns visualization content (image data, HTML, or component config).
        Raises IntegrationError on parse/validation failure.
        """
        ...
```

### `integrations/quizazz.py` — quizazz Integration

```python
from pathlib import Path
from learningfoundry.integrations.protocols import AssessmentProvider

class QuizazzProvider:
    """
    AssessmentProvider implementation backed by the quizazz package.

    Delegates to quizazz.compile_assessment() to produce a manifest dict
    from a single assessment YAML file. quizazz owns internal
    validate-then-compile sequencing; the adapter does not orchestrate it.
    """

    def compile_assessment(self, ref_path: Path, base_dir: Path) -> dict:
        """
        1. Lazy-import `compile_assessment` from the `quizazz` package
           (raise ImportError with install hint if the optional dep is missing).
        2. Call quizazz.compile_assessment(ref_path, base_dir) and return its dict.
        3. Wrap any exception raised by quizazz in IntegrationError, citing ref_path.
        """
        ...
```

### `integrations/nbfoundry_stub.py` — Stub Exercise Provider

```python
from pathlib import Path
from learningfoundry.integrations.protocols import ExerciseProvider

class NbfoundryStub:
    """
    Stub ExerciseProvider for v1.

    Returns a placeholder exercise dict with the ref path and a
    "coming soon" message. The real nbfoundry integration will
    generate Marimo applications for interactive model-training exercises.
    """

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
            "hints": [],
            "environment": None,
        }
```

### `integrations/d3foundry_stub.py` — Stub Visualization Provider

```python
from pathlib import Path
from learningfoundry.integrations.protocols import VisualizationProvider

class D3foundryStub:
    """
    Stub VisualizationProvider for v1.

    Returns a placeholder visualization dict. The real d3foundry
    integration will generate Matplotlib images, D3.js interactive
    visualizations, or brokered artifacts (CNN Explainer, etc.).
    """

    def compile_visualization(self, ref_path: Path, base_dir: Path) -> dict:
        return {
            "type": "visualization",
            "source": "d3foundry",
            "ref": str(ref_path),
            "status": "stub",
            "title": f"Visualization: {ref_path.stem}",
            "caption": "",
            "render_type": "image",
            "content": "",
            "content_type": "image/svg+xml",
            "alt_text": f"Placeholder for {ref_path}",
        }
```

### `pipeline.py` — Pipeline Orchestrator

```python
from pathlib import Path
from learningfoundry.config import AppConfig
from learningfoundry.resolver import ResolvedCurriculum

def run_build(
    curriculum_path: Path,
    output_dir: Path,
    config: AppConfig,
) -> None:
    """
    Full build pipeline:
      1. Parse curriculum YAML (parser.parse_curriculum)
      2. Resolve content references (resolver.resolve_curriculum)
      3. Generate SvelteKit project (generator.generate_app)

    Logs progress at each stage. Fails fast on first error.
    """
    ...

def run_validate(
    curriculum_path: Path,
    config: AppConfig,
) -> None:
    """
    Validation-only pipeline:
      1. Parse curriculum YAML
      2. Resolve content references (validates file existence, URLs, integration refs)
      3. Report "Curriculum is valid." or error details.
    """
    ...

def run_preview(
    curriculum_path: Path,
    output_dir: Path,
    port: int,
    config: AppConfig,
) -> None:
    """
    Build + preview pipeline:
      1. Run full build pipeline
      2. Run `pnpm install` in the generated SvelteKit project
      3. Start `pnpm run dev --port <port>` as a subprocess
      4. Print local URL and stream server output
    """
    ...
```

### `generator.py` — SvelteKit Project Generation

```python
from pathlib import Path
from learningfoundry.resolver import ResolvedCurriculum

def generate_app(
    curriculum: ResolvedCurriculum,
    output_dir: Path,
) -> None:
    """
    Generate a complete SvelteKit project from the resolved curriculum.

    1. Copy the bundled sveltekit_template/ to output_dir, atomically (write
       to sibling temp dir, then rename). State directories listed in
       _PRESERVED_PATHS are moved from the existing output (if any) into the
       fresh template copy before the swap, so install/build artefacts and
       previously-copied image assets survive a rebuild without having to
       re-run pnpm install. The current preserved set:
         - node_modules
         - pnpm-lock.yaml
         - build
         - .svelte-kit
         - static/content   (image assets copied by step 3)
    2. Write curriculum.json into output_dir/static/, containing the full
       resolved curriculum structure (modules, lessons, content blocks with
       resolved content). The `assets` field on ResolvedCurriculum is
       intentionally stripped — it carries on-disk Path objects (not JSON
       serialisable) and is consumed only by the next step.
    3. Copy each Asset record from ResolvedCurriculum.assets into
       output_dir/static/<dest_relative>. Idempotent: a destination file
       whose size matches the source is left untouched (the content-hashed
       path makes matching size a strong identity signal).

    If output_dir exists, the log message is INFO-level and notes which
    state directories are being preserved.
    """
    ...
```

### `exceptions.py` — Exception Hierarchy

```python
class LearningFoundryError(Exception):
    """Base exception for all learningfoundry errors."""

class ConfigError(LearningFoundryError):
    """Config file is malformed or contains invalid values."""

class CurriculumVersionError(LearningFoundryError):
    """Missing or unsupported curriculum YAML version."""

class CurriculumValidationError(LearningFoundryError):
    """Curriculum YAML fails schema validation.
    Includes field path and validation detail from Pydantic."""

class ContentResolutionError(LearningFoundryError):
    """Content reference cannot be resolved.
    Includes block location (module/lesson/block index) and specific cause."""

class IntegrationError(LearningFoundryError):
    """An integration library (quizazz, nbfoundry, d3foundry) returned an error.
    Wraps the library's original error with block location context."""

class GenerationError(LearningFoundryError):
    """SvelteKit project generation failed."""
```

---

## Data Models

### Curriculum YAML Schema (v1)

See `schema_v1.py` above for the full Pydantic model. The YAML structure matches the example in `features.md`:

```yaml
version: "1.0.0"
curriculum:
  title: "Deep Learning Essentials"
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
            - type: visualization
              source: d3foundry
              ref: visualizations/mod-01-cnn-architecture.yml
```

### Resolved Curriculum (in-memory)

The `ResolvedCurriculum` dataclass tree (see `resolver.py` above) is serialized to `curriculum.json` in the generated SvelteKit project for the frontend to consume.

In addition to the module/lesson/content tree, `ResolvedCurriculum` carries an `assets: list[Asset]` field — the deduped union of every image asset referenced by any text block's markdown. Each `Asset` is a `(source: Path, dest_relative: str)` pair where `dest_relative = "content/<sha256[:12]>/<basename>"`. The list is consumed by `generator.generate_app()` to copy files into `output_dir/static/`; it is **stripped before serialisation to curriculum.json** because it carries `Path` objects (not JSON-serialisable) and the SvelteKit frontend only ever needs the rewritten URL embedded in the lesson markdown — never the original source path.

### curriculum.json (generated, consumed by SvelteKit)

```json
{
  "version": "1.0.0",
  "title": "Deep Learning Essentials",
  "description": "...",
  "modules": [
    {
      "id": "mod-01",
      "title": "Introduction to Neural Networks",
      "description": "...",
      "assessments": [
        {
          "id": "pre",
          "role": "pre",
          "position": "before_lessons",
          "source": "quizazz",
          "ref": "assessments/mod-01-pre.yml",
          "pass_threshold": null,
          "content": { "...quizazz manifest..." }
        },
        {
          "id": "post",
          "role": "post",
          "position": "after_lessons",
          "source": "quizazz",
          "ref": "assessments/mod-01-post.yml",
          "pass_threshold": 0.8,
          "content": { "...quizazz manifest..." }
        }
      ],
      "lessons": [
        {
          "id": "lesson-01",
          "title": "What is a Neural Network?",
          "content_blocks": [
            { "type": "text", "content": "<p>Rendered HTML from markdown...</p>" },
            { "type": "video", "content": "https://www.youtube.com/watch?v=..." },
            { "type": "assessment", "content": { "...quizazz manifest..." } },
            { "type": "exercise", "content": { "...nbfoundry output..." } },
            { "type": "visualization", "content": { "...d3foundry output..." } }
          ]
        }
      ]
    }
  ]
}
```

### SQLite Progress Schema (in-browser)

```sql
CREATE TABLE IF NOT EXISTS lesson_progress (
  lesson_id     TEXT PRIMARY KEY,
  module_id     TEXT NOT NULL,
  completed     INTEGER NOT NULL DEFAULT 0,   -- 0 = incomplete, 1 = complete
  completed_at  INTEGER                        -- Unix timestamp, NULL if incomplete
);

-- Content-block-level assessment scores (lesson content blocks of `type: assessment`).
-- Keyed on the global `assessment_ref` because content-block refs are unique
-- across the curriculum.
CREATE TABLE IF NOT EXISTS assessment_scores (
  assessment_ref TEXT NOT NULL,
  score          INTEGER NOT NULL,
  max_score      INTEGER NOT NULL,
  question_count INTEGER NOT NULL,
  completed_at   TEXT NOT NULL,                  -- ISO 8601 timestamp
  PRIMARY KEY (assessment_ref)
);

-- Story J.u — module-level assessment scores (the J.e generalized
-- `assessments[]` array). Distinct table from `assessment_scores` because
-- two modules can legitimately reference the same quizazz YAML — the
-- natural key here is `(module_id, assessment_id)`.
CREATE TABLE IF NOT EXISTS module_assessment_scores (
  module_id      TEXT NOT NULL,
  assessment_id  TEXT NOT NULL,
  score          INTEGER NOT NULL,
  max_score      INTEGER NOT NULL,
  question_count INTEGER NOT NULL,
  completed_at   TEXT NOT NULL,                  -- ISO 8601 timestamp
  PRIMARY KEY (module_id, assessment_id)
);

CREATE TABLE IF NOT EXISTS exercise_status (
  exercise_ref  TEXT PRIMARY KEY,              -- Exercise ref path
  module_id     TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'not_started',  -- "not_started" | "in_progress" | "completed"
  updated_at    INTEGER NOT NULL               -- Unix timestamp
);
```

**Lesson lifecycle (Story I.p / FR-P15).** `lesson_progress.status` stores the four-state machine `not_started → opened → in_progress → complete`. The DB layer exposes:

- `markLessonOpened(moduleId, lessonId)` — upgrade-only `INSERT … ON CONFLICT DO UPDATE` that promotes a row from `not_started` (or absent) to `opened` but never demotes a row already at `opened`/`in_progress`/`complete`. Called from `LessonView.onMount`.
- `markLessonInProgress(moduleId, lessonId)` — promotes to `in_progress` (preserving `complete`). Caller contract narrowed: now invoked on the *first* block-completion event of the mount session, not on mount itself.
- `markLessonComplete(moduleId, lessonId)` — terminal write when every block has fired completion.

`getModuleProgress` derives module-level status from the per-lesson statuses; `opened` falls into the `s !== 'not_started'` branch and surfaces as `in_progress` at the module level. The frontend visually merges `opened` with `in_progress` (`…` icon) so the lifecycle distinction is data-only.

### SvelteKit TypeScript Types (`lib/types/index.ts`)

```typescript
export interface Curriculum {
  version: string;
  title: string;
  description: string;
  modules: Module[];
}

export type AssessmentPosition =
  | "before_lessons"
  | "after_lessons"
  | { before_lesson: string }
  | { after_lesson: string };

export interface AssessmentDefinition {
  id: string;                        // Story J.r — always populated in resolved curriculum.json
  role: string;
  position: AssessmentPosition;
  source: string;
  ref: string;
  pass_threshold: number | null;
  content: AssessmentManifest;
}

export interface Module {
  id: string;
  title: string;
  description: string;
  assessments: AssessmentDefinition[];   // Story J.e — replaces pre/post fields
  lessons: Lesson[];
}

export interface Lesson {
  id: string;
  title: string;
  content_blocks: ContentBlock[];
}

export interface ContentBlock {
  type: "text" | "video" | "assessment" | "exercise" | "visualization" | "placeholder";
  content: string | AssessmentManifest | ExerciseContent | VisualizationContent;
}

export interface AssessmentManifest {
  // Mirrors quizazz compiled manifest structure; QuizazzProvider relabels
  // quizazz's `quizName` wire key to `assessmentName` so the vendor's
  // terminology does not leak into the curriculum.json schema consumed by
  // the SvelteKit frontend.
  assessmentName: string;
  tree: NavNode[];
  questions: Question[];
}

export interface ExerciseContent {
  type: "exercise";
  source: string;
  ref: string;
  status: "ready" | "stub";
  title: string;
  instructions: string;
  sections: ExerciseSection[];
  expected_outputs: ExpectedOutput[];
  hints: string[];
  environment: ExerciseEnvironment | null;
}

export interface ExerciseSection {
  title: string;
  description: string;
  code: string;
  editable: boolean;
}

export interface ExpectedOutput {
  description: string;
  type: "image" | "text" | "table";
  content: string;
}

export interface ExerciseEnvironment {
  python_version: string;
  dependencies: string[];
  setup_instructions: string;
}

export interface VisualizationContent {
  type: "visualization";
  source: string;
  ref: string;
  status: "ready" | "stub";
  title: string;
  caption: string;
  render_type: "image" | "html" | "svelte_component";
  content: string;           // base64 image, HTML string, or component ID
  content_type: string;      // MIME type (e.g., "image/svg+xml", "text/html")
  alt_text: string;
}

export interface LessonProgress {
  lessonId: string;
  moduleId: string;
  completed: boolean;
  completedAt: number | null;
}

// Content-block-level assessment score — keyed on the global `assessmentRef`.
export interface AssessmentScore {
  assessmentRef: string;
  score: number;
  maxScore: number;
  questionCount: number;
  completedAt: string;                  // ISO 8601
}

// Story J.u — module-level assessment score. Distinct shape because two
// modules can reference the same `ref`; identity is `(moduleId, assessmentId)`.
// `passed` is *not* stored — compute on read via `computeAssessmentPassed`
// so YAML threshold edits re-evaluate against the active rule.
export interface ModuleAssessmentScore {
  moduleId: string;
  assessmentId: string;
  score: number;
  maxScore: number;
  questionCount: number;
  completedAt: string;
}

export interface ExerciseStatus {
  exerciseRef: string;
  moduleId: string;
  status: "not_started" | "in_progress" | "completed";
  updatedAt: number;
}

export interface ModuleProgress {
  moduleId: string;
  status: "not_started" | "in_progress" | "complete";
  lessons: Record<string, LessonProgress>;
  // Story J.u — module-level assessment scores keyed by `assessmentId`.
  // Replaces the pre-J.e `preAssessment` / `postAssessment` two-slot fields.
  assessmentScores: Record<string, ModuleAssessmentScore>;
}
```

---

## Configuration

### Precedence (highest to lowest)

1. CLI flags (e.g., `--log-level DEBUG`)
2. Global config file (`~/.config/learningfoundry/config.yml`)
3. Built-in defaults (dataclass defaults in `config.py`)

### Global Config Schema (v1)

```yaml
# ~/.config/learningfoundry/config.yml
logging:
  level: INFO          # DEBUG | INFO | WARNING | ERROR
  output: stdout       # stdout | <file path>
```

Unknown keys are ignored with a warning logged (forward-compatible).

### Settings Model

```python
@dataclass
class LoggingConfig:
    level: str = "INFO"
    output: str = "stdout"

@dataclass
class AppConfig:
    logging: LoggingConfig = field(default_factory=LoggingConfig)
```

---

## CLI Design

### Subcommands

| Command | Arguments | Description |
|---------|-----------|-------------|
| `learningfoundry build <curriculum.yml>` | `--output`, `--log-level`, `--config` | Full pipeline: parse → resolve → generate SvelteKit app |
| `learningfoundry validate <curriculum.yml>` | `--log-level`, `--config` | Schema + reference validation only |
| `learningfoundry preview <curriculum.yml>` | `--port`, `--output`, `--log-level`, `--config` | Build + local dev server |

### Shared Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--config` | Path | `~/.config/learningfoundry/config.yml` | Config file path |
| `--log-level` | Choice | From config or `INFO` | Override log level |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Curriculum validation error (schema, missing files, bad version) |
| `2` | Content resolution error (integration failure, missing content) |
| `3` | Generation error (SvelteKit build failure) |
| `4` | Configuration error (malformed config file) |

---

## Cross-Cutting Concerns

### Error Handling

- **Fail-fast**: Pipeline exits on the first error with a clear, actionable message.
- **Error context**: Every error includes the source location (file path, module/lesson/block index) and a description of what went wrong and how to fix it.
- **Exception hierarchy**: All custom exceptions inherit from `LearningFoundryError`. CLI catches this base class, prints the formatted message, and exits with the appropriate code.
- **Integration errors**: Wrapped in `IntegrationError` with block location context prepended to the library's original message.

### Logging

- Standard library `logging` module with structured formatters.
- Default: `INFO` level to `stdout`.
- Configurable via global config file and `--log-level` CLI flag.
- Pipeline stages log progress at `INFO` (e.g., "Parsing curriculum...", "Resolving content for module mod-01...", "Generating SvelteKit project...").
- Content resolution details at `DEBUG`.
- Warnings for non-fatal issues (empty markdown file, unknown config keys, output directory overwrite).

### YAML Versioning

- Every curriculum YAML must include a top-level `version` field (semver string).
- The parser extracts the major version and dispatches to the corresponding schema module (`schema_v1.py`).
- Currently supported: major version `1`.
- New major versions add a new `schema_vN.py` module and a dispatch entry in `parser.py`.

### WASM Binary Handling

The `sql-wasm.wasm` file is served from the SvelteKit template's `static/` directory. It is provisioned by `pipeline._ensure_sql_wasm`, which runs on **every** preview/build (regardless of `DepState`) and copies `node_modules/sql.js/dist/sql-wasm.wasm` into `static/sql-wasm.wasm` whenever the destination is missing or content-stale (size comparison). If the source is absent in `node_modules/`, it raises `GenerationError` rather than serving a 404. This Python-side step replaced an earlier pnpm `postinstall` hook (Story I.cc), which only ran on actual installs and was unreliable across pnpm version/configuration combinations. The frontend initializes sql.js with `locateFile: () => '/sql-wasm.wasm'` to load from the static root.

### Atomic Output

`generator.generate_app()` writes to a temporary directory first, then moves it to the final `output_dir` atomically. If `output_dir` already exists, it is replaced (with a warning logged). This prevents partial output on failure.

---

## Performance Implementation

No specific performance targets for v1. The pipeline is synchronous and single-threaded.

- **YAML parsing**: PyYAML + Pydantic validation — fast for typical curriculum sizes (10–20 modules).
- **Content resolution**: Sequential file reads and integration calls. No parallelism needed at expected scale.
- **SvelteKit generation**: File copy + JSON serialization. Bottleneck is `pnpm install` on first build.
- **Preview**: Delegates to SvelteKit's Vite dev server, which handles HMR and incremental builds.

Performance optimization is deferred until real workloads identify bottlenecks.

---

## Testing Strategy

### Unit Tests

| Module | What is tested |
|--------|----------------|
| `test_parser.py` | Valid curriculum parsing, missing version, unsupported version, malformed YAML |
| `test_schema_v1.py` | Pydantic model validation: required fields, content block types, ID uniqueness, URL format, lesson/module minimums |
| `test_resolver.py` | Markdown loading, YouTube URL validation, empty markdown warning, integration error propagation (mocked providers) |
| `test_config.py` | Precedence: CLI > config file > defaults; malformed config; unknown keys warning |
| `test_integrations/test_quizazz.py` | QuizazzProvider delegates correctly to quizazz.compile_assessment (mocked); error wrapping |
| `test_integrations/test_nbfoundry_stub.py` | Stub returns placeholder dict with correct structure |
| `test_integrations/test_d3foundry_stub.py` | Stub returns placeholder visualization dict with correct structure |

### Integration Tests

| Test | What is tested |
|------|----------------|
| `test_pipeline.py` | End-to-end build with a small fixture curriculum (2 modules, 3 lessons). Verifies output directory structure. |
| `test_cli.py` | CLI invocation: `build` produces output, `validate` reports OK or errors, `--help` exits 0. Uses a fixture curriculum YAML and mock content files. |
| `test_generator.py` | Generated SvelteKit project contains expected files (`package.json`, `curriculum.json`, route files). Does **not** run `pnpm build` — that is a smoke test. |

### Smoke Tests

- Generated SvelteKit project compiles without errors (`pnpm install && pnpm build` in CI).
- Fixture curriculum with all content block types builds end-to-end.

---

## Packaging and Distribution

### Package Metadata (`pyproject.toml`)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "learningfoundry"
version = "0.1.0"
description = "Turn a YAML curriculum definition into a deployable SvelteKit learning application"
readme = "README.md"
license = "Apache-2.0"
requires-python = "==3.12.*"
authors = [{ name = "Pointmatic" }]
dependencies = [
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "click>=8.1",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "ruff",
    "mypy",
]
quizazz = [
    "quizazz>=0.1",
]
nbfoundry = [
    "nbfoundry>=0.1",
]
d3foundry = [
    "d3foundry>=0.1",
]

[project.scripts]
learningfoundry = "learningfoundry.cli:cli"

[tool.hatch.build.targets.sdist]
include = ["src/learningfoundry", "sveltekit_template"]

[tool.hatch.build.targets.wheel]
packages = ["src/learningfoundry"]
# sveltekit_template is included as package data
```

### Package Data

The `sveltekit_template/` directory is included in the distribution as package data so that the generator can copy it to the output directory at runtime.

### Registry

Published to **PyPI** as `learningfoundry`.

### Installation

```bash
pip install learningfoundry                # core
pip install learningfoundry[quizazz]       # with quizazz integration
pip install learningfoundry[nbfoundry]     # with nbfoundry integration (future)
pip install learningfoundry[d3foundry]     # with d3foundry integration (future)
```

### Console Script

`learningfoundry` → `learningfoundry.cli:cli` (Click entry point).
