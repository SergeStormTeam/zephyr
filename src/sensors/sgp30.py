from logging import getLogger, Logger

import adafruit_sgp30 as SGP30
import board
import busio

import time
from datetime import datetime, timedelta
from sensors.base import BaseSensor
from db import database

logger: Logger = getLogger(__name__)


class SGP30Sensor(BaseSensor):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.i2c: busio.I2C | None = None
        self.sensor: SGP30.Adafruit_SGP30 | None = None
        self.sensor_name = "SGP30"
        self.baseline_saved_at: datetime
        self.cur_eco2: float = 0
        self.cur_tvoc: float = 0

        db, cursor = database.create_new_connection()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sgp30 (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),

                co2_baseline INTEGER NOT NULL,
                voc_baseline INTEGER NOT NULL,
                timestamp REAL NOT NULL
            );
        """)
        db.commit()
        db.close()

    def _connect(self) -> None:
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = SGP30.Adafruit_SGP30(self.i2c)
        self.baseline_saved_at = datetime.now()

        db, cursor = database.create_new_connection()

        row = cursor.execute("""
           SELECT co2_baseline, voc_baseline
            FROM sgp30
            WHERE singleton = 1;
        """).fetchone()

        if row:
            self.sensor.set_iaq_baseline(row["co2_baseline"], row["voc_baseline"])

        db.commit()
        db.close()

        self.sensor.iaq_init()
        time.sleep(15)
        return

    def _disconnect(self) -> None:
        return

    def update(self) -> Exception | None:

        if not self.sensor:
            raise RuntimeError("BME280 was not initalized!")

        if (
            self.ctx.latest_reading
            and self.ctx.latest_reading.temperature
            and self.ctx.latest_reading.humidity
        ):
            self.sensor.set_iaq_relative_humidity(
                self.ctx.latest_reading.temperature, self.ctx.latest_reading.humidity
            )

        self.cur_eco2 = self.sensor.eCO2
        self.cur_tvoc = self.sensor.TVOC

        if datetime.now() > (self.baseline_saved_at + timedelta(minutes=15)):
            db, cursor = database.create_new_connection()

            cursor.execute(
                """
                INSERT OR REPLACE INTO sgp30 (singleton, co2_baseline, voc_baseline, timestamp) VALUES (1, ?, ?, ?)
            """,
                (self.sensor.baseline_eCO2, self.sensor.baseline_TVOC, time.time()),
            )

            db.commit()
            db.close()
        return

    def read(self) -> dict[str, float]:
        return {"co2": self.cur_eco2, "voc": self.cur_tvoc}
