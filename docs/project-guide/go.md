# Project-Guide — Calm the chaos of LLM-assisted coding

This document provides step-by-step instructions for an LLM to assist a human developer in a project. 

## How to Use Project-Guide

### For Developers
After installing project-guide (`pip install project-guide`) and running `project-guide init`, instruct your LLM as follows in the chat interface: 

```
Read `docs/project-guide/go.md`
```

After reading, the LLM will respond:
1. (optional) "I need more information..." followed by a list of questions or details needed. 
  - LLM will continue asking until all needed information is clear.
2. "The next step is ___."
3. "Say 'go' when you're ready." 

For efficiency, when you change modes, start a new LLM conversation. 

### For LLMs

**Modes**
This Project-Guide offers a human-in-the-loop workflow for you to follow that can be dynamically reconfigured based on the project `mode`. Each `mode` defines a focused sequence of steps to guide you (the LLM) to help generate artifacts for some facet in the project lifecycle. This document is customized for scaffold_project.

**Approval Gate**
When you have completed the steps, pause for the developer to review, correct, redirect, or ask questions about your work.  

**Rules**
- Work through each step methodically, presenting your work for approval before continuing a cycle. 
- When the developer says "go" (or equivalent like "continue", "next", "proceed"), continue with the next action. 
- If the next action is unclear, tell the developer you don't have a clear direction on what to do next, then suggest something. 
- Never auto-advance past an approval gate—always wait for explicit confirmation. 
- At approval gates, present the completed work and wait. Do **not** propose follow-up actions outside the current mode step — in particular, do not prompt for git operations (commits, pushes, PRs, branch creation), CI runs, or deploys unless the current step explicitly calls for them. The developer initiates these on their own schedule.
- After compacting memory, re-read this guide to refresh your context.
- Before recording a new memory, reflect: is this fact project-specific (belongs in `docs/specs/project-essentials.md`) or cross-project (belongs in LLM memory)? Could it belong in both? If project-specific, add it to `project-essentials.md` instead of or in addition to memory.
- When creating any new source file, add a copyright notice and license header using the comment syntax for that file type (`#` for Python/YAML/shell, `//` for JS/TS, `<!-- -->` for HTML/Svelte). Check this project's `project-essentials.md` for the specific copyright holder, license, and SPDX identifier to use.
- **Bundled artifact templates** live at `docs/project-guide/templates/artifacts/` in this project (installed by `project-guide init`, refreshed by `project-guide update`). When a mode step references an artifact template by name (e.g. `concept.md`, `stories.md`, `project-essentials.md`), that is the directory to read from — do not search the filesystem, the Python install location, or `site-packages`.

---

## Project Essentials

<!--
This file captures must-know facts future LLMs need to avoid blunders when
working on this project. It is injected verbatim under a `## Project
Essentials` section in every rendered `go.md`, so entries here use `###` for
subsections (not `##`). No top-level `#` title — the wrapper provides it.

Pyve-specific rules live in the bundled `pyve-essentials.md` sibling
artifact and render automatically — do NOT duplicate them here.
-->

### File header conventions

Every new source file must begin with a copyright notice and license
identifier. Use the comment syntax for the file type:

| File type | Comment syntax |
|-----------|---------------|
| Python, YAML, shell, Makefile | `#` |
| JavaScript, TypeScript, Go, Java, C/C++ | `//` or `/* */` |
| HTML, Svelte, XML | `<!-- -->` |
| CSS, SCSS | `/* */` |

**This project's header:**

- **Copyright**: `Copyright (c) 2026 Pointmatic`
- **SPDX identifier**: `SPDX-License-Identifier: Apache-2.0`

Python example:
```python
# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
```

TypeScript example:
```typescript
// Copyright (c) 2026 Pointmatic
// SPDX-License-Identifier: Apache-2.0
```

HTML example:
```html
<!-- Copyright (c) 2026 Pointmatic -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
```

**Compiler exception (FR-8 step 3):** the `nbfoundry` compiler does **not**
inject headers into author-authored notebooks it processes. If an author
has stripped the header from their own notebook, that's their choice —
preserve it as-is rather than re-injecting. This applies only to
hand-authored notebook source consumed by `nbfoundry compile` /
`compile_exercise`; it does **not** apply to files **you** create as part
of this project's source tree, which always carry the header.



### Pyve Essentials

#### Workflow rules — pyve environment conventions

This project uses `pyve` with **two separate environments**. Picking the wrong invocation form often "works" but leads to subtle drift. Use the canonical forms below:

