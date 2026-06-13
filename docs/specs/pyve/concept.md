# concept.md — Pyve

This document defines why the `pyve` project exists.
- **Problem space**: problem statement, why, pain points, target users, value criteria
- **Solution space**: solution statement, goals, scope, constraints
- **Value mapping**: Pain point to solution mapping

For requirements and behavior (what), see [`features.md`](features.md). For implementation details (how), see [`tech-spec.md`](tech-spec.md). For a breakdown of the implementation plan (step-by-step tasks), see [`stories.md`](stories.md). For project-specific must-know facts (workflow rules, hidden coupling, tool-wrapper conventions that the LLM would otherwise random-walk on), see [`project-essentials.md`](project-essentials.md). For the workflow steps tailored to the current mode (cycle steps, approval gates, conventions), see [`docs/project-guide/go.md`](../project-guide/go.md) — re-read it whenever the mode changes or after context compaction.

---

## Problem Space

### Problem Statement

Getting from an empty directory to a clean, secure, ready-to-code environment requires the same fiddly setup tasks every single time — and every language ecosystem reinvents them. Python has asdf/pyenv, venv/conda/poetry/uv, and direnv; Node has nvm/fnm/volta and npm/pnpm/yarn; each tool carries its own quirks and none of them converge. In the LLM era — when a working single-purpose backend can be built in 6–12 hours — spending 30 minutes wrestling with environment setup is a disproportionate tax. Polyglot projects multiply it: a Python API beside a SvelteKit front end means coordinating two ecosystems' version managers, two activation models, and two teardown stories by hand. The false starts, gotchas, and ongoing friction also break the smooth coding flow state that makes LLM-assisted development productive in the first place.

**Why this problem exists:**

Most language ecosystems are not opinionated about environment setup, and their broad audiences — ML engineers, data scientists, analysts, hobbyists, and business users alongside professional developers — skew away from the enterprise, hyper-tooled culture that produces convergent toolchains. The result is tool overlap without convergence: multiple version managers, multiple environment backends, and direnv bolted on top, each behaving a little differently. AI agents now take on more of the coding work without feeling the human-side friction, so the pain isn't surfaced to the people building the next generation of tools. Polyglot projects fall between the cracks entirely — single-ecosystem tools each own their slice and none orchestrates the whole. Together these forces have prevented any single "magical" project-setup tool from emerging.

### Pain Points

- **repetitive_setup**: The same little setup tasks must be repeated for every new (and many existing) projects.
- **command_recall**: Remembering exact command names, syntax, parameters, and the correct sequence across multiple tools is a constant cognitive tax.
- **activation_friction**: Manual environment activation and deactivation is annoying and easy to forget; direnv solves it but adds yet another tool to configure.
- **env_setup_complexity**: Setting up virtual environments *properly* is non-trivial, which incentivizes bad shortcuts that compound later.
- **tool_coordination**: Coordinating a version manager + an environment backend + direnv is fiddly because every tool behaves a little differently — and the exact mix differs per ecosystem.
- **cross_stack_coordination**: Polyglot projects must compose two ecosystems' activation, ignore rules, and teardown by hand, where it's easy to get subtly wrong (PATH ordering, double-activation, half-purges).
- **per_ecosystem_relearning**: Every new language means relearning a different set of version managers and backends from scratch.
- **machine_inconsistency**: Setups drift across machines and CI; the "perfect" recipe from one project is hard to find, copy, and apply consistently to the next.
- **secret_safety**: Accidental secret commits and lost `.env` files on teardown are real risks.
- **cloud_sync_corruption**: Cloud-sync daemons (iCloud, Dropbox, OneDrive, Google Drive) silently corrupt conda environments — projects "break for no reason."
- **reinit_footguns**: Re-initializing a project can wipe test environments or leave lock files drifted from environment files.
- **upgrade_friction**: Moving a project from an old layout to a new one by hand is error-prone and discourages adopting improvements at all.

### Target Users

- **Primary**: Developers building applications, backends, web services, and general-purpose projects on macOS and Linux — historically Python-first, now Python and/or Node / SvelteKit.
- **Polyglot / full-stack**: Developers running a backend (Python or another stack) beside a JavaScript/TypeScript front end in a single repository.
- **Secondary**: ML and scientific-computing practitioners (data scientists, ML engineers, researchers) using conda-style stacks with binary dependencies.
- **Tertiary**: Non-programmer tinkerers who clone a repo to explore or extend it and want it to "just work."
- **Implicit**: CI/CD pipelines and automation scripts that need the same environment behavior as interactive use.

### Value Criteria

