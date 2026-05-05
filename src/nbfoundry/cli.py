# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import logging
import shutil
import sys
from importlib.resources import as_file, files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Annotated

import typer

from nbfoundry import compile_exercise, validate_exercise
from nbfoundry._version import __version__
from nbfoundry.config import load as load_config
from nbfoundry.config import merge_cli
from nbfoundry.errors import ExerciseError
from nbfoundry.logging_setup import configure as configure_logging
from nbfoundry.standalone import compile as compile_standalone

_TEMPLATES_PACKAGE = "nbfoundry.templates"
_TEMPLATE_SKIP = {"__init__.py", "__pycache__"}

app = typer.Typer(
    name="nbfoundry",
    help="Marimo-based notebook framework for ML/DS work.",
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_enable=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"nbfoundry {__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable DEBUG-level logging."),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress all but ERROR-level logging."),
    ] = False,
) -> None:
    if verbose and quiet:
        raise typer.BadParameter("--verbose and --quiet are mutually exclusive")
    level = logging.DEBUG if verbose else logging.ERROR if quiet else logging.WARNING
    configure_logging(level)


@app.command("init")
def cmd_init(
    name: Annotated[str, typer.Argument(help="Project directory name.")],
    template: Annotated[
        str,
        typer.Option("--template", help="Five-stage template name."),
    ] = "data_exploration",
) -> None:
    """Scaffold a new exercise project from a template."""
    target = Path.cwd() / name
    if target.exists():
        raise ExerciseError(target, f"output path already exists: {target}")

    template_root = files(_TEMPLATES_PACKAGE).joinpath(template)
    if not template_root.is_dir():
        available = sorted(
            t.name for t in files(_TEMPLATES_PACKAGE).iterdir()
            if t.is_dir() and t.name not in _TEMPLATE_SKIP
        )
        raise ExerciseError(
            target,
            f"unknown template '{template}'. Available: {', '.join(available) or '(none)'}",
        )

    target.mkdir(parents=True)
    _copy_template_tree(template_root, target)
    typer.echo(str(target))


def _copy_template_tree(src: Traversable, dst: Path) -> None:
    for entry in src.iterdir():
        if entry.name in _TEMPLATE_SKIP:
            continue
        if entry.is_dir():
            sub = dst / entry.name
            sub.mkdir()
            _copy_template_tree(entry, sub)
        else:
            with as_file(entry) as p:
                shutil.copy2(p, dst / entry.name)


@app.command("compile")
def cmd_compile(
    notebook_or_dir: Annotated[Path, typer.Argument(exists=True)],
    out: Annotated[Path | None, typer.Option("--out", help="Output directory.")] = None,
) -> None:
    """Compile a Marimo notebook (or tree) to a standalone artifact directory."""
    cwd = Path.cwd()
    cfg = merge_cli(load_config(cwd), default_out=str(out) if out else None)
    target = Path(cfg.compile.default_out)
    if not target.is_absolute():
        target = (cwd / target).resolve()
    result = compile_standalone(notebook_or_dir, target)
    typer.echo(str(result))


@app.command("compile-exercise")
def cmd_compile_exercise(
    yaml_path: Annotated[Path, typer.Argument(exists=True)],
    base_dir: Annotated[
        Path | None, typer.Option("--base-dir", help="Path resolution root.")
    ] = None,
    out: Annotated[
        Path | None, typer.Option("--out", help="Write JSON to this path instead of stdout.")
    ] = None,
    allow_large_assets: Annotated[
        bool, typer.Option("--allow-large-assets", help="Bypass max_single_asset_mb gate.")
    ] = False,
) -> None:
    """Compile an exercise YAML to its BR-1 JSON artifact."""
    effective_base = (base_dir or yaml_path.parent).resolve()
    relative = yaml_path.resolve().relative_to(effective_base)
    compiled = compile_exercise(relative, effective_base, allow_large_assets=allow_large_assets)
    rendered = json.dumps(
        compiled, sort_keys=False, ensure_ascii=False, separators=(",", ": "), indent=2
    )
    if out is None:
        typer.echo(rendered)
    else:
        out.write_text(rendered + "\n", encoding="utf-8")


@app.command("validate")
def cmd_validate(
    yaml_path: Annotated[Path, typer.Argument(exists=True)],
    base_dir: Annotated[
        Path | None, typer.Option("--base-dir", help="Path resolution root.")
    ] = None,
) -> None:
    """Validate an exercise YAML; exit 0 if clean, 1 with errors on stdout otherwise."""
    effective_base = (base_dir or yaml_path.parent).resolve()
    relative = yaml_path.resolve().relative_to(effective_base)
    errs = validate_exercise(relative, effective_base)
    if errs:
        for e in errs:
            typer.echo(e)
        raise typer.Exit(code=1)


def main() -> None:
    try:
        app()
    except ExerciseError as e:
        typer.echo(str(e), err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
