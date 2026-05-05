# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Literal

from markdown_it import MarkdownIt

MarkdownFlavor = Literal["commonmark", "gfm"]

_GFM_RULES = ("table", "strikethrough")


def _build(flavor: MarkdownFlavor) -> MarkdownIt:
    md = MarkdownIt("commonmark")
    if flavor == "gfm":
        md.enable(list(_GFM_RULES))
    return md


def render(text: str, flavor: MarkdownFlavor) -> str:
    return _build(flavor).render(text).rstrip()
