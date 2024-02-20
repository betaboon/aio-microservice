from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from faststream.rabbit import RabbitBroker, TestRabbitBroker
from typing_extensions import override

from aio_microservice.amqp import AmqpExtension

if TYPE_CHECKING:
    from faststream.rabbit.asyncapi import Publisher

ServiceT = TypeVar("ServiceT", bound=AmqpExtension)


class AmqpBroker:
    def __init__(self, broker: RabbitBroker) -> None:
        self._faststream_rabbit_broker = broker

    def __getattr__(self, attr: str) -> Any:  # noqa: ANN401
        return getattr(self._faststream_rabbit_broker, attr)

    def __setattr__(self, attr: str, val: Any) -> None:  # noqa: ANN401
        if attr == "_faststream_rabbit_broker":
            object.__setattr__(self, attr, val)
        else:
            setattr(self._faststream_rabbit_broker, attr, val)  # pragma: no cover

    def get_published_messages(self, queue: str) -> list[Any]:
        messages: list[Any] = []
        publisher: Publisher | None = None

        for p in self._faststream_rabbit_broker._publishers.values():  # pragma: no branch
            if p.queue.name != queue:
                continue  # pragma: no cover
            publisher = p
            break

        if publisher is None or publisher.mock is None:
            return messages  # pragma: no cover

        for call in publisher.mock.call_args_list:
            args, _ = call
            messages.append(args[0])
        return messages

    def reset_published_messages(self) -> None:
        for publisher in self._faststream_rabbit_broker._publishers.values():
            if publisher.mock is None:
                continue  # pragma: no cover
            publisher.mock.reset_mock()


class TestAmqpBroker(TestRabbitBroker):
    def __init__(self, service: ServiceT, with_real: bool = False) -> None:
        super().__init__(broker=service.amqp._faststream_rabbit_broker, with_real=with_real)
        self._service = service

    @override
    async def __aenter__(self) -> AmqpBroker:  # type: ignore
        broker = await super().__aenter__()
        return AmqpBroker(broker)
