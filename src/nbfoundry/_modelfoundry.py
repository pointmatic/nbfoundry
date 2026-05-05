# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ModelfoundryAdapter(Protocol):
    def prepare_data(self, *args: Any, **kwargs: Any) -> Any: ...
    def train(self, *args: Any, **kwargs: Any) -> Any: ...
    def optimize(self, *args: Any, **kwargs: Any) -> Any: ...
    def evaluate(self, *args: Any, **kwargs: Any) -> Any: ...


_INSTALL_HINT = (
    "modelfoundry is required for this feature but is not installed. "
    "Install it once it is available, or use `nbfoundry` features that do "
    "not depend on modelfoundry."
)


def get_adapter() -> ModelfoundryAdapter:
    try:
        import modelfoundry
    except ImportError as e:
        raise RuntimeError(_INSTALL_HINT) from e

    return modelfoundry  # type: ignore[no-any-return]
