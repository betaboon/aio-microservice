from dataclasses import dataclass

from aio_microservice import AMQPConfig, AMQPMixin, Service, amqp


@dataclass
class SomeMessage:
    greeting: str


class AMQPService(Service, AMQPMixin):
    amqp_config = AMQPConfig()

    @amqp(queue="my.queue")
    async def on_some_message(self, message: SomeMessage) -> Nack | Requeue | None:
        new_message = ""
        await self.amqp.publish(new_message, routing_key="some.routing.key")
