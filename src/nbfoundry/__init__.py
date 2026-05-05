# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0

from nbfoundry._version import __version__
from nbfoundry.compiler import compile_exercise
from nbfoundry.errors import ExerciseError

__all__ = ["ExerciseError", "__version__", "compile_exercise"]
