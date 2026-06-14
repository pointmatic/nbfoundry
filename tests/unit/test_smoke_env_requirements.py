# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
"""Guard the per-framework smoke-env requirements files (Story F.f.3).

The two hardware-smoke envs declared in `pyve.toml` (`smoke-torch` and
`smoke-tensorflow`) are differentiated *only* by their pip requirements files
under `tests/integration/env/`. That separation is what makes the F.f.1
co-residence SIGBUS (PyTorch-MPS + TensorFlow-Metal in one process) and the
F.f.2 keras-hygiene contamination *impossible by construction*: torch and
TensorFlow are never installed into the same env, and the TensorFlow env never
pulls a standalone `keras`.

These hardware-independent tests lock that invariant in so a future edit that
reintroduces co-residence (e.g. adding `tensorflow` to `torch.txt`) fails
loudly in CI rather than re-surfacing as a native crash on developer hardware.
See `docs/specs/env-dependencies.md` sections 5.2 and 5.3.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ENV_DIR = Path(__file__).resolve().parents[1] / "integration" / "env"
TORCH_REQS = ENV_DIR / "torch.txt"
TF_REQS = ENV_DIR / "tensorflow.txt"


def _requirement_names(path: Path) -> set[str]:
    """Lowercased distribution names declared in a pip requirements file.

    Strips comments, blank lines, `-r` include directives, and any version
    specifier / extras / environment marker so only the bare distribution name
    remains.
    """
    names: set[str] = set()
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        # Split off version specifiers, extras, and markers.
        for sep in (";", "[", "=", "<", ">", "!", "~", " "):
            line = line.split(sep, 1)[0]
        name = line.strip().lower()
        if name:
            names.add(name)
    return names


@pytest.mark.parametrize("path", [TORCH_REQS, TF_REQS], ids=["torch", "tensorflow"])
def test_requirements_file_exists_with_license_header(path: Path) -> None:
    assert path.is_file(), f"{path} must exist (declared in pyve.toml)"
    head = path.read_text().splitlines()[:2]
    assert head == [
        "# Copyright (c) 2026 Pointmatic",
        "# SPDX-License-Identifier: Apache-2.0",
    ], f"{path} must carry the Apache-2.0 / Pointmatic header"


def test_torch_env_has_torch_family_stack() -> None:
    names = _requirement_names(TORCH_REQS)
    for required in ("torch", "transformers", "datasets", "peft", "numpy", "pytest"):
        assert required in names, f"torch.txt must declare {required!r}"


def test_tensorflow_env_has_tensorflow_family_stack() -> None:
    names = _requirement_names(TF_REQS)
    for required in ("tensorflow-macos", "tensorflow-metal", "numpy", "pytest"):
        assert required in names, f"tensorflow.txt must declare {required!r}"


def test_torch_env_excludes_tensorflow_family() -> None:
    """The F.f.1 isolation boundary: no TensorFlow / standalone keras in torch env."""
    names = _requirement_names(TORCH_REQS)
    for forbidden in ("tensorflow", "tensorflow-macos", "tensorflow-metal", "keras"):
        assert forbidden not in names, (
            f"torch.txt must NOT declare {forbidden!r} — torch-MPS and TF-Metal "
            "cannot co-reside in one process (F.f.1 SIGBUS)"
        )


def test_tensorflow_env_excludes_torch_and_huggingface_and_standalone_keras() -> None:
    """The F.f.1/F.f.2 isolation boundary for the TensorFlow env."""
    names = _requirement_names(TF_REQS)
    for forbidden in ("torch", "transformers", "datasets", "peft", "keras"):
        assert forbidden not in names, (
            f"tensorflow.txt must NOT declare {forbidden!r} — keeping torch/HF out "
            "(and standalone keras absent) is what makes F.e's hygiene guard pass "
            "by construction (F.f.2)"
        )
