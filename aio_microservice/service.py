# from service import Service as ServiceBase
import service_framework


class ServiceBase:
    def run(self) -> None:
        pass

    # def stop(self) -> None:
    #     pass

    async def on_start(self) -> None:
        pass

    async def after_start(self) -> None:
        pass

    async def on_stop(self) -> None:
        pass

    async def after_stop(self) -> None:
        pass

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
