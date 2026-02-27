"""RabbitMQ event publisher adapter for the remote-sensing service.

Wraps the shared ``RabbitMQPublisher`` to provide a service-local facade
that controllers and application services can depend on.
"""
from __future__ import annotations

from shared.messaging.publisher import RabbitMQPublisher


class RemoteSensingEventPublisher(RabbitMQPublisher):
    """Event publisher for the remote-sensing bounded context.

    Inherits the full ``connect()``, ``close()``, and ``publish()``
    interface from the shared library.  Can be extended with service-
    specific convenience methods if needed.
    """
