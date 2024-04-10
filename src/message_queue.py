from collections.abc import Iterable

from faststream.rabbit import RabbitBroker

from models import Event

__all__ = ('publish_events',)


async def publish_events(
        message_queue_url: str,
        events: Iterable[Event],
) -> None:
    async with RabbitBroker(message_queue_url) as broker:
        for event in events:
            await broker.publish(
                message=event.model_dump(),
                queue='specific-units-event',
            )