- **Time-to-hello-world**: How quickly a developer goes from a fresh directory to running their first line of project code, across any stack (primary metric).
- **Adoption breadth**: Pyve usage per project, proxied by GitHub clones/downloads and Homebrew installs.
- **Command diversity**: Whether users exercise the full surface area (`pyve run`, `pyve test`, `pyve check`, `pyve status`, `pyve lock`, `pyve env`, `pyve package`) or just `pyve init` — broader use signals deeper integration into workflow.
- **Migration uptake**: How readily existing v2 projects move to the v3 manifest via `pyve self migrate` rather than stalling on an old layout.
- **Community signal**: Organic mentions and recommendations on developer communication channels.

---

## Solution Space

`pyve` is a Bash project to wrangle all your virtual environments — across any stack — from one declarative manifest.

### Solution Statement

Pyve is a focused command-line tool that gives every project a single, deterministic, declarative entry point for setting up and managing its environments across multiple language ecosystems on macOS and Linux. A root-level `pyve.toml` manifest names each environment and its purpose (`run`, `test`, `utility`, `temp`); language plugins (Python and Node / SvelteKit today, more through a stable contract) materialize those environments through their own backends — per-project virtualized (venv, micromamba, pnpm), with cache-backed and check-only categories designed in — and compose into one direnv-driven activation, one `.gitignore`, and one health report.

With one command (`pyve init`), Pyve auto-detects each stack, pins language versions through the ecosystem's own version managers, configures direnv for auto-activation, secures a `.env` file with `chmod 600`, and self-heals `.gitignore`. `pyve check` and `pyve status` diagnose and snapshot; `pyve run` and `pyve test` execute inside the right environment; `pyve purge` removes Pyve's footprint while preserving user data; and `pyve self migrate` moves a v2 project onto the v3 manifest in one step. Pyve orchestrates existing tools rather than replacing them — staying small, scriptable, and easy to reason about.

### Goals

- **Provide a single, deterministic entry point** so time-to-hello-world drops from ~30 minutes to under a minute, across stacks (addresses the disproportionate-tax problem).
- **Eliminate command recall** by giving developers one consistent CLI surface across every backend and version manager — Python and Node alike.
- **Make polyglot projects first-class** — one manifest and one composed activation / ignore / health surface across every declared plugin, instead of hand-coordinated per-ecosystem setup.
- **Make the secure, correct default the easy default** — `chmod 600` secrets, self-healing `.gitignore`, smart purge that never destroys data.
- **Unify interactive and CI/CD workflows** so the same tool that helps a developer locally also runs reliably in pipelines via non-interactive flags and `pyve run`.
- **Refuse known footguns loudly** (cloud-synced directories, stale lock files, reserved names, backend conflicts) instead of allowing silent corruption.
- **Provide health visibility** through `pyve check` and `pyve status` so developers can diagnose drift, corruption, or misconfiguration without tribal knowledge.
- **Offer a clean upgrade path** — `pyve self migrate` moves existing projects onto the v3 manifest deterministically, so adopting improvements never means a hand-edit.

### Scope

**In scope:**

- Orchestrating, per ecosystem, a version manager + an environment backend + direnv as a single workflow (Python: asdf/pyenv + venv/micromamba; Node: nvm/fnm/volta + pnpm/npm/yarn).
- A declarative root-level `pyve.toml` manifest: `[project]`, `[env.<name>]` (purpose / backend / plugin-private attributes), `[plugins.<lang>]`.
- Named environments with purposes (`run`, `test`, `utility`, `temp`) and name-based defaults.
- A plugin + backend-provider contract so new languages and backends plug into the same composition layer.
- Composed `init` / `check` / `status` / `purge` / `.envrc` / `.gitignore` across every active plugin, for polyglot as well as single-stack projects.
- Commands: `init`, `purge`, `update`, `check`, `status`, `run`, `test`, `env`, `lock`, `package` (reserved), `python set` / `python show`, `self install` / `self uninstall` / `self migrate`.
- Backend auto-detection from project files.
- Self-healing `.gitignore` template management.
- Secure `.env` lifecycle (creation, preservation, smart purge).
- Smart re-init (`pyve update`, `pyve init --force`) and conflict detection.
- Isolated test / utility environments that survive `pyve init --force`.
- CI/CD-friendly non-interactive flags (`--no-direnv`, `--auto-bootstrap`, `--strict`, …).
- Cloud-synced directory detection.
- Micromamba bootstrap (project or user sandbox).
- Deterministic v2 → v3 migration (`pyve self migrate`).

**Out of scope:**

- Replacing the tools Pyve orchestrates (asdf, pyenv, direnv, micromamba, nvm/fnm/volta, pnpm/npm/yarn).
- Installing version managers (asdf, pyenv, nvm, …) or `conda-lock` as standalone binaries.
- Managing project dependencies beyond initial environment creation.
- GUI or web interface.
- Windows support.

