import time

import uuid_utils as uuid


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

    def __init__(
        self,
        sequence: int,
        temperature: float | None = None,
        humidity: float | None = None,
        pressure: float | None = None,
        voc: float | None = None,
        wind_speed: float | None = None,
        co2: float | None = None,
        precipitation: float | None = None,
    ) -> None:

        self.sequence: int = sequence
        self.temperature: float | None = temperature
        self.humidity: float | None = humidity
        self.pressure: float | None = pressure
        self.voc: float | None = voc
        self.wind_speed: float | None = wind_speed
        self.co2: float | None = co2
        self.precipitation: float | None = precipitation

        self.record_id: str = str(uuid.uuid7())
        self.timestamp: float = time.time()

    def json(self) -> dict[str, float | None | str]:
        return {
            "temperature": self.temperature,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "voc": self.voc,
            "wind_speed": self.wind_speed,
            "co2": self.co2,
            "precipitation": self.precipitation,
            "record_id": self.record_id,
            "timestamp": self.timestamp,
        }

    def json_data(self) -> dict[str, float | None | str]:
        return {
            "temperature": self.temperature,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "voc": self.voc,
            "wind_speed": self.wind_speed,
            "co2": self.co2,
            "precipitation": self.precipitation,
        }
