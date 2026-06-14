import time

from dataclasses import dataclass, field
import uuid_utils as uuid


@dataclass(slots=True)
class ProbeData:
    """
    Class for data readings taken by the probe during operation.

    Attributes:
        sequence (int): The "sequence" of the reading. An auto-incrementing number from the start of the run for ordering purposes

        temperature (float | None): The temperature reading, in Celcius
        humidity (float | None): The humidity reading, in Relative Humidity (percentage of vapor -> air)
        pressure (float | None): The pressure reading, in Barometric Pressure
        voc (float | None): The tVOC reading, in Parts Per Billion
        wind_speed (float | None): The Wind Speed, in GOD knows what!
        co2 (float | None): The eCO2, in Parts Per Million
        precipitation (float | None): The Precipitation amount, in GOD knows what!

        record_id (str): An automatically generated UUID7 for logging purposes
        timestamp (float): An automatically generated timestamp using the Unix epoch
    """

    sequence: int
    temperature: float | None
    humidity: float | None
    pressure: float | None
    voc: float | None
    wind_speed: float | None
    co2: float | None
    precipitation: float | None

    record_id: str = field(default_factory=lambda: str(uuid.uuid7()))
    timestamp: float = field(default_factory=time.time)
