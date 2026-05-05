# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""End-to-end compile-path spike for nbfoundry (Story A.c).

Throwaway script — superseded by `nbfoundry.compiler` in Phase C and deleted
when Story C.a lands. Wires the critical YAML → BR-1 dict path end-to-end
against a hand-written minimal fixture, before any production module exists,
to de-risk the architecture.

Run from the repository root:

    pyve run python scripts/spike_compile_exercise.py

Prints the BR-1-shaped compiled exercise dict as JSON on stdout.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from markdown_it import MarkdownIt

SPIKE_DIR = Path(__file__).resolve().parent
FIXTURE_PATH = SPIKE_DIR / "spike_fixtures" / "minimal.yaml"


def _render(md: MarkdownIt, text: str) -> str:
    return md.render(text).rstrip()


def compile_spike(yaml_path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    md = MarkdownIt("commonmark")

    sections = [
        {
            "title": s["title"],
            "description": _render(md, s.get("description", "")),
            "code": s.get("code", ""),
            "editable": bool(s.get("editable", False)),
        }
        for s in raw.get("sections", [])
    ]

    return {
        "type": "exercise",
        "source": "nbfoundry",
        "ref": str(yaml_path.name),
        "status": "ready",
        "title": raw["title"],
        "instructions": _render(md, raw.get("instructions", "")),
        "sections": sections,
        "expected_outputs": raw.get("expected_outputs", []),
        "assets": [],
        "hints": raw.get("hints", []),
        "submission": raw.get("submission"),
        "environment": raw.get("environment", {}),
    }


def main() -> None:
    compiled = compile_spike(FIXTURE_PATH)
    print(json.dumps(compiled, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
