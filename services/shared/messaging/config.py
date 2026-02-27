"""RabbitMQ connection and topology configuration.

Centralises exchange names, queue names, and routing keys so every
service references the same constants.  Topology is declared once by
whichever service connects first (idempotent via passive=False defaults
in aio-pika).
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------
RABBITMQ_URL: str = os.getenv(
    "RABBITMQ_URL",
    "amqp://guest:guest@rabbitmq:5672/",
)

RECONNECT_INTERVAL: int = int(os.getenv("RABBITMQ_RECONNECT_INTERVAL", "5"))
MAX_RECONNECT_ATTEMPTS: int = int(os.getenv("RABBITMQ_MAX_RECONNECT_ATTEMPTS", "0"))  # 0 = unlimited
PREFETCH_COUNT: int = int(os.getenv("RABBITMQ_PREFETCH_COUNT", "10"))


# ---------------------------------------------------------------------------
# Exchanges – one topic exchange per bounded context
# ---------------------------------------------------------------------------
FACTORY_EXCHANGE = "factory.events"
SENSOR_EXCHANGE = "sensor.events"
ALERT_EXCHANGE = "alert.events"
SATELLITE_EXCHANGE = "satellite.events"
FUSION_EXCHANGE = "fusion.events"


# ---------------------------------------------------------------------------
# Queue names – each consuming service declares its own queue and binds the
# routing-key patterns it cares about.
# ---------------------------------------------------------------------------
# Factory Service queues
FACTORY_VIOLATION_QUEUE = "factory.violation_handler"      # ← alert.violation.detected
FACTORY_SENSOR_STATUS_QUEUE = "factory.sensor_status"      # ← sensor.status.changed

# Sensor Service queues
SENSOR_FACTORY_EVENTS_QUEUE = "sensor.factory_handler"     # ← factory.suspended / factory.resumed

# Alert Service queues
ALERT_SENSOR_READINGS_QUEUE = "alert.sensor_readings"      # ← sensor.reading.created
ALERT_FACTORY_EVENTS_QUEUE = "alert.factory_handler"       # ← factory.status.changed

# Air Quality Service queues
AQ_SENSOR_READINGS_QUEUE = "airquality.sensor_readings"    # ← sensor.reading.created
AQ_ALERT_EVENTS_QUEUE = "airquality.alert_handler"         # ← alert.violation.*

# User Service queues  (minimal – mostly publishes, rarely consumes)
USER_FACTORY_EVENTS_QUEUE = "user.factory_handler"         # ← factory.suspended (notify owner)

# Remote Sensing Service queues
RS_SENSOR_READINGS_QUEUE = "remotesensing.sensor_readings"  # ← sensor.reading.created
RS_FACTORY_EVENTS_QUEUE = "remotesensing.factory_handler"   # ← factory.status.changed

# Air Quality Service – satellite & fusion event queues
AQ_SATELLITE_EVENTS_QUEUE = "airquality.satellite_handler"  # ← satellite.data.fetched
AQ_FUSION_EVENTS_QUEUE = "airquality.fusion_handler"        # ← fusion.completed

# Alert Service – fusion cross-validation queue
ALERT_VALIDATION_QUEUE = "alert.validation_handler"          # ← validation.alert


# ---------------------------------------------------------------------------
# Routing-key → queue binding map per service
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class QueueBinding:
    """Describes one queue and the routing-key patterns it should receive."""

    queue: str
    exchange: str
    routing_keys: List[str] = field(default_factory=list)


# Grouped by consuming service for easy lookup at startup.
FACTORY_SERVICE_BINDINGS: List[QueueBinding] = [
    QueueBinding(
        queue=FACTORY_VIOLATION_QUEUE,
        exchange=ALERT_EXCHANGE,
        routing_keys=["alert.violation.detected"],
    ),
    QueueBinding(
        queue=FACTORY_SENSOR_STATUS_QUEUE,
        exchange=SENSOR_EXCHANGE,
        routing_keys=["sensor.status.changed"],
    ),
]

SENSOR_SERVICE_BINDINGS: List[QueueBinding] = [
    QueueBinding(
        queue=SENSOR_FACTORY_EVENTS_QUEUE,
        exchange=FACTORY_EXCHANGE,
        routing_keys=["factory.suspended", "factory.resumed"],
    ),
]

ALERT_SERVICE_BINDINGS: List[QueueBinding] = [
    QueueBinding(
        queue=ALERT_SENSOR_READINGS_QUEUE,
        exchange=SENSOR_EXCHANGE,
        routing_keys=["sensor.reading.created"],
    ),
    QueueBinding(
        queue=ALERT_FACTORY_EVENTS_QUEUE,
        exchange=FACTORY_EXCHANGE,
        routing_keys=["factory.status.changed"],
    ),
]

AIR_QUALITY_SERVICE_BINDINGS: List[QueueBinding] = [
    QueueBinding(
        queue=AQ_SENSOR_READINGS_QUEUE,
        exchange=SENSOR_EXCHANGE,
        routing_keys=["sensor.reading.created"],
    ),
    QueueBinding(
        queue=AQ_ALERT_EVENTS_QUEUE,
        exchange=ALERT_EXCHANGE,
        routing_keys=["alert.violation.detected", "alert.violation.resolved"],
    ),
    QueueBinding(
        queue=AQ_SATELLITE_EVENTS_QUEUE,
        exchange=SATELLITE_EXCHANGE,
        routing_keys=["satellite.data.fetched"],
    ),
    QueueBinding(
        queue=AQ_FUSION_EVENTS_QUEUE,
        exchange=FUSION_EXCHANGE,
        routing_keys=["fusion.completed"],
    ),
]

USER_SERVICE_BINDINGS: List[QueueBinding] = [
    QueueBinding(
        queue=USER_FACTORY_EVENTS_QUEUE,
        exchange=FACTORY_EXCHANGE,
        routing_keys=["factory.suspended"],
    ),
]

ALERT_SERVICE_BINDINGS_EXTENDED: List[QueueBinding] = [
    QueueBinding(
        queue=ALERT_VALIDATION_QUEUE,
        exchange=FUSION_EXCHANGE,
        routing_keys=["validation.alert"],
    ),
]

# Append extended alert bindings
ALERT_SERVICE_BINDINGS = ALERT_SERVICE_BINDINGS + ALERT_SERVICE_BINDINGS_EXTENDED

REMOTE_SENSING_SERVICE_BINDINGS: List[QueueBinding] = [
    QueueBinding(
        queue=RS_SENSOR_READINGS_QUEUE,
        exchange=SENSOR_EXCHANGE,
        routing_keys=["sensor.reading.created"],
    ),
    QueueBinding(
        queue=RS_FACTORY_EVENTS_QUEUE,
        exchange=FACTORY_EXCHANGE,
        routing_keys=["factory.status.changed"],
    ),
]

# Convenience map: service-name → bindings
SERVICE_BINDINGS: Dict[str, List[QueueBinding]] = {
    "factory-service": FACTORY_SERVICE_BINDINGS,
    "sensor-service": SENSOR_SERVICE_BINDINGS,
    "alert-service": ALERT_SERVICE_BINDINGS,
    "air-quality-service": AIR_QUALITY_SERVICE_BINDINGS,
    "user-service": USER_SERVICE_BINDINGS,
    "remote-sensing-service": REMOTE_SENSING_SERVICE_BINDINGS,
}
