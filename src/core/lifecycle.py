import threading
import logging
from app.context import AppContext

from services import sensor_reader, backup, websocket_connections
from db import database

import uuid_utils as uuid

logger: logging.Logger = logging.getLogger(__name__)


def _generate_session_id() -> str:
    """
    Generates a New UUID using the UUID7 formating

    Returns:
        str: The generated UUID in string form
    """
    generated_uuid: uuid.UUID = uuid.uuid7()
    return str(generated_uuid)


def start_session(ctx: AppContext) -> bool:
    if ctx.session_active:
        return False
    ctx.thread_shutdown.clear()

    logger.info("Starting Initalization Sequence!")

    # sensor_reader.initalize_sensors(ctx=running_context)
    # database.initialize_database()

    ctx.filewriting_thread = threading.Thread(
        target=database.update_database_loop, args=(ctx,)
    )
    ctx.filewriting_thread.start()

    ctx.sensor_reading_thread = threading.Thread(
        target=sensor_reader.read_sensor_loop,
        args=(ctx,),
    )
    ctx.sensor_reading_thread.start()

    ctx.database_backup_thread = threading.Thread(
        target=backup.run_backup_loop, args=(ctx,)
    )
    ctx.database_backup_thread.start()

    ctx.server_live_update_thread = threading.Thread(
        target=websocket_connections.run_websocket_loops, args=(ctx,)
    )
    ctx.session_id = _generate_session_id()

    database.log_event(f"STARTED APPLICATION: {ctx.session_id}", logging.INFO)
    logger.info(
        f"Succussfully Initalized All Applications! Current Session ID: {ctx.session_id}"
    )

    return True


def stop_session(ctx: AppContext) -> bool:
    if not ctx.session_active or ctx.thread_shutdown.is_set():
        return False
    ctx.thread_shutdown.set()

    logger.info("Starting shutdown sequence!")

    database.log_event(f"STOPPED APPLICATION:{ctx.session_id}", logging.INFO)

    if ctx.sensor_reading_thread:
        logger.info("Shutting down sensors")
        ctx.sensor_reading_thread.join()
        ctx.sensor_reading_thread = None

    logger.info("Successfully shut down sensors")

    if ctx.filewriting_thread:
        logger.info("Stopping Filewriting Thread!")
        ctx.filewriting_thread.join()
        ctx.filewriting_thread = None
    logger.info("Stopped Filewriting Thread!")

    if ctx.server_live_update_thread:
        logger.info("Stopping websocket thread!")
        ctx.server_live_update_thread.join()
        ctx.server_live_update_thread = None
    logger.info("Websocket thread stopped.")

    if ctx.database_backup_thread:
        logger.info("Stopping database backup thread!")
        ctx.database_backup_thread.join()
        ctx.database_backup_thread = None
    logger.info("Stopped database backup thread!")

    logger.info("Shutdown complete.")

    ctx.session_active = False
    return True
