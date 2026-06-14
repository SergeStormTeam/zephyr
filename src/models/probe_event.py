import time

from dataclasses import dataclass, field
import uuid_utils as uuid


@dataclass(slots=True)
class ProbeEvent:
    """
    Class for "Events" that occur during operation. Thing like Sensors Disconnecting, Application Starting, etc

    Attributes:
        message (str): The message of the event
        severity (int): The level of severity of the incident (similar to loggers logger.WARNING Enum style)

        record_id (str): An automatically generated UUID7 for logging purposes
        timestamp (float): An automatically generated timestamp using the Unix epoch
    """

    message: str
    severity: int

    record_id: str = field(default_factory=lambda: str(uuid.uuid7()))
    timestamp: float = field(default_factory=time.time)
