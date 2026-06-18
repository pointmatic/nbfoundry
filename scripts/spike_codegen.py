# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Story I.a spike — runnable marimo module from an ExerciseDefinition.

Throwaway prototype proving the Option C cell-emission pattern that
`nbfoundry.codegen.generate` (lands in Story I.c) will follow:

  1. Definition (title + description + sections) → a single self-contained
     `marimo.App()` module as a string.
  2. The generator imports zero ML framework code at build time; framework
     imports (e.g. `import torch`) appear only as source text inside emitted
     cells.
  3. Same definition → byte-identical module string across runs
     (deterministic cell order, deterministic formatting, no timestamps).

The script:
  - Defines a minimal `ExerciseDefinition` dataclass + tiny generator.
  - Writes the generated module to a tempfile.
  - Runs each deliverable check (determinism, build-time purity AST scan,
    syntactic validity of the generated module).
  - Prints the tempfile path so the developer can run `marimo run` /
    `marimo edit` against it on Apple Silicon hardware.

DELETED at the end of Story I.a once findings are captured in
`docs/specs/phase-i-learningfoundry-integration-refactoring-plan.md`. The
production generator lives in `src/nbfoundry/codegen.py` (Story I.c) and
regression coverage lands in Story I.e.
"""

from __future__ import annotations

import ast
import hashlib
import tempfile
from dataclasses import dataclass
from pathlib import Path

# The generated module embeds this string in `__generated_with` so marimo
# can track which version of the toolchain produced it. The production
# generator in I.c will source this from the same place
# `environment.dependencies` is rendered from, rather than hard-coding it.
MARIMO_VERSION = "0.23.9"

# Spike's narrow forbidden list — packages whose presence at build time
# would constitute an FR-7 / AC-10 violation. The full no-ML-import AST
# scan in Story I.e widens this and runs against `codegen.py` and the
# compile path; the spike just self-checks the prototype.
_FORBIDDEN_BUILD_TIME_IMPORTS = (
    "torch",
    "tensorflow",
    "keras",
    "transformers",
    "datasets",
    "peft",
    "sentencepiece",
    "tiktoken",
    "optuna",
    "modelfoundry",
    "datarefinery",
)


@dataclass(frozen=True)
class Section:
    title: str
    description: str  # markdown source
    code: str  # python source (author cell body, may be empty)


@dataclass(frozen=True)
class ExerciseDefinition:
    title: str
    description: str  # markdown source
    sections: tuple[Section, ...]


def _indent(text: str, prefix: str = "    ") -> str:
    stripped = text.rstrip("\n")
    if not stripped.strip():
        return prefix + "pass"
    return "\n".join(prefix + line if line else line for line in stripped.splitlines())


def _header_cell(banner_md: str) -> str:
    # First cell: import marimo as mo, render the banner, export mo so
    # downstream markdown cells can reuse it via marimo's reactive
    # arg-injection.
    return (
        "@app.cell\n"
        "def _():\n"
        "    import marimo as mo\n"
        "\n"
        f"    mo.md({banner_md!r})\n"
        "    return (mo,)\n"
    )


def _markdown_cell(md_source: str) -> str:
    return (
        "@app.cell\n"
        "def _(mo):\n"
        f"    mo.md({md_source!r})\n"
        "    return\n"
    )


def _code_cell(code: str) -> str:
    return "@app.cell\ndef _():\n" + _indent(code) + "\n    return\n"


def _banner_markdown(defn: ExerciseDefinition) -> str:
    return f"# {defn.title}\n\n{defn.description.rstrip()}"


def _section_markdown(section: Section) -> str:
    return f"## {section.title}\n\n{section.description.rstrip()}"


def generate(defn: ExerciseDefinition) -> str:
    """Render `defn` to a self-contained marimo.App() module string."""
    cells = [_header_cell(_banner_markdown(defn))]
    for section in defn.sections:
        cells.append(_markdown_cell(_section_markdown(section)))
        cells.append(_code_cell(section.code))

    header = (
        "import marimo\n"
        "\n"
        f"__generated_with = {MARIMO_VERSION!r}\n"
        "app = marimo.App()\n"
    )
    footer = 'if __name__ == "__main__":\n    app.run()\n'
    return header + "\n\n" + "\n\n".join(cells) + "\n\n" + footer


_SAMPLE = ExerciseDefinition(
    title="MPS smoke",
    description="Confirm torch sees Apple Metal.",
    sections=(
        Section(
            title="Detect device",
            description=(
                "Pick MPS if available, else CPU. The code cell below is the "
                "only one in this spike — wiring reactive dataflow between "
                "multiple author-supplied code cells is an I.c design problem."
            ),
            code=(
                "import torch\n"
                "\n"
                "device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')\n"
                "device\n"
            ),
        ),
    ),
)


def _check_determinism(defn: ExerciseDefinition) -> tuple[bool, str]:
    a = generate(defn)
    b = generate(defn)
    digest = hashlib.sha256(a.encode("utf-8")).hexdigest()
    return a == b, digest


def _check_build_time_purity(spike_path: Path) -> tuple[bool, list[str]]:
    tree = ast.parse(spike_path.read_text(encoding="utf-8"))
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _FORBIDDEN_BUILD_TIME_IMPORTS:
                    bad.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in _FORBIDDEN_BUILD_TIME_IMPORTS:
                bad.append(node.module or "<relative>")
    return (not bad), bad


def _check_generated_module_parses(source: str) -> tuple[bool, str]:
    try:
        ast.parse(source)
    except SyntaxError as exc:
        return False, f"{exc.__class__.__name__}: {exc}"
    return True, ""


def main() -> int:
    source = generate(_SAMPLE)

    out_dir = Path(tempfile.mkdtemp(prefix="nbfoundry_spike_codegen_"))
    out_path = out_dir / "spike_exercise.py"
    out_path.write_text(source, encoding="utf-8")

    same, digest = _check_determinism(_SAMPLE)
    pure, bad = _check_build_time_purity(Path(__file__))
    parses, parse_err = _check_generated_module_parses(source)

    print(f"Generated module:                      {out_path}")
    print(f"Module bytes:                          {len(source.encode('utf-8'))}")
    print(f"SHA-256:                               {digest}")
    print(f"Determinism (two runs byte-identical): {'PASS' if same else 'FAIL'}")
    print(f"Build-time purity (AST scan):          {'PASS' if pure else 'FAIL'}")
    if bad:
        print(f"  Forbidden imports detected:          {bad}")
    print(f"Generated module is valid Python:      {'PASS' if parses else 'FAIL'}")
    if not parses:
        print(f"  Parse error:                         {parse_err}")
    print()
    print("Developer-hardware verify (marimo round-trip):")
    print(f"  marimo run  {out_path}")
    print(f"  marimo edit {out_path}")
    return 0 if (same and pure and parses) else 1


if __name__ == "__main__":
    raise SystemExit(main())
