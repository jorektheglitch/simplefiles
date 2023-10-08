from abc import abstractmethod

from typing import Protocol, TypeVar


T = TypeVar("T", covariant=True)

JSON = str | int | float | list["JSON"] | dict[str, "JSON"] | None


class Renderable(Protocol[T]):
    @abstractmethod
    def render(self) -> T:
        pass
