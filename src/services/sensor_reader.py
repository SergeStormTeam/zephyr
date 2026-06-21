import time
import logging

from sensors.base import BaseSensor
from sensors.bme280 import BME280Sensor
from sensors.sgp30 import SGP30Sensor

from app.config import SENSOR_FAIL_SHUTDOWN_LIMIT, SENSOR_READING_DEBOUNCE_TIME
from db import database
from app.context import AppContext, ProbeData

SENSOR_LIST: list[type[BaseSensor]] = [BME280Sensor, SGP30Sensor]

loaded_sensors: set[BaseSensor] = set()
failed_sensors: dict[BaseSensor, int] = {}

logger: logging.Logger = logging.getLogger(__name__)
current_sequence_number: int = 1


def process_failed_sensor(sensor: BaseSensor, e: Exception) -> None:
    """
    Processes a failed sensor, removing it from running sensors if above the configurated SENSOR_FAIL_SHUTDOWN_LIMIT

    Arguments:
        sensor (types.ModuleType): The sensor that failed
    """
    global loaded_sensors, failed_sensors

    if sensor in failed_sensors:
        failed_sensors[sensor] += 1
        if failed_sensors[sensor] > SENSOR_FAIL_SHUTDOWN_LIMIT:
            if sensor in loaded_sensors:
                loaded_sensors.remove(sensor)
            failed_sensors.pop(sensor, None)

            logger.warning(
                f"SENSOR {sensor.__name__} HAS FAILED MORE THAN {SENSOR_FAIL_SHUTDOWN_LIMIT} TIMES, REMOVING IT FROM PROCESSING!"
            )
            database.log_event(
                f"SENSOR {sensor.__name__} HAS FAILED MORE THAN {SENSOR_FAIL_SHUTDOWN_LIMIT} TIMES, REMOVING IT FROM PROCESSING!",
                logging.WARNING,
            )
            return
    else:
        failed_sensors[sensor] = 1

    logger.warning(
        f"SENSOR {sensor.sensor_name} HAS FAILED {failed_sensors[sensor]} TIMES! SENSOR WILL CONTINUE TO BE PROCESSED"
    )

    database.log_event(
        f"SENSOR {sensor.sensor_name} HAS FAILED {failed_sensors[sensor]} TIMES! SENSOR WILL CONTINUE TO BE PROCESSED: {e}",
        logging.WARNING,
    )


def update_sensor(sensor: BaseSensor) -> Exception | None:
    """
    Processes a sensor, safely updating attributes to be read

    Arguments:
        sensor (types.ModuleType): The sensor to be processed
    """
    global sensor_map, failed_sensors, logger

    try:
        err = sensor.update()

        if err:
            raise err

        if sensor in failed_sensors:
            failed_sensors.pop(sensor)

    except Exception as e:
        logger.warning(f"SENSOR {sensor.__name__} FAILED WITH ERROR: {e}")
        process_failed_sensor(sensor, e)
        return e


def initalize_sensors(ctx) -> None:
    """
    Loads all sensors from the LOADED SENSORS, ensuring that both an "update" and "get_read_functions" exists
    """
    global loaded_sensors

    logger.info("Attempting to Load Sensors!")

    for sensor in SENSOR_LIST:
        new_sensor = sensor(ctx)

        try:
            new_sensor.start()
            loaded_sensors.add(new_sensor)
        except Exception:
            logger.exception(f"SENSOR {new_sensor.sensor_name} FAILED TO INITALIZE!")
            continue

        logger.info(f"Successfully loaded the sensor {new_sensor.sensor_name}")

    logger.info("Sensors Loaded Successfully!")


def read_sensor_loop(ctx: AppContext):
    """
    Running loop for the sensor reading thread
    """
    global loaded_sensors, current_sequence_number

    while not ctx.thread_shutdown.is_set():
        newest_map: dict[str, float] = {}

        for sensor in loaded_sensors:
            error_updating_sensor: Exception | None = update_sensor(sensor)

            if error_updating_sensor:
                logger.warning(f"{error_updating_sensor}")
                continue

            newest_map.update(sensor.read())

        new_data: ProbeData = ProbeData(
            sequence=current_sequence_number,
            temperature=newest_map.get("temperature"),
            humidity=newest_map.get("humidity"),
            pressure=newest_map.get("pressure"),
            voc=newest_map.get("voc"),
            wind_speed=newest_map.get("wind_speed"),
            co2=newest_map.get("co2"),
            precipitation=newest_map.get("precipitation"),
        )

        ctx.event_bus.publish("probe_data_update", new_data.json_data())
        ctx.latest_reading = new_data

        ctx.event_loop.call_soon_threadsafe(ctx.server_update.set)
        ctx.event_loop.call_soon_threadsafe(ctx.laptop_update.set)

        database.log_sensor_data(new_data)
        current_sequence_number += 1

        time.sleep(SENSOR_READING_DEBOUNCE_TIME)


def get_sensor_status(ctx) -> dict[str, bool]:
    sensor_data: dict[str, bool] = {}

    for sensor in loaded_sensors:
        sensor_data[sensor.sensor_name] = True

    for sensor in failed_sensors:
        sensor_data[sensor.sensor_name] = False

    return sensor_data