- **Runtime code (the package itself):** `pyve run python ...` or `pyve run <entry-point> ...`.
- **Tests:** `pyve test [pytest args]` — **not** `pyve run pytest`. Pytest is not installed in the main `.venv/`; it lives in the dev testenv at `.pyve/testenv/venv/`.
- **Dev tools (ruff, mypy, pytest):** `pyve testenv run ruff check ...`, `pyve testenv run mypy ...`.
- **Initialize the testenv (one-time):** `pyve testenv init` creates `.pyve/testenv/venv/`. Required before `pyve testenv install` or `pyve testenv run` will work — those subcommands do not auto-create the env. See [pyve `testenv` subcommand reference](https://pointmatic.github.io/pyve/usage/#testenv-subcommand).
- **Install dev tools:** `pyve testenv install -r requirements-dev.txt` (after `pyve testenv init`). **Do not** run `pip install -e ".[dev]"` into the main venv — that pollutes the runtime environment with test-only dependencies and breaks the two-env isolation.

If `pytest` fails with "not found" that is the signal to use `pyve test`, not to `pip install pytest` into the wrong venv. If `pyve testenv install` or `pyve testenv run` fails complaining the env doesn't exist, run `pyve testenv init` first.

#### LLM-internal vs. developer-facing invocation

`pyve run` is for the LLM's own Bash-tool invocations; developer-facing command suggestions use the bare form verbatim from the mode template.

- ✅ Developer-facing: `project-guide mode plan_phase`
- ❌ Developer-facing: `pyve run project-guide mode plan_phase`
- ✅ LLM Bash-tool: `pyve run project-guide mode plan_phase`

**Why:** the LLM's Bash-tool shell does not auto-activate `.venv/`, so the LLM must wrap its own commands with `pyve run`. The developer's shell is typically already pyve/direnv-activated, so the bare form resolves correctly and matches the commands quoted throughout mode templates and documentation.

**How to apply:** never prepend environment wrappers (`pyve run`, `poetry run`, `uv run`, etc.) to commands you quote back to the developer from a mode template. Use the wrapper only when you execute the command yourself through the Bash tool.

#### Python invocation rule

Always use `python`, never `python3`. The `python3` command bypasses `asdf` version shims and may resolve to the system interpreter rather than the project-pinned version, leading to subtle version mismatches.

#### `requirements-dev.txt` story-writing rule

Any story that introduces dev tooling (ruff, mypy, pytest, types-* stubs) **must** include a task to create or update `requirements-dev.txt` so that `pyve testenv init && pyve testenv install -r requirements-dev.txt` reproduces the full dev environment in two commands. This keeps the dev environment reproducible and prevents "it works on my machine" drift.

#### Editable install and testenv dependency management

LLMs often get confused about *where* to install an editable package when using pyve's two-environment model. The wrong choice "works" but creates subtle drift.

**Main environment only (preferred for library projects):**
```bash
pyve run pip install -e .
```
Then configure pytest to find the source tree without a second editable install:
```toml
# pyproject.toml
[tool.pytest.ini_options]
pythonpath = ["."]   # or ["src"] for src layout
```
`pythonpath` handles import discovery cleanly and avoids maintaining two editable installs with potentially diverging dependency resolution.

**Testenv editable install (required for CLI projects):**
```bash
pyve testenv init                                # one-time, creates .pyve/testenv/venv/
pyve testenv run pip install -e .
pyve testenv install -r requirements-dev.txt
```
Use this when tests invoke CLI entry points (console scripts), because `pythonpath` only handles imports — it does not register entry points.

**Rule of thumb:** use `pythonpath` for library/package projects; use editable install in testenv for projects whose tests exercise CLI entry points.

**Important:** When `pyve` purges and reinitialises the main environment, the testenv remains intact and the testenv editable install survives. Re-running `pyve run pip install -e .` restores the main-environment editable install. See `developer/python-editable-install.md` for the full decision guide.


---

# scaffold_project mode (sequence)

> Scaffold the project foundation (LICENSE, headers, manifest, README, CHANGELOG)


Scaffold the project foundation: license, copyright headers, package manifest, README with badges, CHANGELOG, and .gitignore. This is a one-time scaffolding step after planning is complete, using decisions made in the concept, features, tech-spec, and stories documents.

## Prerequisites

Before starting, the developer must provide (or the LLM must ask for):

1. **Project name** -- the repository and package name
2. **Copyright holder** -- individual or organization name
3. **License preference** -- e.g. Apache-2.0, MIT, MPL-2.0, GPL-3.0

## Steps

### 1. License

1. If a `LICENSE` file exists in the project root, read it and identify the license.
2. If no `LICENSE` file exists, create one based on the developer's preference.
3. Record the license identifier (SPDX format, e.g. `Apache-2.0`) -- this will be used in `pyproject.toml` (or equivalent) and in file headers.

### 2. Copyright and License Header

Establish the standard copyright and license header for all source files in the project. The header format depends on the license and the file's comment syntax.

**Example for Apache-2.0 in a Python file:**

```python
# Copyright (c) <year> <copyright holder>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```

**Example for MIT in a Python file:**

```python
# Copyright (c) <year> <copyright holder>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction. See the LICENSE file for details.
```

Adapt the comment syntax for the file type (`#` for Python/Shell, `//` for JS/TS/Go, `<!-- -->` for HTML/XML, etc.).

### 3. Package Manifest

Create the project's package manifest (e.g. `pyproject.toml`, `package.json`, `Cargo.toml`):

- The `license` field must match the `LICENSE` file (use the SPDX identifier).
- Include the copyright holder in the authors/maintainers field.
- Set the initial version to `0.1.0`.
- Add a placeholder description (will be refined in `document_brand` mode).

### 4. README.md

Create an initial `README.md` with:

- Project name as heading
- One-line description placeholder
- License badge (always include)
- Installation section placeholder
- Usage section placeholder

**Badge reference:**

| Badge | When to include | Example source |
|-------|----------------|----------------|
| **License** | Always | `shields.io/badge/License-Apache%202.0-blue.svg` |
| **CI status** | After CI is configured | GitHub Actions badge URL |
| **Package version** | After publishing to registry | `shields.io/pypi/v/...` |
| **Language version** | After specifying in manifest | `shields.io/pypi/pyversions/...` |
| **Coverage** | After coverage service is configured | Codecov/Coveralls badge URL |

Add badges proactively as each becomes applicable.

### 5. CHANGELOG.md

Create `CHANGELOG.md` in the repository root:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
```

**Guidelines:**
- Update `CHANGELOG.md` in the same commit as the version bump
- Use standard categories: Added, Changed, Deprecated, Removed, Fixed, Security
- Omit empty categories
- Most recent versions at the top

### 6. .gitignore

Create or update `.gitignore` with language-appropriate patterns. Include at minimum:

- Build artifacts
- Virtual environment directories
- IDE/editor files
- OS-specific files (`.DS_Store`, `Thumbs.db`)
- Test/coverage output

### 7. Mark Story A.a Done

Read `docs/specs/stories.md` and locate Story A.a.

- If Story A.a is found and represents project scaffolding: mark all its tasks `[x]` and change its status suffix from `[Planned]` to `[Done]`.
- If Story A.a is not found or does not appear to be a scaffolding story: warn the developer ("Story A.a not found or does not match expected scaffolding content — skipping story update") and continue.

### 8. Project Essentials: Verify or Create, then Memory Review

**8a. Verify or create `project-essentials.md` with concrete file headers.**

Check whether `docs/specs/project-essentials.md` exists:

- **If it does NOT exist**: create it from the artifact template at `docs/project-guide/templates/artifacts/project-essentials.md` (installed by `project-guide init`; refreshed by `project-guide update`). The **File header conventions** section is mandatory baseline content — substitute `<YEAR>`, `<OWNER>`, and `<LICENSE>` with the concrete values gathered in steps 1–3 above (the SPDX identifier from step 1, the copyright holder from the prerequisites, and the current year). Remove the trailing TODO note. Do **not** ask the developer whether to include the headers.
- **If it exists**: read the **File header conventions** section. If it still contains `<YEAR>`, `<OWNER>`, or `<LICENSE>` placeholders (or a trailing TODO note), substitute the concrete values from steps 1–3 and remove the TODO note. If the section is already concrete, leave it alone.

**8b. Memory review (append additional project-specific facts).**

Read your recorded memories for this project (e.g., `.claude/projects/<project-path>/memory/` for Claude Code users).

For each memory, evaluate: is this fact **project-specific** (belongs permanently in `docs/specs/project-essentials.md`) rather than — or in addition to — being stored in LLM memory?

Present candidates to the developer:

> "I found N memories. These may belong in `project-essentials.md`: [list with one-line summaries]. Which (if any) should I copy across?"

Await confirmation, then append confirmed items to `docs/specs/project-essentials.md` following the heading convention (`###` subsections, no top-level `#`). If the memory store is empty or inaccessible, note this briefly and continue.

### 9. Present for Approval

Present the scaffolded project to the developer for review:

- [ ] LICENSE file present and correct
- [ ] Copyright header format established
- [ ] Package manifest created with correct metadata
- [ ] README.md with license badge
- [ ] CHANGELOG.md initialized
- [ ] .gitignore configured

Once approved, proceed to coding:

```bash
project-guide mode code_direct
```

**After completing all steps below**, prompt the user to change modes:

```bash
project-guide mode code_direct
```

---


