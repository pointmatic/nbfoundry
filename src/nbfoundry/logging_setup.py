# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import sys

_FORMAT = "%(levelname)s %(name)s: %(message)s"
_LOGGER_NAME = "nbfoundry"


def configure(level: int) -> None:
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_FORMAT))
    logger.addHandler(handler)
