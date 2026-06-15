# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Markdown unit sweep (Story G.b) — commonmark vs gfm divergence."""

from __future__ import annotations

from nbfoundry.markdown import render

_TABLE = "| a | b |\n| - | - |\n| 1 | 2 |"
_STRIKE = "~~gone~~"


def test_basic_rendering_and_rstrip() -> None:
    out = render("hello", "commonmark")
    assert out == "<p>hello</p>"  # trailing newline stripped


def test_emphasis_and_strong() -> None:
    assert render("*x*", "commonmark") == "<p><em>x</em></p>"
    assert render("**x**", "commonmark") == "<p><strong>x</strong></p>"


def test_commonmark_does_not_render_tables() -> None:
    out = render(_TABLE, "commonmark")
    assert "<table>" not in out


def test_gfm_renders_tables() -> None:
    out = render(_TABLE, "gfm")
    assert "<table>" in out
    assert "<td>1</td>" in out


def test_commonmark_does_not_render_strikethrough() -> None:
    out = render(_STRIKE, "commonmark")
    assert "<s>" not in out and "<del>" not in out


def test_gfm_renders_strikethrough() -> None:
    out = render(_STRIKE, "gfm")
    assert "<s>gone</s>" in out


def test_fenced_code_block_common_to_both() -> None:
    src = "```\nx = 1\n```"
    for flavor in ("commonmark", "gfm"):
        assert "<code>" in render(src, flavor)  # type: ignore[arg-type]
