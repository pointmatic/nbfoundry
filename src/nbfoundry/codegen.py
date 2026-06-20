# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Marimo notebook generator (Story I.c).

`generate(defn, *, base_dir)` turns an `ExerciseDefinition` into a
self-contained `marimo.App()` module string per the cell-emission pattern
captured in the Story I.a spike findings. See
`docs/specs/phase-i-learningfoundry-integration-refactoring-plan.md`
§ "Story I.a — Spike Findings" for the target module shape and the
rationale behind the design decisions baked in below.

Build-time purity: this module imports no ML framework. Framework
imports (`import torch`, `import tensorflow`, ...) appear only as source
text inside emitted cells. Story I.e extends the no-ML-import AST scan
to cover this file authoritatively.

Marimo version sourcing: `importlib.metadata.version("marimo")` is read
at generation time and used both for `__generated_with` and for the
default `marimo>=<installed>` pin appended to
`environment.dependencies` when the author omits it.
"""

from __future__ import annotations

from importlib.metadata import version as _pkg_version
from pathlib import Path

from nbfoundry.errors import ExerciseError
from nbfoundry.paths import resolve_under
from nbfoundry.schema import (
    CompiledEnvironment,
    EnvironmentModel,
    ExerciseDefinition,
    SectionModel,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _marimo_version() -> str:
    return _pkg_version("marimo")


def _indent(text: str, prefix: str = "    ") -> str:
    stripped = text.rstrip("\n")
    if not stripped.strip():
        return prefix + "pass"
    return "\n".join(prefix + line if line else line for line in stripped.splitlines())


def _section_code(section: SectionModel, base_dir: Path) -> str:
    if section.code is not None:
        return section.code
    # SectionModel's `code_xor_code_file` validator guarantees exactly one
    # of code/code_file is set, so code_file is non-None here.
    assert section.code_file is not None
    code_path = resolve_under(base_dir, section.code_file)
    try:
        return code_path.read_text(encoding="utf-8")
    except OSError as e:
        raise ExerciseError(
            file_path=code_path,
            message=f"could not read code_file {section.code_file}: {e}",
        ) from e


# ---------------------------------------------------------------------------
# Cell emitters
# ---------------------------------------------------------------------------


def _header_cell(banner_md: str) -> str:
    # The banner is pure presentation: hide its code (Story I.h) so the learner
    # sees the rendered title+description, not the `import marimo as mo` /
    # `mo.md(...)` boilerplate. `mo` is still defined and exported, so the
    # markdown cells' dataflow is unchanged — `hide_code` is display-only.
    return (
        "@app.cell(hide_code=True)\n"
        "def _():\n"
        "    import marimo as mo\n"
        "\n"
        f"    mo.md({banner_md!r})\n"
        "    return (mo,)\n"
    )


def _markdown_cell(md_source: str) -> str:
    # Per-section markdown (header) cells are pure presentation, like the banner
    # (Story I.i): hide their `mo.md(...)` code. `mo` is still injected via
    # marimo's reactive args — `hide_code` is display-only.
    return f"@app.cell(hide_code=True)\ndef _(mo):\n    mo.md({md_source!r})\n    return\n"


def _code_cell(code: str, *, hide_code: bool = False) -> str:
    decorator = "@app.cell(hide_code=True)" if hide_code else "@app.cell"
    return decorator + "\ndef _():\n" + _indent(code) + "\n    return\n"


def _banner_markdown(defn: ExerciseDefinition) -> str:
    return f"# {defn.title}\n\n{defn.description.rstrip()}"


def _section_markdown(section: SectionModel) -> str:
    return f"## {section.title}\n\n{section.description.rstrip()}"


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


def generate(defn: ExerciseDefinition, *, base_dir: Path) -> str:
    """Render `defn` to a self-contained `marimo.App()` module string.

    Sections with inline `code` are emitted verbatim. Sections with
    `code_file` are read from disk relative to `base_dir`, guarded by
    `paths.resolve_under` (raises `ExerciseError` on escape or missing
    file).
    """
    cells = [_header_cell(_banner_markdown(defn))]
    for section in defn.sections:
        cells.append(_markdown_cell(_section_markdown(section)))
        cells.append(_code_cell(_section_code(section, base_dir), hide_code=section.hide_code))

    header = f"import marimo\n\n__generated_with = {_marimo_version()!r}\napp = marimo.App()\n"
    footer = 'if __name__ == "__main__":\n    app.run()\n'
    return header + "\n\n" + "\n\n".join(cells) + "\n\n" + footer


def _dep_is_marimo(dep: str) -> bool:
    """True iff `dep` is a requirement specifier for the `marimo` package.

    Matches `marimo`, `marimo>=...`, `marimo==...`, `marimo[lsp]>=...`,
    etc. Does **not** match other packages whose names happen to start
    with `marimo`, e.g. `marimo-extension` or `marimo_helper`.
    """
    stripped = dep.strip()
    if not stripped.startswith("marimo"):
        return False
    rest = stripped[len("marimo") :]
    return rest == "" or rest[0] in "[=<>!~ "


def ensure_marimo_pinned(env: EnvironmentModel | None) -> CompiledEnvironment | None:
    """Surface `marimo` into the compiled environment.

    - `env is None` → returns `None` (author opted out of declaring a
      learner-runtime environment; codegen does not synthesize one).
    - `env` provided but `dependencies` has no marimo entry → appends
      `marimo>=<installed-version>`.
    - `env` already lists marimo (with or without a version specifier or
      extras) → passes the dependencies list through verbatim.

    `python_version` and `setup_instructions` are preserved unchanged.
    """
    if env is None:
        return None
    deps = list(env.dependencies)
    if not any(_dep_is_marimo(d) for d in deps):
        deps.append(f"marimo>={_marimo_version()}")
    return CompiledEnvironment(
        python_version=env.python_version,
        dependencies=deps,
        setup_instructions=env.setup_instructions,
    )
