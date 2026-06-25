from collections.abc import Sequence
from typing import Protocol, TypeVar

T = TypeVar("T")


class RandomProvider(Protocol):
    def choice(self, seq: Sequence[T]) -> T:
        """Returns a random element from the non-empty sequence."""
        ...
