import threading
from dataclasses import dataclass
import asyncio
from models.probe_data import ProbeData
from models.event_bus import EventBus


@dataclass(slots=True)
class AppContext:
    """
    Class for the applications running context

    Attributes:
        event_loop (asyncio.AbstractEventLoop): The running asyncio loop to be used throughout the application

        probe_mode (str): The current mode of the probe, determines if some actions are taken like backing up data

        sensor_reading_thread (threading.Thread): The thread that the sensor reader runs on
        filewriting_thread (threading.Thread): The thread that the system writes to the database locally on
        database_backup_thread (threading.Thread): The thread that the system backs up to the server
        server_live_update_thread (threading.Thread): The thread that sends the latest updates to the server

        server_connected (bool): Is the backup server connected?
        server_update: (asyncio.Event): Event that fires whenever a reading is taken for the server to update

        laptop_connected (bool): Is the local laptop connected?
        server_update: (asyncio.Event): Event that fires whenever a reading is taken for the laptop to update

        latest_reading (ProbeData): The most recent reading from the probe, None if none has been taken yet
        thread_shutdown (threading.Event): The multi-thread event that fires to start shutting down the application gracefully
    """

    event_loop: asyncio.AbstractEventLoop

    probe_mode: str = "field"

    sensor_reading_thread: threading.Thread | None = None
    filewriting_thread: threading.Thread | None = None
    database_backup_thread: threading.Thread | None = None
    server_live_update_thread: threading.Thread | None = None

    session_active: bool = False
    session_id: str = ""

    server_connected: bool = False
    server_update: asyncio.Event = asyncio.Event()

    laptop_connected: bool = False
    laptop_update: asyncio.Event = asyncio.Event()

    latest_reading: ProbeData | None = None
    thread_shutdown: threading.Event = threading.Event()

    event_bus: EventBus = EventBus()


loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
asyncio.set_event_loop(loop=loop)
CurrentContext: AppContext = AppContext(event_loop=loop)
