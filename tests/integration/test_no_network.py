# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Integration: compile/validate make zero network calls (Story G.c, AC-9 / SC-2).

A socket-level sandbox monkeypatches `socket.socket.connect` to raise. Because
`compile_exercise` / `validate_exercise` only read local files, they must succeed
with the sandbox active; if either ever opened a socket the test fails closed.
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest

from nbfoundry.compiler import compile_exercise, validate_exercise


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access attempted during compile/validate")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)


def test_sandbox_blocks_real_connections(no_network: None) -> None:
    # sanity: the sandbox itself fails closed.
    with pytest.raises(AssertionError, match="network access attempted"):
        socket.create_connection(("127.0.0.1", 9), timeout=0.1)


def test_compile_exercise_makes_no_network_calls(
    no_network: None, tmp_base_dir: Path, sample_yaml: Path
) -> None:
    out = compile_exercise(sample_yaml, tmp_base_dir)
    assert out["type"] == "exercise"


def test_validate_exercise_makes_no_network_calls(no_network: None, tmp_base_dir: Path) -> None:
    assert validate_exercise(Path("valid_minimal.yaml"), tmp_base_dir) == []
