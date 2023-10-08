from __future__ import annotations

from typing import Awaitable, AsyncContextManager
from typing import Callable, Concatenate, ParamSpec
from typing import TypeVar

from .response import Response


T = TypeVar("T")
Params = ParamSpec("Params")


def ctx_injector(
    ctx_factory: Callable[[], AsyncContextManager[T]]
) -> Callable[[Callable[Concatenate[T, Params], Awaitable[Response[T]]]], Callable[Params, Awaitable[Response[T]]]]:
    def with_ctx(
        executor: Callable[Concatenate[T, Params], Awaitable[Response[T]]]
    ) -> Callable[Params, Awaitable[Response[T]]]:
        return inject_ctx(executor, ctx_factory)
    return with_ctx


def inject_ctx(
    executor: Callable[Concatenate[T, Params], Awaitable[Response[T]]],
    ctx_factory: Callable[[], AsyncContextManager[T]]
) -> Callable[Params, Awaitable[Response[T]]]:
    async def with_ctx(*args: Params.args, **kwargs: Params.kwargs) -> Response[T]:
        async with ctx_factory() as ctx:
            result = await executor(ctx, *args, **kwargs)
        return result
    return with_ctx
