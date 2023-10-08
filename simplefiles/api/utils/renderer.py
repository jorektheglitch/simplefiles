from typing import Protocol, TypeVar

from .response import Response


T = TypeVar("T")
Output = TypeVar("Output", covariant=True)


class Renderer(Protocol[T, Output]):
    def __call__(self, response: Response[T]) -> Output:
        pass
