# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

import typer

from nbfoundry._version import __version__

app = typer.Typer(
    name="nbfoundry",
    help="Marimo-based notebook framework for ML/DS work.",
    no_args_is_help=True,
    add_completion=False,
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
) -> None:
    pass


def main() -> None:
    app()


if __name__ == "__main__":
    main()
