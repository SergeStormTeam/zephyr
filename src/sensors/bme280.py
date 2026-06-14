from logging import getLogger, Logger
import board
import busio
from adafruit_bme280 import basic as BME280
from app.config import SEA_LEVEL_PRESSURE

from sensors.base import BaseSensor

logger: Logger = getLogger(__name__)


class BME280Sensor(BaseSensor):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.i2c: busio.I2C | None = None
        self.sensor: BME280.Adafruit_BME280_I2C | None = None
        self.sensor_name = "BME280"

        self.cur_pressure: float = 0
        self.cur_humidity: float = 0
        self.cur_temperature: float = 0

    def _connect(self) -> None:
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = BME280.Adafruit_BME280_I2C(self.i2c)
        self.sensor.sea_level_pressure = SEA_LEVEL_PRESSURE
        return

    def _disconnect(self) -> None:
        return

    def update(self) -> Exception | None:

        if not self.sensor:
            raise RuntimeError("BME280 was not initalized!")

        self.cur_pressure = self.sensor.pressure
        self.cur_humidity = self.sensor.humidity
        self.cur_temperature = self.sensor.temperature

        return

    def read(self) -> dict[str, float]:
        return {
            "pressure": self.cur_pressure,
            "humidity": self.cur_humidity,
            "temperature": self.cur_temperature,
        }
