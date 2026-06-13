# concept.md — Pyve

This document defines why the `pyve` project exists. 
- **Problem space**: problem statement, why, pain points, target users, value criteria
- **Solution space**: solution statement, goals, scope, constraints
- **Value mapping**: Pain point to solution mapping

For requirements and behavior (what), see [`features.md`](features.md). For implementation details (how), see [`tech-spec.md`](tech-spec.md). For a breakdown of the implementation plan (step-by-step tasks), see [`stories.md`](stories.md). For project-specific must-know facts (workflow rules, hidden coupling, tool-wrapper conventions that the LLM would otherwise random-walk on), see [`project-essentials.md`](project-essentials.md). For the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), see [`docs/project-guide/go.md`](../project-guide/go.md) — re-read it whenever the mode changes or after context compaction.

---

## Problem Space

### problem_statement

Python is one of the most popular programming languages in the world, but getting from zero to a clean, secure, ready-to-code environment requires the same fiddly setup tasks every single time. In the LLM era — when a fully functional single-purpose backend can be built in 6–12 hours — spending 30 minutes wrestling with environment setup is a disproportionate tax. The false starts, gotchas, and ongoing friction also break the smooth coding flow state that makes LLM-assisted development productive in the first place.

### problem_why

Python is not opinionated about environment setup, and its broad audience — ML engineers, data scientists, analysts, hobbyists, and business users alongside professional developers — skews away from the enterprise, hyper-tooled programming culture that produces convergent toolchains. The ecosystem instead has tool overlap (asdf/pyenv, venv/conda/poetry/pipenv/uv, direnv) without convergence, and each tool has its own quirks. Now AI agents are taking on more of the coding work without feeling the human-side friction, so the pain isn't being surfaced to the people building the next generation of tools. Together these forces have prevented any single "magical" Python project setup tool from emerging.

### pain_points

- **repetitive_setup**: The same little setup tasks must be repeated for every new (and many existing) Python projects.
- **command_recall**: Remembering exact command names, syntax, parameters, and the correct sequence across multiple tools is a constant cognitive tax.
- **activation_friction**: Manual venv/conda activation and deactivation is annoying and easy to forget; direnv solves it but adds yet another tool to configure.
- **venv_setup_complexity**: Setting up virtual environments *properly* is non-trivial, which incentivizes bad shortcuts that compound later.
- **tool_coordination**: Coordinating asdf/pyenv + venv/micromamba + direnv is fiddly because every tool behaves a little differently.
- **machine_inconsistency**: Setups drift across machines and CI; the "perfect" recipe from one project is hard to find, copy, and apply consistently to the next.
- **secret_safety**: Accidental secret commits and lost `.env` files on teardown are real risks.
- **cloud_sync_corruption**: Cloud-sync daemons (iCloud, Dropbox, OneDrive, Google Drive) silently corrupt conda environments — projects "break for no reason."
- **reinit_footguns**: Re-initializing a project can wipe test environments or leave lock files drifted from environment files.

### target_users

- **Primary**: Python developers building applications, backends, web services, and general-purpose Python projects on macOS and Linux.
- **Secondary**: ML and scientific computing practitioners (data scientists, ML engineers, researchers) using conda-style stacks with binary dependencies.
- **Tertiary**: Non-programmer tinkerers who clone a Python repo to explore or extend it and want it to "just work."
- **Implicit**: CI/CD pipelines and automation scripts that need the same environment behavior as interactive use.

### value_criteria

- **Time-to-hello-world**: How quickly a developer goes from a fresh directory to running their first line of project code (primary metric).
- **Adoption breadth**: Pyve usage per Python project, proxied by GitHub clones/downloads and Homebrew installs.
- **Command diversity**: Whether users exercise the full surface area (`pyve run pytest`, `pyve testenv run`, `pyve doctor`, `pyve lock`) or just `--init` — broader use signals deeper integration into workflow.
- **Community signal**: Organic mentions and recommendations on developer communication channels.

---

## Solution Space

### one_liner

wrangles your Python virtual environments with one command

### solution_statement

Pyve is a focused command-line tool that provides a single, deterministic entry point for setting up and managing Python virtual environments on macOS and Linux. It orchestrates Python version management (asdf or pyenv), virtual environments (venv or micromamba), and direnv integration in one script. It supports interactive workflows with auto-activation and non-interactive CI/CD pipelines with explicit execution via `pyve run`.

With one command (`pyve init`), Pyve auto-detects the right backend, pins a Python version, configures direnv for auto-activation, secures a `.env` file with `chmod 600`, and self-heals `.gitignore`. For teardown, `pyve purge` removes Pyve's footprint while preserving user data (non-empty `.env` files, user code, git history). Pyve orchestrates existing tools rather than replacing them — staying small, scriptable, and easy to reason about.

### goals

