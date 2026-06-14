from queue import Queue
import threading
from dataclasses import dataclass
import asyncio
from models.probe_data import ProbeData


class EventQueue:
    """
    Custom Pub/Sub implementation

    Attributes:
        event_loop (asyncio.AbstractEventLoop): The running asyncio loop to be used throughout the application

        server_connected (bool): Is the backup server connected?
        server_update: (asyncio.Event): Event that fires whenever a reading is taken for the server to update

        laptop_connected (bool): Is the local laptop connected?
        server_update: (asyncio.Event): Event that fires whenever a reading is taken for the laptop to update

        latest_reading (ProbeData): The most recent reading from the probe, None if none has been taken yet
        thread_shutdown (threading.Event): The multi-thread event that fires to start shutting down the application gracefully

    Methods:

    """

    def __init__(self) -> None:
        self.subscribers: dict[str, list[Queue]] = {}

    def subscribe(self, event: str):
        queue: Queue = Queue()
        self.subscribers.setdefault(event, []).append(queue)
        return queue

    def publish(self, event: str, data):
        for subscriber in self.subscribers.get(event, []):
            subscriber.put(data)

    def unsubscribe(self, event: str, queue: Queue):
        if event not in self.subscribers:
            return

        try:
            self.subscribers[event].remove(queue)
        except ValueError:
            pass


@dataclass(slots=True)
class AppContext:
    """
    Class for the applications running context

    Attributes:
        event_loop (asyncio.AbstractEventLoop): The running asyncio loop to be used throughout the application

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

    event_bus: EventQueue = EventQueue()


loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
asyncio.set_event_loop(loop=loop)
CurrentContext: AppContext = AppContext(event_loop=loop)
