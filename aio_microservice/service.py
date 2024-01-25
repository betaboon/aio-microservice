from __future__ import annotations


class A:
    """A class."""


class Service(A):
    """A class."""

    def __init__(self, some_arg: str) -> None:
        """Constructor docu.

        Args:
            some_arg: this arg
        """

    # def run(self) -> None:
    #     pass

    # def stop(self) -> None:
    #     pass

    async def on_start(self) -> None:
        """A Function."""

    async def some_function(
        self,
        arg1: str,
        arg2: bool = True,
        arg3: str | None = None,
        arg4: str | A | None = None,
    ) -> None:
        """Some function.

        Args:
            arg1: Some argument
            arg2: Some argument
            arg3: some description
            arg4: some more description

        Examples:
            You could use it like this:

            >>> foobar
        """

    # async def after_start(self) -> None:
    #     pass

    # async def on_stop(self) -> None:
    #     pass

    # async def after_stop(self) -> None:
    #     pass

    # async def on_sigint(self) -> None:
    #     pass

    # async def on_sigterm(self) -> None:
    #     pass

    # async def on_sighub(self) -> None:
    #     pass


# see: https://github.com/kalaspuff/tomodachi
# see: https://github.com/cjrh/aiorun/blob/master/aiorun.py


# class Service:
#     def __init__(self) -> None:
#         pass

#     def run(self) -> None:
#         pass

#     async def on_start(self) -> None:
#         pass

#     async def _on_int(self) -> None:
#         pass

#     async def _on_term(self) -> None:
#         pass

#     async def _on_hup(self) -> None:
#         pass