- **Provide a single, deterministic entry point** so time-to-hello-world drops from ~30 minutes to under a minute (addresses the disproportionate-tax problem).
- **Eliminate command recall** by giving developers one consistent CLI surface across all backends and version managers.
- **Make the secure, correct default the easy default** — `chmod 600` secrets, self-healing `.gitignore`, smart purge that never destroys data.
- **Unify interactive and CI/CD workflows** so the same tool that helps a developer locally also runs reliably in pipelines via non-interactive flags and `pyve run`.
- **Refuse known footguns loudly** (cloud-synced directories, stale lock files, reserved names, backend conflicts) instead of allowing silent corruption.
- **Provide health visibility** through `pyve doctor` so developers can diagnose drift, corruption, or misconfiguration without tribal knowledge.

### scope

**In scope:**

- Orchestrating asdf/pyenv + venv/micromamba + direnv as a single workflow
- Commands: `--init`, `--purge`, `--python-version`, `run`, `doctor`, `lock`, `test`, `testenv`, `--validate`, `--install`, `--uninstall`
- Backend auto-detection from project files
- Self-healing `.gitignore` template management
- Secure `.env` lifecycle (creation, preservation, smart purge)
- Smart re-init (`--update`, `--force`) and conflict detection
- Isolated dev/test runner environment that survives `--init --force`
- CI/CD-friendly non-interactive flags (`--no-direnv`, `--auto-bootstrap`, `--strict`, `--auto-install-deps`)
- Cloud-synced directory detection
- Micromamba bootstrap (project or user sandbox)

**Out of scope:**

- Replacing asdf, pyenv, direnv, or micromamba
- Installing asdf, pyenv, or `conda-lock`
- Managing project dependencies beyond initial install
- GUI or web interface
- Docker container or cloud environment management
- Windows support

### constraints

- **Pure Bash**, no runtime dependencies, no background daemons
- **macOS and Linux only**
- **Orchestrate, don't replace** — must defer to existing tools where they already work
- **Idempotent** — every operation must produce the same result on repeated runs
- **Never destroy user data** — non-empty `.env` files, user code, and git history are inviolable
- **Asks before invasive actions** — networked installs of non-critical dependencies (micromamba, pytest) require confirmation in interactive mode
- **Apache 2.0 licensed**

---

## Pain Point to Solution Mapping

**repetitive_setup**:
  - `pyve init` collapses Python version selection, venv creation, direnv configuration, `.env` setup, and `.gitignore` management into a single command
  - Smart re-init (`--update` / `--force`) handles existing projects without manual cleanup

**command_recall**:
  - One consistent CLI (`pyve`) replaces the need to remember asdf, pyenv, venv, micromamba, conda-lock, and direnv syntax separately
  - Short flags (`-i`, `-p`, `-h`, `-v`, `-c`) for the most common operations
  - `pyve doctor` surfaces current state without requiring memorized inspection commands

**activation_friction**:
  - direnv integration is configured automatically by `pyve init`, giving auto-activation/deactivation on directory entry/exit for free
  - `pyve run <cmd>` provides explicit, stateless execution for contexts where direnv isn't appropriate

**venv_setup_complexity**:
  - Pyve encodes the "right way" to create and configure a venv so users don't take shortcuts to avoid friction
  - Micromamba projects get correct `.vscode/settings.json` and distutils shim handling automatically
  - Reserved venv directory names are rejected before they cause confusion

**tool_coordination**:
  - Pyve presents a single, uniform interface over asdf/pyenv + venv/micromamba + direnv
  - Backend auto-detection (`environment.yml` → micromamba, `pyproject.toml` → venv) removes the need to know which tool fits which project
  - `.pyve/config` records backend and version choices so the project's environment intent is portable

**machine_inconsistency**:
  - The same `pyve init` produces the same environment shape on every machine
  - CI/CD-friendly flags (`--no-direnv`, `--auto-bootstrap`, `--strict`) make the same workflow work in pipelines as on a laptop
  - `pyve validate` and `pyve doctor` confirm that a project's setup matches expectations

**secret_safety**:
  - `.env` is created with `chmod 600` (owner read/write only)
  - `.env` is automatically added to `.gitignore` to prevent accidental commits
  - `pyve purge` preserves non-empty `.env` files instead of deleting them
  - `~/.local/.env` template can be copied with `--init --local-env`

**cloud_sync_corruption**:
  - `pyve init` refuses to initialize inside known cloud-synced directories (`~/Documents`, `~/Dropbox`, `~/Google Drive`, `~/OneDrive`, `~/Library/Mobile Documents`) using both path heuristics and macOS xattr inspection
  - Error messages include the detected sync provider, recommended `mv` command, and `--allow-synced-dir` override for users who have disabled sync on the directory

**reinit_footguns**:
  - The dev/test runner environment lives at `.pyve/testenv/venv/`, separate from the project environment, so `pyve init --force` cannot wipe it
  - `--update` rejects backend changes that would require a destructive rebuild
  - `--force` requires interactive confirmation before purging
  - `pyve doctor` and `--strict` mode surface stale `conda-lock.yml` files before they cause divergence

---

## Next Action

The next step is to **change modes** to plan_features:

```bash
project-guide mode plan_features
```