**Roadmap (under consideration via the plugin contract — not shipped in v3.0):**

- Additional language plugins (e.g. Ruby, Rust, Go).
- Additional backend categories and providers — cache-backed (e.g. Rust, Go) and check-only (e.g. Docker / Podman, Homebrew, apt, mobile toolchains).
- `pyve package` providers (the verb is reserved and scaffolded in v3.0; concrete providers land post-v3.0).

### Constraints

- **Pure Bash**, no runtime dependencies, no background daemons (Pyve's own Python helpers run in a hidden, Pyve-owned toolchain venv, never the user's environment).
- **macOS and Linux only**
- **Orchestrate, don't replace** — must defer to existing tools where they already work
- **Idempotent** — every operation must produce the same result on repeated runs
- **Never destroy user data** — non-empty `.env` files, user code, git history, `package.json`, and lockfiles are inviolable
- **Asks before invasive actions** — networked installs of non-critical dependencies (micromamba, pytest) require confirmation in interactive mode
- **Apache 2.0 licensed**

---

## Value Mapping

**repetitive_setup**:
  - `pyve init` collapses language-version selection, environment creation, direnv configuration, `.env` setup, and `.gitignore` management into a single command
  - Smart re-init (`pyve update` / `pyve init --force`) handles existing projects without manual cleanup

**command_recall**:
  - One consistent CLI (`pyve`) replaces the need to remember asdf, pyenv, venv, micromamba, nvm, pnpm, conda-lock, and direnv syntax separately
  - `pyve check` and `pyve status` surface current state without requiring memorized inspection commands

**activation_friction**:
  - direnv integration is configured automatically by `pyve init`, giving auto-activation/deactivation on directory entry/exit for free
  - `pyve run <cmd>` provides explicit, stateless execution for contexts where direnv isn't appropriate

**env_setup_complexity**:
  - Pyve encodes the "right way" to create and configure each backend so users don't take shortcuts to avoid friction
  - Micromamba projects get correct `.vscode/settings.json` handling automatically
  - Reserved environment directory names are rejected before they cause confusion

**tool_coordination**:
  - Pyve presents a single, uniform interface over each ecosystem's version manager + backend + direnv
  - Backend auto-detection (`environment.yml` → micromamba, `pyproject.toml` → venv, `package.json` + lockfile → the matching Node provider) removes the need to know which tool fits which project
  - `pyve.toml` records each environment's backend and version intent so the project's setup is portable

**cross_stack_coordination**:
  - The composition layer fans one `pyve <cmd>` across every declared plugin and composes the results into one `.envrc`, one `.gitignore`, and one `check` / `status` / `purge` surface
  - Polyglot `pyve init` scaffolds Python and Node at distinct paths, so two plugins never collide on the project root

**per_ecosystem_relearning**:
  - The same verbs and the same manifest shape work for every plugin — learn `pyve` once instead of each ecosystem's tool zoo

**machine_inconsistency**:
  - The same `pyve init` produces the same environment shape on every machine
  - CI/CD-friendly flags make the same workflow work in pipelines as on a laptop
  - `pyve check` and `pyve status` confirm that a project's setup matches expectations

**secret_safety**:
  - `.env` is created with `chmod 600` (owner read/write only)
  - `.env` is automatically added to `.gitignore` to prevent accidental commits
  - `pyve purge` preserves non-empty `.env` files instead of deleting them

**cloud_sync_corruption**:
  - `pyve init` refuses to initialize inside known cloud-synced directories (`~/Documents`, `~/Dropbox`, `~/Google Drive`, `~/OneDrive`, `~/Library/Mobile Documents`) using both path heuristics and macOS xattr inspection
  - Error messages include the detected sync provider, a recommended `mv` command, and an `--allow-synced-dir` override for users who have disabled sync on the directory

**reinit_footguns**:
  - Test and utility environments are declared in `pyve.toml` and materialize under `.pyve/envs/<name>/<backend>/`, separate from the run environment, so `pyve init --force` cannot wipe them
  - `pyve update` rejects backend changes that would require a destructive rebuild
  - `pyve init --force` requires interactive confirmation before purging
  - `pyve check` and `--strict` mode surface stale `conda-lock.yml` files before they cause divergence

**upgrade_friction**:
  - `pyve self migrate` reads a project's legacy v2 sources, writes the equivalent `pyve.toml`, backs the old files up, and rebuilds the environments at the v3 layout — deterministically and idempotently, with `--dry-run` / `--no-rebuild` to preview
