"""Compatibility helpers for the repository's supported Python >=3.10."""

from __future__ import annotations
try:
    from enum import StrEnum
except ImportError:  # Python 3.10
    from enum import Enum

    class StrEnum(str, Enum):
        def __str__(self) -> str:
            return str(self.value)
