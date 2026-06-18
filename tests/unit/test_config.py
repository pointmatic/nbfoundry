# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Config unit sweep (Story G.b) — defaults, toml load, precedence, bad keys."""

from __future__ import annotations

from pathlib import Path

from nbfoundry.config import Config, load, merge_cli


def test_missing_toml_returns_defaults(tmp_path: Path) -> None:
    cfg = load(tmp_path)
    assert cfg == Config()
    assert cfg.compile.default_out == "dist/"
    assert cfg.exercise.markdown_flavor == "commonmark"
    assert cfg.environment.spec_path == "requirements-base.txt"


def test_toml_overrides_defaults(tmp_path: Path) -> None:
    (tmp_path / "nbfoundry.toml").write_text(
        '[compile]\ndefault_out = "build/"\n[exercise]\nmarkdown_flavor = "gfm"\n',
        encoding="utf-8",
    )
    cfg = load(tmp_path)
    assert cfg.compile.default_out == "build/"
    assert cfg.exercise.markdown_flavor == "gfm"
    # untouched sections keep defaults
    assert cfg.environment.spec_path == "requirements-base.txt"


def test_unknown_keys_are_ignored(tmp_path: Path) -> None:
    (tmp_path / "nbfoundry.toml").write_text(
        '[compile]\ndefault_out = "out/"\nbogus_key = 1\n[mystery]\nfoo = "bar"\n',
        encoding="utf-8",
    )
    cfg = load(tmp_path)
    assert cfg.compile.default_out == "out/"
    assert not hasattr(cfg.compile, "bogus_key")


def test_merge_cli_overrides_take_precedence() -> None:
    base = Config()
    merged = merge_cli(base, default_out="cli_out/", markdown_flavor="gfm")
    assert merged.compile.default_out == "cli_out/"
    assert merged.exercise.markdown_flavor == "gfm"


def test_merge_cli_ignores_none_values() -> None:
    base = merge_cli(Config(), default_out="x/")
    merged = merge_cli(base, default_out=None, markdown_flavor=None)
    assert merged.compile.default_out == "x/"  # unchanged by None


def test_precedence_cli_over_toml_over_defaults(tmp_path: Path) -> None:
    (tmp_path / "nbfoundry.toml").write_text('[compile]\ndefault_out = "toml/"\n', encoding="utf-8")
    cfg = load(tmp_path)  # toml > default
    assert cfg.compile.default_out == "toml/"
    final = merge_cli(cfg, default_out="cli/")  # cli > toml
    assert final.compile.default_out == "cli/"
